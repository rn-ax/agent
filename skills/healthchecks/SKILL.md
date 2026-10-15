---
name: healthchecks
description: Use whenever the user asks about Healthchecks.io — a check showing down, the Home Assistant `healthchecksio` integration, which project a check lives in, or any need for a Healthchecks.io API key or ping URL (Contabo, TrueNAS or Home projects). This is the accumulating knowledge base for how this user's Healthchecks.io projects, credentials and Home Assistant integration are set up, so read it before hunting for a key or debugging a silent check.
---

# Healthchecks.io

This is the accumulating knowledge base for the user's Healthchecks.io setup. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content.

**Related systems**: the Home Assistant side (integration, entry, sensors) is covered in the `home-assistant` skill; the 1Password wrapper convention is in the `home` skill.

## Purpose

Healthchecks.io is the external watchdog for all of the user's systems: it lives outside the home network and the Contabo boxes, so it keeps working when everything else is down. Each system pings its own check on a schedule, and a missed ping notifies the user's phone through Pushover so they can react. A check going down therefore means the system stopped pinging (or lost its path to the internet), and that notification is the user's first signal that something is wrong.

**Coverage rule:** every individual system or component the user maintains that is expected to stay up has its own check — servers, apps, tunnels, the Home Assistant instance. Personal computers and other devices that are legitimately off or away are outside it. A new always-on system or component gets its check in the project matching where it runs, as part of setting it up.

## Credentials

The "Healthchecks" item in the "Agent" 1Password vault holds one **section per Healthchecks.io project**: `Contabo`, `TrueNAS` and `Home`. Each section has:
- `password` (concealed) — that project's API key, prefixed `hcw_`.
- `website` — the project's URL, `https://healthchecks.io/projects/<project-uuid>/`.

The item's top-level `username`/`password`/`notesPlain` fields are empty. A key only sees the checks of its own project, so pick the section matching the check.

Read it with the read-only wrapper (see the `home` skill) and select the key by its section label; field labels repeat across sections, so the section label is what identifies a key:

```sh
~/tasks/op-service-account item get Healthchecks --vault Agent --format json --reveal \
  | python3 -c "import sys,json; print([f['value'] for f in json.load(sys.stdin)['fields'] if f.get('section',{}).get('label')=='Home' and f['type']=='CONCEALED'][0])"
```

Pipe the value straight into whatever consumes it; it never needs to be printed. Rotating a key in Healthchecks.io means updating the matching section here, then anything that stored a copy (see below).

## Home Assistant integration

The `healthchecksio` custom integration (`rn-ax/ha-healthchecksio`) does two jobs per config entry: it pings the entry's `check` (the check's UUID, `https://hc-ping.com/<uuid>`) on every 5-minute coordinator update, and it lists the project's checks through `/api/v1/checks/` to create one `binary_sensor` per check. The Home Assistant check's UUID is `62ee8b72-f7d6-443c-9c77-1aa5ce07beb3`, in the `Home` project.

- **The key is stored in the config entry** (`api_key`), a copy of the 1Password value. After a rotation the entry has to be recreated with the new key: remove it with `DELETE /api/config/config_entries/entry/<id>`, then start a `healthchecksio` flow (`api_key`, `check`, `self_hosted: false`) over the config-entries REST API. The installed flow has no reconfigure step.
- **An invalid key silences the ping.** Healthchecks.io answers `401 {"error": "wrong api key"}`, the integration receives a JSON body without `checks`, creates zero sensors, and a coordinator with no listeners stops polling — so the ping stops too, while the entry still shows `loaded` and nothing is logged. A check that goes down while its entry reads `loaded` and its sensors read `unavailable` is this case; test the stored key against `/api/v1/checks/` from the Pi.
- **Sensors cover one project per entry.** The key decides which project's checks become sensors, so the TrueNAS and Contabo checks need their own entries with their own section's key.
