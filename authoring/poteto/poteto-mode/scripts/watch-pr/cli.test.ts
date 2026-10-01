import { describe, expect, it } from "bun:test";
import { chmod, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { type CliRuntime, main, parseArgs } from "./cli.ts";
import { fakeReader, passingCheck } from "./fakes.test-helper.ts";
import { renderJson, renderPretty } from "./render.ts";
import type { GitHubReader, WatcherVerdict } from "./types.ts";
import { parsePrNumber } from "./types.ts";

const silentIo = { stdout: () => {}, stderr: () => {} };
const WATCH_PR = join(import.meta.dir, "watch-pr");

interface FakeGhOptions {
  readonly authError?: boolean;
  readonly mergeable?: "MERGEABLE" | "CONFLICTING" | "UNKNOWN";
  readonly mergeStateStatus?: "CLEAN" | "BLOCKED" | "UNKNOWN";
  readonly statusOnly?: boolean;
}

async function runCliWithFakeGh(options: FakeGhOptions = {}): Promise<{
  readonly code: number;
  readonly stdout: string;
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
    "--pretty",
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
      pretty: false,
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
        "--pretty",
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
    expect(parsed.pretty).toBe(true);
  });

  it("rejects every invalid mode and numeric shape as usage", async () => {
    const invalid = [
      ["--unknown"],
      ["--interval", "0"],
      ["--sweep-interval", "-1"],
      ["--timeout", "-1"],
      ["--max-query-errors", "1.5"],
      ["--stack", "--queued-stack"],
      ["--stack-prs", "1,2"],
      ["--queued-stack", "--stack-prs", "1,1"],
    ];
    for (const argv of invalid) {
      const harness = testRuntime(fakeReader());
      expect(await main(argv, harness.runtime)).toBe(64);
      expect(harness.stdout).toEqual([]);
      expect(harness.stderr.join("")).toContain("error:");
    }
  });
});

describe("rendering", () => {
  const context = {
    owner: "owner",
    repo: "repo",
    number: parsePrNumber(1),
  };
  const status = {
    schemaVersion: 1,
    sequence: 1,
    observedAt: "2026-07-26T00:00:00.000Z",
    mode: "single",
    kind: "STATUS",
    terminal: true,
    exitCode: 0,
    reason: "status-only",
    rows: [
      {
        kind: "merged",
        context,
        facts: {
          context,
          mergeable: "MERGEABLE",
          mergeStateStatus: "CLEAN",
          reviewDecision: "APPROVED",
          headRefOid: "head",
          headRefName: "feature",
          baseRefName: "main",
          state: "MERGED",
          mergedAt: "now",
          isDraft: false,
        },
      },
    ],
  } satisfies WatcherVerdict;

  it("emits compact valid JSON by default", () => {
    const rendered = renderJson(status);
    expect(rendered.endsWith("\n")).toBe(true);
    expect(JSON.parse(rendered)).toEqual(status);
  });

  it("renders the Markdown table from the same verdict only", () => {
    const rendered = renderPretty(status);
    expect(rendered).toContain("| PR | CI | Review | Merge |");
    expect(rendered).toContain(
      "| [#1](https://github.com/owner/repo/pull/1) | \u2014 | \u2014 | ✅ merged |"
    );
  });
});

describe("main", () => {
  it("accepts an authoritative empty check set in one status-only pass", async () => {
    const result = await runCliWithFakeGh();
    expect(result.code).toBe(0);
    expect(result.stdout).toContain(
      "| [#121](https://github.com/owner/repo/pull/121) | ✅ | ✅ | ✅ |"
    );
    expect(result.stdout).not.toContain("RETRY");
    expect(result.calls).toHaveLength(5);
  });

  it("fails a status-only authentication error without retrying", async () => {
    const result = await runCliWithFakeGh({ authError: true });
    expect(result.code).toBe(7);
    expect(result.stdout).toContain("BLOCKER: status-query");
    expect(result.stdout).toContain("failures=1");
    expect(result.stdout).not.toContain("RETRY");
    expect(result.calls).toHaveLength(1);
  });

  it("reports READY only for an affirmatively mergeable empty-check PR", async () => {
    const cases = [
      {
        mergeable: "MERGEABLE",
        mergeStateStatus: "CLEAN",
        code: 0,
        output: "READY:",
      },
      {
        mergeable: "MERGEABLE",
        mergeStateStatus: "BLOCKED",
        code: 4,
        output: "BLOCKER: failing-checks",
      },
      {
        mergeable: "UNKNOWN",
        mergeStateStatus: "UNKNOWN",
        code: 4,
        output: "BLOCKER: failing-checks",
      },
    ] as const;
    for (const item of cases) {
      const result = await runCliWithFakeGh({
        mergeable: item.mergeable,
        mergeStateStatus: item.mergeStateStatus,
        statusOnly: false,
      });
      expect(result.code).toBe(item.code);
      expect(result.stdout).toContain(item.output);
    }
  });

  it("returns EX_USAGE 64 and writes usage errors only to stderr", async () => {
    const harness = testRuntime(fakeReader());
    expect(await main(["--interval", "0"], harness.runtime)).toBe(64);
    expect(harness.stdout).toEqual([]);
    expect(harness.stderr.join("")).toContain(
      "option '--interval <seconds>' argument '0' is invalid"
    );
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
    const verdict: unknown = JSON.parse(harness.stdout[0]);
    expect(verdict).toMatchObject({
      kind: "STATUS",
      terminal: true,
      exitCode: 0,
      mode: "queued-stack",
    });
    expect(harness.stdout[0]).not.toContain('"kind":"QUEUE"');
  });

  it("returns exit 4 for a hidden GitHub-side CI refusal", async () => {
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
    expect(code).toBe(4);
    expect(harness.stdout).toHaveLength(1);
    expect(JSON.parse(harness.stdout[0])).toMatchObject({
      kind: "BLOCKER",
      exitCode: 4,
      blocker: {
        kind: "failing-checks",
        ci: { kind: "ci-github-rejected" },
      },
    });
  });

  it("shows help without touching the reader", async () => {
    const reader = fakeReader();
    const harness = testRuntime(reader);
    expect(await main(["--help"], harness.runtime)).toBe(0);
    expect(harness.stdout.join("")).toContain("JSON (NDJSON while polling)");
    expect(reader.calls).toEqual([]);
  });
});
