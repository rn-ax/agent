---
name: writing-skills
description: Use whenever creating or editing a skill in rn-agent, meaning its SKILL.md, the scripts and API wrappers that live beside it, or anything under `skills/`. This is the guide for how skills are laid out, what belongs in them, and above all how their scripts are designed, so read it before adding a script or restructuring a skill.
---

# Writing skills

A skill is the accumulated knowledge about one system or workflow: where it runs, how to reach it, how it behaves, and how to operate it. It lives in `skills/<name>/` in this repo and is symlinked into `~/.claude/skills`. Scripts that operate the system live beside its `SKILL.md`.

## Layout

The directory name, the `name` in the frontmatter and the skill's trigger word are the same.

The `description` is all an agent sees before loading the skill, so it says when to use it: it starts with "Use whenever…", lists the situations, systems and phrases that should trigger it, and says what the skill holds.

`SKILL.md` is organised by system: where it runs and how to authenticate (name the 1Password item and its fields, never a value), how to talk to it, its conventions, procedures, and known failure modes. A "Related systems" line names the neighbouring skills.

Scripts are executable files without an extension, each starting with a docstring that gives the usage, what it reads, what it writes and what its exit codes mean.

## Content

Record durable, non-obvious facts: what took investigation to establish, or what isn't visible where the reader will look. A fact the tool already shows doesn't need a line.

Describe how things work now. State a lesson as a fact plus how to apply it, without the story of when it was found. The `repo-docs` skill has the full set of writing rules and they apply here.

## Scripts

A script performs one operation against one interface: one API, one system, or one file. An operation can have several internal steps when they belong together, such as writing a value and reading it back to confirm. A workflow that spans several operations or several interfaces is composed by the agent from the steps in the skill text. Every extra step and every extra interface adds error cases (a step that partly completed, an API that changed, a state the script didn't expect), and the number of cases that can go unhandled grows with each one. An unhandled case inside a script fails silently or leaves things half done, while the same case between two separate commands is visible to the agent, which can decide what to do.

- **Output drives the next step.** Print what the agent needs to proceed: the ids, paths, counts or JSON fields the next command takes as input. Normal output goes to stdout as one value (a JSON document, or one record per line), progress and diagnostics go to stderr.
- **Errors say what went wrong.** Exit non-zero and name the failing input, the cause, and the state left behind ("nothing was written" or "3 of 10 written, ids …"). Never swallow an error or fall back silently.
- **Writes are explicit and checked.** A script that changes something takes explicit targets, offers `--dry-run` or defaults to a report, is safe to run twice, reads back what it wrote and says so, and refuses input that is empty or malformed.
- **Inputs are explicit.** Ids, files and flags come from arguments or stdin, so the output of one script can feed the next. There are no interactive prompts and no inferred targets.
- **Scope is what the arguments name.** A script that can sweep a whole system takes a filter such as `--only`, so one task never edits unrelated records.
- **Keep state minimal and visible.** If a script keeps a local file, the docstring names it, and it is gitignored when it belongs to one machine.
- **API wrappers stay thin.** `<system>-api <method> <path> [curl args]` adds authentication and the base URL and nothing else, so every request is an agent decision.
- **Reuse before writing.** Check for an existing script or skill first. When one nearly fits, improve it so every caller benefits.

## Flows

The sequence of a workflow lives in the skill text: the steps in order, which script performs each, what to look at in its output, and what to do when a step fails. A new workflow starts as a list of steps in `SKILL.md`. A script is added for a single operation that is mechanical and repeated, and it stays within one interface.
