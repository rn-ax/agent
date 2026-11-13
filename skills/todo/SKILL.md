---
name: todo
description: >
  Use whenever tracking work items, side-quests, or a task queue across coding sessions or repos. Claude Code's built-in TaskCreate/TaskList panel is disabled in this environment — GitHub issues are the replacement. Other skills (e.g. agent-code-pusher) refer here instead of duplicating the convention.
---

# Todo Tracking: GitHub issues

Work items live as GitHub issues, so any machine and any coding agent sees the same queue. Use `gh issue` for everything; the issue number is the stable id.

## Where an issue goes

- **A task about a repo goes in that repo's own issues** — `gh issue create -R rn-ax/<repo>`. The repo already says which project it belongs to, so the title carries only the action.
- **A task in a monorepo names its sub-app with a `app:<name>` label** (e.g. `app:bookworm`), or `app:common` when a change spans several apps or touches shared code. Skip it for a repo that isn't a monorepo.
- **A task not tied to a repo goes in `rn-ax/agent`.**
- Whether something is a feature, bug, followup, or side-quest is already obvious from the title ("Fix ..." vs "Add ..."), so a label repeating it just drifts out of sync. If a batch of issues is genuinely one initiative, make them sub-issues of one tracking issue.

## Writing an issue

- The title is one imperative line, specific enough to act on without re-deriving context (same bar as a commit subject), at most 80 characters, with the repo and sub-app left to where the issue lives.
- Background, rationale, and conditions such as "once there's enough data volume to make it useful" go in the body. State goes in GitHub's own fields (assignee, sub-issues, "blocked by" relationships), so the title stays free of tags like `[Deferred]`.
- For a handoff to a session rooted elsewhere, the body carries what that session needs to act without re-deriving the investigation: the target repo/app, relevant files (with line numbers), the concrete change, and any gotchas.

## Commands

| Action | Command |
|---|---|
| Add an issue | `gh issue create -R rn-ax/<repo> --title "<text>" --body "<details>"` |
| List open issues for a repo | `gh issue list -R rn-ax/<repo>` |
| List open issues you can work on, across repos | `gh search issues --owner rn-ax --state open --no-assignee` |
| Read one | `gh issue view <number> -R rn-ax/<repo>` |
| Edit title/body | `gh issue edit <number> -R rn-ax/<repo> --title "..." --body "..."` |
| Add a sub-issue or blocker | the issue's *Relationships* section on github.com, or `gh api` against the sub-issues / dependencies endpoints |
| Complete | `gh issue close <number> -R rn-ax/<repo> --comment "<resolution>"` |
| Find the issue a PR closes | `gh pr view <number> --json closingIssuesReferences` |

## Claiming, so agents don't collide

When you pick work off the queue autonomously (rather than acting on an issue the user pointed you at), claim it first by assigning yourself and commenting the session:

```
gh issue edit <number> -R rn-ax/<repo> --add-assignee @me
gh issue comment <number> -R rn-ax/<repo> --body "Claimed by session:$CLAUDE_CODE_SESSION_ID"
```

Check the assignee list before claiming; an issue that already has an assignee belongs to someone. `$CLAUDE_CODE_SESSION_ID` is set in every session's environment, and the comment is what traces a PR back to the exact session that did the work (`~/.claude/projects/*/<id>.jsonl` is that session's transcript). Working an issue the user asked for directly needs no claim.

If you start a claimed issue and can't finish it, unassign yourself (`--remove-assignee @me`) and comment why, so the history shows it was picked up and dropped.

## Linking pull requests

Put `Closes #<number>` (or `Closes rn-ax/<repo>#<number>` across repos) in the PR body. GitHub links the PR to the issue and closes the issue when the PR merges. A task that goes through several PRs keeps every link in its timeline.

### When a PR is only safe to merge after other work lands

Sometimes a PR is complete and reviewable, but merging it would be premature — e.g. it depends on a fix in another repo that hasn't shipped yet. Cover both sides:

1. File an issue for the merge step itself ("Merge <PR>'s <thing> once <dependency> lands"), referencing the PR, and mark it blocked by the real blocker issue.
2. Convert the PR to draft with `gh pr ready --undo` (see `agent-code-pusher`'s PR format section). Whoever completes the blocking issue un-drafts the PR (`gh pr ready <number>`) in that same pass.

## Using this from a coding workflow

- **Side-quests** (noticed but out of scope for the current change): log instead of chasing — `gh issue create -R rn-ax/<repo> --title "<short imperative title>"`. Mention any newly filed issues in the end-of-turn summary.
- **Before starting work in a repo**: `gh issue list -R rn-ax/<repo>` to see what's already queued for it.
- **Plan Mode steps**: add each step as an issue, and close each as it completes.
- **Rename the session after claiming an issue**: end your reply with a `<!--rename: TITLE -->` marker (e.g. `<!--rename: #42 fix login bug -->`), using the issue title. See "Session renaming" below.

## Session renaming

Claude Code can only set a session's title from a `SessionStart` or `UserPromptSubmit` hook, not from a `Stop` hook — there's no supported way for the model to rename its own session mid-turn. The workaround (from https://github.com/anthropics/claude-code/issues/29355#issuecomment-4926999826): end a reply with `<!--rename: TITLE -->`, and a `UserPromptSubmit` hook that scans the previous assistant turn for that marker emits `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","sessionTitle":"TITLE"}}`, which the harness applies — landing one message late instead of instantly. That hook lives at `~/.claude/hooks/rename-session.py`, wired up globally in `~/.claude/settings.json`.

If a first-class rename mechanism ever ships (check that issue), retire this hook and the marker convention in favor of it.
