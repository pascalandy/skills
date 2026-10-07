import { writeSync } from "node:fs";

// Every entry point answers in one compact JSON line with `ok` first: a
// success on stdout, a failure as the last line of stderr with stdout empty.
// `ok` is true exactly when the exit code is 0.
export interface Io {
  readonly stdout: (value: string) => void;
  readonly stderr: (value: string) => void;
}

function write(fd: number, value: string): void {
  const buffer = Buffer.from(value);
  let offset = 0;
  while (offset < buffer.length) {
    try {
      offset += writeSync(fd, buffer, offset);
    } catch (error) {
      if (
        !(error instanceof Error) ||
        !("code" in error) ||
        error.code !== "EAGAIN"
      )
        throw error;
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 1);
    }
  }
}

export const processIo: Io = {
  stdout: (value) => write(1, value),
  stderr: (value) => write(2, value),
};

// JSON.stringify leaves U+2028 and U+2029 raw, and a line reader such as
// Python's splitlines() breaks the answer on them
export function oneLine(value: unknown): string {
  return JSON.stringify(value).replace(/[\u2028\u2029]/g, (char) =>
    `\\u${char.charCodeAt(0).toString(16)}`
  );
}

export function answer(
  io: Io,
  code: number,
  fields: Readonly<Record<string, unknown>> = {}
): number {
  const body: Record<string, unknown> = { ok: code === 0, ...fields };
  body.ok = code === 0;
  (code === 0 ? io.stdout : io.stderr)(`${oneLine(body)}\n`);
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
