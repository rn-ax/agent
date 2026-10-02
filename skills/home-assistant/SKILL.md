---
name: home-assistant
description: Use whenever the user asks for help with Home Assistant — automations, integrations, dashboards, entities, or anything touching their smart-home setup — and whenever a task involves their Inteno home router (stats, connected-device/presence detection, remote reboot), even if they don't say "Home Assistant" explicitly. This is the accumulating knowledge base for how this user's Home Assistant instance and connected devices are actually set up, so read it before assuming HA's location, auth method, or any device's capabilities from scratch.
---

# Home Assistant

This is the accumulating knowledge base for the user's Home Assistant setup. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content. If a section below is marked **TBD**, ask the user rather than assuming, and update this file once you learn the answer so the next session doesn't have to ask again.

**Related systems**: see the `home` skill for the full topology map. Home Assistant runs on a network-isolated VLAN separate from TrueNAS and the rest of the LAN (see `home-network`) — confirm reachability explicitly before assuming any integration with `windmill` or another TrueNAS-hosted app can just talk to it directly.

## Instance

Runs on a **Raspberry Pi 5**, on `192.168.3.71:8123` — a deliberately separate network/VLAN from the main LAN (192.168.1.x, where TrueNAS and the router live), kept isolated for security. This is why it isn't reachable via `docker ps -a` on TrueNAS (different device entirely) and why `homeassistant.local` (mDNS) stopped resolving at some point — mDNS generally doesn't cross subnet/VLAN boundaries without a reflector, so use the IP directly, not the `.local` name, unless/until that's set up.

**Also reachable publicly via Nabu Casa remote access, confirmed working 2026-08-22.** The same REST/websocket API, same token, works over `https://home.rutinerad.com` — this is the path to use for anything that needs to reach the instance from somewhere that can't be on the LAN/VLAN (e.g. a GitHub Actions runner that isn't self-hosted on this network). Never put this URL in a public repo's tracked files or a plain (non-secret) CI variable — it's personal/identifying the same way the local IP would be; use a repo secret if wiring it into a workflow.

Confirmed reachable: `GET http://192.168.3.71:8123/` serves the real HA frontend; `GET http://192.168.3.71:8123/api/` returns `401: Unauthorized` (expected — confirms the REST API is live and just needs a token).

**Auth: confirmed working.** Long-lived access token stored in `~/.config/home-assistant/env` (mode 600) as `HOME_ASSISTANT_TOKEN`, alongside `HOME_ASSISTANT_URL`. Don't `source` that file directly in a worktree-isolated session — the sandbox blocks `source` even for unrelated files; instead extract the value with `grep '^HOME_ASSISTANT_TOKEN=' ~/.config/home-assistant/env | cut -d= -f2-` in a single flat command. Verified 2026-08-22: `curl -H "Authorization: Bearer $TOKEN" http://192.168.3.71:8123/api/` returns `{"message":"API running."}`, HTTP 200. Never echo/print the token value itself in output.

Being on a separate, security-isolated network matters for anything that needs to reach the router (e.g. triggering a reboot from HA): confirm a network path from this Pi's VLAN to the router's admin interface on 192.168.1.1 exists before assuming HA can reach it at all, rather than only checking once an automation is written. Confirmed 2026-08-22: the path exists — a plain `ping 192.168.1.1` from the Pi got 0.86–1.3ms, 0% loss.

**SSH/root access — confirmed working 2026-08-22.** `ssh root@192.168.3.71` using the default key (`~/.ssh/id_ed25519`) — found via a long-abandoned `~/Projects/hass-config/.vscode/sftp.json` (an old VSCode SFTP remote-edit config pointing at `homeassistant.local:/config`, username `root`). That hostname no longer resolves (see mDNS note above), but the same host answers at `192.168.3.71` with an identical host key — added a fresh known_hosts entry for the IP rather than relying on the stale hostname. Config root is `/config`, and `/config/custom_components/` is exactly where a new integration's code goes to be picked up by HA.

