---
name: todo
description: >
  Use whenever tracking work items, side-quests, or a task queue across coding sessions or repos. Claude Code's built-in TaskCreate/TaskList panel is disabled in this environment — this is the replacement. Other skills (e.g. agent-code-pusher) refer here instead of duplicating the convention.
---

# Todo Tracking: atask

Task tracking in this environment goes through `atask` (`~/Projects/agent-tasks`, symlinked onto `PATH` as `atask`), not an in-app task panel. One shared SQLite database, tagged by repo/project, so tasks logged from any repo or any coding agent end up in the same queue.

Unlike a flat file, tasks have stable integer ids and support atomic claiming — so when multiple agents are picking work off the same queue, only one of them can actually claim a given task. See `~/Projects/agent-tasks/AGENTS.md` for the schema and full CLI reference.

## Setup

Data lives in `~/.config/agent-tasks/tasks.db`. Already initialized — nothing to set up before using it.

## Conventions

- **`--project` tag = repo name** — e.g. `--project monocoque`, `--project agent-tasks`. Use `--project personal` for anything not tied to a repo.
- **`--context` tag = sub-app, only inside a monorepo** — some repos (e.g. `monocoque`) hold multiple apps under `apps/<app>`; `--context` names which one a task belongs to (`--context stringbean`, `--context bookworm`), or `--context common` when a change spans several apps or touches shared/common code. Skip `--context` entirely for a repo that isn't a monorepo — `--project` alone already identifies it.
- Don't use `--context` (or any tag) to classify the *kind* of work — whether something is a feature, a bug, a followup, or a side-quest should already be obvious from the title text itself (e.g. "Fix ..." vs "Add ..."). A tag carrying that same information duplicates the title, drifts out of sync with it, and doesn't hold up as a real taxonomy — in practice it degrades into free-form labels (`@feature`, `@enhancement`, `@auth-phase2`, `@nutcracker-build`) that don't mean anything consistent across tasks. If a batch of tasks is genuinely one initiative and the grouping matters, use `--parent`/`child_of` (subtasks of one tracking task) rather than inventing a context label for it.
- One line of text per task, imperative and specific enough to act on without re-deriving context (same bar as a commit subject line). State only the action — the repo and sub-app already live in `--project`/`--context`, so leave them out of the title's text. Don't prefix the title with the repo or app name (e.g. `monocoque: fix login bug`) and don't work it into prose either (e.g. `In the bookworm app, fix login`) — write `atask add "Fix login bug" --project monocoque --context bookworm` instead. `atask ls` already groups/filters by these tags, so restating them in the title is pure redundancy, and it's the first thing to cut if a title is running long.
- **Titles (`text`) are capped at 80 characters** — put background, rationale, or "why deferred" in `--details` instead of running it all into one long sentence. If an existing task's title has grown too long, split it with `atask edit <id> --text "..." --details "..."` rather than leaving it as a run-on. Don't invent ad hoc bracket tags in the title either (e.g. `[Deferred]`) to encode state nobody's agreed the meaning of — the actual condition (e.g. "once there's enough data volume to make it useful") belongs in `--details`.

## Commands

| Action | Command |
|---|---|
| Add a task | `atask add "<task text>" --project <repo> [--context <sub-app>]` |
| Add with details | `atask add "<task text>" --details "<longer text>" ...` |
| Add already blocked | `atask add "<task text>" --blocked-by <id> ...` |
| Edit title/details later | `atask edit <id> --text "..." --details "..."` |
| Add/remove a dependency later | `atask edit <id> --blocked-by <blocker-id> ...` / `atask edit <id> --unblocked-by <blocker-id> ...` |
| Link a pull request | `atask edit <id> --pr <pr-url> ...` |
| List open tasks | `atask ls` |
| List for one project | `atask ls --project <repo>` |
| Get the next task | `atask ls --limit 1` |
| Claim a task | `atask claim <id> session:$CLAUDE_CODE_SESSION_ID` |
| Release a claim | `atask release <id>` |
| Complete a task | `atask done <id> [--resolution "..."]` |
| Full detail + claim history | `atask show <id>` |
| Find a task by PR number | `atask ls --pr <number> --status all` |
| Find a task by session id | `atask ls --reference session:<id> --status all` |

There's no dedicated `block`/`unblock`/`pr` command — `edit` is the one mutation path for everything about a task except the lifecycle transitions above (`claim`/`release`/`done`), which stay dedicated verbs because they're race-sensitive state changes, not plain attribute edits. Task ids are plain integers, assigned once at creation and never reused — reference one directly ("work on 42"), no lookup step needed.

## Dependencies (blocked/blocks)

A task can depend on another via `atask edit <id> --blocked-by <blocker-id>` — `<id>` can't be claimed until `<blocker-id>` is `done`; `atask claim` refuses loudly while an open blocker remains. `atask ls` shows each task's current open blockers; `atask show <id>` shows both directions (`blocked by` and `blocks`) regardless of status. Prefer this over writing "(depends on X)" into the title — same reasoning as `--details`: state belongs in a structured field, not prose in the title.

## Linking pull requests

