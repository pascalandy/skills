import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { answer, processIo } from "./answer.ts";

const scriptsDirectory = import.meta.dir;
const nodeModulesDirectory = join(scriptsDirectory, "node_modules");
const commanderPackagePath = join(
  nodeModulesDirectory,
  "commander",
  "package.json"
);
const installKeyPath = join(
  nodeModulesDirectory,
  ".poteto-mode-tools-install-key"
);

function currentInstallKey(): string {
  return createHash("sha256")
    .update(readFileSync(join(scriptsDirectory, "package.json")))
    .update("\0")
    .update(readFileSync(join(scriptsDirectory, "bun.lock")))
    .digest("hex");
}

function fail(message: string): never {
  process.exit(
    answer(processIo, 1, {
      errors: [
        `${message}; run: cd ${scriptsDirectory} && bun install --frozen-lockfile`,
      ],
    })
  );
}

export function ensureDependenciesInstalled(): void {
  try {
    install();
  } catch (error) {
    // A read-only scripts folder throws here; the answer stays one JSON line
    fail(
      `could not prepare the dependencies: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

function install(): void {
  const installKey = currentInstallKey();
  if (
    existsSync(commanderPackagePath) &&
    existsSync(installKeyPath) &&
    readFileSync(installKeyPath, "utf8").trim() === installKey
  ) {
    return;
  }

  const result = Bun.spawnSync(
    [process.execPath, "install", "--frozen-lockfile"],
    { cwd: scriptsDirectory }
  );
  if (result.exitCode !== 0) {
    processIo.stderr(result.stdout.toString());
    processIo.stderr(result.stderr.toString());
    fail(`bun install --frozen-lockfile exited with status ${result.exitCode}`);
  }
  if (!existsSync(commanderPackagePath)) {
    fail("bun install --frozen-lockfile completed without installing commander");
  }

  writeFileSync(installKeyPath, `${installKey}\n`);

  const restarted = Bun.spawnSync([process.execPath, ...process.argv.slice(1)], {
    cwd: process.cwd(),
    env: process.env,
    stdin: "inherit",
    stdout: "inherit",
    stderr: "inherit",
  });
  process.exit(restarted.exitCode ?? 1);
}
