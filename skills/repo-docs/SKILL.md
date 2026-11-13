---
name: repo-docs
description: Use whenever writing or editing a repository's own documentation — README.md, AGENTS.md, DOMAIN.md, CLAUDE.md, code comments in configuration files, or the repo's description/topics on GitHub — for what each file holds, where an explanation belongs, and how to write content that stays accurate as the project changes, rather than freezing a snapshot of today's feature set.
---

# Repository documentation

Anything that summarizes a repo's current capabilities as an enumerated list — a README opener, an AGENTS.md summary, a GitHub repo description or its topics — goes stale the moment that list changes. "Does X, Y, and Z" is accurate right up until Z gets cut or a fourth feature ships, and nothing forces a future edit to catch up; it just quietly becomes wrong and sits that way, since nobody re-reads a repo description looking for drift.

State what the thing **is**, not a snapshot of what it currently does. "A Home Assistant integration for an Inteno/IOPSYS router" stays true for the life of the project; "for stats, connected devices, and reboot" is only true until the next feature is added or one gets dropped.

This applies anywhere a repo describes itself, not just prose docs:
- README/AGENTS.md opening summaries
- GitHub's own repo `description` field and `topics`
- Package manifests' `description` fields

The same reasoning extends to *any* documentation that describes desired behavior via contrast with a past or rejected alternative ("not X", "instead of Y") rather than stating the thing directly — that framing is tied to whatever came before and rots the same way once the codebase moves past it. State the current architecture/behavior on its own terms.

## Status doesn't belong in durable docs either

A "Project status" or "Current scope" section is the same rot pattern applied to progress instead of features — it's a snapshot of what's done/in-progress/planned *right now*, and it's wrong again the next time an issue closes or a new one opens. Worse than a stale feature list, because a tracker (GitHub Issues, a project board) already shows this live, natively, in its own UI — a section restating it in README/AGENTS.md isn't just liable to drift, it's redundant with something that can't drift by construction. Don't add the section, don't add a sentence pointing at the tracker either — GitHub already surfaces Issues on its own tab with no doc needed to find it. If a doc needs to say anything about scope, describe the problem the project solves (stable), not how much of solving it is currently done (constantly moving).

## Self-contained, not a pointer

A repo's own README/AGENTS.md needs to make sense to someone who has nothing but the repo — "see the `foo` skill for X" or "see the `bar` repo's AGENTS.md for Y" means something to whoever's sitting in the exact private session that produced it, and nothing to anyone else who clones the repo, since they have no way to reach what's being pointed at. If a contributor genuinely needs a fact that is specific to this repo (a protocol detail, a required field), state it. General knowledge of a framework or tool belongs in that tool's own documentation or skill. If it's not something contributing to *this* repo requires, drop the topic rather than citing where it lives. A real relationship between projects belongs in actual dependency management — a package dependency, a documented API — not a reference to a knowledge store the reader can't open.

## State the lesson, not the incident

An operational note ("use X, not Y", "this fails when...") should read as a fact plus how to apply it, never as a dated incident report. Drop `confirmed <date>: ...` framing, drop the narrative of what happened and when it was discovered, drop exact error text kept as evidence the claim is true — keep only the thing that's actually true now and what to do about it. A dated incident log is itself a snapshot: a future reader can't tell from "confirmed 2026-10-03" whether that's still current or three rewrites out of date, so the date doesn't even achieve the freshness-tracking it looks like it's for — it just adds narrative weight to parse before reaching the actual instruction. For example, "confirmed 2026-10-03, this machine's installed `wrangler` was `4.141.0` and `wrangler login`'s post-auth redirect landed on a dashboard route that version no longer serves (\"Page not found: /wrangler does not exist\") — `npx wrangler@latest login` avoids the mismatch entirely" becomes "Use `npx wrangler@latest`, not a locally-installed `wrangler` — an outdated version's login redirect can land on a dashboard route that no longer exists."

## What each file holds

Each app or repository keeps `AGENTS.md`, `DOMAIN.md` and the README scoped to their own concern, and the concerns stay separate. Task tracking (what is done, what is next) lives in GitHub issues per the `todo` skill.

### AGENTS.md

Technical and architecture conventions for coding agents: stack, patterns, gotchas, non-obvious constraints, and how the parts fit together. It is agent-agnostic, readable by any coding tool and not only Claude.

An `AGENTS.md` holds facts that are specific to its repository. Knowledge about a framework, tool or system that applies to any app built on it lives in that system's skill, where every app benefits from it.

