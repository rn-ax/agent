---
name: windmill
description: Use whenever the user asks for help with their Windmill instance — scripts, flows, triggers, workers, the AI copilot, or anything about "windmill" or "windmill.rn.ax" explicitly. This is the accumulating knowledge base for how this user's Windmill instance is actually set up, so read it before assuming its architecture, access method, or conventions from scratch.
---

# Windmill

This is the accumulating knowledge base for the user's self-hosted Windmill instance. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content.

**Related systems**: see the `home` skill for the full topology map and cross-system integration notes — in particular, Windmill is meant to be the automation layer sitting on top of `baserow`/`saltcorn` (both have plain REST APIs a flow can call) and is a candidate trigger/target for `home-assistant` automations too, though that link isn't built yet. Check `home`'s integration-threads section before assuming a Windmill task is self-contained. See the `cloudflare` skill for account-level facts (credential inventory, the Access service-token bypass mechanism in general, Workers/wrangler tooling, GitHub-Actions-secrets-on-Free-plan gotcha) — this file covers only what's specific to the Windmill instance itself.

## Instance

Self-hosted on TrueNAS (`truenas.lan`) as the `windmill` app in TrueNAS's Apps catalog — see the `truenas` skill's `apps.md` for the install/permissions incidents specific to getting the app running at all.

**Two different base URLs depending on caller:**
- `https://windmill.rn.ax` — the public hostname, routed through a Cloudflare Tunnel back to TrueNAS's Caddy. This sits behind **Cloudflare Access (Zero Trust)**, which intercepts every request (including API calls with a valid Windmill bearer token) with a 302 redirect to `rutinerad.cloudflareaccess.com/cdn-cgi/access/login/...` demanding an interactive login. A plain bearer-token API client can't get through this on its own — but see "Public HTTP-triggered flows" below for the Access **service-token bypass** that lets a Cloudflare Worker through.
- `http://truenas.lan:30155` — direct LAN access to the same instance, bypassing Cloudflare/Access entirely. **Use this for any API/agent access from a machine already on the LAN** (confirmed working with a Windmill API token via `Authorization: Bearer <token>`).

API access credentials live in `~/.config/windmill/env` (mode 600): `WINDMILL_BASE_URL` (the LAN URL above), `WINDMILL_TOKEN`, `WINDMILL_WORKSPACE`. Extract with `grep`/`cut` rather than `source`, same pattern as the other `~/.config/*/env` files in this environment.

**Workspace**: `claude` — created for agent use specifically. The instance also has a separate **`admins`** workspace (created during initial instance setup, per Windmill's own onboarding prompt) that `~/.config/windmill/env`'s `WINDMILL_TOKEN` has no access to at all — `GET /api/workspaces/list` with that token only ever returns `claude`. This turned out not to matter for git-sync (see below) — a resource created via API directly in `claude` worked fine once selected in the UI — but it's worth knowing this second workspace exists and the agent's token can't see into it, in case something else workspace-level comes up empty for no apparent reason.

## AI copilot

Configured at the instance level (Instance settings → Windmill AI), so every workspace inherits it unless overridden:
- **Anthropic**: `claude-haiku-4-5-20251001` (picked for cost — cheapest current Claude model). API key from a real (paid) Anthropic account with credits.
- **Google Gemini**: `gemini-2.5-flash-lite` (confirmed cheapest Gemini model, cheaper than the newer `gemini-3.1-flash-lite-preview`) — API key from a **free-tier** Google AI Studio key (`aistudio.google.com/apikey`, no billing attached). Free tier is rate-limited (~10 req/min, ~250 req/day for Flash-tier as of 2026-09) and Google may use free-tier request data to improve their models — don't route sensitive work through this provider, use the Anthropic one for anything that matters.

Both providers accept typing a model name directly rather than relying on Windmill's dropdown, which can lag behind current model releases.

## Email-triggered flows

Rather than using Windmill's native inbound-SMTP trigger (would require exposing port 25 publicly — residential ISP port-25 blocking is a real risk, untested), flows are triggered by email through a **generic Cloudflare Worker** that fronts `rutinerad.com`'s already-existing Cloudflare Email Routing (a separate domain from `rn.ax`; `rn.ax`'s own mail goes straight to Fastmail via apex MX and was deliberately not touched — Cloudflare's Email Routing "enable" flow defaults to the zone apex and would have added a second, conflicting SPF TXT record there).

**Setup**: one Cloudflare Email Routing **catch-all rule** on `rutinerad.com` → Send to Worker → `windmill-mail-router` (source in the `rn-ax/workers` GitHub repo, cloned locally as `~/Projects/rn-workers/windmill-mail-router`; deployed via `wrangler`). The Worker parses the recipient's local-part itself, so **no new Cloudflare rule or Worker redeploy is needed per flow** — this was a deliberate requirement (the user explicitly didn't want a per-flow setup).

