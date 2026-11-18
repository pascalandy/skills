# Refresh YouTube cookies

Use this procedure for requests to refresh, renew or update Transcript's YouTube cookies or login, including « rafraîchis le cookie pour Transcript » and « renouvelle la connexion YouTube de Transcript ». Treat the request as authorization to renew the session, within the available tool permissions. Handle these requests as authentication maintenance.

The session lives only in the fnox vault: the age-encrypted entry `YOUTUBE_COOKIES_TXT` of the `pascalandy/dotfiles` store, with `as_file = true`. No machine keeps a plaintext cookies file. Renewal therefore ends in a dotfiles PR that `just merge` lands, which updates every machine.

## 1. When to re-login in Helium

Check the session first, from any machine, with no paid call:

```bash
just transcript-cli auth check
```

- It succeeds: the session is valid. Renew nothing
- It reports that YouTube refused or did not confirm the session: Google signed it out or expired it. Re-login in Helium's `CLI` profile, then run the renewal below. No fixed interval applies; Google can invalidate the session at any time
- It reports a network failure or rate limit: retry later. That is not a signed-out session, so ask for no login

Re-login also applies when the export itself fails, or when the `CLI` profile does not exist yet. The `CLI` profile is used only by tools, so YouTube never rotates its cookies. Ask the user for one of these interactions only when a command requires it:

- **No `CLI` profile.** The user creates a Helium profile named `CLI` and signs in to YouTube there with the account Transcript should use. Then the user opens `https://www.youtube.com/robots.txt` and closes that profile's window
- **Google signed the session out.** The user signs in to YouTube again in the `CLI` profile, opens `robots.txt`, and closes the window
- **First Keychain prompt.** The user chooses `Always Allow` for `Helium Storage Key`

The command creates the export itself; the user supplies no cookie contents, Netscape export or export path.

## 2. Locate the source Mac and prepare the worktree

Use the Mac with Helium's `CLI` profile; resolve its identity and skills checkout from available machine context or an installed fleet inventory, and confirm it before running commands. It must be awake with its desktop session unlocked, and have `just`, `uv`, `fnox` (`~/.local/bin/fnox` when `PATH` lacks it) and `gh`. Noninteractive SSH can omit Homebrew from `PATH`; use the verified executable paths or supply that `PATH`.

Create a worktree of `pascalandy/dotfiles` from `origin/HEAD` on that Mac, as `docs/operations/secrets.md` of that repository describes under « Ajouter ou remplacer un secret ». Read its `AGENTS.md` first. Never write in the dotfiles clone.

Preview the write; it opens no cookies or Keychain:

```bash
just --justfile <skills-checkout>/justfile transcript-auth-refresh --dotfiles-worktree <dotfiles-worktree> --dry-run
```

## 3. Run Just in the desktop session

From a terminal in the source Mac's unlocked desktop session:

```bash
cd <skills-checkout>
just transcript-auth-refresh --dotfiles-worktree <dotfiles-worktree>
```

An installed-only environment without that justfile can run `uv run <skill_dir>/scripts/transcript.py auth refresh --dotfiles-worktree <dotfiles-worktree>` on the same Mac.

The command exports only YouTube domains from the `CLI` profile, verifies the login against YouTube, and only then runs `fnox set YOUTUBE_COOKIES_TXT --provider age --from-file /dev/stdin -c <dotfiles-worktree>/dot_config/private_fnox/private_config.toml`. It restores `as_file = true` on the entry when `fnox set` dropped it, and reads the value back through `fnox exec` to prove it matches the verified export. The export sits in a private temporary directory that is removed on exit; no plaintext file is left. A failure before the write leaves the worktree unchanged. Its answer lists the `changes` and the `next` steps.

### When working from another machine

Use an available, authorized desktop control to run the same Just command in the source Mac's logged-in session. Plain SSH can reach the Mac while Keychain refuses to release Helium's cookie key. That refusal does not establish that the session is unavailable.

With macOS automation available over SSH, `osascript` can start the command in a new Terminal window. Use a new window owned by this operation, record its window ID and tab TTY, and capture stdout, stderr and the exit status in a private temporary directory. Wait for the command to finish before reading the captured result. Close only the recorded window after checking that its TTY still matches and the tab is no longer busy. Leave the user's existing windows untouched.

If no authorized desktop control is available, report that exact limitation and give the user the same Just command to run locally. Do not change Keychain permissions or browser security settings to work around the session boundary.

## 4. Land the dotfiles PR

Require exit `0` and an `ok: true` JSON answer. Then, in the dotfiles worktree:

1. `git diff --stat` shows only `dot_config/private_fnox/private_config.toml`, with one encrypted value replaced. Anything else keeps its own review
2. Commit the file, push, and open the PR with `gh pr create`. Titles follow `chore(secrets): refresh the YouTube cookies ciphertext`
3. Run `just merge` from the worktree when you have the authority to merge. A diff that only replaces one encrypted value merges without a delegated review. The recipe merges the PR, then updates and applies the dotfiles clone on each machine. Leave Pascal no `git pull` or `chezmoi apply`

## 5. Verify and report

After the deploy, on each relevant machine:

```bash
just transcript-cli auth check
```

A passing check reads the vault and asks YouTube; it needs no Deepgram, summary model or paid E2E run. Report which machines pass or still need action, and name the merged dotfiles PR. Keep values out of chat, logs and Git. Once every machine passes, delete any leftover plaintext `~/.local/share/transcript/youtube.cookies.txt` from the earlier managed-file design; nothing reads it any more.
