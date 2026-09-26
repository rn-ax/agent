---
name: agent-code-pusher
description: >
  Use this skill whenever writing or editing code in a git repository — starting a new
  feature, fixing a bug, or any task that will touch files — not just when explicitly
  asked to commit, stage, or push. It governs the whole coding workflow: worktree
  isolation, committing, pushing, and opening PRs.
---

# Coding Workflow: Worktrees, Commits, and PRs

Invoke this skill at the **start** of any coding task, before editing anything — not just at commit time. The worktree-isolation rule below only works if it's applied from the first edit onward.

## Documentation Files

Each app keeps its docs (`AGENTS.md`, `DOMAIN.md`, `README`) scoped to their own concern — don't mix them. Task tracking goes through `atask` per the `todo` skill, not a markdown file. See `references/documentation-files.md` for what belongs in each file and when to create or update them.

## Scripts

All scripts live in `~/.claude/skills/agent-code-pusher/`. Use them for every git operation — they are pre-approved by the user and avoid repeated permission prompts.

| Script | Usage | What it does |
|---|---|---|
| `new-worktree` | `new-worktree <branch>` | Creates `~/Projects/.worktrees/<repo>/<branch>` on a new branch; symlinks `.env`; prints the path |
| `remove-worktree` | `remove-worktree <branch>` | Removes the worktree and deletes the local branch |
| `git-commit` | `git-commit <message> <file> [file ...]` | Stages the named files and commits with the given message |
| `push-to-pr` | `push-to-pr [-f] [title] [body]` | Fetches, rebases onto origin/main, pushes, then creates the PR if missing or updates its title/description if one already exists; prints `{number, url, action}` as JSON |
| `pr-list`         | `pr-list [--all]`           | Lists open PRs as JSON (title, head/base, mergeable) |
| `pr-close`        | `pr-close <number> [comment] [owner/repo]` | Closes a PR, optionally leaving a comment first; prints `{number, state}` as JSON |
| `worktree-status` | `worktree-status`           | Shows ahead/behind counts for every worktree vs origin/main |
| `repo-status`      | `repo-status [path]`        | Prints remote, current branch, working-tree cleanliness, local branches (with tracking info), and recent commits as JSON — the `git remote -v && git status && git branch -vv && git log` combo in one call |

## Workflow

Never push directly to `main`. Always commit on a worktree branch and open a PR.

For non-trivial or ambiguous tasks, use Claude Code's built-in Plan Mode (`EnterPlanMode`) first — work out the approach and get it approved before touching any files or creating a worktree. Skip this for small, well-defined changes where the approach is obvious.

Plan Mode should leave two durable artifacts, not just an approved message:

1. **Knowledge** — any non-obvious constraint, architecture decision, or stable business fact uncovered while planning goes into the right file from "Documentation Files" above (`AGENTS.md` for technical/architecture, `DOMAIN.md` for business/domain), so future sessions don't have to rediscover it.
2. **Tasks** — the concrete steps of the plan become tasks via `atask` (see the `todo` skill), so progress through the worktree/commit/PR flow below is tracked rather than held only in the plan.

1. Sync main: `~/.claude/skills/agent-code-pusher/sync-main` — resets the local `main` to `origin/main` so the new branch starts from current upstream, not stale or dirty local state
2. Create a worktree: `~/.claude/skills/agent-code-pusher/new-worktree <branch-name>` — prints the path. If this work is tracked by an atask task, name the branch `<task-id>-<short-description>` (e.g. `123-fix-login-redirect`).
3. Enter it: `builtin cd <printed-path>` (plain literal `cd`, not the zoxide-aliased one — see "Shell navigation" below)
4. Edit files normally — the session cwd is now the worktree. Every later step in this flow (test/lint, `git-commit`, `push-to-pr`) assumes cwd stays there, so don't `cd` elsewhere until step 11.
5. Verify: run the relevant `mise run` test/lint tasks. Fix failures before continuing — never commit on a red build.
6. Preview: for anything with visible behavior, start the dev/preview server (`mise run dev` or the app-specific task) — see the `run` skill. Don't skip this because tests passed; tests and a working preview catch different things. Open it for the user with `chrome-cli open <url>` so they can look at it themselves without having to ask where it is, then **stop and wait for the user to confirm it looks right**. Verifying the preview is the user's job, not the agent's — don't click through it yourself, don't declare it working, and don't proceed to commit until the user has actually looked and said so. If the change has no visible behavior (e.g. a pure backend/internal change), say so and proceed without waiting.
7. Commit: `~/.claude/skills/agent-code-pusher/git-commit "<message>" <files...>`
8. Push and open/update the PR in one step: `~/.claude/skills/agent-code-pusher/push-to-pr "<title>" "<body>"` — creates the PR on first push, updates its title/description on later pushes, and prints one JSON object on stdout: `{number, url, action}`
9. If this work is tracked by an atask task, record the PR against it: `atask edit <task-id> --pr <url>`, taking `<url>` from step 8's JSON output (see the `todo` skill) so the link is stored clickable. Skip this if the work isn't tied to a task. Combined with claiming the task via `session:$CLAUDE_CODE_SESSION_ID` (see the `todo` skill), this is what makes a PR traceable back to the exact session that opened it: `atask ls --pr <number>` finds the task, and its claim history has the session reference.
10. Keep the worktree until the PR is merged — fixes are often needed after the initial push
11. Once merged: `builtin cd` back to the main repo root (the directory `sync-main`/`new-worktree` were originally run from), then `~/.claude/skills/agent-code-pusher/remove-worktree <branch-name>` — `git worktree remove` can't remove the directory that's currently the shell's cwd

