# Lead draft (written before reading the delegates)

Why v3 confuses: the verify loop is drawn as a step three times with three verbs (add to it at step 2, run it at step 5, strengthen it after retros), and its maintainer appears on one path but not on the retro path. A reader cannot tell what the loop is.

Fix: the verify loop is not a step. It is a resource beside the flow with exactly one writer and two readers.

- One writer: maintain-verification-skill. Every change to the loop goes through it
- Two readers: diagnose (how to read each layer, working cases, past readings) and the verify step (run, compare with the last good run)

One cycle, three kinds of request:

    request (feature | bug | retro issue)
      -> bug only: diagnose -> confirmed cause + the reading that found it
      -> change: code + loop update (maintain-verification-skill), one PR
      -> CI -> run the loop (delegate agent) -> barrages (interrogate) -> merge
      -> retros -> new issues -> back to "request"

A retro lesson about the loop is an issue, and an issue enters the cycle like any feature. So there is no retro -> loop shortcut, and the loop has one way in.