**HACS is already installed** (`/config/custom_components/hacs`), and other custom integrations already present: `aarlo`, `grocy`, `healthchecksio` (matches monocoque apps' `healthcheck_id` pattern), `spook`, and — notably — `truenas` (worth checking what it already surfaces before assuming nothing covers TrueNAS-side monitoring).

**Scripts in this skill directory** (`~/.claude/skills/home-assistant/`) — read each script's own header comment for details, not duplicated here:
- `hacs-install <owner/repo> <category>` — installs a custom repository through HACS.
- `wait-ready` — run after any HA restart, before checking entities/config-entry state.
- `ws-call '<json payload>'` — sends one ad-hoc command over HA's websocket API and prints the result; reach for this before writing a one-off Python websocket script (e.g. renaming a config entry via `config_entries/update`, or any other command not reachable over the REST API).

**Restarting HA core is slow and disruptive on this instance** (it has a lot of integrations — Sonos, MQTT, ESPHome, etc. — full startup takes a couple of minutes) — treat it as a real cost, not a routine step after every deploy. It's only actually necessary for a **Python code change**: HA caches imported modules in memory, so editing a `.py` file in `custom_components/` and reloading the config entry alone reuses the stale in-memory version, not what's on disk — only a full core restart re-imports it. A config-entry reload (no restart) is enough for anything that doesn't change code (re-reading YAML config, retrying a failed setup, picking up a HACS download once `pending-restart` has already cleared some other way). When multiple code changes are coming in the same session, batch them into one `rsync` + one restart instead of restarting after each file.

## Router monitoring/control project

Tracked as atask 185 (parent) and its children — check `atask show 185` for current status rather than assuming this file has it. The integration itself lives in `rn-ax/ha-inteno-router`.

## HomeKit Bridge

This instance uses several separate `homekit` config entries rather than one bridge exposing everything — each scoped to a specific purpose (e.g. "HASS Bridge" exposes just the `light` domain, "HASS Bridge 7L" exposes just `button` for the router reboot button). Follow that same pattern rather than adding new entities to an existing bridge or widening its domain list, since HomeKit has a per-bridge accessory limit and a domain-wide bridge silently picks up every future entity in that domain, not just the ones intended.

The whole flow is driveable via the config-entries REST API, the same pattern used for creating the Cover Group above:
1. `POST /api/config/config_entries/flow` with `{"handler": "homekit", "show_advanced_options": false}` starts a new bridge. The first step asks for `include_domains` (multi-select) — this is only a coarse starting filter, not the final entity list.
2. Submitting that step goes straight to a `pairing` step with no further choices; submitting `{}` there creates the entry (`state: loaded`) and assigns it a bridge name/port.
3. To scope it down to specific entities rather than a whole domain, open its **options** flow (`POST /api/config/config_entries/options/flow` with `{"handler": "<entry_id>"}`), then submit `{"mode": "bridge", "include_exclude_mode": "include", "domains": []}` — leaving `domains` empty (even though the field is marked required, an empty list is a valid value) means only the explicit entity list matters, not a whole-domain include. The next step accepts `{"entities": ["cover.x", "cover.y"]}` for exactly the entities wanted. A further optional `bridged_device_triggers` step follows for bridging buttons/remotes as HomeKit triggers — submit `{"devices": []}` to skip it and finish.
4. Saving options triggers `homekit`'s own update listener to reload that entry automatically (`state` stays `loaded`, `modified_at` bumps) — no full HA restart needed, same as any other options-only change.
5. A newly-created bridge still needs pairing in the Home app before it's usable — there's no REST endpoint that returns the pairing code/QR; it's only shown in the HA frontend under Settings → Devices & Services → the bridge's device page.
6. A bridge's default title (e.g. "HASS Bridge T1") isn't set during creation and isn't editable through the REST config-entries endpoint (405) — rename it with `ws-call '{"type": "config_entries/update", "entry_id": "<entry_id>", "title": "<name>"}'` instead. Reloads with `require_restart: false`, same as any options change.

Re-opening an options flow without submitting its final step (e.g. just to inspect current settings) leaves a pending flow session — clean it up with `DELETE /api/config/config_entries/options/flow/<flow_id>` (or `.../flow/<flow_id>` for a regular config flow) rather than letting it dangle.

## YAML config layout & conventions

`configuration.yaml` splits domains out into their own included files. Known ones:
- `template: !include templates.yaml` — all template entities live here. The file's top level is a **list** of template blocks; each block is either trigger-based (`- trigger:` + `sensor:`) or plain (`- sensor:`). Reload without a restart via the `template.reload` service (`POST /api/services/template/reload`) or Developer Tools → YAML → "Template entities".
- `automation: !include automations.yaml` — UI-managed. Create/update one without hand-editing the file via `POST /api/config/automation/config/<id>` (body is the automation minus `id`); HA writes it and reloads.

**Custom Jinja macros** live in `/config/custom_templates/*.jinja`, imported per use like `{% from 'formatting.jinja' import duration %}` (works in template entities, automations, scripts). After editing one, call `homeassistant.reload_custom_templates`, then `template.reload` for any template entity that imports it. What's there:
- `formatting.jinja` — `duration(seconds, min_unit='s')` → compact human duration (`"1h 02m 05s"`, `"1h 35m"` with `min_unit='m'`). Use it instead of hand-rolling h/m/s math.
- `mappings.jinja` — Grocy chore lookups and `user_name_to_notify('samuel'|'amanda'|'olivia'|'madde')` → that person's `notify.mobile_app_*` service (Samuel = `notify.mobile_app_rutinerad_iphone`).

**Friendly-name convention for user-authored entities: `<Area or Device> · <Thing>`** — space-middot-space separator, Title Case on both sides (e.g. `Smoker · Cook Started`, `Smoker · Cook Time`). Set it with `name:` on the template entity; also set `unique_id:` so the entity_id stays stable. HA slugifies the name for the entity_id, dropping the `·` (`Smoker · Cook Started` → `sensor.smoker_cook_started`).

**Language: Swedish for anything named by the user or the agent** — helpers, template entities, HomeKit bridge titles, and automation/script aliases alike, e.g. `Sovmorgon`, `Läggdags`, `Läggdags · Förbered rummet`. Confirmed explicitly 2026-09: "Anything you name should be in swedish." This only applies where a name is actually being chosen; a device or integration's own default name (e.g. "IKEA of Sweden TRADFRI bulb...", "Rutinerad skärm") stays as-is even when it's English, since the user hasn't bothered overriding it. Existing automation aliases predate this rule and are a mix of Swedish and English — don't read that mix as license; every new name the agent picks (entity `name:`, automation `alias:`, script `alias:`, bridge `title:`, entity_id slugs derived from them) defaults to Swedish, translated to match the household's existing tone (`·` separator, e.g. `Kök · Alarm vattenläckage i kylskåp`). Ask only if a natural translation isn't obvious.

## Grouping related entities across domains

Four separate mechanisms exist, each with a different scope — reach for the narrowest one that fits rather than defaulting to naming convention alone:

- **Device** — entities from one integration config entry that represent one physical thing (e.g. all `climate`/`sensor`/`switch`/`binary_sensor`/`number` entities the `traeger` integration creates for the grill share device id `24d0775a84de08d3d9e1c178e8d9412a`, named "Happy Grillmore"/"Smoker"). This grouping is automatic from the integration and can't be retrofitted onto template entities or automations, which have no device.
- **Category** (`config/category_registry/{list,create}` with a `scope`, e.g. `"automation"` or `"script"`) — a named folder *within one domain's own UI list*, set per-entity via `entity_registry/update`'s `categories: {"automation": "<category_id>"}`. Automations and scripts get their own category namespaces; a category created under `scope: "automation"` only ever shows up filtering the Automations list, not entities. This instance already had a "Smoker" automation category (`01M1K5TBNYEJPFTM9MBT0EB31E`, alongside "Barnen"/"Arbete"/"Grocy"/"Sova") in use for the smoker automations before this was ever written down here — check `config/category_registry/list` for existing categories before creating a new one, and assign any new automation to the matching one if it belongs to a system that already has one.
- **Label** (`config/label_registry/{list,create}`, then `labels: ["<label_id>"]` via `entity_registry/update` for an entity or `device_registry/update` for a device) — the only mechanism that spans every domain (sensors, binary_sensors, helpers, template entities, automations, scripts, devices) and isn't tied to one physical device or one domain's own list. This is the right tool for "these things conceptually belong together" when they're a mix of a device's own entities, template entities/helpers built on top, and automations — e.g. label `smoker` (created 2026-10, icon `mdi:grill`) is applied to the Traeger device itself plus every custom `sensor.smoker_*`/`binary_sensor.smoker_*`/`input_boolean.smoker_wrapped` template entity and all four `automation.smoker_*` entities, so the whole cook-lifecycle system is one filterable group regardless of where each piece's logic happens to live.
- **Area** — physical location. Every entity (not just devices) carries its own `area_id` in the entity registry and can be set directly regardless of domain, overriding whatever area its device (if any) belongs to — but this is a "where", not a "what system is this part of", so it's the wrong tool for grouping a feature built from a device + template entities + automations unless that whole feature happens to live in one room.

None of these replace the friendly-name convention above (`<Area or Device> · <Thing>`) — that's still what makes entities legible at a glance in pickers and history. Labels/Categories are for filtering and dashboard/automation-list organization on top of that.

## Battery monitoring

**Battery Notes** (HACS integration `andrew-codechimp/HA-Battery-Notes`) is the mechanism for tracking low batteries. Config entry id `01M1VSF1CHSDFA8N647N0C874Q`, default low threshold 10%, autodiscovery on. A "battery note" is attached per device as a `battery_note` subentry; each one adds `sensor.<device>_battery_plus` (battery % with metadata), `sensor.<device>_battery_type`, `sensor.<device>_battery_last_replaced`, `binary_sensor.<device>_battery_plus_low`, and `button.<device>_battery_replaced` (press when the battery is swapped). This version has no global aggregate entity — cross-device state comes from the `battery_notes_battery_threshold` event.

**Which devices get a note:** anything with a replaceable or standalone battery that stays in place and would otherwise die silently — sensors, remotes, alarms, blinds, cameras, doorbells — at the 10% default threshold. Devices that get charged routinely (phones, tablets, laptops, watches, the robot vacuum) stay out, since a daily dip below 10% is normal for them; the exception is giving such a device a note with a low single-digit threshold when a genuine "charge it now" alert is wanted. `battery_type`/`battery_quantity` on each note are informational (they drive the "2× AAA" label and replacement reminders), so a rough guess by device model is fine and can be corrected later in the subentry.

**Adding a device via API** (no restart needed): `POST /api/config/config_entries/subentries/flow` with `{"handler": ["01M1VSF1CHSDFA8N647N0C874Q", "battery_note"]}` → submit `{"next_step_id": "device"}` → submit `{"device_id": "<id>"}` → submit the `battery` step: `battery_type` (text, required), `battery_quantity` (int, required), `note` (""), `battery_low_threshold` (0 = use the 10% default), `battery_increase_threshold` (0), `advanced_settings` ({} or `{"filter_outliers": false}` — the section is required even when empty).

**Automation `automation.battery_notes_low_battery_notification`** (id `1788713400000`) notifies Samuel's iPhone on the `battery_notes_battery_threshold` event when `battery_low` is true, and again on Battery Notes' own periodic reminder (event carries `reminder: true`) while a device stays low. It covers every tracked device, so per-device low-battery automations aren't needed. Event data keys: `device_id`, `area_name`, `device_name`, `battery_low`, `battery_level`, `battery_low_threshold`, `battery_type_and_quantity`, `battery_type`, `battery_quantity`, `previous_battery_level`, `battery_last_replaced`, `reminder`.

## iOS Shortcuts / Focus integration

The Companion App's **"Perform Action"** Shortcuts action (call any HA service from a Shortcut) has worked since iOS 17 — not new, not version-gated beyond that.

**Sleep Focus specifically couldn't trigger a Shortcuts automation before iOS 27.** Apple's Focus-based automation trigger (Shortcuts → Automation → Focus) supported every Focus mode except Sleep prior to iOS 27; iOS 27 (released 2026-09-14) is what added Sleep to that list. So a "when Sleep Focus turns on/off → Perform Action" automation is only buildable on iOS 27+; on earlier iOS, "Home Assistant" not showing up isn't an app-registration problem, it's that the whole automation type doesn't exist yet for that specific Focus. Source: https://www.derekseaman.com/2026/08/ios-27-flips-the-script-home-assistant-can-now-control-your-apple-devices.html

## Device & entity notes

`references/devices.md` holds per-device knowledge that the config and entity list don't show on their own — behavioural quirks, what a misleadingly-named entity actually means, why a custom entity was built a certain way. Read the relevant section when a task touches a specific device, and add one when you set a device up (keep it to what's *not* already readable from Developer Tools). Covered so far: Traeger smoker.