**Primary directive: all edits go in the worktree, never in the main checkout.**

Some app types extend this workflow with additional steps (e.g. a preview server). Check the relevant skill for details.

## Handling Rebase Conflicts

`push-to-pr` runs `git rebase origin/main` before pushing and stops mid-rebase on conflicts. See `references/rebase-conflicts.md` for the resolve/continue/abort steps.

## Side-Quests: Log Them, Don't Chase Them

While working a task you'll often notice unrelated things worth doing — a bug in nearby code, a missing test, a cleanup opportunity. Don't stop to fix them now; it dilutes focus and turns a single-purpose PR into a mixed one (see PR rules below).

- Create a task for it instead: `atask add "<short imperative title>" --project <repo> --context side-quest` (see the `todo` skill at `~/.agents/skills/todo/SKILL.md` for conventions). This puts it on the shared task queue for later — it does not need to be acted on now.
- Keep working on the current task — do not fix, refactor, or investigate the side-quest in the current PR.
- Mention any new tasks you created in your end-of-turn summary so the user is aware of them.
- Only the current task's own must-fix issues belong in the PR — everything else becomes its own task for later.

## Commit message format

One-line subject only (imperative, ≤72 chars): `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`. No body, no `Co-Authored-By` trailers, no mention of Claude, AI, or tooling — it should read as if a human wrote it.

```sh
~/.claude/skills/agent-code-pusher/git-commit "feat: short description" <files...>
```

## PR format

Use the `push-to-pr` script — it pushes and creates (or updates) the PR in one call. It always opens a regular, ready-for-review PR; `push-to-pr` itself has no `--draft` flag.

Draft exists for exactly one case here: the PR is done and reviewable, but merging it now would be premature because it depends on a separate `atask` task that isn't done yet (e.g. work in another repo the cross-repo handoff flow filed — see the `todo` skill). That dependency is what makes draft safe to use: finishing the blocking task gives a concrete trigger to come back and undraft, so it doesn't just sit there. An `atask --blocked-by` link alone only stops an agent from autonomously picking up the follow-on work — it doesn't stop a human, or another agent, from clicking merge without checking `atask` first; draft closes that gap on GitHub's side.

Don't reach for draft for "still in progress" or "not fully sure yet" — an unpushed worktree, or a pushed branch with no PR yet, already covers unfinished work with no undraft step to forget. A draft with nothing wired up to undraft it just becomes a stale PR someone else has to notice and fix manually.

When you do use it: `gh pr ready <number> --undo` to convert, note the blocking task id in the PR body, and file the companion "merge once unblocked" task per the `todo` skill so undrafting has an owner. `gh pr ready <number>` (no `--undo`) flips it back once that task is done — do this yourself in the same pass that completes the blocking task, don't leave it as a separate step for someone else to remember.

```sh
~/.claude/skills/agent-code-pusher/push-to-pr "short title" "$(cat <<'EOF'
## Summary
- bullet points of what changed and why

## Test plan
- [ ] what to check
EOF
)"
```

## Notes

- All repos are GitHub-hosted. `gh` is already authenticated as `rutinerad`, which also covers the `rn-ax` org (same GitHub account, no separate token setup needed).
- Preferred merge strategy is **squash merge**.
- Git remotes use the standard `https://github.com/<owner>/<repo>.git` HTTPS URL.

