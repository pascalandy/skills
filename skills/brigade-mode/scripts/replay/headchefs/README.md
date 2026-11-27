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

The active section includes open Head Chefs even between runs. A Head Chef stays open until T3 settles or archives the thread or its title marks it as finished or stopped. A run in progress in the brigade also keeps its Head Chef active. Active timelines extend to the capture time. Only the Head Chef's own runs count toward their active hours, on the HF line. The Cooks and QA lines add the active hours of every Cook or QA thread since launch, with overlapping runs of one thread counted once.
