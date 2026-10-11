---
name: homebox
description: Use whenever the user asks about their home inventory — what they own, specs/manuals/warranty for an item, adding or updating an item, or anything about "homebox" explicitly. This is the accumulating knowledge base for how this user's Homebox instance is set up and how to talk to its API, so read it before assuming access method, API shape, or inventory conventions from scratch.
---

# Homebox

The user's home inventory: everything they own (loosely defined), with exact specs, links to relevant pages, and PDF manuals, searchable by an agent.

**Related systems**: Homebox runs as an app on TrueNAS — see the `truenas` skill for the install playbook and `apps.md` for this app's install notes; `home` has the topology map.

## Instance

Runs as the `homebox` app from TrueNAS's `community` catalog train. The LAN URL is `http://truenas.lan:30149`; there is no public Cloudflare route.

API credentials live in the "Homebox" item in the "Agent" 1Password vault: `password` = API token, the **website** URL = base URL. The URL sits in the item's `urls` array rather than `fields`, so it needs `item get --format json | jq -r '.urls[0].href'`.

Use `hb-api <method> <path> [curl-args...]` (this skill's own directory) for an authenticated call. `<path>` is relative to `<base_url>/api/v1`, e.g. `hb-api GET '/entities?q=mac&pageSize=5'`. Like `wm-api`, it goes through `~/tasks/op-service-account`, so it needs that machine's `op-service-account-agent` Keychain entry set up first. Multipart uploads (`-F`) work: the wrapper only sets a JSON content type when no `-F` is passed.

## API shape (v0.26)

The live OpenAPI spec is at `<base_url>/swagger/doc.json` (UI at `/swagger/index.html`); read it rather than guessing routes.

This version names things differently from older Homebox docs and blog posts:
- Inventory records are **entities** (`/entities`), not items. Locations are entities too, distinguished by `/entity-types`; `/entities/tree` returns the hierarchy.
- Labels are **tags** (`/tags`).
- `/entities/fields` and `/entities/fields/values` list the custom field names and values already in use — check these before inventing a new custom field name, so specs stay consistent across items.
- Attachments: `POST /entities/{id}/attachments` uploads a file; `POST /entities/{id}/attachments/external` links one by URL.
- `/templates` and `/templates/{id}/create-item` create items from a reusable field set.
- `/group/exports` and `/entities/export` produce backups; `/actions/wipe-inventory` deletes everything, so treat it as off-limits without explicit instruction.
