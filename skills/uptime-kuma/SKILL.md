---
name: uptime-kuma
description: Use whenever the user asks whether an app or service is up, about uptime monitoring or alerting for the TrueNAS apps, adding or changing a monitor, or anything about "uptime kuma" explicitly. This is the accumulating knowledge base for how this user's Uptime Kuma instance is set up and how an agent drives it, so read it before adding a monitor to a new app or assuming how an app is monitored.
---

# Uptime Kuma

This is the accumulating knowledge base for the user's Uptime Kuma. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content.

**Related systems**: Kuma runs on TrueNAS (see the `truenas` skill for the install playbook and dataset conventions). Kuma watches everything on TrueNAS; Healthchecks.io watches TrueNAS, Kuma itself and the systems outside TrueNAS (see the `healthchecks` skill).

## Role

Kuma is the monitor for every app on TrueNAS. It actively probes each app, so an app needs no ping logic of its own. Expectation: every TrueNAS app has a monitor, and a new app gets its monitor as part of being installed. Kuma dies together with TrueNAS, so an external watcher covers that (Healthchecks.io, see below).

## Instance

Catalog app `uptime-kuma` (community train), web UI on `http://truenas.lan:31050` (LAN only). Data is a single SQLite database under `/app/data`, a host-path mount at `/mnt/Storage/Configuration/uptime-kuma/data`.

The container runs as root with all capabilities dropped except `NET_RAW`. Root without `CAP_DAC_OVERRIDE` obeys file permissions, so the data directory keeps `apps:apps` ownership and carries a POSIX ACL granting `root` (UID 0) `rwx`, access and default (`setfacl -R -m u:0:rwx -d -m u:0:rwx`). Without that grant the container crash-loops on `EACCES: mkdir 'data/upload/'`.

The Docker socket is not mounted: it gives the container root-equivalent control of the host's Docker. Container-state checks go through a push monitor (see "Apps with no network surface").

The "Uptime Kuma" item of the "Agent" 1Password vault holds an API key in `password`. The user's own login (`samuel`) is held by the user and not available to agents.

## Reading status: `kuma-api`

`kuma-api <path>` (this skill's directory) calls Kuma over HTTP with the API key from the 1Password item, the same way `wm-api` does for Windmill. The key opens `/metrics`, the Prometheus text endpoint, which carries every monitor's state:

```sh
kuma-api /metrics | grep '^monitor_status'
```

Each `monitor_status{monitor_name="…",monitor_type="…",…}` line ends in `1` (up), `0` (down), `2` (pending) or `3` (maintenance). `monitor_response_time` and `monitor_cert_days_remaining` sit alongside. API keys authenticate only these HTTP endpoints; the socket.io API below needs the user's login.

## Changing monitors

Changes go through Kuma's socket.io API, which has no REST equivalent and authenticates with the user's login rather than the API key. A task that adds or edits monitors therefore needs the user to supply the login for that run. Use the `uptime-kuma-api-v2` Python library (it targets Kuma 2.x):

```sh
uv run --no-project --with uptime-kuma-api-v2 python -I script.py
```

with `api = UptimeKumaApi('http://truenas.lan:31050'); api.login(user, password)`; never print the password. Behaviours worth knowing:
- `add_monitor(type=MonitorType.…, name=…, interval=60, retryInterval=60, maxretries=3, …)`; `get_monitors()` lists them; `get_monitor_beats(id, hours)` returns recent heartbeats (the last entry's `status` and `msg` say why a monitor is down).
- A `JSON_QUERY` monitor needs `jsonPathOperator='=='` next to `jsonPath` and `expectedValue`; without it every check fails with "Invalid condition null".
- A `PUSH` monitor gets its token from the server on creation; read it back with `get_monitor(id)['pushToken']`. The push URL is `/api/push/<token>?status=up`.
- The library has no wrapper for every field; `api._call('editMonitor', monitor_dict)` sends the raw socket event.

## Monitor conventions

All monitors use a 60 second interval with 3 retries (60 second retry interval), so an outage alerts after about four minutes. Names are the app's title (`Radarr`, `Eclipse Mosquitto`).

| Kind | Monitor | Apps |
|---|---|---|
| Apps with a JSON health endpoint | `JSON_QUERY` on `http://truenas.lan:<port>/ping`, `status == OK` | Radarr, Sonarr, Prowlarr, Bookshelf |
| Web apps | `HTTP` on the app's own health or login URL, accepting `200-299`, `300-399`, `401` | the rest of the web apps; where an app has a dedicated endpoint it is used (`/api/health` for Beszel, `/api/v1/status` for Homebox and Seerr, `/identity` for Plex, `/api/version` for Windmill, `/status` for Tautulli, `/accounts/login/` for Paperless) |
| TCP services | `PORT` on `truenas.lan:<port>` | Redis, Eclipse Mosquitto |
| Apps behind the tunnel | `HTTP` on the public hostname, which exercises Cloudflare end to end | Butterfly (no published port), Cloudflared (`https://rn.ax/`) |
| Apps with no network surface | `PUSH` monitor fed by a TrueNAS cron job | Beszel Agent |

### Apps with no network surface

An app that exposes no port (the Beszel agent connects out to the hub) is checked by a TrueNAS cron job that runs as root every minute: `[ "$(docker inspect -f '{{.State.Running}}' <container>)" = true ] && curl -fsS -m 10 -o /dev/null "http://127.0.0.1:31050/api/push/<token>?status=up"`, paired with a `PUSH` monitor whose interval is 180 seconds. The cron job is created with `cronjob.create`; to change a cron job use `ssh truenas 'sudo midclt call cronjob.update <id> "$(cat)"' <<<'{"command": …}'` (the `tn-api` wrapper passes a single parameter, which `*.update` calls need two of).

## Watching Kuma itself

The Healthchecks.io check "Uptime Kuma" is pinged by the TrueNAS cron job "Uptime Kuma healthcheck" every 5 minutes. It requests `http://127.0.0.1:31050/api/entry-page` and pings only when the answer contains `entryPage`, so a stopped or wedged Kuma stops pinging and Healthchecks.io alerts.