Once a task's work is up for review, link the PR to it: `atask edit <id> --pr <pr-url>`, passing the full GitHub PR URL (`push-to-pr` prints it as the `url` field). `atask` stores it so `atask show` / `atask ls --json` can hand back a clickable link; a bare number is still accepted but records no URL. It's repeatable, so a task that goes through more than one PR (e.g. a rejected first attempt) keeps the full history rather than overwriting — `atask show <id>` lists every PR ever linked. See the `agent-code-pusher` skill for exactly when to do this in the push/PR flow.

### When a PR is only safe to merge after other work lands

Sometimes a PR is itself complete and reviewable, but merging it would be premature — e.g. it depends on a fix in another repo that hasn't shipped yet (the cross-repo case in `agent-code-pusher`'s handoff flow). `--blocked-by` on the original task only stops an agent from autonomously picking up follow-on work; it doesn't stop a human, or another agent, from just clicking merge on GitHub without checking `atask` first. Cover both:

1. File a task for the merge step itself — e.g. "Merge <PR>'s <thing> once <dependency> lands" — tagged `--pr <pr-url>` and `--blocked-by <the-real-blocker-id>`.
2. Also mark the PR itself as a GitHub-enforced block: see `agent-code-pusher`'s PR format section for converting it to draft with `gh pr ready --undo`. The blocking task is what makes this safe — it's a concrete signal to come back and undraft, not an open-ended "in progress" marker. Whoever completes the blocking task un-drafts the PR (`gh pr ready <number>`, no `--undo`) as part of that same pass, not as a separate step to remember later.

## Claiming, so agents don't collide

If you're picking work off the queue autonomously (rather than acting on a task the user pointed you at directly), claim it before starting:

```
atask claim <id> session:$CLAUDE_CODE_SESSION_ID
```

`atask claim` requires the reference to be a namespaced identifier (`<namespace>:<value>`) — `session:$CLAUDE_CODE_SESSION_ID` is the convention for a Claude Code session, and `$CLAUDE_CODE_SESSION_ID` is set in the environment of every session (interactive or background), so it's always available without extra lookup. Use it, not a plain agent name: it's what makes a claim (and, once linked, the PR that comes out of it) traceable back to the exact session that did the work — `atask ls --reference session:<id>` finds the task, and `~/.claude/projects/*/<id>.jsonl` is that session's transcript.

This fails loudly if someone already has it, or if the reference isn't namespaced. If you're just going to work the task yourself right now because the user asked for it directly, you don't need to claim it first — claiming matters when multiple agents might independently pull from the same queue.

If you start a claimed task and can't finish it (blocked, handing off, running out of turn), `atask release <id>` rather than leaving it claimed — `atask show <id>` prints the full claim history, so anyone can see a task was picked up and dropped.

## Finding a task from a PR or a session id

- **From a PR number**: `atask ls --pr <number> --status all` — a PR is normally linked to one task, so this is typically a single result.
- **From a session id** (yours, or one read out of a claim's reference): `atask ls --reference session:<id> --status all`. This matches the task's full claim history, not just an open claim, so it still works after the task is released or done.

Chained together, this is how a PR traces back to the session that opened it: `atask ls --pr <number>` → task id → `atask show <id>`'s claim history → the `session:<id>` reference on the claim that did the work → that session's transcript.

## Using this from a coding workflow

- **Side-quests** (noticed but out of scope for the current change): log instead of chasing — `atask add "<short imperative title>" --project <repo>`. Mention any newly logged items in the end-of-turn summary.
- **Before starting work in a repo**: `atask ls --project <repo>` to see what's already queued for it.
- **Plan Mode steps**: instead of `TaskCreate`, add each step as `atask add "<step>" --project <repo>`, and `atask done <id>` as each completes.
- **Rename the session after claiming a task**: right after `atask claim <id> session:$CLAUDE_CODE_SESSION_ID`, end your reply with a `<!--rename: TITLE -->` marker (e.g. `<!--rename: task 42: fix login bug -->`), using the claimed task's text as the title. A `UserPromptSubmit` hook (`~/.claude/hooks/rename-session.py`, registered in `~/.claude/settings.json`) scans your last reply for that marker and renames the session on the next message — see "Session renaming" below for why it can't happen sooner. Keeps the session list legible when several sessions are pulling off the shared queue at once. Skip this if you're just working a task the user pointed you at directly in an already-well-named session.

## Session renaming

Claude Code can only set a session's title from a `SessionStart` or `UserPromptSubmit` hook, not from a `Stop` hook — there's no supported way for the model to rename its own session mid-turn. The workaround (from https://github.com/anthropics/claude-code/issues/29355#issuecomment-4926999826): end a reply with `<!--rename: TITLE -->`, and a `UserPromptSubmit` hook that scans the previous assistant turn for that marker emits `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","sessionTitle":"TITLE"}}`, which the harness applies — landing one message late instead of instantly. That hook lives at `~/.claude/hooks/rename-session.py`, wired up globally in `~/.claude/settings.json`.

If a first-class rename mechanism ever ships (check that issue), retire this hook and the marker convention in favor of it.
