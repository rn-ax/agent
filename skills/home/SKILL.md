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
| Homebox | Home inventory — specs, links, PDF manuals, warranty for everything owned | app on TrueNAS, `https://home.rn.ax` (Cloudflare Access), LAN `truenas.lan:30149` | `homebox` |
| Backups | Backup design and status: TrueNAS data, Macs, the M1 Mac mini backup server with its drive enclosure, offsite copies | `server.lan` (planned target), TrueNAS `Storage` pool (source) | `backup` |
| Shelly devices | Shelly relays and other Shelly gear (the office 2PM Gen4 on Zigbee through ZHA): pairing, profiles, firmware, wall-switch inputs | paired to Home Assistant, Wi-Fi on the IoT network | `shelly` |
| Fastmail | Personal email (`rn.ax`), calendar, contacts; read-only MCP token for agents | hosted, `api.fastmail.com/mcp` | `email` |
| Home Assistant | Smart home | Raspberry Pi 5, `192.168.3.71:8123` (isolated IoT VLAN) — also `home.rutinerad.com` via Nabu Casa | `home-assistant` |
| Cloudflare | Tunnel + Access fronting most `*.rn.ax` apps on TrueNAS; Email Routing on the separate `rutinerad.com` domain | account "rutinerad" | `cloudflare` |
| monocoque | Separate Django monorepo, several custom apps (`newshound`, etc.), deployed to TrueNAS too | repo at `~/Projects/monocoque` | its own repo docs, not a home-infra skill |
| Contabo hosts | Two VPS boxes running self-hosted GitHub/Gitea Actions runners + a few small apps; reach TrueNAS directly over Cloudflare WARP | `contabo-1`/`contabo-2`, IaC at `~/Projects/rn-infra` | `contabo-hosts` |
| agent-tasks (`atask`) | Cross-session task queue, not a home system but referenced constantly when scoping multi-session work | `~/Projects/agent-tasks` | `todo` skill |

## Devices and hardware live in Homebox

Every device in the house — smart-home gear, servers, network equipment, peripherals, appliances — is recorded in Homebox (see the `homebox` skill), with exact model numbers, specs, connectivity and manuals. Any task that involves a physical device starts with a Homebox lookup (`hb-api GET '/entities?q=<term>'`), before web searches or questions to the user. Typical payoffs: which radios and ports a device has, what hardware a host carries (a Zigbee dongle on the Home Assistant Pi, say), and whether the user already owns something that solves the problem. Every mention of a device in a reply or in a skill is a markdown link to its Homebox entry, `[Raspberry Pi 5 (8 GB)](https://home.rn.ax/item/<entity id>)`; the entity id comes from the lookup, and the asset id (`#000-041`) may follow the link as the short reference. The map above lists the software systems; Homebox is the source for the hardware under and around them.

## Topology notes that matter across systems

- **Two VLANs, not one flat network.** Main LAN (`192.168.1.x`) has TrueNAS and the router itself; Home Assistant sits deliberately isolated on `192.168.3.x` for security. Any integration crossing that boundary (Windmill on TrueNAS talking to Home Assistant, say) needs the reachability confirmed explicitly — don't assume it works because both are "on the home network." See `home-network` for the full VLAN breakdown and `home-assistant` for the confirmed-reachable path to the router specifically.
- **Cloudflare Tunnel is shared infrastructure, not per-app.** One tunnel (named "TrueNAS", account "rutinerad") fronts ~26 different hostnames across many TrueNAS apps, each with its own Access application but sharing one reusable Access policy ("Samuel"). A change to the tunnel's ingress config is a single write that touches every one of those apps at once — see `truenas`'s app-install playbook and the Windmill incident notes in the `windmill` skill's "TrueNAS deployment" section before touching it. Tunnel/Access/DNS writes are treated as too high-blast-radius for direct agent API calls (see atask 247, the Terraform/IaC migration analysis) — prepare the change, but expect a human to apply it.
- **`rn.ax` (real personal email, Fastmail) and `rutinerad.com` (side-project domain, Cloudflare Email Routing) are deliberately different domains** — don't assume a DNS/email pattern that works on one applies to the other.
- **TrueNAS is the physical host for most of the software stack** — Windmill, `cloudflared`, and a long tail of media/other apps all run there as Docker containers. The install playbook, Configuration/Logs dataset convention, and permission gotchas in `truenas`/SKILL.md apply to *any* app added there, not just the ones with their own dedicated skill.

## Integration threads (in progress or worth considering)

- **Email-triggered Windmill flows** via a generic Cloudflare Worker on `rutinerad.com`'s Email Routing (addressing convention `<flow|script>+<workspace>+<path>@rutinerad.com`) — built for the "bank sends an invoice email → reminder gets created" use case. Any future "trigger something from an email" need should reuse this pipeline rather than building a new one.
- **Windmill ↔ Home Assistant is not wired up yet**, but both expose real APIs (Home Assistant's REST/websocket API is documented in its own skill) — worth considering for any automation whose logic is more complex than what HA's own automation engine handles well, or as a trigger source in the other direction. Remember the VLAN boundary above before assuming reachability.
- **`monocoque`'s `newshound` app may be replaceable by a Windmill flow** — atask 246 tracks that analysis (what it actually does, whether a scheduled flow is the right shape given it might need to serve a live RSS endpoint rather than run as a batch job).
- **Contabo boxes have a direct path to TrueNAS's LAN services** via Cloudflare WARP (see `contabo-hosts`) — any private repo's CI that needs to reach something on TrueNAS (Windmill, etc.) should run on a Contabo self-hosted runner rather than a GitHub-hosted one going through a public Access-gated hostname.