## TrueNAS integration

The `tomaae/homeassistant-truenas` HACS integration (`custom_components/truenas`) is installed and configured (entry `01JCQYAWKHM6N4BG7SH14X36F6`). Confirmed 2026-09-13 what it does and doesn't cover for app updates:

- Each TrueNAS app gets a `binary_sensor.truenas_apps_<name>` (running/stopped) whose attributes include `update_available` and `image_updates_available` — usable for tracking/notifying on pending app updates.
- There is no per-app `update` entity and no service to trigger an app upgrade — the only app-related services are `app_start`/`app_stop`. The integration's one `update` entity (`system_update`) covers the TrueNAS OS version only, not apps.
- Triggering an actual app update therefore isn't native to this integration; it would need a `shell_command`/`rest_command` automation calling TrueNAS's own `midclt call app.upgrade '["<app>"]'` over SSH, gated on the `update_available` attribute above.
- As of 2026-09-13 the config entry itself was in `setup_retry` ("TrueNas Disconnected"), so all `truenas_apps_*` sensors read `unavailable` — check `state`/`reason` on this entry before trusting any TrueNAS entity's data.

## Plex integration

Config entry `01JCETA417DYYQXTPSD48Y4MFG`, server "TrueNAS" at `192.168.1.142:32400` (the TrueNAS Plex app — confirmed up and running fine via `binary_sensor.truenas_apps_plex` whenever this has come up, so an auth failure here is not a reachability problem on the Plex Media Server side).