The root `AGENTS.md` holds what applies across the whole repository: the stack, the workflow, and how the parts fit together. A convention that applies to one directory or component goes in a nested `AGENTS.md` in that directory (`backend/AGENTS.md`, `frontend/AGENTS.md`), which an agent reads when it works there.

An `AGENTS.md` records what the implementation does not show: a constraint, a gotcha, a reason that spans files. What a reader can see in the code, the configuration or the tests stays out, such as names, directory structure, values, task lists, where a file lives and behavior that a test pins down. A reason that belongs to one line is a comment on that line.

When an `AGENTS.md` grows, each fact either moves to the nested file of the component it concerns or is deleted because the implementation already says it.

### DOMAIN.md

Stable business knowledge: what the real-world concepts of the app mean and what must always hold about them. A repo that is developed spec-first has no `DOMAIN.md`: the meaning of its concepts is the `# Context` of its `spec/` files, and what must always hold is written there as acceptance criteria. A domain decision that lands mid-task is written into the spec file first, and the rest of this section applies to repos that keep a `DOMAIN.md`. It lives at the root of the app's directory (`apps/<app>/DOMAIN.md` in monocoque, the repository root elsewhere), changes rarely, and describes the problem, not the code or its implementation status.

A question like "can a Tab exist without a Song?" belongs here. A question like "which view handles tab upload?" belongs in the code or `AGENTS.md`.

Write it as plain prose under a single title, a few paragraphs covering what the core entities mean, how they relate and what must always hold about them. Use a heading or a list only when the content does not read as prose, such as a long enumeration.

Create or update it at these moments:
- **New app:** write it as part of the initial scaffold, alongside `AGENTS.md`.
- **Model or domain change:** update it in the same PR whenever a change alters what an entity means or what invariants hold, such as a new required relationship or a new type with business meaning. Pure refactors, renames and implementation-only changes leave it alone.
- **Missing on an existing app:** when a change touches the app's domain model and there is no `DOMAIN.md`, add one that captures the current business knowledge as part of that change.

When a domain decision lands mid-task (the user settles what an entity means, corrects an assumption, or draws a new boundary between concepts), write the decision into `DOMAIN.md` first and then implement against the updated document. Writing it down first catches an inconsistency, with an existing paragraph or with the decision as just stated, while it is still cheap to fix.

### README

Setup and usage instructions for people, when the project has one.

## A comment explains one setting; AGENTS.md explains how things fit

A comment in a configuration or code file explains one line or one setting: why it has this value, or what breaks when it changes. It stays on that line, so whoever edits the line sees the reason.

How components fit together (which role, host or file depends on which), procedures, conventions and failure modes that span files live in the repository's AGENTS.md, in the section for the system they belong to.

The test: if a comment needs a second file to make sense, it describes how things fit and belongs in AGENTS.md. A file or role header that restates AGENTS.md is deleted, and so is a comment that records what a setting used to be.

## One fact per paragraph or bullet

A paragraph or bullet should carry exactly one independently-true claim. When a sentence introduces a new claim rather than elaborating the one before it, give it its own paragraph or bullet instead of appending it with an em dash or "also" to whatever came first. A bundled paragraph has no seam to edit one fact without rereading (and risking disturbing) the others, and a reader skimming for one fact has to parse the whole block to find it. For example, a paragraph stating a workspace's id, a rule for resolving it that overrides the id, a separate fact about a second workspace existing, and an aside about an unrelated git-sync quirk is four facts — it should be four paragraphs (or a lead sentence plus three bullets), not one.

## Don't generalize a single instance into a universal fact

When compressing an observation about one specific thing into a durable lesson, keep the generalization's scope matched to what was actually established. A fact about one device, machine, or account doesn't become a fact about its whole category just because the surrounding incident narrative gets dropped — that's worse than keeping the narrative, since it launders a single observation into something a future reader will trust as settled. If the specific detail is worth keeping, give it its own header identifying the specific instance by a stable identifier (hardware MAC/model, hostname, account id) rather than folding it into general prose. If there's no such identifier to anchor it to, drop the specific detail entirely rather than smuggling it into the general claim.

## No manual line wrapping within a paragraph

Write each paragraph as one continuous line and let the renderer/editor soft-wrap it for display — never insert a line break to hit a visual line-length target. A hard-wrapped paragraph turns a one-word edit into a multi-line diff, since changing an early word can reflow every line after it; a single unwrapped line keeps the diff to exactly the sentence that changed. This applies to every markdown file in a repo (README, AGENTS.md, CHANGELOG, docs/*) — line breaks are for actual structure (new paragraphs, list items, headings), not line length.
