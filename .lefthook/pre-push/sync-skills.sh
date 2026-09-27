#!/bin/sh
# lefthook skips a pre-push command when the push only deletes files, such as
# retiring a skill; it always runs a script, which reads git's refs on stdin.
exec just sync-hook pre-push
