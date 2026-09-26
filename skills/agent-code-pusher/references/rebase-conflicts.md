# Handling Rebase Conflicts

`push-to-pr` runs `git rebase origin/main` before pushing. If that rebase hits conflicts, it stops mid-rebase and exits non-zero — resolve before retrying:

1. Look at the conflicting files (`git status`) and fix them in place, same as any merge conflict.
2. Stage the resolved files (`git add <file>...`) and continue: `git rebase --continue`. Repeat if more commits conflict.
3. Once the rebase finishes cleanly, re-run `push-to-pr`.
4. If the conflicts aren't resolvable from within the worktree (e.g. main moved in a way that invalidates the approach), bail out with `~/.claude/skills/agent-code-pusher/rebase-abort` rather than leaving the worktree mid-rebase, then reassess — don't force-push through an unresolved conflict.
