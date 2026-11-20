# Refresh YouTube cookies

Use this procedure when asked to refresh, renew or update Transcript's YouTube cookies or login. The request authorizes renewal within the available tool permissions.

The session lives in the age-encrypted fnox entry `YOUTUBE_COOKIES_TXT`, with `as_file = true`. Renewal in the fleet uses the `pascalandy/dotfiles` store. See `docs/operations/secrets.md` in that repository for the worktree and deployment procedure.

## 1. Check the current session

Run the free check from any machine with the deployed fnox entry.

```bash
just transcript-cli auth check
```

- A passing check needs no renewal
- If YouTube refuses the stored session or cannot confirm it, sign in again in the configured Helium profile and close its window before renewing
- For a network failure or rate limit, retry the check later

## 2. Configure the Mac that exports cookies

Create `~/.config/transcript/youtube-session.toml` on the Mac with the Helium profile. If `XDG_CONFIG_HOME` is set to an absolute directory, use `$XDG_CONFIG_HOME/transcript/youtube-session.toml`.

```toml
browser_data_dir = "/absolute/path/to/browser-data"
profile_name = "Automation profile"
keychain_service = "Example Safe Storage"
keychain_account = "example-account"
# user_agent = "ExampleBrowser/1.0"
```

- Set `browser_data_dir` to the Helium data directory that contains `Local State`. In the intended profile, open `chrome://version` and use the parent of its `Profile Path`. Absolute paths and paths starting with `~/` work. The selected profile's database may be at `Cookies` or `Network/Cookies`
- Set `profile_name` to that profile's displayed name. Use a dedicated profile for the YouTube account Transcript should use. After signing in, open `https://www.youtube.com/robots.txt` in that profile and close its window
- Set `keychain_service` and `keychain_account` to the service and account of the browser's generic password item in Keychain Access. The TOML file holds these identifiers only. Keychain supplies the password when the exporter runs. If prompted in the unlocked desktop session, choose `Always Allow`
- Set `user_agent` only to override the User-Agent of the YouTube login check. The default comes from the pinned yt-dlp release. A machine that only consumes the fnox session or uses `--cookies FILE` can run the check without a local TOML file

Keep the TOML file local. Keep the cookies in fnox and the browser encryption key in Keychain.

## 3. Prepare the dotfiles worktree and renew

On the source Mac, prepare a linked worktree of `pascalandy/dotfiles` as its `docs/operations/secrets.md` describes. Read its `AGENTS.md` first. Use the unlocked desktop terminal, with `just`, `uv`, `fnox` and `gh` available. If working remotely, run the command in the source Mac's authorized desktop session so Keychain can prompt.

From the skills checkout, preview the target store. The preview checks the worktree and can run before you configure the profile.

```bash
just transcript-auth-refresh --dotfiles-worktree <dotfiles-worktree> --dry-run
```

Run the same command without `--dry-run` once the local configuration is ready.

```bash
just transcript-auth-refresh --dotfiles-worktree <dotfiles-worktree>
```

With only the installed skill, run `uv run <skill_dir>/scripts/transcript.py auth refresh --dotfiles-worktree <dotfiles-worktree>` on the same Mac.

The command exports YouTube cookies into a private temporary file and checks that YouTube recognizes the session. After a successful check it writes to `dot_config/private_fnox/private_config.toml` in the worktree through `fnox set` with the age provider and stdin. It restores `as_file = true` if needed, verifies the write through `fnox exec`, and removes the temporary file. The answer supplies the changes and the next steps.

## 4. Land and verify the dotfiles change

1. Require exit `0` and `ok: true`. Use `git diff --stat` to confirm that only the fnox source file changed. Follow the dotfiles secret procedure if additional changes need review
2. Commit the source file, push, and open the PR using the commands in the answer. Run `just merge` from the worktree when authorized. The recipe deploys the updated store across the fleet
3. After deployment, run `just transcript-cli auth check` on each relevant machine. Report the merged PR and the check results. Once the fnox check passes, remove any plaintext export or target list left by an earlier managed-file setup

Keep cookie contents and Keychain passwords out of chat, logs and Git.
