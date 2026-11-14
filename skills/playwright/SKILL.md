---
name: playwright
description: Use whenever writing, running or re-recording Playwright end-to-end or screenshot tests — the pinned Playwright container, screenshot baselines, running the container natively or on CI, and why pixels differ between CPU architectures. Holds how the container runs and what is compared where, as established building rn-ax apps.
---

# Playwright

**Related systems**: `sveltekit` and `pocketbase` (the app and the backend these tests drive), `spec-driven-dev` (how tests relate to acceptance criteria).

## Baselines

- Screenshot baselines are recorded in the pinned Playwright container as linux/amd64, because Chromium renders the same pixels only inside one pinned image and CPU architecture.
- The image tag equals the `@playwright/test` version.
- Baselines are only re-recorded on amd64, which is what CI compares against.

## Themes

- Screenshot tests record and compare only the primary theme, the one the app is actually used in (dark for these apps), because the themes differ in color alone and each extra theme doubles the baselines to record and verify.

## Running the container

- The Playwright image is published for amd64 and arm64. A run on a machine of the other architecture uses the image natively, because emulating amd64 is several times slower, and compares with a pixel tolerance chosen from `process.arch`.
- The amd64 run on CI compares with zero tolerance and is the gate.
- The container runs as the invoking user with `HOME=/tmp`, so nothing root-owned lands in the workspace and a runner's next checkout can clean it. The task creates the results directory first for the same reason.
