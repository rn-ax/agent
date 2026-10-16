# agent

Claude Code skills, kept here as the source of truth and symlinked into `~/.claude/skills`.

Do not create or use Git worktrees for this repository. Make changes directly in the primary checkout on a non-default branch. `~/.claude/skills/<name>` symlinks point at this checkout directly, so edits made in a separate worktree won't be reflected in the live skills a session actually loads until they're merged back into this checkout's `main`.

## Skills

A skill is the accumulated knowledge about one system or workflow: where it runs, how to reach it, how it behaves and how to operate it. It lives in `skills/<name>/`. `SKILL.md` has a frontmatter `name` (the directory name) and a `description` that starts "Use whenever…" and lists the situations that should load it, because the description is all an agent sees before loading. Scripts sit beside `SKILL.md`, executable and without an extension, each starting with a docstring that gives the usage, what it reads, what it writes and its exit codes.

A skill records durable, non-obvious facts: what took investigation to establish or what isn't visible where the reader will look. It describes how things work now and states a lesson as a fact plus how to apply it, without the story of when it was found. Credentials are named by 1Password item and field, never by value. The `repo-docs` skill has the full writing rules.

The sequence of a workflow lives in the skill text: the steps in order, which script performs each, what to check in its output, and what to do when a step fails. The agent composes the scripts and stays in control of the flow.

## Scripts

A script makes at most one write. Reading and validating are harmless, so a script reads as much as it needs, from as many interfaces as it needs, and checks everything before it changes anything. Each write is a point where something can go wrong and leave systems disagreeing, so a workflow with several writes is several commands, and the agent sees each result before it decides on the next. A write that an interface forces into several calls counts as one, and so does the same write repeated across independent targets, reported per target. Scratch files a script produces for its own use are outputs, not writes.

Every script builds a context object when it starts, adds each step to it as it works together with whatever the next step might need (ids, counts, paths of files produced, values the API returned), and prints it as one JSON document on stdout when it exits, on success and on failure alike. On failure the context carries an `error` that names the step that failed and the detail the interface returned, so it shows what was done and what state was left behind. The exit code is 0 for success, 1 for a failed operation and 2 for a usage error. Progress for a human goes to stderr.

A script that changes something validates its input first, takes explicit targets, offers `--dry-run`, is safe to run twice, and reads back what it wrote. Ids, files and flags come from arguments, with no prompts and no inferred targets. A script that could sweep a whole system takes a filter such as `--only`. A local state file is named in the docstring and gitignored. An API wrapper (`<system>-api <method> <path>`) adds authentication and the base URL and nothing else. An existing script that nearly fits is improved so every caller benefits.

`skills/writing-skills/SKILL.md` has the complete guide, including a skeleton of the context pattern.
