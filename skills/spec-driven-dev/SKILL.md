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
- Criteria live in `spec/`, grouped into files by the context they apply to. A criterion may move between files. When a file grows too big, find the groups in it and split it along them.
- Each file is an [OKF](https://github.com/GoogleCloudPlatform/open-knowledge-format) concept file: markdown with YAML frontmatter (`type` is the one required key, `title` and `description` are recommended) followed by the list `- AC-<n>: <rule>`.
- A test that proves a criterion carries `[AC-<n>]` in its title.
- Domain facts that explain what the app's concepts mean stay in the app's `DOMAIN.md`.

## Method

1. Identify the criteria together: the agent proposes them in plain sentences, Samuel corrects, and the result is written to the criteria files.
2. Implement against them. There is no separate implementation plan, because the criteria are the plan and the agent decides the files, names and structure.
3. Verify every criterion in CI before anything merges.

## The gate

CI runs the full suite on every branch push. When the checks pass, the PR merges itself (squash), and CI on `main` builds, tests and deploys the merged commit.

- On GitHub Free a private repo has no branch protection or rulesets, so the gate is workflow logic that nothing enforces against a direct push. A Team plan enforces it with required checks, native auto-merge and a merge queue; moving there changes where the gate lives and leaves the method alone.
- A merge made with `GITHUB_TOKEN` starts no workflows, except `workflow_dispatch` and `repository_dispatch`, so the follow-up run on `main` is started with `gh workflow run`.

## Backup and rollback

- **Every deploy is preceded by a backup** of the SQLite database, a copy with a UTC timestamp suffix. The running version makes it, so it holds the state from before the deploy. An app with a built-in backup API (PocketBase) uses it, since a plain copy of a SQLite file can tear while the app writes. A failed backup stops the deploy.
- **Rollback** runs the previous version against the database restored from the backup made before the failed deploy. Writes made after that deploy are discarded, which suits a single-user app and needs a different design for anything with many writers.

## Working with the superpowers plugin

The plugin's `brainstorming` and `writing-plans` skills default to dated design documents under `docs/superpowers/specs/` and implementation plans under `docs/superpowers/plans/`. This workflow takes precedence over those defaults:

- The result of brainstorming is the criteria files, in the flat directory. It produces no dated design document.
- After Samuel approves the criteria, implementation starts directly, test-first per criterion. The `writing-plans` step is skipped.
- Criteria files and the repo's docs name no plugin; how the plugin is used lives only in this skill.

## Known weaknesses

- Agents may edit workflows, tests and screenshot baselines, so an agent can weaken its own gate. The criteria Samuel approves are the only fixed point.