**Addressing convention**: `<flow|script>+<workspace>+<path-with-dots-instead-of-slashes>@rutinerad.com`. Example: `flow+claude+reminders.invoice_email@rutinerad.com` triggers `POST {WINDMILL_BASE_URL}/api/w/claude/jobs/run/f/reminders/invoice_email`. The Worker POSTs the parsed email as JSON with keys `from`, `from_name`, `to`, `subject`, `text`, `html`, `attachments` (filename/mimeType/size only, not content) — any flow meant to be triggered this way needs input args matching those names it cares about.

The Worker authenticates to Windmill via a `WINDMILL_TOKEN` secret plus the Cloudflare Access service-token headers described below (both set via `wrangler secret put`; `WINDMILL_TOKEN` is the same token family as `~/.config/windmill/env`, not a separate one) — it targets `windmill.rn.ax` (the public, Access-gated URL), since a Worker runs on Cloudflare's edge and has no route to the LAN URL. See the `cloudflare` skill for the wrangler-token scope this Worker's deploys use and the bindings-verification step that caught this Worker shipping once with `WINDMILL_TOKEN` unbound.

## Public HTTP-triggered flows (wm.rn.ax)

For a Windmill flow/script that needs to serve a **stable public URL that an arbitrary external client polls directly** (an RSS/JSON-feed reader, a webhook source that can't be reconfigured per-flow, etc.) rather than being invoked by something Windmill-aware, the pattern is a generic proxy Worker rather than exposing `windmill.rn.ax` itself:

- **`windmill-public-proxy`** (`rn-ax/workers` repo, `~/Projects/rn-workers/windmill-public-proxy` locally), bound to the custom domain **`wm.rn.ax`**. It forwards `wm.rn.ax/<path>` → `https://windmill.rn.ax/api/w/<workspace>/jobs/run_wait_result/<path>`, attaching both the Cloudflare Access service-token headers and the Windmill bearer token — so the caller needs no auth of its own, and `wm.rn.ax` itself is a plain Worker custom domain, not behind Cloudflare Access.
- **The Access bypass**: uses the general Cloudflare Access service-token mechanism (see the `cloudflare` skill for how that works and the policy-attachment gotcha that bit this setup once). Credentials live in `~/.config/cloudflare-access/env` (mode 600): `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET` — the "Windmill · Public worker" service token, scoped at the whole-app level covering all of `windmill.rn.ax` (not narrowed to specific paths).
- **Sync endpoint timeout**: Windmill's `jobs/run_wait_result` has a server-side `TIMEOUT_WAIT_RESULT` (default **20 seconds**) — a script/flow triggered this way that runs longer just fails the HTTP call. This caps how much live work (e.g. scraping N articles) a single request can safely do.
- **Feed-shaped webhooks (design decision)**: for a script that live-builds something like an RSS/JSON feed on every poll (mirroring an upstream source plus per-item enrichment), the chosen pattern is **one synchronous script, best-effort per run**, not a separate scheduled-flow-writes-cache + fast-read-only-endpoint split. The script keeps a persistent cache (Windmill's `wmill.get_state()`/`set_state()`, keyed by item URL with its own TTL) so most items are already cached between polls; each run only does live work for new/changed items, checks elapsed time against a safety margin under the 20s ceiling, and returns whatever it has — cached items plus however many new ones it got through — rather than trying to guarantee full-set completeness or raising on a partial result. A slow run just caches fewer new items that pass; the next poll picks up where it left off. This was chosen over a scheduled-flow split specifically because per-item caching already bounds the live-work window to just the delta since the last successful pass, making a hard split (and its added freshness-lag/complexity) unnecessary.
- **JSON Feed content-type**: `windmill-public-proxy` passes through whatever content-type Windmill returns (plain `application/json`), but a feed's registered media type is `application/feed+json` — some readers (Feedbin) use the header alone to decide something is a feed, before ever parsing the body. The proxy overrides to `application/feed+json` for any path under `feeds/` (see its `src/index.ts`).
- **Feed endpoints need a WAF bot-check exemption**: the `rn.ax` zone's Bot Fight Mode / WAF was blocking non-browser clients (the official JSON Feed validator, likely Feedbin's fetcher too) with a 403 at Cloudflare's edge, before the request ever reached the Worker — invisible to browser-like tools (curl, WebFetch) since it's IP/TLS-fingerprint based, not User-Agent based, so it can't be reproduced by spoofing headers from an unflagged network. Confirmed and fixed directly in the Cloudflare dashboard (Security → WAF) rather than via API — the token in `~/.config/cloudflare/env` has no Zone Settings or Firewall/WAF read/edit scope. Any new public feed/webhook path under `wm.rn.ax` meant for non-browser bots to poll should get the same exemption up front.

## Git-sync (workspace ↔ GitHub)

The `claude` workspace's scripts/flows/resources are mirrored to **`rn-ax/windmill`** (GitHub, cloned locally as `~/Projects/rn-windmill` per the `rn-ax` naming convention — see the `github` skill) via Windmill's native git-sync feature, rather than by hand-copying script source into an app repo (an earlier attempt put a Windmill script inside the `rn-ax/workers` repo, which was wrong — that repo is for actual Cloudflare Workers only).

**Setup, in order:**
1. A `git_repository`-type resource (path `f/git_sync/windmill_repo` in the `claude` workspace) holds the repo URL: `https://x-access-token:<PAT>@github.com/rn-ax/windmill.git`, `branch: "main"`. The PAT is a **fine-grained** GitHub token scoped to only `rn-ax/windmill`, Contents: Read and write — GitHub has no API/CLI way to mint a fine-grained PAT, it must be created via the web UI (`github.com/settings/tokens?type=beta`); stored at `~/.config/windmill-git-sync/env` (mode 600) as `GITHUB_PAT`.
2. Workspace Settings → **Git Sync** tab (not reachable from a plain "Workspace Settings" landing view the way other tabs are — if it's not immediately visible, keep looking rather than assuming the feature is missing) → select that resource. **Read-only verification** ("Test connection") — Windmill only confirms it can read the repo, not that it can push; it won't catch a token that's read-only until an actual deploy tries to write.
3. `f/**` and similar path filters control what syncs; defaults are broad enough to not need adjusting for a single dedicated sync repo like this one.

**Two credential paths exist, and only one works on this instance**: Windmill's docs describe a newer `POST /w/{workspace}/git_sync/credential` endpoint that stores the PAT separately from the resource (avoiding the token ever sitting in a URL field). That endpoint **404s on this Community Edition build (v1.817.0)** — it's Enterprise-only, even though git-sync itself is CE-available (up to 2 users; this workspace has 1). The fallback — and the only way to authenticate git-sync on this instance — is embedding the token directly in the resource's `url` field, e.g. `https://x-access-token:<PAT>@github.com/...`. The Claude Code permission classifier flags writing a URL like that as **credential leakage** (correctly, in general) and needs explicit user sign-off each time before proceeding; it's an accepted tradeoff here specifically because the resource lives only inside Windmill's own workspace (never exposed through anything under `wm.rn.ax`, which only ever returns a script's own return value, never a resource's contents) and the user explicitly OK'd it on that basis.

**Feed scripts specifically**: the Ålandstidningen script (`f/feeds/alandstidningen`, see "Public HTTP-triggered flows" above) is the first thing synced this way — its source lives only in Windmill + this git mirror, not in any app repo.

**No separate dev workspace**: considered and deliberately skipped — every change already deploys through git-sync to `rn-ax/windmill`, so a bad edit is a plain git revert away rather than needing workspace-level isolation to recover from.

**Tooling note**: see the `cloudflare` skill's "Workers & wrangler" section for the `wrangler`/Node setup quirk on this machine — not Windmill-specific.

## Job execution / workers

**Job isolation**: set to **None** (not Unshare or Nsjail) — the TrueNAS-packaged `worker`/`worker-native` containers run with `cap_drop: ["ALL"]` and no relevant `cap_add`, plus `no-new-privileges`, so both other isolation modes would fail outright trying to create namespaces (`CAP_SYS_ADMIN` unavailable). The container-level hardening is already the real sandboxing boundary here; the in-process isolation modes are redundant on this deployment, not just unnecessary.

**Native worker threads**: left at the default of 8 despite the coordinator's tight 2 CPU/4GB budget — each native-mode job (only `nativets` + direct DB-query job types, not general-purpose scripts) is cheap enough that this wasn't worth trading off against.

**Retention / Instance object storage**: both are Enterprise-Edition-gated settings visible in the setup wizard even on the Community Edition this instance runs. Retention silently caps at 30 days regardless of what's entered; instance object storage (S3/Azure-backed log offload + shared Python/Go dependency cache across workers) does nothing without a paid license. Both left at defaults/blank.

**Planned, not yet built**: delegating actual job *execution* to external workers on the Contabo hosts (`contabo-1`/`contabo-2`, see the `truenas` skill or `~/.ssh/config` for access), with TrueNAS staying a lightweight coordinator (server + Postgres only). Connectivity plan was Cloudflare Access (Zero Trust) with a TCP application + service token for the Contabo workers to reach TrueNAS's Postgres — not yet implemented as of this writing.
