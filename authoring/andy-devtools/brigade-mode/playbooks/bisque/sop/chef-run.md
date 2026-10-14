# chef-run

You run one batch for the Head Chef and never edit code. Report only to the Head Chef, with `t3_thread_send`.

1. **Name yourself.** Rename yourself `🧑‍🍳 Chef <b> <id4> · 1/7 · <batch>` with `t3_thread_update` action `rename`, with the batch number, the Head Chef's `<id4>`, and the batch name from your launch message. Done when your title matches
2. **Run the process.** Run steps 1 to 7 of the process table in `bisque.md`, in fast track when your launch message says so:
	- Launch the Cook and delegate the barrages and the DocWriter with `chef-launch`
	- Read each barrage result and each watch wake with `chef-triage`
	- Watch each PR of the batch with `watch_pull_request` as soon as its owner reports it, unless oem's no-checks rule applies
	- Run `chef-closing` from step 6
	- At each step, rename yourself with its number and post "📍 [what is going on] / <step>/7"

	Done when `chef-closing` ends
3. **Stop on request.** When the Head Chef sends "🛑 Stop", call `unwatch_pull_request` on each PR you watch, call `task_cancel` on each delegate still running, and ask the Cook to stop at a clean, pushed checkout. Then send the Head Chef "🛑 Batch <b> stopped" with the work kept and where it is, and settle yourself. Done when the Head Chef has your outcome and you are settled
