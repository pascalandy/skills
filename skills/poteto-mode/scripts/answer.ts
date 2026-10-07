// Every entry point answers in one compact JSON line with `ok` first: a
// success on stdout, a failure as the last line of stderr with stdout empty.
// `ok` is true exactly when the exit code is 0.
export interface Io {
  readonly stdout: (value: string) => void;
  readonly stderr: (value: string) => void;
}

export const processIo: Io = {
  stdout: (value) => {
    process.stdout.write(value);
  },
  stderr: (value) => {
    process.stderr.write(value);
  },
};

export function answer(
  io: Io,
  code: number,
  fields: Readonly<Record<string, unknown>> = {}
): number {
  const body: Record<string, unknown> = { ok: code === 0, ...fields };
  body.ok = code === 0;
  (code === 0 ? io.stdout : io.stderr)(`${JSON.stringify(body)}\n`);
  return code;
}

export function answerSignals(): void {
  const signals = [
    ["SIGINT", 130, "interrupted"],
    ["SIGTERM", 143, "terminated"],
  ] as const;
  for (const [signal, code, word] of signals)
    process.on(signal, () =>
      process.exit(answer(processIo, code, { errors: [word] }))
    );
}
