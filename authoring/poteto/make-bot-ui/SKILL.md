---
name: "make-bot-ui"
description: "Use when building a custom UI that starts agent tasks through a webhook or local runner."
kind: "dev"
---

# Make a bot UI

Build a page whose buttons submit bounded jobs to a server. The server authenticates the request and starts an agent task. Keep credentials on the server. Read [agent runtime](../poteto-mode/references/agent-runtime.md) before selecting the runner.

## Select the runner

Discover the installed agent's supported automation interface. Inspect its CLI help or server API before writing the adapter. A chat interface alone is not a webhook receiver.

| Agent | Available integration to check |
| --- | --- |
| Codex | A server-owned `codex exec` process with JSON event output or a configured SDK integration |
| Claude Code | A server-owned `claude -p` process with structured output or Agent SDK integration |
| Pi | A supervised `pi --mode rpc` process, SDK session, or separate print-mode invocation |
| OpenCode | Its configured server/SDK session API, including asynchronous prompts where supported |

Use an existing authenticated webhook service if the user already has one. Read its actual URL, authentication scheme, request format, and success semantics. Otherwise implement the local server as the adapter to the selected runner. Record whether jobs start fresh sessions or resume a specific task session. Serialize requests to a shared session or checkout.

If no callable runner is available, prepare the UI and request contract, then report that starting agent jobs is blocked. Do not claim that a button can wake the current chat or survive a restart without a configured service that does so.

## Define the job contract

Name the allowed actions and their JSON fields. Validate input at the server boundary. Pass data separately from fixed task instructions and use process argument arrays or structured SDK calls, never a shell command assembled from request text.

Return a job ID when the server accepts work. Report queued, running, completed, or failed from the runner's actual events and exit status. An accepted HTTP request does not prove that the agent started or completed the task. Use an idempotency key if requests can be retried. Persist pending jobs only when recovery is required, and mark interrupted jobs explicitly after restart.

## Configure credentials

Use the environment's secret-entry facility when available. Otherwise ask the user to enter credentials directly into a server-side secret store or restricted local configuration file. Never request secret values in chat. Follow the repository's managed-file rules for configuration.

Keep provider credentials and upstream webhook keys out of browser code, responses, URLs, screenshots, and logs. Use the upstream service's documented authentication headers. Do not copy authentication headers from another provider.

## Serve the UI

Serve the page and job endpoints from one origin. Keep the agent API behind this server. Authenticate job submission, enforce the allowed action list, and restrict browser origins. Set a short timeout for accepting a request and a separate job runtime limit. A slow agent must not hold a browser request open indefinitely.

Prefer a localhost listener behind an existing Tailscale proxy. If using a direct tailnet listener, bind to the node's Tailscale address and confirm the interface. Do not expose an unauthenticated agent API on all network interfaces.

Use an existing online Tailscale node. Inspect `tailscale status` and `tailscale ip -4`, then report the actual reachable URL. Follow the installed version's setup workflow if the node is not connected. Authentication belongs in the user's browser or secret-entry UI, not in chat. Do not install or reconfigure another node without need.

## Prove the complete path

Use a harmless allowed action. Click the real page, observe the accepted job ID, then inspect the runner's start event, completion event, and expected result. Verify that failed starts and malformed input produce useful errors. If recovery or retries are supported, prove that resubmission does not execute the same job twice.

Report the UI URL, selected runner, where job status is visible, and what must remain running. A local server stops providing service when its host stops unless another configured host takes over.

Integration references: [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive), [Claude Code programmatic use](https://code.claude.com/docs/en/headless), [Pi RPC](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/rpc.md), [OpenCode server](https://opencode.ai/docs/server/).
