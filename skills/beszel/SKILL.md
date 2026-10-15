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

The `beszel` app on TrueNAS, installed from the community catalog (`beszel-hub`), reachable on the LAN at `http://truenas.lan:30333` and publicly at `https://bzl.rn.ax`, which sits behind Cloudflare Access (an unauthenticated request gets a 302 to the Access login). Agents and scripted API calls use the LAN address.

- Data lives in `Storage/Configuration/beszel/data` (config tree: system definitions, users and alerts matter), owned by `apps:apps`; the container runs as UID 568.
- The first account created in the web UI becomes the admin. The user's own login stays with the user; agent sessions use the dedicated API superuser described under "API access".
- The catalog entry is the hub only. Agents are always deployed separately.
- Keep the hub and agent image versions in step (both `0.21.0` at install time).

## Agents

Every agent dials out to the hub over WebSocket, so no agent publishes a port and nothing listens on 45876. All agents share one **universal token** (Add System dialog in the hub; enable the permanent option so it does not expire) and the hub's public SSH key, which is the same for every agent and not a secret. Each agent sets `SYSTEM_NAME` to a display name (`TrueNAS`, `Contabo 1`, `Contabo 2`) so every host registers as its own system under a readable name; without it a universal-token agent registers under the machine hostname (`vmi…` on the Contabo boxes). `SYSTEM_NAME` applies only at first registration, so a rename of an already-registered system happens in the hub UI.

Env values in the rn-infra `.env` are single-quoted by the `app` role, so display names with spaces pass through intact.

Common agent shape: `henrygd/beszel-agent`, `network_mode: host`, `/var/run/docker.sock` mounted read-only (that mount is what provides per-container stats), state in `/var/lib/beszel-agent`, environment `HUB_URL`, `KEY`, `TOKEN`, `SYSTEM_NAME`.

| System | Deployed as | Token lives in |
|---|---|---|
| `TrueNAS` | TrueNAS custom app `beszel-agent` on the `henrygd/beszel-agent-nvidia:<version>-slim` image (compose in the app config, `HUB_URL=http://192.168.1.142:30333`, state in `Storage/Logs/beszel/agent-data`) | the app's compose config on TrueNAS |
| `Contabo 1`, `Contabo 2` | `apps/beszel-agent` in `~/Projects/rn-infra`, deployed by the generic `app` role (`mise run apps`), `HUB_URL=http://truenas.lan:30333` over the WARP private-network route | ansible-vault, `inventory/group_vars/app_hosts/vault.yml` (`beszel_agent_token`) |

To add a host: another `beszel-agent` entry in rn-infra's `apps` list for a Contabo-style box, or a custom app on TrueNAS following the install playbook in the `truenas` skill (own the mount ownership yourself; a custom app gets no automatic permissions help).

## API access

Use `bz-api <method> <path>` (this skill's own directory) for ad-hoc hub API calls, e.g. `bz-api GET /collections/systems/records` or `bz-api GET '/collections/network_monitors/records?perPage=50'`. It reads the "Beszel" item in the "Agent" 1Password vault (`email` and `password` fields, LAN URL first), signs in as the hub superuser `agent@beszel.local` on every call and keeps no token. The path is relative to `<base_url>/api`.

That superuser was created with `sudo docker exec ix-beszel-beszel-1 /beszel superuser create <email> <password> --dir /beszel_data` on TrueNAS; rotate or remove it with the same binary's `superuser update` / `delete`, and update the 1Password item to match.

## GPU stats (TrueNAS)

The GTX 1650 is reported through NVML. The TrueNAS agent uses the NVIDIA image variant and attaches the GPU with a compose device reservation (`deploy.resources.reservations.devices`: `driver: nvidia`, `count: all`, `capabilities: [gpu]`) plus `NVIDIA_DRIVER_CAPABILITIES=utility`; the container runtime then injects `libnvidia-ml.so.1`, `nvidia-smi` and the device nodes. The slim image has no shell; inspect it from the host through `/proc/<pid>/root`. Contabo boxes carry no GPU and use the standard image.

## Network monitors

Network monitors are probes that each agent runs from its own host: `icmp`, `tcp` (target plus port), `http` (HTTPS monitors also track certificate expiry) and `dns` (optional DNS server to query). They appear under Network Monitors in the hub and can be compared across systems. They are records in the hub's database, created in the web UI or through the hub's authenticated API; `config.yml` defines systems only, so monitors have no file-based definition. ICMP works from the host-network agent container without extra capabilities.

Monitors are managed through the hub API with `bz-api` (see "API access"): `GET /collections/network_monitors` returns the live field list, and `POST /collections/network_monitors/records` takes `system` (record id from `/collections/systems/records`), `target`, `protocol`, `interval` (seconds), `enabled`, plus `port` for TCP and `server` for DNS. Probe results (`res`, `resAvg1h`, `loss1h`) are in microseconds.

Reachability shapes which monitors make sense, and each was tested from the real host before it was created:
- TrueNAS sits directly on the Inteno router's `192.168.1.x` network, so it reaches `192.168.1.1`; the Synology router (`192.168.0.1`) is behind the Inteno and unreachable from there.
- ICMP from the Contabo boxes to `192.168.1.142` fails because WARP carries TCP and UDP but not ping. Reachability of TrueNAS from the Contabo boxes is therefore watched with TCP and HTTP.

Current monitors (60 s interval): TrueNAS — ICMP `192.168.1.1`, ICMP `1.1.1.1`, DNS `rn.ax` (system resolver), DNS `cloudflare.com` via `1.1.1.1`. Contabo 1 and Contabo 2, each — ICMP `1.1.1.1`, TCP `truenas.lan:30333` (the hub itself), HTTP `http://truenas.lan:30155/api/version` (Windmill, the service CI depends on).

## Open items

- The TrueNAS agent logs `Using most active device for root I/O … device=sdd`. If the disk graph tracks the wrong drive, set the agent's `FILESYSTEM` option.
