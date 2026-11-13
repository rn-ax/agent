---
name: spec-driven-dev
description: Use whenever a repo is set up, or a change is planned, so that Samuel writes specs and agents own everything after them (implementation, tests, CI, merging, deployment, rollback) with no human code or PR review — also for "agent-driven", "fully automatic", "no manual approval", "auto-merge", "specs as the source of truth", or the pre-deploy backup and rollback safety net. Holds the method, the merge gate on GitHub Free, the spec and traceability conventions, and the known weaknesses; it is the skill to iterate on as the method improves.
---

# Spec-driven development

Samuel writes the specs. Agents own what follows: implementation, tests, CI, merging, deployment and rollback. Nobody reviews code or pull requests. Two things make that safe: CI that proves the specs hold, and a backup taken before every deployment that a rollback can restore.

**Related systems**: `github` (org conventions, plan limits, secrets), `agent-code-pusher` (worktree and PR flow), `truenas` and `contabo-hosts` (where deploys and CI run), `pushover` (failure notifications).

## Roles

- **Samuel** writes or approves every change to the specs, and sets the access the pipeline needs (secrets, variables, team access).
- **Agents** do everything else, and may change workflows, tests and tooling as part of normal work.
- The repo's `AGENTS.md` records that no review step exists, so every session in it knows. A global rule that Samuel merges his own PRs gives way to that statement.

## Specs

- A spec is `specs/<feature>.md`. App concepts and invariants stay in the app's `DOMAIN.md`; a spec says what the software must do.
- Acceptance criteria are lines of the form `- AC-<n>: <behavior>`. An ID is unique across all specs of the repo and never reused. A criterion is concrete enough to execute; one that cannot be tested is a defect in the spec.
- Every test that proves a criterion carries `[AC-<n>]` in its title. A traceability check in CI fails the build when a criterion has no test, a tag names no criterion, or an ID appears twice. A tag on a skipped or todo test, or in a comment, covers nothing.
- A repo that already has behavior starts with a spec drafted by an agent from the domain notes and the existing tests, which Samuel approves before it counts.

## The gate

CI runs the full suite on every branch push: build, types, unit, integration, the same integration tests against the built image, end-to-end and visual tests in a pinned container, the traceability check, and dependency and secret scanning. A final merge job squash-merges the PR when the checks pass.

- A PR that changes anything under `specs/` is held for Samuel, including one that also changes code.
- A PR merges only when its branch contains the tip of `main`; a PR that is behind is updated and its checks run again.
- Merges are serialized so two PRs never verify against the same base.
- After merging, the job starts CI on `main`, which builds, tests and deploys the merged commit. A merge made with `GITHUB_TOKEN` starts no workflows, except `workflow_dispatch` and `repository_dispatch`, so every follow-up run is started with `gh workflow run`.
- On GitHub Free a private repo has no branch protection or rulesets, so this gate is workflow logic that nothing enforces against a direct push. A Team plan enforces it with required checks, native auto-merge and a merge queue; moving there changes where the gate lives and leaves the method alone.

## Safety net

- **Backup before every deploy.** The running version creates a timestamped backup, so the backup holds the state from before the deploy. An app with a built-in backup API (PocketBase) uses it, since a plain copy of a SQLite file can tear while the app writes. A failed backup stops the deploy before anything is updated.
- **Health check after the update.** The deploy waits for the app's health endpoint. A failure triggers the rollback.
- **Rollback** deploys the previous release's tag and then restores the backup made for the failed deploy. Writes made in between are discarded. Releases named with the version are the record of successful deploys, and a repo with no previous release reports that and leaves the running app alone.
- **Retention** keeps the newest backups of the pre-deploy kind and never deletes any other backup.
- **Notifications** report failed deploys and rollbacks to Samuel's phone.
- **Rollback drill.** A manually started workflow deploys a deliberately unhealthy image and passes only when the previous version is running again, healthy, with the earlier data present. It is the proof that rollback works and is run before auto-merge is switched on.

## Pipeline code

Pipeline logic lives in small tested modules in the repo (backup, release choice, notification, traceability, merge decision), run through the repo's task runner, with the workflows only sequencing those tasks. Each module has a pure function for the decision and a thin command around it, so the decision is unit tested without a CI run.

## Adopting it in a repo

1. Write the design and the implementation plan, and have Samuel approve both.
2. Provision the target and the access: the deployment target, its API credentials, a CI superuser for backups, the notification credentials, team access for review requests, squash merge and branch deletion in the repo settings. Credentials Samuel must store are written to a dated file on the Desktop, per the usual convention.
3. Record the currently running version as a release, so the first rollback has a target.
4. Build the pieces in this order, each as its own PR that Samuel merges: repo rules in `AGENTS.md`, backup and restore, release and notification helpers, backup-then-deploy with automatic rollback, the first spec with the traceability check, scanning, the rollback drill, and the merge job last.
5. After the merge job lands, a trivial docs PR is the first run through it; it must merge and deploy with no human action.

## Known weaknesses

- Agents may edit workflows, tests and screenshot baselines, so an agent can weaken its own gate. The traceability check and the drill are the mitigations; a re-recorded screenshot baseline is reviewed by nobody.
- Only the specs are protected, and only by the merge job's own rule.
- Rolling back discards data written after the deploy, which suits a single-user app and needs a different design for anything with many writers.
- A restore restarts the app inside its container; the drill is what confirms it works on the real target.

## Reference implementation

`rn-ax/trotter` carries the design and plan this skill was drawn from, under `docs/superpowers/`.
