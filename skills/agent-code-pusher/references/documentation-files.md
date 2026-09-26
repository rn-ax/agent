# Documentation Files

Each app keeps these docs scoped to their own concern — don't mix them. Task tracking (what's done, what's next) goes through `atask` per the `todo` skill (`~/.agents/skills/todo/SKILL.md`), not in a markdown file.

## AGENTS.md

Technical/architecture conventions for coding agents: stack, patterns, gotchas, non-obvious constraints. Agent-agnostic — readable by any coding tool, not just Claude.

## DOMAIN.md

Stable business knowledge: what the app's real-world concepts mean and what must always hold true about them, kept at `apps/<app>/DOMAIN.md`. It should rarely change; it describes the problem, not the code or its current implementation status.

A question like "can a Tab exist without a Song?" belongs here. A question like "which view handles tab upload?" belongs in the code or `AGENTS.md`.

Write it as plain prose under a single title, not a bullet-pointed spec sheet — a few paragraphs covering what the core entities mean, how they relate, and what must always hold true about them. Reach for a heading or a list only if the content genuinely doesn't read as prose (e.g. a long enumeration); don't default to one.

When to create or update it:

- **New app** — write it as part of the initial scaffold, alongside `AGENTS.md`.
- **Model/domain change** — update it in the same PR whenever a change alters what an entity means or what invariants hold (e.g. a new required relationship, a new type/category with business meaning). Don't update it for pure refactors, renames, or implementation-only changes that don't change the business meaning.
- **Missing on an existing app** — if you're touching an app's domain model and it has no `DOMAIN.md` yet, add one capturing the current-state business knowledge as part of that change.

When a domain decision lands mid-task — the user settles what an entity means, corrects an assumption, or draws a new boundary between concepts — write that decision into `DOMAIN.md` first, then implement against the updated document. Writing it down first is what catches an inconsistency (with an existing paragraph, or with the decision as just stated) while it's still cheap to fix, before code has been built on top of it.

## README

Setup/usage instructions, if present.
