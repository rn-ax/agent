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

## Inventory conventions

Homebox's model: locations nest (room → shelf → box) and hold items; items can hold child items; tags group across the tree; templates and entity types pre-fill fields. The conventions below keep records consistent so an agent can search them.

- **Locations** are physical places. A new account is seeded with default rooms (Attic, Basement, Bathroom, Bedroom, Garage, Kitchen, Living Room, Office); items go into these or into shelves/boxes nested under them.
- **Item names** read as `Product (year, variant)` — recognisable in a list, e.g. `Mac mini (2023, M2 Pro)`.
- **Built-in fields first**: `manufacturer`, `modelNumber`, `serialNumber`, `purchaseDate`/`purchasePrice`/`purchaseFrom`, `warrantyExpires`/`warrantyDetails`, `lifetimeWarranty`, `notes`. A fact that has a built-in field stays out of custom fields.
- **Custom fields** carry the remaining specs. Names are Title Case and reused across items — check `GET /entities/fields` for names already in use before inventing one. Values carry their unit (`16 GB unified`). The API accepts `text`, `number`, `boolean` and `time` types; use `text` for specs so the unit stays attached.
- **Links** go in a text custom field as markdown, `[Label](https://…)`, which Homebox renders as a clickable button.
- **Child items** model parts that have their own serial or warranty — a server's disks are children of the server item.
- **Tags** are lowercase single words (`computer`, `homelab`, `storage`) and describe what the item is or does.
- **Attachments** use the type that matches the file (`manual`, `warranty`, `photo` or `attachment`); see "Documents worth attaching" for what to include.
- **Description** is markdown and holds the one-line "what is this and what is it for".

## Documents worth attaching

An attachment earns its place when someone (or an agent) would open it to operate, maintain, repair, or claim on the item.

| Document | Attachment type |
|---|---|
| User manual / setup guide | `manual` |
| Installation, service, or repair manual | `manual` |
| Spec sheet / datasheet with exact ratings (power, dimensions, capacity, pinouts) | `attachment` |
| Warranty card or terms | `warranty` |
| Parts list or exploded diagram | `attachment` |
| Maintenance schedule, wiring or plumbing diagram | `attachment` |
| Photos of the item, its label, and its serial plate | `photo` |

Receipts and invoices live in Paperless; Homebox records the purchase facts in the built-in `purchaseDate`, `purchasePrice` and `purchaseFrom` fields.

Documents that stay out: environmental reports, regulatory and compliance declarations, marketing brochures, release notes, and legal-only leaflets that ship in the box. A manual that exists only as a web page is recorded as a link in a custom field (for example `Manual`).

Attachment names state the document and language, such as `User Manual (English)`. The official vendor PDF in the owner's language is preferred; one comprehensive manual beats several fragments.

## Adding an item

1. Read what exists: `GET /tags`, `GET /entities/fields`, `GET /entities/tree`.
2. Collect exact specs from an authoritative source — a command on the device itself (`system_profiler SPHardwareDataType`, `lscpu`, `dmidecode`, `lsblk -o NAME,MODEL,SERIAL`) or the vendor's spec page.
3. `POST /entities` with `name`, `parentId`, `quantity` and `tagIds`; the create call accepts only these basics.
4. `GET /entities/{id}`, merge the specs into the body (`tagIds` from `tags`, `parentId` from `parent`, plus `fields`), and `PUT /entities/{id}`. PUT replaces the whole record, so send the full body.
5. Attach the documents worth keeping: `hb-api POST /entities/{id}/attachments -F file=@x.pdf -F type=manual -F name='Title'`.
6. `GET /entities/{id}` and check the result; for a batch, check `GET /entities?pageSize=50` too.

## Behaviour worth knowing

- Locations take asset IDs from the same sequence as items, so IDs are not contiguous across items.
- Item search matches serial numbers and asset IDs (`q=%23000-012` finds asset `000-012`).
- Uploads are capped by `HBOX_WEB_MAX_UPLOAD_SIZE` (MB), which defaults to 10. This instance sets it to 100 so full-size manuals fit; an over-limit upload fails with `Connection reset by peer` or `failed to parse multipart form`.
- Homebox attachments can't be imported or exported through CSV, so files are uploaded through the API after the records exist.