**Auth failures show up as `state: setup_error`** with `reason: "Token not accepted, please reauthenticate Plex server 'TrueNAS'"` on the config entry, sourced from a `homeassistant.components.plex.server` log line `Not authorized to access plex.tv with provided token` — this is plex.tv itself rejecting HA's stored API token (account-level revocation, password change, or the device being removed from plex.tv's Authorized Devices list), not a local network/connection issue. Diagnose by checking the config entry's `reason` field and grepping `ha core logs` for `plex`, rather than assuming it's the same class of problem as a local integration losing its device.

**Reauthenticating through the UI can itself crash** with a `StopIteration`/`RuntimeError` inside `plex/server.py`'s `_connect_with_token` (`homeassistant.components.plex` "Unknown error connecting to Plex server") — this happens when the freshly-authenticated plex.tv account's server resource list doesn't contain a server matching the config entry's stored `clientIdentifier`. Confirmed this occurs when the reauth flow's Plex account (or its resource-list timing) doesn't line up with the account that actually owns/shares the "TrueNAS" server. If "Reauthenticate" hits this crash, don't keep retrying the same repair flow — remove the Plex integration entirely and re-add it fresh (Settings → Devices & Services → Add Integration → Plex → sign in), which goes through full server discovery instead of matching against the old stored identifier. Double-check which Plex.tv account is used during sign-in.

