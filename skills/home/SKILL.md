---
name: home
description: Use whenever a task spans more than one home-infrastructure system, asks how two components fit or should fit together, or needs a map of what exists before diving into one system's details — e.g. "what's the best way to trigger X from Y", "what do we already have running", planning a new integration, or general home-lab/homelab questions. This is the hub/index skill: it holds topology and cross-system integration knowledge that doesn't belong to any single system's own skill, and points to the deep-dive skill for each system rather than duplicating their detail. Load this first for any "make these work together" task, then load whichever spoke skills it points to.
---

# Home infrastructure — hub

This is the index for everything running across this user's home infrastructure. Each system has its own deep-dive skill (a "spoke") with full operational detail — this file exists so a cross-system task doesn't start from zero, and so a mention of one system prompts consideration of the others it actually relates to. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content. Every spoke skill below links back here under its own "Related systems" section — if a new system gets its own skill, add it to the map here and add a back-link there, in the same pass.

## Map

| System | What it is | Where | Deep-dive skill |
|---|---|---|---|
| Inteno router | ISP-facing gateway/modem | `192.168.1.1` | `home-network` |
| Synology SRM router | Actual WiFi/VLANs, behind the Inteno | `192.168.0.1` | `home-network` |
| TrueNAS | Main server — hosts most of the apps below via Docker | `truenas.lan` / `192.168.1.142` | `truenas` |
| Windmill | Automation/agent layer (scripts, flows, AI copilot) | app on TrueNAS, `windmill.rn.ax` (public, Access-gated) / `truenas.lan:30155` (LAN, for API) | `windmill` |
| NocoDB | Airtable-style data store | app on TrueNAS, `noco.rn.ax` | *(no dedicated skill yet)* |
| Baserow | Airtable-style data store — hit paywalled features (unique constraint, row coloring) | app on TrueNAS, `baserow.rn.ax` / `truenas.lan:30163` (LAN, for API) | `baserow` |
| Saltcorn | No-code app builder, genuinely no paid tier — chosen after NocoDB/Baserow both gated basic features | Custom App on TrueNAS, `truenas.lan:31399` (no public tunnel route yet) | `saltcorn` |
| Home Assistant | Smart home | Raspberry Pi 5, `192.168.3.71:8123` (isolated IoT VLAN) — also `home.rutinerad.com` via Nabu Casa | `home-assistant` |
| Cloudflare | Tunnel + Access fronting most `*.rn.ax` apps on TrueNAS; Email Routing on the separate `rutinerad.com` domain | account "rutinerad" | `cloudflare` |
| monocoque | Separate Django monorepo, several custom apps (`newshound`, etc.), deployed to TrueNAS too | repo at `~/Projects/monocoque` | its own repo docs, not a home-infra skill |
| agent-tasks (`atask`) | Cross-session task queue, not a home system but referenced constantly when scoping multi-session work | `~/Projects/agent-tasks` | `todo` skill |

## Topology notes that matter across systems

- **Two VLANs, not one flat network.** Main LAN (`192.168.1.x`) has TrueNAS and the router itself; Home Assistant sits deliberately isolated on `192.168.3.x` for security. Any integration crossing that boundary (Windmill on TrueNAS talking to Home Assistant, say) needs the reachability confirmed explicitly — don't assume it works because both are "on the home network." See `home-network` for the full VLAN breakdown and `home-assistant` for the confirmed-reachable path to the router specifically.
- **Cloudflare Tunnel is shared infrastructure, not per-app.** One tunnel (named "TrueNAS", account "rutinerad") fronts ~26 different hostnames across many TrueNAS apps, each with its own Access application but sharing one reusable Access policy ("Samuel"). A change to the tunnel's ingress config is a single write that touches every one of those apps at once — see `truenas`'s app-install playbook and the Windmill incident notes in `apps.md` before touching it. Tunnel/Access/DNS writes are treated as too high-blast-radius for direct agent API calls (see atask 247, the Terraform/IaC migration analysis) — prepare the change, but expect a human to apply it.
- **`rn.ax` (real personal email, Fastmail) and `rutinerad.com` (side-project domain, Cloudflare Email Routing) are deliberately different domains** — don't assume a DNS/email pattern that works on one applies to the other.
- **TrueNAS is the physical host for most of the software stack** — Windmill, NocoDB, Baserow, Saltcorn, `cloudflared`, and a long tail of media/other apps all run there as Docker containers. The install playbook, Configuration/Logs dataset convention, and permission gotchas in `truenas`/SKILL.md apply to *any* app added there, not just the ones with their own dedicated skill.

## Integration threads (in progress or worth considering)

- **Windmill as the automation hub for the data stores.** Baserow and Saltcorn both expose plain REST APIs (bearer token per user) — the whole point of standing up Windmill alongside them is flows that read/write those tables, not just manual data entry. When a Windmill task comes up, consider whether it's actually about moving data into/out of Baserow or Saltcorn.
- **Email-triggered Windmill flows** via a generic Cloudflare Worker on `rutinerad.com`'s Email Routing (addressing convention `<flow|script>+<workspace>+<path>@rutinerad.com`) — built for the "bank sends an invoice email → reminder gets created" use case. Any future "trigger something from an email" need should reuse this pipeline rather than building a new one.
- **Windmill ↔ Home Assistant is not wired up yet**, but both expose real APIs (Home Assistant's REST/websocket API is documented in its own skill) — worth considering for any automation whose logic is more complex than what HA's own automation engine handles well, or as a trigger source in the other direction. Remember the VLAN boundary above before assuming reachability.
- **`monocoque`'s `newshound` app may be replaceable by a Windmill flow** — atask 246 tracks that analysis (what it actually does, whether a scheduled flow is the right shape given it might need to serve a live RSS endpoint rather than run as a batch job).
- **Baserow vs. Saltcorn as the "real" data store is still being decided** — Baserow works but has known paywalled features; Saltcorn has no paywall risk but a fundamentally different UI (app-builder, not spreadsheet-grid, until the Tabulator plugin's grid view is actually set up and proven out). Don't assume either has "won" without checking how that settled.
