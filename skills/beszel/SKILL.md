---
name: beszel
description: Use whenever the user asks about monitoring or resource usage history for their servers — CPU/memory/disk/network over time for TrueNAS or the Contabo boxes, per-container usage ("what was eating CPU at 03:00"), finding a slow or overloaded host — or anything about "beszel" explicitly. This is the accumulating knowledge base for how this user's Beszel hub and agents are set up, so read it before deploying an agent, adding a host, or assuming where metrics live.
---

# Beszel

This is the accumulating knowledge base for the user's Beszel monitoring. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content.

**Related systems**: see the `home` skill for the full topology map. The `truenas` skill covers the Apps platform the hub and the TrueNAS agent run on, and its install playbook and dataset conventions apply. The `contabo-hosts` skill covers the two VPS boxes whose agents come from `~/Projects/rn-infra`.

## What it is for

Host-level and per-container CPU, memory, disk and network history for TrueNAS and both Contabo boxes, so a question like "why is Plex using 50% CPU" can be answered from a graph instead of a live `docker top`. TrueNAS's own Reporting keeps host-level history (7 days full resolution, 30 days at 5-minute resolution); Beszel adds the per-container breakdown.

## Hub

The `beszel` app on TrueNAS, installed from the community catalog (`beszel-hub`), reachable on the LAN at `http://truenas.lan:30333`. It has no Cloudflare Tunnel or Access entry.

- Data lives in `Storage/Configuration/beszel/data` (config tree: system definitions, users and alerts matter), owned by `apps:apps`; the container runs as UID 568.
- The first account created in the web UI becomes the admin. Login credentials are the user's own; the agent holds none, and no hub API credential exists for agent sessions.
- The catalog entry is the hub only. Agents are always deployed separately.
- Keep the hub and agent image versions in step (both `0.21.0` at install time).

## Agents

Every agent dials out to the hub over WebSocket, so no agent publishes a port and nothing listens on 45876. All agents share one **universal token** (Add System dialog in the hub; enable the permanent option so it does not expire) and the hub's public SSH key, which is the same for every agent and not a secret. Each agent sets `SYSTEM_NAME` so every host registers as its own system under a meaningful name; without it a universal-token agent registers under the machine hostname (`vmi…` on the Contabo boxes). `SYSTEM_NAME` applies only at first registration, so a rename of an already-registered system happens in the hub UI.

Common agent shape: `henrygd/beszel-agent`, `network_mode: host`, `/var/run/docker.sock` mounted read-only (that mount is what provides per-container stats), state in `/var/lib/beszel-agent`, environment `HUB_URL`, `KEY`, `TOKEN`, `SYSTEM_NAME`.

| System | Deployed as | Token lives in |
|---|---|---|
| `truenas` | TrueNAS custom app `beszel-agent` (compose in the app config, `HUB_URL=http://192.168.1.142:30333`, state in `Storage/Logs/beszel/agent-data`) | the app's compose config on TrueNAS |
| `contabo-1`, `contabo-2` | `apps/beszel-agent` in `~/Projects/rn-infra`, deployed by the generic `app` role (`mise run apps`), `HUB_URL=http://truenas.lan:30333` over the WARP private-network route | ansible-vault, `inventory/group_vars/app_hosts/vault.yml` (`beszel_agent_token`) |

To add a host: another `beszel-agent` entry in rn-infra's `apps` list for a Contabo-style box, or a custom app on TrueNAS following the install playbook in the `truenas` skill (own the mount ownership yourself; a custom app gets no automatic permissions help).

## Open items

- The TrueNAS agent logs `Using most active device for root I/O … device=sdd`. If the disk graph tracks the wrong drive, set the agent's `FILESYSTEM` option.
- GPU stats for the GTX 1650 need Beszel's NVIDIA agent variant plus the nvidia runtime in the app; the current agent reports no GPU data.