## Dashboards / Lovelace

**Editing a storage-mode dashboard programmatically**: don't hand-edit `.storage/lovelace.lovelace` while HA is running — reads can catch a stale pre-flush snapshot (the Store's save is debounced by a few seconds; the same lag applies to `core.device_registry`/`core.entity_registry` — verify a just-made registry change over the live websocket API, e.g. `config/device_registry/list`, not by cating the file right after). Fetch and save the real config over the websocket API instead: `ws-call '{"type": "lovelace/config"}'` returns the full config (all views/sections/cards) for the default dashboard; mutate the Python dict and send it back with `{"type": "lovelace/config/save", "config": <the whole modified config>}`. `ws_call.py`'s single ad-hoc call doesn't fit a fetch-then-mutate-then-save round trip — write a one-off script using the same connect/auth pattern as `ws_call.py` (see its source) instead of trying to chain multiple `ws-call` invocations by hand. Non-default dashboards take a `"url_path"` key alongside `"type"` in both calls.

**`flex-table-card`** (HACS plugin, `custom-cards/flex-table-card` — install via `hacs-install custom-cards/flex-table-card plugin`) turns a sensor's list-valued attribute into an actual sortable table, which is the standard fit whenever a sensor exposes `{"some_attr": [{...}, {...}]}` for display. Config shape:
```yaml
type: custom:flex-table-card
entities:
  include: sensor.some_sensor
columns:
  - name: Column Label
    attr_as_list: some_attr   # the list-valued attribute name
    modify: x.field_name      # x is each list item; can be a JS expression, e.g. x.a + x.b
sort_by: field_name-          # trailing '-' = descending
```
`attr_as_list` is what expands the list into rows — without it, `flex-table-card`'s default mode treats each *entity* (via `entities.include` as a regex) as one row instead, which doesn't apply here.

