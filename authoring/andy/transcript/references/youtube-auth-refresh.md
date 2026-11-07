# Refresh YouTube cookies

Use this procedure for requests to refresh, renew or update Transcript's YouTube cookies or login, including « rafraîchis le cookie pour Transcript » and « renouvelle la connexion YouTube de Transcript ». Treat the request as authorization to renew the session, within the available tool permissions. Handle these requests as authentication maintenance.

## 1. Locate the source Mac

Use the Mac with the signed-in Arc Default profile and the configured `~/.local/share/transcript/youtube-targets.txt`. Resolve its identity and skills checkout from available machine context or an installed fleet inventory. Confirm the source machine's identity before running commands. The consuming machine may be a different Mac or Linux computer.

The source Mac must be awake with its desktop session unlocked. When a skills checkout is available, confirm its `transcript-auth-refresh` recipe and the `just` and `uv` executables. Otherwise use the installed-only CLI fallback in step 3 for preview and renewal. Noninteractive SSH can omit Homebrew from PATH; use the verified executable paths or supply that PATH.

If Google requires reconnection, ask the user to sign in to YouTube in Arc on this Mac. Ask only for this necessary interaction or the unavailable machine access. The command creates the export itself; no cookie contents, Netscape export or export path need to be supplied by the user.

## 2. Preview the configured destinations

Run on the source Mac, replacing `<skills-checkout>` with its absolute checkout path:

```bash
just --justfile <skills-checkout>/justfile transcript-auth-refresh --dry-run
```

This reads the non-secret target list without opening cookies or Keychain. Confirm that the preview includes the source store and the intended fleet destinations. A missing target file means local renewal only. Configure that file once from the user's known SSH destinations if fleet distribution was requested; keep it outside Git. Use the configured targets on routine renewals.

## 3. Run Just in the desktop session

From a terminal in the source Mac's unlocked desktop session:

```bash
cd <skills-checkout>
just transcript-auth-refresh
```

This is the preferred command when the repository checkout is available. An installed-only environment without that justfile can run `uv run <skill_dir>/scripts/transcript.py auth refresh` on the same Mac.

### When working from another machine

Use an available, authorized desktop control to run the same Just command in the source Mac's logged-in session. Plain SSH can reach the Mac while Keychain refuses to decrypt Arc cookies. That refusal does not establish that the session is unavailable.

With macOS automation available over SSH, `osascript` can start the command in a new Terminal window. Use a new window owned by this operation, record its window ID and tab TTY, and capture stdout, stderr and the exit status in a private temporary directory. Wait for the command to finish before reading the captured result. Close only the recorded window after checking that its TTY still matches and the tab is no longer busy. Leave the user's existing windows untouched.

If no authorized desktop control is available, report that exact limitation and give the user the same Just command to run locally. Do not change Keychain permissions or browser security settings to work around the session boundary.

## 4. Verify renewal and distribution

Require exit `0` and an `ok: true` JSON answer. Check the reported `changes` against the preview so a local-only refresh cannot be mistaken for a fleet refresh. The command exports only YouTube domains, verifies login on the source and each receiver, and replaces private permanent files atomically. A partial failure reports successful changes and failed destinations; report both and retry only after resolving the stated access or network problem.

For an independent free login check, run in each relevant checkout:

```bash
just transcript-cli auth check
```

A network failure or HTTP rate limit is distinct from a signed-out session. Ask for Google reconnection only when the response requires it. Authentication maintenance never needs Deepgram, a summary model or a paid E2E run.

## 5. Report the result

Report which machines were updated or still need action. The permanent store is `~/.local/share/transcript/youtube.cookies.txt` in each user's home, with file permissions `0600` inside a `0700` directory. Future YouTube runs discover it automatically. Keep values out of chat, logs and Git. Google can invalidate the session at any time; no fixed renewal interval or automatic Google reconnection is promised.
