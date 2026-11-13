---
name: spec-driven-dev
description: Use whenever a repo is developed so that Samuel and an agent write acceptance criteria together and agents implement everything after them (code, tests, CI, merging, deployment, rollback) with no human code or PR review — also for "agent-driven", "fully automatic", "no manual approval", "auto-merge", "acceptance criteria", or "spec-driven". Holds the method, the merge gate on GitHub Free, the pre-deploy backup, and how to run it alongside the superpowers plugin; it is the skill to iterate on as the method improves.
---

# Spec-driven development

Samuel and an agent identify the acceptance criteria together. Agents then implement everything those criteria require: code, tests, CI, merging, deployment and rollback. Nobody reviews code or pull requests, and the criteria and CI are what make that safe.

**Related systems**: `github` (org conventions, plan limits, secrets), `agent-code-pusher` (worktree and PR flow), `truenas` and `contabo-hosts` (where deploys and CI run).

## Roles

- **Samuel** takes part in writing the criteria, and sets the access the pipeline needs (secrets, variables, team access).
- **Agents** propose criteria for Samuel to correct, choose the implementation, and make sure every criterion holds. They may change workflows, tests and tooling as part of normal work.
- The repo's `AGENTS.md` records that no review step exists, so every session in it knows. A global rule that Samuel merges his own PRs gives way to that statement.

## Acceptance criteria

- A rule the software must satisfy is an acceptance criterion `AC-<n>`: one line that is compact, concise, independent of the others, and states behavior that can be checked. One that cannot be checked is a defect in the criterion.
- A criterion is immutable. It is deleted when it no longer applies and never edited; changing a rule means deleting the criterion and adding a new one with a new number. A deleted number is never reused.
- Criteria live in `spec/`. Each discrete functionality has its own file, `spec/<functionality>.md`, holding everything known about it. `spec/general.md` holds everything that is not large enough for a file of its own. When a part of `general.md` grows large enough, it moves into a new functionality file. A criterion may move between files.
- Each file is an [OKF](https://github.com/GoogleCloudPlatform/open-knowledge-format) concept file: markdown with YAML frontmatter (`type` is the one required key) and two sections, `# Context` above `# Criteria`. The frontmatter is how an agent finds the right file, so every value is on one line: `title`, a `description` that says what the functionality covers in the words someone would search for, and `tags` as an inline list of keywords. `rg -l 'tags:.*backup' spec` then lists the files about backups. The description and tags are kept current as the functionality changes.
- `# Context` holds why the functionality exists and what is out of scope, as it is now: it is edited when it changes, carries no dates and records no history. A choice is written down only when it stops someone taking a wrong turn; how a choice was reached stays in the pull request and git history.
- `# Criteria` is the list `- AC-<n>: <rule>`.
- A test relates to exactly one criterion and carries its `[AC-<n>]` in the title. A criterion can have several tests.
- Domain facts that explain what the app's concepts mean stay in the app's `DOMAIN.md`.

## Method

1. Find the files that apply: `rg -l` over the frontmatter in `spec/` (`tags:` and `description:` lines). Read their context and criteria before proposing anything.
2. Identify the criteria together: the agent proposes them in plain sentences, Samuel corrects, and the result is written to the functionality's file. A new functionality gets its own file when it is large enough, and `general.md` takes the rest. A rule that changes is deleted and added again under a new number.
3. Implement against the criteria. There is no separate implementation plan, because the criteria are the plan and the agent decides the files, names and structure. Each criterion gets its own tests, tagged with its ID; a test that checks two criteria is split.
4. Verify every criterion in CI before anything merges.

The spec changes first. Criteria are written and approved before the code that satisfies them, and a change to the method is made in this skill before any repo is changed to follow it.

Where other information lives: what the concepts mean in `DOMAIN.md`, technical constraints and non-obvious gotchas in `AGENTS.md`, why a choice was made and which approaches were rejected in the pull request description.

## Delivery

A repo that uses the method states its delivery rules as criteria in `spec/delivery.md`: pull requests merge themselves when CI passes, a merge to `main` deploys, every deploy is preceded by a database backup, and a faulty deploy is rolled back with that backup. The notes below are how that is built.

- CI runs the full suite on every branch push. A passing PR is squash-merged, and CI on `main` builds, tests and deploys the merged commit.
- On GitHub Free a private repo has no branch protection or rulesets, so the merge gate is workflow logic that nothing enforces against a direct push. A Team plan enforces it with required checks, native auto-merge and a merge queue; moving there changes where the gate lives and leaves the method alone.
- A merge made with `GITHUB_TOKEN` starts no workflows, except `workflow_dispatch` and `repository_dispatch`, so the follow-up run on `main` is started with `gh workflow run`.
- The running version makes the backup, so it holds the state from before the deploy. An app with a built-in backup API (PocketBase) uses it, since a plain copy of a SQLite file can tear while the app writes.
- Rollback discards the writes made after the deploy, which suits a single-user app and needs a different design for anything with many writers.

## Working with the superpowers plugin

The plugin's `brainstorming` and `writing-plans` skills default to dated design documents under `docs/superpowers/specs/` and implementation plans under `docs/superpowers/plans/`. This workflow takes precedence over those defaults:

- The design that brainstorming produces is the functionality's file in `spec/`, with its context and criteria. Approaches considered go in the pull request description.
- After Samuel approves the criteria, implementation starts directly, test-first per criterion. The `writing-plans` step is skipped.
- Criteria files and the repo's docs name no plugin; how the plugin is used lives only in this skill.

## Known weaknesses

- Agents may edit workflows, tests and screenshot baselines, so an agent can weaken its own gate. The criteria Samuel approves are the only fixed point.
