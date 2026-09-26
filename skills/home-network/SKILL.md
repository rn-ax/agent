---
name: home-network
description: Use whenever a task touches the user's home network — either router (the Inteno/IOPSYS ISP gateway or the Synology SRM router behind it), WiFi networks/VLANs/subnets, network diagnostics, latency/connectivity problems, pulling stats or connected-device/presence data, or triggering a reboot — even if the user doesn't name a specific device explicitly. This is the accumulating knowledge base for how this user's home network is actually laid out and how to talk to each piece of it, so read it before assuming topology, capabilities, API, or credentials from scratch.
---

# Home network (Inteno gateway + Synology SRM router)

**Related systems**: see the `home` skill for the full topology map. TrueNAS and the routers share the main LAN (`192.168.1.x`); Home Assistant sits on a deliberately separate VLAN (`192.168.3.x`, see `home-assistant`) — don't assume reachability between them without checking.

The accumulating knowledge base for the user's home network: its topology, both routers, and the WiFi networks/VLANs riding on top. Fill in sections as they're actually confirmed; don't guess. Sections marked **TBD** need the user's input — ask rather than assume, and update this file once answered so future sessions don't re-ask.

## Topology overview

Two routers in series: the **Inteno** (ISP-facing gateway/modem, `192.168.1.x`) uplinks to a **Synology router running SRM** behind it, which does all the actual WiFi and network segmentation for the house. Anything about a specific WiFi network, VLAN, or which devices can reach each other belongs to the Synology — see "Synology router" below. Anything about the DSL/WAN line itself, or wired clients directly on the Inteno's own LAN ports, belongs to the Inteno sections that follow immediately below.

## Inteno router (ISP gateway)

### Identity

