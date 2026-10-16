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

A script makes at most one write. Reading and validating are harmless, so a script reads as much as it needs, from as many interfaces as it needs, and checks everything it can before it changes anything. Each write is a point where something can go wrong and leave a system half changed, so a workflow that needs several writes is several commands, and the agent composes them from the steps in the skill text and stays in control of the flow. Between two commands the agent sees the result of the first and decides what to do. Inside one script, a failure between two writes can leave the systems disagreeing with nothing to say so.

A write that an interface forces into several calls (create a record, then fill it in) counts as one write, and the script reports exactly which calls completed.

Within its one write a script handles the realistic scenarios itself: pagination, empty results, state that already exists, retries that are safe.

## Report context

Every script that does more than print one value builds a context object when it starts, fills it in as it works, and prints it as JSON when it exits, whether it succeeded or not.

- **At start** the context records the script name and its resolved inputs (ids, paths, URLs, flags, never secrets) and an empty list of steps.
- **While running** each completed action is added as soon as it is done, together with everything the next step might need: ids read or written, counts, the paths of files produced, values the API returned. Bulky data (text, images, page dumps) goes to a file and the context holds its path.
- **At exit** the context is printed to stdout as a single JSON document. On failure the same context carries an `error` (the step that failed, the exception type, the message, and any detail the interface returned), so it shows exactly what was done before the failure and what state was left behind. The exit code is 0 for success, 1 when the operation failed and 2 for a usage error.
- **Every path prints it.** Use `try`/`except`/`finally` in Python, `try`/`finally` in Node, or an `EXIT` trap in shell, so an unexpected exception cannot skip the report.

```python
import json, sys

ctx = {"script": "example", "args": {"id": 42}, "steps": []}
def step(name, **data): ctx["steps"].append({"step": name, **data})
code = 0
try:
    step("read", chars=1200)
    step("write", verified=True)
except Exception as e:
    ctx["error"] = {"step": ctx["steps"][-1]["step"] if ctx["steps"] else "start", "type": type(e).__name__, "message": str(e)}
    code = 1
finally:
    print(json.dumps(ctx, ensure_ascii=False))
sys.exit(code)
```

Progress for a human goes to stderr. Stdout holds only the context.

## Script rules

- **Writes are explicit and checked.** A script that changes something validates its input first (refusing anything empty or malformed), takes explicit targets, offers `--dry-run` or defaults to a report, is safe to run twice, and reads back what it wrote and records that in the context.
- **Inputs are explicit.** Ids, files and flags come from arguments or stdin, so the context of one script gives the next its inputs. There are no interactive prompts and no inferred targets.
- **Scope is what the arguments name.** A script that can sweep a whole system takes a filter such as `--only`, so one task never edits unrelated records.
- **Keep state minimal and visible.** If a script keeps a local file, the docstring names it, and it is gitignored when it belongs to one machine.
- **API wrappers stay thin.** `<system>-api <method> <path> [curl args]` adds authentication and the base URL and nothing else, so every request is an agent decision.
- **Reuse before writing.** Check for an existing script or skill first. When one nearly fits, improve it so every caller benefits.

## Flows

The sequence of a workflow lives in the skill text: the steps in order, which script performs each, what to look at in the context it prints, and what to do when a step fails. A new workflow starts as a list of steps in `SKILL.md`. A script is added for a single write (or a read) that is mechanical and repeated.
