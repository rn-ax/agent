---
name: baserow
description: Use whenever the user asks for help with their Baserow instance — tables, fields, API access, or anything about "baserow" or "baserow.rn.ax" explicitly. This is the accumulating knowledge base for how this user's Baserow instance is actually set up, so read it before assuming its architecture, access method, or feature availability from scratch.
---

# Baserow

This is the accumulating knowledge base for the user's self-hosted Baserow instance. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content.

## Instance

Self-hosted on TrueNAS (`truenas.lan`) as the `baserow` app — installed via the TrueNAS Apps catalog (community train; not visible by default, see the `truenas` skill for the train-enablement note). See the `truenas` skill's `apps.md` for the full install incident (the permissions/UID troubleshooting, same class of issue as Windmill's).

**Two base URLs, same as Windmill**: `https://baserow.rn.ax` (public, behind Cloudflare Access — an interactive-login gate, unusable for bearer-token API calls) vs. `http://truenas.lan:30163` (LAN, no Access, use this for API/agent access). `BASEROW_PUBLIC_URL` must exactly match whatever hostname is used to access the web UI, or the frontend fails with a "Site not found" error — this bit both the initial LAN-only setup and the later switch to the public hostname; always keep this in sync when the access URL changes.

API credentials live in `~/.config/baserow/env` (mode 600): `BASEROW_BASE_URL`, `BASEROW_TOKEN`.

## Known paywalled features (self-hosted Enterprise License required)

Confirmed by the user hitting them directly, not from docs alone:
- **Row coloring** — Premium feature.
- Unique-field-constraint status was never fully confirmed one way or the other before the user moved on to evaluating other tools.

This was the deciding factor in also standing up Saltcorn (see that skill) as a genuinely-no-paywall alternative — Baserow isn't necessarily abandoned, but don't assume it "won" the data-store decision without checking current status.

## Related systems

See the `home` skill for the full topology map. Most relevant here:
- **Windmill** is the intended consumer of Baserow's data via its REST API (bearer token, same shape as Saltcorn's) — a Baserow task that's actually about automation belongs in a Windmill flow, not manual UI work.
- **Cloudflare** (Tunnel + Access) fronts the public hostname — see `truenas`'s app-install playbook for how that tunnel is shared across many apps, and why a tunnel-config change is treated as too high-blast-radius for direct agent API writes.
