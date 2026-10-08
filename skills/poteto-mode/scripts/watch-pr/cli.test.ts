import { describe, expect, it } from "bun:test";
import { chmod, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { type CliRuntime, main, parseArgs } from "./cli.ts";
import { fakeReader, passingCheck } from "./fakes.test-helper.ts";
import { WatcherQueryError } from "./github.ts";
import type { GitHubReader } from "./types.ts";

const silentIo = { stdout: () => {}, stderr: () => {} };
const WATCH_PR = join(import.meta.dir, "watch-pr");

function lastLine(text: string): unknown {
  return JSON.parse(text.trimEnd().split("\n").at(-1) ?? "");
}

interface FakeGhOptions {
  readonly authError?: boolean;
  readonly mergeable?: "MERGEABLE" | "CONFLICTING" | "UNKNOWN";
  readonly mergeStateStatus?: "CLEAN" | "BLOCKED" | "UNKNOWN";
  readonly statusOnly?: boolean;
}

async function runCliWithFakeGh(options: FakeGhOptions = {}): Promise<{
  readonly code: number;
  readonly stdout: string;
  readonly stderr: string;
  readonly calls: readonly string[];
}> {
  const directory = await mkdtemp(join(tmpdir(), "watch-pr-test-"));
  const bin = join(directory, "bin");
  const calls = join(directory, "gh-calls.txt");
  const facts = JSON.stringify({
    mergeable: options.mergeable ?? "MERGEABLE",
    mergeStateStatus: options.mergeStateStatus ?? "CLEAN",
    reviewDecision: "",
    headRefOid: "head",
    headRefName: "feature",
    baseRefName: "main",
    state: "OPEN",
    mergedAt: null,
    isDraft: false,
  });
  await mkdir(bin);
  const gh = join(bin, "gh");
  await writeFile(
    gh,
    `#!/usr/bin/env bash
set -euo pipefail
printf 'call\\n' >> "${calls}"
if [ "\${FAKE_GH_AUTH_ERROR:-0}" = 1 ]; then
  printf 'authentication failed\\n' >&2
  exit 1
fi
case "$*" in
  "pr view 121 --repo owner/repo --json mergeable,mergeStateStatus,reviewDecision,headRefOid,headRefName,baseRefName,state,mergedAt,isDraft")
    printf '%s\\n' '${facts}'
    ;;
  "pr checks 121 --repo owner/repo --json name,state,description,link,workflow,bucket")
    printf 'no checks reported\\n' >&2
    exit 1
    ;;
  *ReviewThreads*)
    printf '%s\\n' '{"data":{"repository":{"pullRequest":{"reviewThreads":{"nodes":[]}}}}}'
    ;;
  *PrCheckRollup*)
    printf '%s\\n' '{"data":{"repository":{"pullRequest":{"commits":{"nodes":[{"commit":{"statusCheckRollup":null}}]}}}}}'
    ;;
  *PrCommitStatuses*)
    printf '%s\\n' '{"data":{"repository":{"pullRequest":{"commits":{"nodes":[{"commit":{"oid":"head","statusCheckRollup":null}}]}}}}}'
    ;;
  *)
    printf 'unexpected gh arguments: %s\\n' "$*" >&2
    exit 2
    ;;
esac
`
  );
  await chmod(gh, 0o755);
  const args = [
    process.execPath,
    WATCH_PR,
    "--owner",
    "owner",
    "--repo",
    "repo",
    "--pr",
    "121",
    ...(options.statusOnly === false ? [] : ["--status-only"]),
    "--interval",
    "0.01",
    "--timeout",
    "0.001",
  ];
  const result = Bun.spawnSync(
    args,
    {
      env: {
        ...process.env,
        PATH: `${bin}:${process.env.PATH ?? ""}`,
        FAKE_GH_AUTH_ERROR: options.authError ? "1" : "0",
      },
    }
  );
  const output = {
    code: result.exitCode,
    stdout: result.stdout.toString(),
    stderr: result.stderr.toString(),
    calls: (await readFile(calls, "utf8")).trim().split("\n"),
  };
  await rm(directory, { recursive: true, force: true });
  return output;
}

function testRuntime(reader: GitHubReader): {
  readonly runtime: CliRuntime;
  readonly stdout: string[];
  readonly stderr: string[];
} {
  const stdout: string[] = [];
  const stderr: string[] = [];
  return {
    stdout,
    stderr,
    runtime: {
      reader,
      clock: {
        now: () => 0,
        observedAt: () => "2026-07-26T00:00:00.000Z",
        async sleep() {
          throw new Error("test unexpectedly slept");
        },
      },
      stdout: (value) => stdout.push(value),
      stderr: (value) => stderr.push(value),
    },
  };
}

describe("parseArgs", () => {
  it("uses the specified defaults", () => {
    expect(parseArgs([], silentIo)).toMatchObject({
      owner: null,
      repo: null,
      pr: null,
      mode: "single",
      stackPrs: [],
      statusOnly: false,
      polling: {
        interval: 60,
        sweepInterval: 300,
        timeout: 0,
        maxQueryErrors: 5,
        allowDraft: false,
      },
    });
  });

  it("parses a frozen queued stack bottom-to-top", () => {
    const parsed = parseArgs(
      [
        "--queued-stack",
        "--stack-prs",
        "#10, 11,#12",
        "--interval",
        "2.5",
        "--sweep-interval",
        "30",
        "--timeout",
        "0",
        "--max-query-errors",
        "3",
        "--allow-draft",
      ],
      silentIo
    );
    expect(parsed.mode).toBe("queued-stack");
    expect(parsed.stackPrs.map(Number)).toEqual([10, 11, 12]);
    expect(parsed.polling).toEqual({
      interval: 2.5,
      sweepInterval: 30,
      timeout: 0,
      maxQueryErrors: 3,
      allowDraft: true,
    });
  });

  it("rejects every invalid mode and numeric shape as usage", async () => {
    const invalid = [
      ["--unknown"],
      ["--sweep-interval", "-1"],
      ["--timeout", "-1"],
      ["--max-query-errors", "1.5"],
      ["--stack", "--queued-stack"],
      ["--stack-prs", "1,2"],
      ["--queued-stack", "--stack-prs", "1,1"],
    ];
    for (const argv of invalid) {
      const harness = testRuntime(fakeReader());
      expect(await main(argv, harness.runtime)).toBe(2);
      expect(harness.stdout).toEqual([]);
      expect(lastLine(harness.stderr.join(""))).toMatchObject({
        ok: false,
        help: "watch-pr --help",
      });
    }
  });
});

describe("main", () => {
  it("accepts an authoritative empty check set in one status-only pass", async () => {
    const result = await runCliWithFakeGh();
    expect(result.code).toBe(0);
    expect(result.stderr).toBe("");
    expect(JSON.parse(result.stdout)).toMatchObject({
      ok: true,
      verdict: {
        kind: "STATUS",
        rows: [
          {
            kind: "open",
            context: { owner: "owner", repo: "repo", number: 121 },
            threads: [],
            ci: { kind: "ci-clean" },
            facts: { mergeable: "MERGEABLE", isDraft: false },
          },
        ],
      },
    });
    expect(result.calls).toHaveLength(5);
  });

  it("fails a status-only authentication error without retrying", async () => {
    const result = await runCliWithFakeGh({ authError: true });
    expect(result.code).toBe(1);
    expect(result.stdout).toBe("");
    expect(result.stderr).not.toContain("RETRY");
    expect(lastLine(result.stderr)).toEqual({
      ok: false,
      errors: [
        "GitHub status query failed (1 in a row): authentication failed; check gh auth status and the PR number, then rerun watch-pr",
      ],
    });
    expect(result.calls).toHaveLength(1);
  });

  it("reports READY only for an affirmatively mergeable empty-check PR", async () => {
    const cases = [
      {
        mergeable: "MERGEABLE",
        mergeStateStatus: "CLEAN",
        verdict: { kind: "READY" },
      },
      {
        mergeable: "MERGEABLE",
        mergeStateStatus: "BLOCKED",
        verdict: { kind: "BLOCKER", blocker: { kind: "failing-checks" } },
      },
      {
        mergeable: "UNKNOWN",
        mergeStateStatus: "UNKNOWN",
        verdict: { kind: "BLOCKER", blocker: { kind: "failing-checks" } },
      },
    ] as const;
    for (const item of cases) {
      const result = await runCliWithFakeGh({
        mergeable: item.mergeable,
        mergeStateStatus: item.mergeStateStatus,
        statusOnly: false,
      });
      expect(result.code).toBe(0);
      expect(JSON.parse(result.stdout)).toMatchObject({
        ok: true,
        verdict: item.verdict,
      });
    }
  });

  it("answers a usage error on stderr with exit 2", async () => {
    const harness = testRuntime(fakeReader());
    expect(await main(["--interval", "0"], harness.runtime)).toBe(2);
    expect(harness.stdout).toEqual([]);
    expect(harness.stderr).toEqual([
      `${JSON.stringify({
        ok: false,
        errors: [
          "option '--interval <seconds>' argument '0' is invalid. must be greater than zero",
        ],
        help: "watch-pr --help",
      })}\n`,
    ]);
  });

  it("streams each poll to stderr and answers the verdict on stdout", async () => {
    const harness = testRuntime(fakeReader());
    const code = await main(
      ["--owner", "owner", "--repo", "repo", "--pr", "1", "--stack"],
      harness.runtime
    );
    expect(code).toBe(0);
    expect(harness.stderr).toHaveLength(1);
    expect(JSON.parse(harness.stderr[0])).toMatchObject({
      kind: "STATUS",
      terminal: false,
      reason: "poll",
    });
    expect(harness.stdout).toHaveLength(1);
    const answer = JSON.parse(harness.stdout[0]);
    expect(Object.keys(answer).sort()).toEqual(["ok", "verdict"]);
    expect(answer).toMatchObject({
      ok: true,
      verdict: { kind: "READY", terminal: true, scope: { kind: "stack" } },
    });
    expect(answer.verdict).not.toHaveProperty("exitCode");
  });

  it("fails when GitHub stays unreadable until the deadline", async () => {
    const detail = "HTTP 502\u2028\u2029";
    const harness = testRuntime({
      ...fakeReader(),
      async pullRequest() {
        throw new WatcherQueryError({
          kind: "command-exit",
          retryable: true,
          code: 1,
          detail,
        });
      },
    });
    let now = 0;
    const runtime = {
      ...harness.runtime,
      clock: { ...harness.runtime.clock, now: () => (now += 10) },
    };
    const code = await main(
      ["--owner", "owner", "--repo", "repo", "--pr", "1", "--timeout", "1"],
      runtime
    );
    expect(code).toBe(1);
    expect(harness.stdout).toEqual([]);
    expect(harness.stderr).toHaveLength(2);
    for (const line of harness.stderr)
      expect(line).not.toMatch(/[\u2028\u2029]/);
    expect(JSON.parse(harness.stderr[0])).toMatchObject({
      kind: "RETRY",
      consecutiveFailures: 1,
    });
    expect(JSON.parse(harness.stderr[1])).toEqual({
      ok: false,
      errors: [
        `GitHub status stayed unavailable until --timeout: ${detail}; check gh auth status and the PR number, then rerun watch-pr`,
      ],
    });
  });

  it("bypasses the queue machine for queued-stack status-only", async () => {
    const reader = fakeReader();
    const harness = testRuntime(reader);
    const code = await main(
      [
        "--owner",
        "owner",
        "--repo",
        "repo",
        "--queued-stack",
        "--stack-prs",
        "1",
        "--status-only",
      ],
      harness.runtime
    );
    expect(code).toBe(0);
    expect(harness.stdout).toHaveLength(1);
    expect(harness.stderr).toEqual([]);
    expect(JSON.parse(harness.stdout[0])).toMatchObject({
      ok: true,
      verdict: { kind: "STATUS", terminal: true, mode: "queued-stack" },
    });
    expect(harness.stdout[0]).not.toContain('"kind":"QUEUE"');
  });

  it("answers a hidden GitHub-side CI refusal as a blocker", async () => {
    const reader = fakeReader({
      facts: { mergeStateStatus: "BLOCKED" },
      fastPath: { kind: "checks", checks: [passingCheck()] },
      commitRollups: [{ oid: "head", state: "FAILURE" }],
    });
    const harness = testRuntime(reader);
    const code = await main(
      ["--owner", "owner", "--repo", "repo", "--pr", "1"],
      harness.runtime
    );
    expect(code).toBe(0);
    expect(harness.stdout).toHaveLength(1);
    expect(JSON.parse(harness.stdout[0])).toMatchObject({
      ok: true,
      verdict: {
        kind: "BLOCKER",
        blocker: {
          kind: "failing-checks",
          ci: { kind: "ci-github-rejected" },
        },
      },
    });
  });

  it("shows help without touching the reader", async () => {
    const reader = fakeReader();
    const harness = testRuntime(reader);
    expect(await main(["--help"], harness.runtime)).toBe(0);
    expect(harness.stdout.join("")).toContain("go to stderr as one JSON line");
    expect(harness.stderr).toEqual([]);
    expect(reader.calls).toEqual([]);
  });
});
