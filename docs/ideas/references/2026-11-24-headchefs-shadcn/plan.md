# Build dashboard components once and reuse them on refresh

Keep the dashboard from [PR #1275](https://github.com/pascalandy/skills/pull/1275) visually and behaviorally intact. Start with the five existing history period buttons. Contributors edit a shadcn/ui component and preview it with Vite. The publisher receives the same kind of standalone HTML it serves today.

`UI edit → pinned pnpm build → template.html`  
`T3 refresh → validated snapshot + prebuilt template → dashboard.html → existing publication receipt`

## How to read this

One box is one unit of work and names the evidence that closes it. Check a box only when its evidence exists. The implementation follows poteto-mode's `playbooks/refactoring.md`. The implementation owner maintains the [tracking issue](https://github.com/pascalandy/skills/issues/1278). This document records the reviewed starting plan.

**Implementation prompt.** Implement [#1278](https://github.com/pascalandy/skills/issues/1278) against the dashboard from #1275. Migrate the period buttons to shadcn/ui, preserve the existing appearance and single-file publication, and demonstrate an offline refresh without the UI toolchain.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Steps

| Step | Deliverable | Location | State |
| --- | --- | --- | --- |
| 1 of 1 | One component workflow and its reproducibly built runtime template | `pascalandy/skills`, implementation PR | Planned |

## Program checklist

### Arm the program

- [ ] Begin on the operator's implementation prompt. Record the baseline revision, implementation worktree and issue in a local `goal.md`. For a long-running session, send a status message at its 30-minute checkpoint.
- [ ] Read the repository instructions and `git show origin/main:authoring/poteto/poteto-mode/playbooks/refactoring.md` before editing. Record which revision supplies the dashboard.

### Spawn owners

- [ ] One owner delivers one implementation PR. If #1275 is open, branch from its current head and target its branch. If merged, branch from updated main and locate the landed files. Keep #1275 under its existing owner's control. Record its head before branching. After its squash merge, replay only the refactor commits onto updated main and retarget the implementation PR to main. Recheck the resulting head and verify its diff contains only this refactor.

### PR mechanics

- [ ] Put `Part of #1278 · Step 1 of 1` in the implementation PR. Record the base and head used for the comparisons below.

### Verdict and merge

- [ ] Collect the checks and browser evidence at the implementation head. Record the operator's UI parity verdict before the repository merge procedure.

### Boot recipe for verification

- [ ] From an isolated worktree run the dashboard recipes with explicit synthetic database and artifact paths. Keep the baseline and candidate previews in different temporary directories. Open each generated file in Chromium with external network requests blocked. For delivery tests, use a disposable loopback publisher, archive, config and receipt.

## Migrate the history period buttons (implementation PR)

**Depends on.** The generator and recipes introduced in #1275. Inspect the current [source package](https://github.com/pascalandy/skills/tree/82050f48b90d7d270537a9190b9b8a18f9df2685/authoring/andy/brigade-mode/scripts/replay/headchefs) before editing. Paths below are relative to that package unless otherwise specified.

**Files.**

- [ ] Move the human-edited template into a colocated `ui/` source directory. Include the Vite entry, TypeScript component, pinned pnpm lockfile, and local styles. Use the shadcn CLI to copy only the Button component and its required dependencies. Review and version the component source and required license notices.
- [ ] Keep `template.html` beside `snapshot.py` as a **committed build product**. Document the dev, build and regeneration commands in the package README. Keep installed dependencies, temporary build output and test snapshots out of the package.
- [ ] Make changes under `authoring/`. Run `just compile-skills` and `just remote-skills` to regenerate the distributed copy. Inspect the resulting diff and confirm the runtime template is included.

**Build.**

- [ ] Capture baseline previews using one synthetic snapshot for both versions. Include enough inactive entries for two pages and different period results. Apply the same capture time, theme, viewport and browser to both previews.
- [ ] Mount React only in the existing history control group. Render the same five buttons, French labels, default seven-day selection, group label, pressed state and focus behavior. Keep the theme selector and Gantt under their current owners. Match existing CSS tokens and scope any new styles to the control. Check that global resets do not restyle the page.
- [ ] Keep the archive filter state in one place. Replace the original period button listeners with one callback from the component. It sets the selected period, resets the page to zero, calls `renderArchive()` once and reflects the selected button. Remove the cached period-node list. Let keyboard focus stay on the activated button after rendering.
- [ ] Provide a local Vite preview that exercises the real component, page and archive with a **synthetic** snapshot. For release, build in production mode and explicitly inline the entry JavaScript, React runtime and CSS in the shell. Open the finished HTML directly from disk. Account for any Vite preload, imports, fonts, URLs and lazy chunks when checking that it is self-contained.
- [ ] Keep the existing snapshot marker on exactly one line. `render()` replaces it once and escapes literal less-than signs. `read_snapshot()` must read the prior HTML as well as the new HTML so manual waits and titles survive the first refresh. Preserve script initialization order and keep the marker outside the minified bundle.
- [ ] Run the UI build when component source or dependencies change. Add a reproducibility check to the contributor workflow that rebuilds the template from the lockfile and compares the bytes. Only build and refresh render the committed shell. Check parses an already generated HTML file. Status reads the local receipt. Retry resends the saved bytes for a pending attempt. All five operations run without the frontend toolchain. Preserve the artifact name, private target, bound URL, receipt and `html-publish` CLI interface. Leave SQL collection and scheduling to separate work.

**You see.**

- [ ] A contributor can edit the period control, preview it locally and regenerate one template. The installed dashboard generates a fresh standalone page from changed T3 data on a host with just the existing runtime tools.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Extend `../tests/test_headchefs_dashboard.py` or an adjacent focused fixture. Round-trip old and new snapshots with matching manual waits, a display title and text containing `</script>`. Confirm exactly one marker before render and one parseable snapshot afterward. Run `just check --only brigade-replay` and `just check`.
- [ ] Regenerate the template twice with the pinned toolchain and compare bytes. Compare embedded snapshot values against the baseline at the same clock. Inspect the generated skill for accidental dependencies, maps or scratch files.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten verification lanes at the PR head can share the same fixture and browser session. Keep evidence outside the repository.

- [ ] Lane 1. Regression lane against trunk. Compare the baseline dashboard from #1275 with the candidate at equal data and viewport. Save `overview.png`. Pass when layout, labels, bars and totals agree.
- [ ] Lane 2. Activate 7, 15, 30, 60 and 90 days. Save `periods.png`. Pass when the corresponding entries and pressed state match the baseline.
- [ ] Lane 3. Change periods from page two with an archive entry open. Save `archive-reset.png`. Pass when the first page appears and the old detail closes.
- [ ] Lane 4. Tab to a period and use Space and Enter. Save `keyboard.png`. Pass when selection changes once and focus remains visible on the activated control.
- [ ] Lane 5. Use touch at 390 px. Save `touch.png`. Pass when periods can be selected and a timeline bar still reveals its detail without page overflow.
- [ ] Lane 6. Exercise all six themes, including a theme selected by URL and one restored from storage. Save `themes.png`. Pass when the control and its focus ring follow the theme and the Gantt retains its colors.
- [ ] Lane 7. Seed the disposable publisher with annotated HTML from #1275 and its existing `dashboard-headchefs` receipt. Run the candidate's first `just refresh-headchefs` against that artifact and matching synthetic data. Save `annotations.png`. Pass when the receipt still points to the same URL, the old waits and manual display title survive, and `just check-headchefs --input` validates the delivered HTML.
- [ ] Lane 8. Open a generated page from disk with network blocked. Save `offline.png`. Pass when the controls and all populated lanes work and the browser attempts zero external requests.
- [ ] Lane 9. Run the normal `just build-headchefs`, `just check-headchefs`, `just refresh-headchefs` and `just status-headchefs` recipes against the isolated fixture with Node, Vite and pnpm unavailable. Also invoke the generated `skills/brigade-mode/scripts/replay/headchefs_dashboard.py` directly to build and check a separate preview from that fixture. Save `runtime.png` plus the command log. Pass when changed fixture data appears at the isolated receipt URL without regenerating the template.
- [ ] Lane 10. Interrupt delivery in the loopback fixture, change the input database, then run `just retry-headchefs` on the saved attempt with the UI toolchain unavailable. Save `retry.png` plus the receipt states. Pass when the accepted bytes match the pending attempt and its bound URL stays the same.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Record uncompressed standalone HTML bytes, the embedded snapshot bytes, build invocations per data refresh and elapsed time to an interactive period control.
- [ ] Probe. Alternate baseline and candidate on the same synthetic data and idle machine, with the same browser and cold page loads. Measure five pairs. Record the median and the fixture size.
- [ ] Baseline. Use the dashboard from #1275, or its landed equivalent, for both metrics. Run one UI build separately to document contributor cost.
- [ ] Rule. Fail if a refresh starts the UI toolchain (budget zero) or page interaction needs an external request (budget zero). Report shell growth and median timings for the operator's tradeoff decision. The refactor promises no measured speedup.

**Review gate.**

- [ ] Show the operator paired screenshots and a short video of a keyboard and touch selection. Record any accepted differences before landing the implementation.

**Merge.**

- [ ] Run the repository signoff on the reviewed implementation head. Merge with the repository recipe after the UI verdict. Record the merge SHA and proof in #1278.

## Close the program

- [ ] The implementation owner updates issue #1278 after a stack append or merge. Record an append as ready and a merge as merged. Close the issue only when the implementation and its evidence have landed.

## Appendix A. Prototype evidence

The baseline investigation exercised build and check on synthetic SQLite, offline mobile history selection and a real loopback publish/failure/retry cycle. These observations establish the comparison surface. The shadcn bundle, its byte cost and its parity with this template still need the implementation checks above.

## Appendix B. Alternatives rejected

A standard Vite `dist/` with relative assets is supported by html-publish. It would change the generator's publication input and require testing a multi-file load across revisions. The single-file option preserves the established receipt workflow and direct file preview. A full React rewrite would also move the Gantt without helping this first control.

## Appendix C. Risks

The minifier can rewrite the snapshot marker. Global CSS can affect the Gantt. A dev preview can hide an external chunk missing from the published file. The marker round trip, theme comparisons and offline browser run cover these risks. To roll back, revert the UI source, bundle and generated skill copy together and rebuild with the previous template. Handle pending delivery using the saved receipt before generating another capture.

## Appendix D. Links and reading list

[Dashboard source PR](https://github.com/pascalandy/skills/pull/1275) · [shadcn/ui and Vite](https://ui.shadcn.com/docs/installation/vite) · [Vite production build](https://vite.dev/guide/build) · [html-publish input and delivery contract](https://github.com/pascalandy/html-publish/blob/9943fb098b1b4c8f32a9ffc7f2fa9909f75e2a94/docs/contract.md)
