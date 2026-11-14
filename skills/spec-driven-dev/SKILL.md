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
- `spec/` holds information specific to the repository. A convention that lives in a skill or in the repo's agent instructions is not an acceptance criterion and has no test of its own in each repo.
- Criteria live in `spec/`. Each discrete functionality has its own file, `spec/<functionality>.md`, holding everything known about it. `spec/general.md` exists only when it holds useful content that does not fit a functionality file, or that is not extensive enough to warrant one. When a part of it grows large enough, it moves into a new functionality file, and the file is deleted when nothing useful is left. A criterion may move between files.
- Each file is an [OKF](https://github.com/GoogleCloudPlatform/open-knowledge-format) concept file: markdown with YAML frontmatter (`type` is the one required key) and two sections, `# Context` above `# Criteria`. The frontmatter is how an agent finds the right file, so every value is on one line: `title`, a `description` that says what the functionality covers in the words someone would search for, and `tags` as an inline list of keywords. `rg -l 'tags:.*backup' spec` then lists the files about backups. The description and tags are kept current as the functionality changes.
- `# Context` holds why the functionality exists and what is out of scope, as it is now: it is edited when it changes, carries no dates and records no history. A choice is written down only when it stops someone taking a wrong turn; how a choice was reached stays in the pull request and git history.
- `# Criteria` is the list `- AC-<n>: <rule>`.
- A test relates to exactly one criterion and carries its `[AC-<n>]` in the title. A criterion can have several tests.
- What the app's concepts mean and what must always hold about them are written in the spec files: the meaning in `# Context`, the invariants as criteria. The repo has no `DOMAIN.md`.

## Method

1. Find the files that apply: `rg -l` over the frontmatter in `spec/` (`tags:` and `description:` lines). Read their context and criteria before proposing anything.
2. Identify the criteria together, one tightly scoped concept at a time. The agent picks the next concept, asks the user only the specific questions it needs to design it, and proposes that concept's criteria, a handful at most, in plain sentences. The user approves or corrects them as a multi-select of the criteria. Approved criteria are written to the functionality's file before the next concept is taken up. A new functionality gets its own file when it is large enough, and `general.md` takes the rest. A rule that changes is deleted and added again under a new number.
3. Implement against the criteria. There is no separate implementation plan, because the criteria are the plan and the agent decides the files, names and structure. Each criterion gets its own tests, tagged with its ID; a test that checks two criteria is split.
4. Verify every criterion in CI before anything merges.

The spec changes first. Criteria are written and approved before the code that satisfies them, and a change to the method is made in this skill before any repo is changed to follow it.

Where other information lives: what the concepts mean in the context of the spec files, facts specific to the repo (constraints and non-obvious gotchas) in `AGENTS.md`, why a choice was made and which approaches were rejected in the pull request description.

## Scenarios

A scenario is a specific thing the user wants to accomplish with the app, kept as an issue with the label `scenario`. Its body is the user's own account of it in their own words, with every detail given, and the issue is closed when the whole account is represented in the production app.

1. The user gives the scenario. The agent opens the `scenario` issue (creating the label when the repo has none) and keeps the text verbatim.
2. The agent breaks the scenario down into the concepts the app needs to represent it. Each concept is its own issue that starts with `Part of #<scenario>`, and a concept an existing issue already covers is linked and not opened again. The scenario's body lists them as a checklist, with the entry of the scenario's data in production as its last item.
3. Where a concept can be modelled in more than one way, its issue states the options and a recommendation, and the user decides in the issue before its criteria are written.
4. Each concept follows the method above: criteria first, then tests and code, then the merge and deploy. Concepts are delivered in the order that lets the most of the scenario be entered after each deploy.
5. After each deploy the user enters what the app can now represent. Whatever cannot yet be entered shows which concept comes next, and the checklist is updated as concepts land.
6. The scenario is closed when all of it is entered.

## Delivery

Every repo that uses the method satisfies these delivery rules. They belong to the method, so a repo's `spec/` does not repeat them.

- A pull request whose CI checks pass is merged without human action, and one with a failing check is never merged.
- A commit merged to the default branch is deployed without human action once CI on that commit passes.
- Every deploy is preceded by a backup of the SQLite database whose name ends in a UTC timestamp, and a deploy does not start when its backup failed.
- A deployed version can be rolled back by running the previous version against the database restored from the backup taken before that deploy. Writes made after that deploy are lost.

A repo with several SQLite databases has each of them backed up before a deploy, and its `AGENTS.md` names them and where they live.

State that is not in a database, such as files on a dataset, is outside the backup and the rollback. When the databases only cache what those files say, a rollback leaves the files as they are.

Rollback discards the writes made after the deploy, which suits a single-user app and needs a different design for anything with many writers.

How the rules are built is in the `github` skill (the merge gate and workflow triggers) and in the skill of the app's stack (backups, for PocketBase the `pocketbase` skill). `rn-ax/trotter` is the first implementation.

## Working with the superpowers plugin

The plugin's `brainstorming` and `writing-plans` skills default to dated design documents under `docs/superpowers/specs/` and implementation plans under `docs/superpowers/plans/`. This workflow takes precedence over those defaults:

- The design that brainstorming produces is the functionality's file in `spec/`, with its context and criteria. Approaches considered go in the pull request description.
- After Samuel approves the criteria, implementation starts directly, test-first per criterion. The `writing-plans` step is skipped.
- Criteria files and the repo's docs name no plugin; how the plugin is used lives only in this skill.

## Known weaknesses

- Agents may edit workflows, tests and screenshot baselines, so an agent can weaken its own gate. The criteria Samuel approves are the only fixed point.