**Collapsible content without a new plugin**: a plain built-in `markdown` card renders raw HTML, including a `<details><summary>...</summary>...</details>` block — this is enough for a "click to expand" section (e.g. a long history table) with no extra HACS card. A markdown table needs a blank line before and after it inside the `<details>` block, same as top-level CommonMark. The card's `content:` field is itself templated live (Jinja), so a `{% for %}` loop over a sensor attribute works directly inside it — write the template to a plain string first and preview it with `POST /api/template {"template": "..."}` before pasting it into the dashboard, since a spacing mistake silently breaks the table rather than erroring.

**`apexcharts-card`** (HACS plugin, `RomRider/apexcharts-card`) is the fit for an actual line/bar chart driven by a sensor's list-valued attribute, via its `data_generator` option — a JS function body (as a YAML string) that returns `[timestamp_ms, value][]`:
```yaml
type: custom:apexcharts-card
graph_span: 90d      # must cover the actual data range; card-level, no per-series override
series:
  - entity: sensor.some_sensor
    type: column      # column = vertical bars ("bar" is horizontal in ApexCharts' own terms); line/area also supported
    data_generator: |
      return entity.attributes.some_attr.map(w => [new Date(w.some_date_field).getTime(), w.some_value_field]);
```
`data_generator` bypasses the card's normal history-fetch/caching entirely, so nothing needs to be recorded to long-term statistics for this to work — it just re-reads the entity's live attribute on every update.

## General Home Assistant help

Once the instance location and auth are known, standard ways to help:

- **YAML automations/scripts**: Home Assistant config is YAML-first even when authored through the UI. If the user pastes an automation or asks to write one, standard HA YAML conventions apply (triggers/conditions/actions, `service:`/`action:` calls, entity IDs like `domain.object_id`).
- **REST API**: `https://<instance>/api/...` with `Authorization: Bearer <long-lived token>` — useful for scripted stats-pulling or one-off queries outside of writing a full integration.
- **Custom integrations vs. scripting from outside**: A real `custom_components/` integration (Python, installed into HA itself) is the way to add support for hardware HA doesn't already know about — configurable through HA's own UI, restart-safe, manageable like any other integration. Reach for HA's REST API from an external script instead only for a genuine one-off query, not for anything meant to run continuously.
