#!/usr/bin/env bun

import { resolve } from "node:path";
import { answer, answerSignals, processIo, type Io } from "../answer.ts";
import { ensureDependenciesInstalled } from "../bootstrap.ts";
import {
  UsageError,
  openStore,
  parseVerdict,
  type Store,
  type Verdict,
} from "./store.ts";

ensureDependenciesInstalled();
const {
  Command: CommanderCommand,
  CommanderError,
  InvalidArgumentError,
  Option,
} = await import("commander");
type Command = InstanceType<typeof CommanderCommand>;

interface GlobalOptions {
  readonly store?: string;
  readonly verbose: boolean;
  readonly force: boolean;
}

interface UnitAddOptions {
  readonly track: string;
  readonly brief?: string;
}

interface UnitSetOptions {
  readonly state: string;
  readonly branch?: string;
  readonly pr?: number;
  readonly sha?: string;
}

interface UnitListOptions {
  readonly state?: string;
  readonly track?: string;
}

interface LedgerRecordOptions {
  readonly evidence: string;
  readonly verifier?: string;
}

interface InboxPushOptions {
  readonly report?: string;
}

interface InboxDrainOptions {
  readonly peek: boolean;
}

interface GateParkOptions {
  readonly question: string;
  readonly options: string;
  readonly default: string;
}

interface GateResolveOptions {
  readonly answer: string;
}

