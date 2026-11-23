# Refresh the Head Chefs dashboard

From the skills checkout on the host with T3 and the existing private publication, run:

```sh
just refresh-headchefs
```

The command reads a consistent snapshot of the T3 database, checks the run intervals and time totals, and publishes at the URL bound to the existing `dashboard-headchefs` receipt. It prints the verified URL in `publication.url`. Reload that URL to see the new capture. The refresh runs with `uv`, SQLite, and the configured `html-publish` CLI.

## Build and check a preview

```sh
just build-headchefs
just check-headchefs
```

Open the path in the build result's `file` field to view the preview. To check another generated page, use `just check-headchefs --input PATH`. Run any recipe with `--help` for its path overrides and options.

## Recover a publication

Run `just status-headchefs` to read the local publication receipt. If a delivery is pending, run `just retry-headchefs`. It resumes with the saved bytes, even if T3 has recorded new activity. For a conflicting revision, follow `html-publish skills get recovery`.

## Source and state

`template.html` contains the dashboard interface. `snapshot.py` reads T3 and computes the intervals. The generated pages and the publication receipt stay in the local artifact directory listed by `just refresh-headchefs --help`. A refresh carries forward manual waits and their display title from the preceding local page when the chef and launch match.
