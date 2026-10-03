---
name: repo-docs
description: Use whenever writing or editing a repository's own documentation — README.md, AGENTS.md, CLAUDE.md, or the repo's description/topics on GitHub — for guidance on writing content that stays accurate as the project changes, rather than freezing a snapshot of today's feature set.
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

A repo's own README/AGENTS.md needs to make sense to someone who has nothing but the repo — "see the `foo` skill for X" or "see the `bar` repo's AGENTS.md for Y" means something to whoever's sitting in the exact private session that produced it, and nothing to anyone else who clones the repo, since they have no way to reach what's being pointed at. If a contributor genuinely needs a specific fact to work on the repo (a protocol detail, a required field), inline it. If it's not something contributing to *this* repo requires, drop the topic rather than citing where it lives. A real relationship between projects belongs in actual dependency management — a package dependency, a documented API — not a reference to a knowledge store the reader can't open.

## State the lesson, not the incident

An operational note ("use X, not Y", "this fails when...") should read as a fact plus how to apply it, never as a dated incident report. Drop `confirmed <date>: ...` framing, drop the narrative of what happened and when it was discovered, drop exact error text kept as evidence the claim is true — keep only the thing that's actually true now and what to do about it. A dated incident log is itself a snapshot: a future reader can't tell from "confirmed 2026-10-03" whether that's still current or three rewrites out of date, so the date doesn't even achieve the freshness-tracking it looks like it's for — it just adds narrative weight to parse before reaching the actual instruction. For example, "confirmed 2026-10-03, this machine's installed `wrangler` was `4.141.0` and `wrangler login`'s post-auth redirect landed on a dashboard route that version no longer serves (\"Page not found: /wrangler does not exist\") — `npx wrangler@latest login` avoids the mismatch entirely" becomes "Use `npx wrangler@latest`, not a locally-installed `wrangler` — an outdated version's login redirect can land on a dashboard route that no longer exists."

## One fact per paragraph or bullet

A paragraph or bullet should carry exactly one independently-true claim. When a sentence introduces a new claim rather than elaborating the one before it, give it its own paragraph or bullet instead of appending it with an em dash or "also" to whatever came first. A bundled paragraph has no seam to edit one fact without rereading (and risking disturbing) the others, and a reader skimming for one fact has to parse the whole block to find it. For example, a paragraph stating a workspace's id, a rule for resolving it that overrides the id, a separate fact about a second workspace existing, and an aside about an unrelated git-sync quirk is four facts — it should be four paragraphs (or a lead sentence plus three bullets), not one.

## No manual line wrapping within a paragraph

Write each paragraph as one continuous line and let the renderer/editor soft-wrap it for display — never insert a line break to hit a visual line-length target. A hard-wrapped paragraph turns a one-word edit into a multi-line diff, since changing an early word can reflow every line after it; a single unwrapped line keeps the diff to exactly the sentence that changed. This applies to every markdown file in a repo (README, AGENTS.md, CHANGELOG, docs/*) — line breaks are for actual structure (new paragraphs, list items, headings), not line length.