- LAN gateway at `192.168.1.1`, hostname `Inteno.lan`.
- Brand: **Inteno**, running **IOPSYS** (Inteno's own OpenWrt-based, ISP-oriented firmware — actively maintained, published API, see github.com/iopsys) with the **JUCI** web admin UI (AngularJS-based, distinct from stock OpenWrt's LuCI).
- Confirmed 2026-08-22 via `curl http://192.168.1.1/`: serves the JUCI shell, loading (among others) `juci-owsd.js`, `juci-mod-system.js` (likely reboot), `juci-network-device.js`, `juci-dnsmasq-dhcp.js` (DHCP leases — connected-device/presence data), `juci-realtime-graphs.js` (stats).
- Response header `server: owsd` confirms **`owsd`** (OpenWrt's ubus-over-websocket daemon) is live. The real API underneath JUCI is **`ubus`**, reached over a websocket at `/ubus` — not a plain HTTP JSON-RPC endpoint, so a normal `curl -X POST` won't work; need an actual websocket client.

### Auth — confirmed working, 2026-08-22

Client connects to **`ws://192.168.1.1/ubus`** (a real WebSocket, subprotocol `ubus-json` — found in `01-juci.js`: `new WebSocket(host, "ubus-json")`). There's no plain-HTTP fallback; `POST /ubus` 404s. Use Python's `websockets` library (`pip install websockets`), not `curl`.

Login call:
```json
{"jsonrpc":"2.0","id":1,"method":"call",
 "params":["00000000000000000000000000000000","session","login",
           {"username":"<user>","password":"<pass>"}]}
```
`00000000...` (32 zeros) is ubus's convention for "no session yet." Returns a `ubus_rpc_session` token — pass that (not the zeros) as `params[0]` on every subsequent call. **Session expires in 300s (`timeout`/`expires` fields in the login response)** — re-login for anything longer-running rather than assuming one token lasts a whole automation cycle.

Credentials live in `~/.config/inteno-router/env` (mode 600): `ROUTER_IP` (bare IP, e.g. `192.168.1.1` — not a URL despite the similarly-named `HOME_ASSISTANT_URL` convention elsewhere), `ROUTER_USERNAME`, `ROUTER_PASSWORD`. Extract with `grep`/`cut` in a single flat command rather than `source` (worktree-isolated sessions block `source` even for unrelated files) — same pattern as `~/.config/home-assistant/env`. Never print the password; the session token itself is short-lived and low-sensitivity by comparison, fine to handle less carefully.

### Full ACL (from a real login response, 2026-08-22)

The login response's `acls.ubus` object is an **exact, complete map** of every callable `ubus` object → its allowed methods for this account — no guessing needed, query it directly rather than trusting the summary below if it ever seems stale:

- **`router.system`**: `info`, `memory_bank`, `password_set`, `fs`, `processes` — general router stats.
- **`router.graph`**: `client_traffic`, `iface_traffic`, `load`, `connections` — live throughput/load graphs, what `juci-realtime-graphs.js` uses.
- **`router.network`**: `leases`, `dump`, `ports`, `clients` — `leases` and `clients` are exactly the connected-device data.
- **`router.net`**: `arp`, `ip_conntrack`, `ipv4_routes`, `ipv6_routes`, `ipv6_neigh`, `igmp_snooping` — ARP table useful for cross-checking actually-online vs. "has a lease".
- **`juci.system`**: `reboot`, `defaultreset`, `listusers`, `zonelist`, `led_status`, `operator_config_info` — `reboot` is the method for triggering a router reboot, object is `juci.system` (not stock OpenWrt's bare `system`).
- **`system`**: `info`, `board` — lower-level system object, also present.
- **`dsl`** / **`router.dsl`**: `status`, `stats` — DSL line stats.
- **`juci.diagnostics`**: `ping`, `traceroute`, `tptest_start`/`tptest_stop` (throughput test) — useful for running network diagnostics from the router itself instead of only from a client's side.

Confirmed working end-to-end 2026-08-22 (`router.network clients` and `router.system info`, both with real data — see example shapes below). Still untested: everything else in the ACL above — confirm each method's real output before building against an assumed shape.

### `router.network clients` — example response

```json
{"client-2": {
  "hostname": "truenas", "ipaddr": "192.168.1.142",
  "macaddr": "1c:6f:65:3f:34:21", "network": "lan", "device": "br-lan",
  "dhcp": true, "connected": true, "active_connections": 660,
  "wireless": false, "ethport": "eth6",
  "linkspeed": "Auto-negotiated 10 Mbps Full Duplex"
}, "...": "one entry per connected client, keyed client-N"}
```

Only wired LAN clients showed up in this call (all four had `"wireless": false`) — no phones/WiFi devices appeared. This isn't a gap in the query: confirmed 2026-09-20 that both `router.wireless stas` and the `wifix stations` object return empty on this router because **it isn't doing WiFi at all** — see the Synology section below. For WiFi presence on this network, query the Synology router instead.

### `router.system info` — example response

Gives `system.uptime`, `system.cpu_per`, `memoryKB.{total,used,free}`, hardware/firmware identity, and `specs` (wifi/adsl/vdsl/voice/usb capability flags) — solid stats source on its own.

### Resolved incident, 2026-08-22: a failing router port caused LAN-wide latency for one client

TrueNAS (`truenas.lan`, `192.168.1.142`) measured ~600ms latency and intermittent packet loss pinging this router directly, which cascaded into hung `docker compose`/GHCR pulls on TrueNAS (see monocoque's PR #19 history / atask 164 for the full debugging chain). TrueNAS's own CPU, memory, NIC error counters, and routing were all clean, and a second device (a Raspberry Pi on a different VLAN) pinged the same router fine at the same time — ruling out general router unhealth and pointing specifically at TrueNAS's physical link.

`router.network clients`' `linkspeed` field caught the first real clue: TrueNAS, on router port `eth6`, was negotiated at `Auto-negotiated 10 Mbps Full Duplex` while every other wired client sat at `1000 Mbps`. The port then failed further, down to no carrier at all (`ip link show` on TrueNAS itself showed `NOCARRIER`) — confirmed via two different cables and a TrueNAS reboot, neither of which changed anything, ruling out the cable and TrueNAS's own NIC. Moving TrueNAS to a different router port (`eth4`) fixed it immediately: full connectivity, `1000 Mbps Full Duplex`. **Root cause: router port `eth6` itself was failing hardware**, not TrueNAS, not the cable, and not general router health — a router reboot alone (tried earlier) did not fix it, matching a hardware port failure rather than a software/session issue.

A scheduled-reboot capability is still worth having on the router integration project regardless — it preempts a different class of problem (whatever accumulates over long uptime), even though it wasn't the fix for this specific incident.

## Synology router (behind the Inteno, does the actual WiFi/VLANs)

The Inteno is the ISP-facing box, but a **Synology router running SRM (Synology Router Manager)** sits behind it and handles all actual WiFi and network segmentation — this is why the Inteno's own wireless ubus calls (`router.wireless stas`, `wifix stations`) always come back empty: its radios simply aren't in use. The Synology shows up in the Inteno's own DHCP lease list under hostname "Puppetmaster" (`192.168.1.232`) — that's its WAN-side uplink address, not where its admin UI lives.

**Admin UI**: `https://192.168.0.1:8001/` (self-signed cert — `curl -k`). Reachable directly by IP from this agent's usual working environment too — an earlier note here claiming otherwise was wrong. The real cause was the coding tool's own default network sandboxing blocking the request; disabling that sandbox for the specific command that needs to reach the home network resolves it. mDNS (`.local`) resolution still doesn't work even with sandboxing disabled — use IPs, not `puppetmaster.local`.

**API**: SRM runs the same Web API framework as DSM — plain HTTP(S) GET requests to `/webapi/entry.cgi` (or `auth.cgi`, `query.cgi`), a real documented mechanism, not something that needs the UI. A few curl calls cover it, no SDK needed:
- **Auth**: `GET /webapi/auth.cgi?api=SYNO.API.Auth&method=Login&version=2&account=<user>&passwd=<pass>&format=sid` → `{"data":{"sid":"..."}}`. Pass that `sid` as a cookie (`id=<sid>`) on every subsequent call, not as a URL param.
- **Discover available APIs**: `GET /webapi/query.cgi?api=SYNO.API.Info&method=query&version=1&query=all` lists every callable API namespace + its `path`/`maxVersion` — but not method names, so don't guess those from this response (see below).
- **Credentials/account**: a dedicated user in Control Panel → User, with "Grant the administrator privilege to this user" ticked in its Edit dialog (SRM has no group system at all, unlike DSM — a per-user checkbox is the only way to grant admin/manager rights, and several settings 402/permission-error without it) and 2-step verification left off (the login API has no way to submit a 2FA code). Credentials live in `~/.config/synology-srm/env` (mode 600): `SRM_HOST`, `SRM_PORT` (8001), `SRM_USERNAME`, `SRM_PASSWORD` — same extraction pattern as the other `~/.config/*/env` files in this skill set.
- **Method names are undocumented** — `SYNO.API.Info` doesn't expose them, and guessing common ones (`get`/`list`/`set`) 103s more often than it hits. The fastest real source is other people's reverse-engineered clients on GitHub (`gh search code "SYNO.Wifi.Network.Setting"` turned up exact working calls immediately, e.g. `ibruzg/synology-srm-ha`'s `wifi.py`) — check there before trying to reverse-engineer the SRM web UI's own JS.
- **WiFi network config**: `SYNO.Wifi.Network.Setting`, `method=get`, `version=1` (not 2, despite `maxVersion: 2` in the API.Info listing) returns `{"profiles": [...]}`, one entry per SSID group (Primary/Guest/each custom network), each with a `radio_list` (one per band: SmartConnect/2.4G/5G-1/5G-2) carrying `enable_client_isolation` and `advance.ap_isolation` — the two candidate isolation toggles, confirmed both present as of 2026-09-20. Same API's `method=set` with a `profiles` param (JSON-encoded) writes it back.

**Three WiFi networks, confirmed 2026-09-20** (via `SYNO.Wifi.Network.Setting`):
- **Rutinerat** — main network (`network_type: primary`), the user's own personal devices. Gateway `192.168.0.1`.
- **Rutinerade saker** ("Routine things", `network_type: custom`) — the home IoT network, `192.168.3.x` (this is the network Home Assistant and its paired devices live on, described elsewhere in this skill set as "a deliberately separate network/VLAN, kept isolated for security"). Intent: IoT devices on this network should be able to reach each other locally, but often *not* the internet — internet access is blocked per-device as a deliberate privacy measure (e.g. done for a Tuya thermometer via the SRM UI), not network-wide. Uses a simpler/weaker WiFi password than the other two networks, to stay compatible with cheap IoT hardware that doesn't support stronger WPA modes. **Both `enable_client_isolation` and `ap_isolation` are already `false`** on this network's every radio — isolation is not, and was never, the cause of any local-reachability problem here.
- **Deplorables** (`network_type: guest`) — guest network. Always has internet access, never access to the main network. `enable_client_isolation: true` here (as expected for a guest network), `ap_isolation: false`.

**Resolved red herring, 2026-09-20**: a battery-powered WiFi thermometer on Rutinerade saker was completely unreachable at the network level (ARP failed, ping failed, direct TCP to its local API port failed) from a wired device on the same `192.168.3.x` subnet (the Home Assistant Pi) — even moments after the thermometer had freshly reported to its cloud service (proving it was online and WiFi-associated). AP/client isolation looked like the obvious explanation but is confirmed off on this network (see above) — ruled out entirely. The real explanation is almost certainly the device's own power-save behavior: it's a battery sensor that spends most of its time dozing (a companion device teardown project noted this exact hardware wakes for only ~10 seconds every ~55 minutes), and a dozing WiFi station commonly stays associated but doesn't reliably answer unsolicited ARP/ping/TCP probes from other LAN hosts even though it can still send its own outbound traffic on its own schedule. Opening the device's app (which nudges it to wake and report in) is the practical way to get a brief window where it actually responds to a new connection attempt from Home Assistant/LocalTuya — don't assume a failed reachability test against a battery IoT device means a network config problem without first checking whether the device is just asleep.