interface FrontierSetOptions {
  readonly repo?: string;
  readonly prs?: readonly number[];
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function positiveInteger(value: string): number {
  const parsed = Number(value);
  if (!/^[1-9]\d*$/.test(value) || !Number.isSafeInteger(parsed)) {
    throw new InvalidArgumentError("must be a positive integer");
  }
  return parsed;
}

function prList(value: string): readonly number[] {
  const parts = value.split(",");
  if (parts.some((part) => part.length === 0)) {
    throw new InvalidArgumentError("requires a comma-separated PR list");
  }
  return parts.map(positiveInteger);
}

function storeDirectory(program: Command): string {
  const value = program.opts<GlobalOptions>().store;
  if (value === undefined || value.trim().length === 0) {
    throw new UsageError("set --store <dir> or ORCH_STORE");
  }
  return value;
}

function frontierRepo(options: FrontierSetOptions): string {
  const value = options.repo;
  if (value === undefined || value.trim().length === 0) {
    throw new UsageError("set --repo <dir> or ORCH_REPO");
  }
  return value;
}

async function runStore<T>(
  program: Command,
  io: Io,
  operation: (store: Store) => Promise<T>,
  fields: (
    result: T,
    directory: string
  ) => Readonly<Record<string, unknown>>
): Promise<void> {
  const options = program.opts<GlobalOptions>();
  const directory = storeDirectory(program);
  const note = (text: string): void => {
    if (options.verbose) io.stderr(`${text}\n`);
  };
  const store = openStore(directory, {
    force: options.force,
    onLockStolen: (holder) =>
      note(`stealing store lock held by pid ${holder}`),
    onStaleLock: (holder) =>
      note(`replacing stale store lock (pid ${holder} is dead)`),
  });
  let result: T;
  try {
    result = await operation(store);
  } finally {
    await store.close();
  }
  answer(io, 0, fields(result, directory));
}

function leaf(parent: Command, name: string, description: string): Command {
  return parent
    .command(name)
    .description(description)
    .allowExcessArguments(false);
}

function requireSubcommand(program: Command): never {
  storeDirectory(program);
  throw new UsageError("a valid command is required");
}

function createProgram(io: Io): Command {
  const program = new CommanderCommand("orch")
    .description("Plain-file orchestrate bookkeeping")
    .usage("[--store <dir>] [--force] [-v] <command>")
    .addHelpText(
      "after",
      '\nEach command answers one JSON line: {"ok":true,...} on stdout, or\n{"ok":false,"errors":[...]} as the last line of stderr.\n\nExit codes:\n  0    success\n  1    failure, a missing unit, gate, or ledger row included\n  2    usage error\n  130  interrupted'
    )
    .configureOutput({
      writeOut: io.stdout,
      writeErr: io.stderr,
      outputError: () => {},
    })
    .exitOverride()
    .allowExcessArguments(false)
    .addOption(
      new Option("--store <dir>", "store directory (or ORCH_STORE)").env(
        "ORCH_STORE"
      )
    )
    .option("--force", "steal an existing store lock", false)
    .option("-v, --verbose", "report lock recovery on stderr", false);

  leaf(program, "init", "initialize the store").action(() =>
    runStore(
      program,
      io,
      (store) => store.init(),
      (result) => result
    )
  );

  const unit = program
    .command("unit")
    .description("manage work units")
    .action(() => requireSubcommand(program));
  leaf(unit, "add <id>", "add a unit")
    .requiredOption("--track <track>", "unit track")
    .option("--brief <path>", "brief path")
    .action((id: string, options: UnitAddOptions) =>
      runStore(
        program,
        io,
        (store) =>
          store.units.add({
            id,
            track: options.track,
            brief: options.brief,
          }),
        (unit) => ({ unit })
      )
    );
  leaf(unit, "set <id>", "update a unit")
    .requiredOption("--state <state>", "unit state")
    .option("--branch <branch>", "branch name")
    .option("--pr <number>", "pull request number", positiveInteger)
    .option("--sha <sha>", "commit SHA")
    .action((id: string, options: UnitSetOptions) =>
      runStore(
        program,
        io,
        (store) =>
          store.units.set({
            id,
            state: options.state,
            branch: options.branch,
            pr: options.pr,
            sha: options.sha,
          }),
        (unit) => ({ unit })
      )
    );
  leaf(unit, "get <id>", "get a unit").action((id: string) =>
    runStore(
      program,
      io,
      (store) => store.units.get(id),
      (unit) => ({ unit })
    )
  );
  leaf(unit, "list", "list units")
    .option("--state <state>", "filter by state")
    .option("--track <track>", "filter by track")
    .action((options: UnitListOptions) =>
      runStore(
        program,
        io,
        (store) => store.units.list(options),
        (units) => ({ units })
      )
    );
  leaf(unit, "counts", "count units by state").action(() =>
    runStore(
      program,
      io,
      (store) => store.units.counts(),
      (counts) => ({ counts })
    )
  );

  const ledger = program
    .command("ledger")
    .description("manage verification records")
    .action(() => requireSubcommand(program));
  leaf(ledger, "record", "record a verification verdict")
    .argument("<pr>", "pull request number", positiveInteger)
    .argument("<sha>", "commit SHA")
    .argument("<verdict>", "verification verdict", parseVerdict)
    .requiredOption("--evidence <path>", "evidence path")
    .option("--verifier <name>", "verifier name")
    .action(
      (
        pr: number,
        sha: string,
        verdict: Verdict,
        options: LedgerRecordOptions
      ) =>
        runStore(
          program,
          io,
          (store) =>
            store.ledger.record({
              pr,
              sha,
              verdict,
              evidence: options.evidence,
              verifier: options.verifier,
            }),
          (row) => ({ row })
        )
    );
  leaf(ledger, "check", "check a verification verdict")
    .argument("<pr>", "pull request number", positiveInteger)
    .argument("<sha>", "commit SHA")
    .action((pr: number, sha: string) =>
      runStore(
        program,
        io,
        (store) => store.ledger.check({ pr, sha }),
        (row) => ({ row })
      )
    );
  leaf(ledger, "summary", "count verification verdicts").action(() =>
    runStore(
      program,
      io,
      (store) => store.ledger.summary(),
      (counts) => ({ counts })
    )
  );

  const inbox = program
    .command("inbox")
    .description("manage agent pointers")
    .action(() => requireSubcommand(program));
  leaf(inbox, "push <agent> <unit> <status>", "push an inbox pointer")
    .option("--report <path>", "report path")
    .action(
      (
        agent: string,
        unitId: string,
        status: string,
        options: InboxPushOptions
      ) =>
        runStore(
          program,
          io,
          (store) =>
            store.inbox.push({
              agent,
              unit: unitId,
              status,
              report: options.report,
            }),
          (result) => ({ pointer: result.pointer })
        )
    );
  leaf(inbox, "drain", "drain inbox pointers")
    .option("--peek", "read without draining", false)
    .action((options: InboxDrainOptions) =>
      runStore(
        program,
        io,
        (store) =>
          options.peek ? store.inbox.peek() : store.inbox.drain(),
        (pointers) => ({ pointers })
      )
    );
  leaf(inbox, "count", "count inbox pointers").action(() =>
    runStore(
      program,
      io,
      (store) => store.inbox.count(),
      (count) => ({ count })
    )
  );

  const gate = program
    .command("gate")
    .description("manage decision gates")
    .action(() => requireSubcommand(program));
  leaf(gate, "park <id>", "park a decision gate")
    .requiredOption("--question <question>", "gate question")
    .requiredOption("--options <options>", "gate options")
    .requiredOption("--default <answer>", "default answer")
    .action((id: string, options: GateParkOptions) =>
      runStore(
        program,
        io,
        (store) =>
          store.gates.park({
            id,
            question: options.question,
            options: options.options,
            defaultAnswer: options.default,
          }),
        (gate) => ({ gate })
      )
    );
  leaf(gate, "list", "list open decision gates").action(() =>
    runStore(
      program,
      io,
      (store) => store.gates.list(),
      (gates) => ({ gates })
    )
  );
  leaf(gate, "resolve <id>", "resolve a decision gate")
    .requiredOption("--answer <answer>", "chosen answer")
    .action((id: string, options: GateResolveOptions) =>
      runStore(
        program,
        io,
        (store) => store.gates.resolve({ id, answer: options.answer }),
        (gate) => ({ gate })
      )
    );

  const frontier = program
    .command("frontier")
    .description("manage the stack frontier")
    .action(() => requireSubcommand(program));
  leaf(frontier, "set", "discover a stack and set the frontier")
    .addOption(
      new Option(
        "--repo <dir>",
        "repository directory (or ORCH_REPO)"
      ).env("ORCH_REPO")
    )
    .option(
      "--prs <n,...>",
      "ordered GitHub PR chain, bottom-up",
      prList
    )
    .action((options: FrontierSetOptions) =>
      runStore(
        program,
        io,
        (store) =>
          store.frontier.set({
            repo: frontierRepo(options),
            prs: options.prs,
          }),
        (frontier) => ({ frontier })
      )
    );
  leaf(frontier, "show", "show the frontier").action(() =>
    runStore(
      program,
      io,
      (store) => store.frontier.show(),
      (frontier) => ({ frontier })
    )
  );

  leaf(program, "status", "render status.md and answer its summary").action(
    () =>
      runStore(
        program,
        io,
        (store) => store.status.render(),
        (report, directory) => ({
          file: resolve(directory, "status.md"),
          summary: report.summary,
          changed: report.changed,
        })
      )
  );

  const standing = program
    .command("standing")
    .description("manage standing orders")
    .action(() => requireSubcommand(program));
  leaf(standing, "show", "show standing orders").action(() =>
    runStore(
      program,
      io,
      (store) => store.standing.show(),
      (orders) => ({ orders })
    )
  );
  leaf(standing, "add <line>", "add a standing order").action((line: string) =>
    runStore(
      program,
      io,
      (store) => store.standing.add({ line }),
      (order) => ({ order })
    )
  );

  program.action(() => requireSubcommand(program));
  return program;
}

function handleError(error: unknown, io: Io): number {
  if (error instanceof CommanderError) {
    if (error.exitCode === 0) return 0;
    return answer(io, 2, {
      errors: [error.message.replace(/^error: /, "")],
      help: "orch --help",
    });
  }
  if (error instanceof UsageError)
    return answer(io, 2, { errors: [error.message], help: "orch --help" });
  return answer(io, 1, { errors: [message(error)] });
}

export async function main(
  argv: readonly string[],
  io: Io = processIo
): Promise<number> {
  const program = createProgram(io);
  try {
    await program.parseAsync(argv, { from: "user" });
    return 0;
  } catch (error) {
    return handleError(error, io);
  }
}

if (import.meta.main) {
  answerSignals();
  process.exitCode = await main(process.argv.slice(2));
}
