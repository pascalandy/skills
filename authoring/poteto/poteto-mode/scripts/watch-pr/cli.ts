import { setTimeout as delay } from "node:timers/promises";
import {
  Command,
  CommanderError,
  InvalidArgumentError,
  Option,
} from "commander";
import { answer, oneLine, processIo } from "../answer.ts";
import {
  GhGitHubReader,
  WatcherQueryError,
  discoverStack,
  resolveContext,
} from "./github.ts";
import {
  runQueued,
  runSimple,
  statusQueryVerdict,
  verdictFactory,
  type WatchClock,
} from "./policy.ts";
import type * as T from "./types.ts";
import { nonEmpty, parsePrNumber } from "./types.ts";
export interface CliOptions {
  readonly owner: string | null;
  readonly repo: string | null;
  readonly pr: T.PrNumber | null;
  readonly mode: T.WatchMode;
  readonly stackPrs: readonly T.PrNumber[];
  readonly statusOnly: boolean;
  readonly polling: T.PollingOptions;
}
function positiveNumber(value: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0)
    throw new InvalidArgumentError("must be greater than zero");
  return parsed;
}
function nonNegativeNumber(value: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0)
    throw new InvalidArgumentError("must be zero or greater");
  return parsed;
}
function positiveInteger(value: string): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0)
    throw new InvalidArgumentError("must be a positive integer");
  return parsed;
}
function prNumber(value: string): T.PrNumber {
  try {
    return parsePrNumber(Number(value.replace(/^#/, "")));
  } catch {
    throw new InvalidArgumentError("must be a positive integer");
  }
}
function stackPrList(value: string): T.NonEmpty<T.PrNumber> {
  const numbers = value.split(",").map((part) => prNumber(part.trim()));
  if (new Set(numbers).size !== numbers.length)
    throw new InvalidArgumentError("contains a duplicate PR");
  const parsed = nonEmpty(numbers);
  if (parsed === null) throw new InvalidArgumentError("cannot be empty");
  return parsed;
}
interface RawOptions {
  readonly owner?: string;
  readonly repo?: string;
  readonly pr?: T.PrNumber;
  readonly stack: boolean;
  readonly queuedStack: boolean;
  readonly stackPrs?: T.NonEmpty<T.PrNumber>;
  readonly interval: number;
  readonly sweepInterval: number;
  readonly timeout: number;
  readonly maxQueryErrors: number;
  readonly statusOnly: boolean;
  readonly allowDraft: boolean;
}
export function parseArgs(
  argv: readonly string[],
  io: Pick<CliRuntime, "stdout" | "stderr">
): CliOptions {
  const program = new Command("watch-pr")
    .description(
      'Watch one pull request, a connected stack, or an immutable queued stack.\nProgress verdicts go to stderr as one JSON line; the run ends with\n{"ok":true,"verdict":{...}} on stdout.'
    )
    .addHelpText(
      "after",
      "\nExit codes:\n  0    answered a verdict, a blocker or a timeout included\n  1    GitHub could not be read, or the watcher failed\n  2    usage error\n  130  interrupted\n  143  terminated"
    )
    .configureOutput({
      writeOut: io.stdout,
      writeErr: io.stderr,
      outputError: () => {},
    })
    .exitOverride()
    .option("--owner <owner>", "GitHub repository owner")
    .option("--repo <repo>", "GitHub repository name")
    .option("--pr <number>", "pull request number", prNumber)
    .addOption(
      new Option("--stack", "watch the connected open stack")
        .default(false)
        .conflicts("queuedStack")
    )
    .option(
      "--queued-stack",
      "watch the captured stack until all PRs merge",
      false
    )
    .option(
      "--stack-prs <n,...>",
      "frozen bottom-to-top queue (queued mode only)",
      stackPrList
    )
    .option("--interval <seconds>", "poll interval", positiveNumber, 60)
    .option(
      "--sweep-interval <seconds>",
      "whole-stack sweep interval",
      positiveNumber,
      300
    )
    .option(
      "--timeout <seconds>",
      "deadline; 0 disables it",
      nonNegativeNumber,
      0
    )
    .option(
      "--max-query-errors <count>",
      "consecutive query-error budget",
      positiveInteger,
      5
    )
    .option("--status-only", "read the status once and answer it", false)
    .option("--allow-draft", "do not treat a draft as a merge gate", false);
  program.parse(argv, { from: "user" });
  const raw = program.opts<RawOptions>();
  if (raw.stackPrs !== undefined && !raw.queuedStack)
    program.error("--stack-prs requires --queued-stack");
  return {
    owner: raw.owner ?? null,
    repo: raw.repo ?? null,
    pr: raw.pr ?? null,
    mode: raw.queuedStack ? "queued-stack" : raw.stack ? "stack" : "single",
    stackPrs: raw.stackPrs ?? [],
    statusOnly: raw.statusOnly,
    polling: {
      interval: raw.interval,
      sweepInterval: raw.sweepInterval,
      timeout: raw.timeout,
      maxQueryErrors: raw.maxQueryErrors,
      allowDraft: raw.allowDraft,
    },
  };
}
export interface CliRuntime {
  readonly reader: T.GitHubReader;
  readonly clock: WatchClock;
  readonly stdout: (value: string) => void;
  readonly stderr: (value: string) => void;
}
function realRuntime(): CliRuntime {
  return {
    reader: new GhGitHubReader(),
    clock: {
      now: () => performance.now() / 1_000,
      observedAt: () => new Date().toISOString(),
      sleep: async (seconds) => {
        await delay(seconds * 1_000);
      },
    },
    ...processIo,
  };
}
function failure(verdict: T.TerminalVerdict): string | null {
  const retry = "check gh auth status and the PR number, then rerun watch-pr";
  if (verdict.kind === "BLOCKER" && verdict.blocker.kind === "status-query")
    return `GitHub status query failed (${verdict.blocker.failures} in a row): ${verdict.blocker.failure.detail}; ${retry}`;
  if (
    verdict.kind === "TIMEOUT" &&
    verdict.reason.kind === "status-unavailable"
  )
    return `GitHub status stayed unavailable until --timeout: ${verdict.reason.failure.detail}; ${retry}`;
  return null;
}
async function watch(
  options: CliOptions,
  runtime: CliRuntime
): Promise<T.TerminalVerdict> {
  const emit = (verdict: T.ProgressVerdict): void =>
    runtime.stderr(`${oneLine(verdict)}\n`);
  let contexts: T.NonEmpty<T.PrContext>;
  try {
    const seed = await resolveContext({
      reader: runtime.reader,
      owner: options.owner,
      repo: options.repo,
      pr: options.pr ?? options.stackPrs[0] ?? null,
    });
    contexts =
      nonEmpty(options.stackPrs.map((number) => ({ ...seed, number }))) ??
      (options.mode === "single"
        ? [seed]
        : await discoverStack(runtime.reader, seed));
  } catch (error) {
    if (!(error instanceof WatcherQueryError)) throw error;
    return statusQueryVerdict(
      verdictFactory(runtime.clock, options.mode),
      1,
      error.failure
    );
  }
  const dependencies = { reader: runtime.reader, clock: runtime.clock, emit };
  return options.mode === "queued-stack" && !options.statusOnly
    ? runQueued({ dependencies, contexts, options: options.polling })
    : runSimple({
        dependencies,
        contexts,
        mode: options.mode,
        statusOnly: options.statusOnly,
        options: options.polling,
      });
}
export async function main(
  argv: readonly string[],
  runtime: CliRuntime = realRuntime()
): Promise<number> {
  try {
    const verdict = await watch(parseArgs(argv, runtime), runtime);
    const error = failure(verdict);
    if (error !== null) return answer(runtime, 1, { errors: [error] });
    // The exit code says whether the watcher worked and the kind says what it
    // found, so the verdict keeps no exit code of its own
    const { exitCode: _exitCode, ...found } = verdict;
    return answer(runtime, 0, { verdict: found });
  } catch (error) {
    if (error instanceof CommanderError)
      return error.exitCode === 0
        ? 0
        : answer(runtime, 2, {
            errors: [error.message.replace(/^error: /, "")],
            help: "watch-pr --help",
          });
    return answer(runtime, 1, {
      errors: [error instanceof Error ? error.message : String(error)],
    });
  }
}