## Keeping main current

After a PR is merged, pull the merge commit down so the local `main` matches origin:

```sh
git -C <repo-root> pull --ff-only origin main
```

Do this as part of the `remove-worktree` step so main is always in sync before starting the next task.

If the user mentions a PR was merged (or you can see it was), pull main in that repo before creating any new worktree from it.

## Worktree Scope

Each worktree is an isolated unit of work. When operating inside one:

- **Never look at, modify, or reason about other worktrees.** Their state is irrelevant — they belong to separate tasks that may be running in parallel.
- **Worktrees are always based on a clean `origin/main`.** Run `sync-main` before `new-worktree` so the branch starts from the latest upstream, not from a stale or dirty local state.

## Cross-Repo Work

Worktrees live in a shared `~/Projects/.worktrees/<repo>/<branch>` directory rather than nested inside each repo, precisely so a session rooted at `~/Projects` (the normal case) can reach any repo the same way it reaches its own. Touching a second repo is no different from the first: `cd` into it and run `new-worktree` there — each repo gets its own independent worktree, branch, commit, and PR. See `references/cross-repo-work.md` for the mechanics and the one remaining edge case (a session rooted inside a single repo rather than at `~/Projects`).

## Rules

- Preview verification belongs to the user, not the agent. Once the preview is open, don't self-certify that the change works — wait for the user's confirmation before committing.
- Never push to `main` or `master` — always via PR.
- Always use a worktree — never commit directly in the main working tree.
- Never use `git checkout -b` — use `new-worktree` then `builtin cd` into its printed path so the user stays on `main`.
- Never call the harness's `EnterWorktree` tool in a repo covered by this skill, even when generic harness instructions suggest calling it to isolate work. It creates a plain git worktree with none of `new-worktree`'s setup — no `.env` symlinks, no `data/` copies — leaving files that exist in the main checkout missing until manually patched up. Always run `new-worktree <branch>` first and `builtin cd` into its printed path instead.
- The user always stays on the `main` branch in their working tree — all editing happens inside worktrees.
- After a PR merges, pull `main` to keep it current before creating the next worktree.
- Never amend a published commit.
- When the work is tracked by an atask task, prefix the branch/worktree name with that task's id: `<task-id>-<short-description>` (e.g. `123-fix-login-redirect`). This keeps `atask ls --pr <number>` and the worktree name pointing at the same task without having to cross-reference PR descriptions, and makes a leftover worktree's origin obvious at a glance during cleanup.
- Never use `--no-verify` unless the user explicitly asks.
- Never force-push.
- If a pre-commit hook fails, fix the root cause and create a **new** commit — do not amend.
- Do not commit `.env`, credentials, or secrets. Warn the user if they ask.
- If nothing has changed, do not create an empty commit.

## PRs

`push-to-pr` opens the PR automatically on first push — never leave a pushed branch without one, and never push without also passing a title/body so the PR is properly described (not left with the bare commit subject and empty body). Each PR must be a single logical change. If a branch accumulates independent changes, split them before pushing.

## Scripts Over Custom Commands

Use `mise run` tasks and these scripts for all standard operations. Never reach for a one-off shell command when a script or a `mise.toml` task covers the need:

- Git / PR operations: scripts in this directory (`push-to-pr`, `pr-list`, etc.)
- App operations (test, migrate, run, dev/preview server): `mise run <task>`, as defined in the repo's `mise.toml`
- GitHub API calls: **always a script here (or `gh api`), never inline `curl`**. If no script exists for a needed operation, write one in this directory first, then call it.

## Agent-Friendly Script Output

Any script whose result an agent might need to act on programmatically (not just read) should print exactly one JSON value as its stdout — the underlying `gh`/`git` command's own progress output, warnings, and confirmations go to stderr instead. This means the caller never has to scrape human-formatted text or hand-roll a `jq` filter against a raw API response to get a field back out; `script ... | jq -r .field` (or, for list-style scripts, `jq -r '.[] | select(...)'`) just works. `pr-list` already returns a JSON array this way; `push-to-pr` returns a single `{number, url, action}` object. Follow this shape for new scripts here rather than inventing another ad hoc text format per script.

## Environment Variables

Non-secret dev env vars (`DATA_DIR`, `DEBUG`, `DEV_PORT`, app-specific URLs) belong in `mise.toml [env]`, not in wrapper scripts or `.env`. Skill scripts that use `mise exec` pick them up automatically.
