---
name: sveltekit
description: Use whenever building or changing a SvelteKit 3 frontend — configuration, imports, Svelte 5 state, a static single-page build served by another server, component tests with vitest, or Playwright end-to-end and screenshot tests. Holds the version-specific behavior that is easy to get wrong, as established building rn-ax apps.
---

# SvelteKit

Facts here were established on SvelteKit 3 with Svelte 5.

**Related systems**: `pocketbase` (the backend that serves these apps' static build), `spec-driven-dev` (how the apps are specified and shipped).

## Configuration and imports

- SvelteKit 3 is configured in the `sveltekit(...)` plugin options in `vite.config.ts`, and the app has no `svelte.config.js`.
- `bun install` runs `svelte-kit sync` through the `prepare` script, which generates the SvelteKit configuration that the tests need in a fresh checkout.
- `browser` is exported from `$app/env`, and `$app/environment` no longer exists.
- TypeScript resolves package.json `imports` (such as `#lib/*`) literally, so those imports include the file extension.
- TypeScript stays on 5.x, because SvelteKit 3 reads `ts.sys`, which TypeScript 7 does not provide.

## Static single-page build

`ssr = false` with `adapter-static` and `fallback: "index.html"` produces a build that another server serves, with client-side routes falling back to `index.html`.

## Svelte 5 state

`$state` wraps array items in proxies, so state that is compared by identity uses `$state.raw`.

## daisyUI

The `tab-content` class hides panels it does not manage, so tab panels are plain conditionally rendered elements.

## Tests

- Component tests run in jsdom without SvelteKit, and its virtual `$app/*` modules are aliased to mocks.
- Playwright screenshot baselines are recorded in the pinned Playwright container as linux/amd64, because Chromium renders the same pixels only inside one pinned image and CPU architecture. The image tag equals the `@playwright/test` version.
- The Playwright container runs as the invoking user with `HOME=/tmp`, so nothing root-owned lands in the workspace and a runner's next checkout can clean it.
