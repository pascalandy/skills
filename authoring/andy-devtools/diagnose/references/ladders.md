# Ladders

Each stack has a ladder of layers, from the cheapest to read (the report, logs) to the deepest (kernel tables). Start at layer 1, pair every reading with the same control, and descend one layer at a time, logging why. Stop at the strongest signal, not the deepest layer. A tool is a probe at a layer; save each probe's output under `artifacts/` before you read it.

## Cautions for every ladder

- **Capture before restart.** Restarting a stuck process destroys the evidence: take stacks, port tables, and open files first
- **Read-only in production.** Probes read; they never change config, restart, or inject code. A live hotfix or a debugger attach on a production or daily-driver surface needs Pascal's explicit authority
- **Mind the probe's cost.** A tracer on a hot path can slow the process it measures. Start with sampling and counts, and note the overhead in the fact's source
- **One host is a sample.** Read several failing instances and several control instances before trusting a reading
- **Pascal's machines.** Reach them through the `fleet` skill with read-only commands. They need no approval

## CLI, Pascal's main stack

Python and Bash tools run through `uv` on Linux and macOS, answering in one JSON line.

1. **The answer.** The JSON line, exit code, and stderr; `--debug` output; the version from `--version` or `git describe`
2. **Inputs.** Arguments, environment variables, config files, lockfiles, and the diff between the last good and first bad version
3. **Repro under a control.** The same command on the last good and first bad build, or with the suspected input flipped. Bisect only when the facts cannot narrow the range
4. **Process.** `strace -f -c` or `dtruss` for system calls, `py-spy dump` and `py-spy record` for Python stacks, `tracemalloc` for Python memory, `hyperfine` for timing, `lsof` for files and sockets
5. **Kernel.** `perf`, `bpftrace`, `dmesg`, the journal, and core dumps through the `diagnose-crash` skill

## Service

A server or client running across many hosts, often in containers.

1. **Detectors.** Alerts and dashboards, read as raw telemetry queries, not screenshots: rates, errors, latency percentiles per population
2. **Deploy and config.** Versions per host, flags on every side, manifests, and the rollout timeline
3. **Logs and traces.** Structured request logs and distributed traces, split by population
4. **Host network.** DNS lookups and their answers, TCP and TLS handshake times, connections per peer (a packet capture, `ss -ti`, resolver logs)
5. **Process.** Function call counts (`bpftrace` uprobes, `py-spy`), CPU profiles, GC pauses, thread dumps
6. **Kernel and cgroup.** CPU throttling in `cpu.stat`, memory pressure, run queues, `perf`

## Desktop

A daemon or app on macOS or Linux, often known only through user reports and diagnostic bundles.

1. **The report.** The user's words, screenshots, and the app's own error text, clustered by version and OS
2. **System log.** `log show --predicate` on macOS, `journalctl` on Linux, and crash reports
3. **Packets.** The app's connections in a packet capture: what flowed, and when it stopped
4. **Process state.** CPU time from `ps`, then `sample`, `spindump`, or `/proc/<pid>/stack`: is the thread spinning or waiting, and on what
5. **IPC and kernel objects.** Open files and sockets with `lsof`, a service's state with `launchctl print`; on Linux, `busctl monitor` and `/proc/<pid>/fd`

The OS's own diagnostic bundle holds most of these layers, captured at one moment.

## Web

A browser app and the services behind it.

1. **The report.** Screenshot, console errors, browser and version
2. **Network.** A HAR: requests, statuses, timings, cache headers
3. **Server side.** Logs and traces for the requests the HAR names
4. **Browser runtime.** Performance traces and heap snapshots, through poteto-mode's `trace-forensics` playbook, or a live session over the DevTools protocol through `runtime-forensics`
5. **Environment.** Browser flags, extensions, and profile. Use the same profile with one change as the control

## Mobile

An app on phones and tablets, with users spread across builds and OS versions.

1. **The report.** Store reviews, support tickets, and crash reports, clustered by build and OS before any comparison
2. **App logs.** `os_log` or `logcat`, and the analytics events of the failing session
3. **Network.** A proxy capture of the app's traffic, and the server logs for those requests
4. **Device state.** OS version, memory warnings, background state, thermal state
5. **Process.** Symbolicated crash stacks, then Instruments or Android Profiler traces
