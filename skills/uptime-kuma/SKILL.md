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

The "Uptime Kuma" item of the "Agent" 1Password vault holds the login (`username`, `password`), the LAN and public (`https://kuma.rn.ax/`) URLs, and an `api key` field.

## Driving it: `kuma-api`

`kuma-api <method> [json-args]` (this skill's directory) logs in as the user from the "Uptime Kuma" 1Password item (`username`, `password`, and the first URL as base) and calls one method of the `uptime-kuma-api-v2` Python library, with the JSON object as keyword arguments:

```sh
kuma-api status                                   # one line per monitor: state, type, name, last message
kuma-api get_monitors
kuma-api add_monitor '{"type": "http", "name": "Foo", "url": "http://truenas.lan:1234/", "interval": 60, "retryInterval": 60, "maxretries": 3}'
kuma-api edit_monitor '{"id_": 5, "maxretries": 3}'
```

Kuma's API is socket.io only (no REST), and this library is the client; its method names and fields are what the wrapper accepts. A `type` string converts to the library's `MonitorType` (`NotificationType` for `*_notification` methods). Behaviours worth knowing:
- `get_monitor_beats(id_, hours)` returns recent heartbeats; the last entry's `status` and `msg` say why a monitor is down.
- A `json-query` monitor needs `"jsonPathOperator": "=="` next to `jsonPath` and `expectedValue`; without it every check fails with "Invalid condition null".
- A `push` monitor gets its token from the server on creation; read it back with `get_monitor` (`pushToken`). The push URL is `/api/push/<token>?status=up`.
- A field the library has no keyword for can still be set through the raw socket event from a script: `api._call('editMonitor', monitor_dict)`.

The item also carries an `api key` field. Kuma API keys authenticate only the Prometheus `/metrics` endpoint (basic auth, empty username), which `kuma-api` does not use.

## Alerting

A notification named `Pushover` (the `Uptime Kuma` application token, see the `pushover` skill) is default-enabled and attached to every monitor, so a monitor that goes down notifies the user's phone. A new monitor created through `kuma-api add_monitor` gets the default notification only when `notificationIDList` names it (`{"1": true}` for the Pushover notification); pass it explicitly.

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
