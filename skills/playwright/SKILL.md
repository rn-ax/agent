---
name: playwright
description: Use whenever writing, running or re-recording Playwright end-to-end or screenshot tests — the pinned Playwright container, screenshot baselines, running the container natively or on CI, and how the pinned image renders across CPU architectures. Holds how the container runs and what is compared where, as established building rn-ax apps.
---

# Playwright

**Related systems**: `sveltekit` and `pocketbase` (the app and the backend these tests drive), `spec-driven-dev` (how tests relate to acceptance criteria).

## Baselines

- Screenshot baselines are recorded in the pinned Playwright container as linux/amd64, which is what CI compares against.
- Chromium renders the same pixels inside the pinned image on amd64 and arm64: trotter's amd64 baselines passed on arm64 with zero tolerance (116 tests). Re-measure by running the suite natively whenever the image tag or the screenshot content changes.
- The image tag equals the `@playwright/test` version.
- Baselines are only re-recorded on amd64.

## Themes

- Screenshot tests record and compare only the primary theme, the one the app is actually used in (dark for these apps), because the themes differ in color alone and each extra theme doubles the baselines to record and verify.

## Running the container

- The Playwright image is published for amd64 and arm64. Local runs use the image natively on the machine's architecture, since emulating amd64 is several times slower, and compare with the same zero tolerance as CI.
- The amd64 run on CI is the gate.
- The container runs as the invoking user with `HOME=/tmp`, so nothing root-owned lands in the workspace and a runner's next checkout can clean it. The task creates the results directory first for the same reason.
