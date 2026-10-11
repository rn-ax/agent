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

Attachment names state the document and language, such as `User Manual (English)`. A manual is only worth attaching when it is in Swedish or English; extra languages in the same file do no harm, while a manual in neither language is not attached. The official vendor PDF is preferred, and one comprehensive manual beats several fragments.

## What goes in the inventory

The inventory holds durable things the user owns and has owned. Each candidate is shown to the user with its date and price, always asked as "do you still own this?" (a selected item is owned), and the user confirms its status:
- **Owned**: created as a normal item.
- **Gone** (sold, thrown away, given away): created as an archived item, so the purchase history stays on record. A sale also gets `soldDate`, `soldTo`, `soldPrice` and `soldNotes`; any other exit is noted in `notes`.
- **Not theirs** (bought for someone else, never owned): left out, not archived.

A candidate that gets no answer is not created. Candidates are presented item by item; a receipt or order is never approved as a whole, because one receipt mixes owned items, items for others, and out-of-scope items.

Categories that stay out:
- Cables.
- Mounting hardware (wall, ceiling and desk mounts, brackets).
- Batteries.
- Bags, backpacks and suitcases.
- Simple kitchen utensils and accessories (spatulas, strainers, peelers, containers).
- Storage boxes and containers.
- Cables and connectors.
- Simple chargers (charging hubs and stations are in scope).
- Consumables and books.
- Items bought for someone else.
- Computer parts (drives, motherboards, RAM, CPUs, GPUs, coolers, drive stabilizers). They are added as child items of the computer they live in, once the computers are mapped; until then they wait in a scratch list.

When the user rules out another category, it is added to this list.

Board games are recorded as well (they come with rulebooks). Manuals decide scope: anything electronic, and anything the user assembles themselves (IKEA furniture, shelving, wardrobes), comes with a manual the user keeps, so it is recorded and its manual is attached. Furniture and small items without a manual are not tracked.

An order that has been placed but not delivered yet is recorded straight away with the `ordered` tag and an `Expected Delivery` field; the tag and field are removed when it arrives. An order that never shipped is dropped. A repeated identical order placed minutes or days apart is checked for fulfilment emails ("finns att hämta", "shipped"): when only one was fulfilled it is a single item, and when both were, the user is asked how many they received.

Employer-owned items the user has in their possession (a work laptop, a work phone) are recorded too, with the `employer-owned` tag and a note saying so; their price stays empty when the employer paid.

Things that belong to another household member carry a person tag (their lowercase first name) and sit among the rest of the inventory.

## Following up on missing information

The `needs-info` tag marks live items that lack information worth chasing, and the item's `Missing Info` field lists what: serial number (whole devices only, not peripherals or internal parts), model number (not furniture or board games), purchase date, and purchase price (not gifts or employer-owned items). `hb-needs-info` (this skill's directory) sets and clears the tag and field across the inventory and is safe to re-run; `--dry-run` shows what would change. Filter by the tag in Homebox, or `hb-api GET '/entities?tags=<tag id>'`, to work through the follow-ups, then run the script again to clear the completed ones.

A kit that combines individual products is recorded as those products, never as a single kit item: a starter kit of bulbs and a remote becomes the bulbs and the remote, each with its own quantity. The kit's price is divided evenly over its pieces and the `Part Of Kit` and `Kit Price Split` fields say so.

## Computers and their parts

A computer or NAS is an item, and its parts are child items (CPU, board, RAM, PSU, case, GPU, drives). The installed hardware is read from the machine itself and matched to purchase emails by model number or serial:
- Linux hosts: `lscpu`, `lsblk -o NAME,MODEL,SERIAL,SIZE`, `dmidecode`, `lspci -v`, `nvidia-smi`.
- Synology: `/proc/mdstat`, `/sys/block/*/device/model` and `/usr/syno/bin/synodisk --info /dev/<disk>`.
- macOS: `system_profiler SPHardwareDataType SPStorageDataType`.

A part that was replaced stays as an archived child with a note on what replaced it. A gift records the giver's purchase date and price when known, with a note saying it was a gift. An order page the user pastes works as a source in place of an email, and the `Source` field says so.

## Importing from purchase emails

Order confirmations and receipts in the mailbox (see the `email` skill and its `fm-api`) are the source for purchase history.

1. **Harvest**: page through `search_email` with purchase-style subject terms in each language the mailbox uses (Swedish `kvitto`, `orderbekräftelse`, `beställning`; Finnish `tilausvahvistus`; English `receipt`, `order confirmation`, `your order`, `shipped`). Combine terms as `subject:a OR subject:b`; parenthesised groups are rejected. Pages hold 50 results and continue with `cursor`.
2. **Find the shops**: group results by sender domain. Product retailers are worth parsing; banks, payment processors, food, travel and app-store receipts are not.
3. **Parse per shop and era**: each shop formats its confirmations differently, and a shop's layout can change over the years. Webhallen's older "Tack för din beställning" mails list `SKU: name N st á PRICE kr` plus `Ordernummer`/`Orderdatum`; its newer ones are point-of-sale receipts.
4. **Show candidates newest first** per shop, durable items only, and wait for the user's confirmation per item.
5. **Create** each approved item with the purchase fields below.

Purchase facts go in the built-in fields: `purchaseDate` (`YYYY-MM-DD`, the order date), `purchasePrice`, `purchaseFrom` (the shop). `purchasePrice` is in the collection currency, EUR, converted at the ECB rate on the purchase date with `hb-eur <amount> <currency> <date>` (weekends use the previous business day).

`purchasePrice` includes VAT. Retail prices paid in Sweden and in shops in Åland already include VAT. Online purchases delivered to the user's address in Åland (outside the EU VAT area; the user lives there from late 2019) are checked out without VAT, and the user pays Finnish VAT on arrival (24% until 2024-08-31, 25.5% from 2024-09-01). The stored price is the checkout price plus that VAT. The ship-to address in an order email shows where the user lived at the time, and when it is unclear whether a price includes VAT, the user is asked.

Amazon.de emails differ by era, so each layout is checked against the order total before pricing:
- The "Ordered:" layout (2025 onward) lists item prices that include German VAT (19%), while the order total is ex-VAT (item sum ÷ 1.19). The stored price is `listed ÷ 1.19 × (1 + Finnish rate)`.
- The 2020 layout shows a separate German VAT line (16% in the second half of 2020, 19% after) in the order total.
- The 2023-2024 layout lists items and a total without a VAT line, and the prices there appear to be ex-VAT.

The listed price is kept in `Purchase Price (Original)` as `<amount> EUR listed (incl. German VAT)` (or `excl. VAT` where that applies), and the `VAT` field records what was removed and added. Custom fields keep the trail back to the source:
- `Order Number`
- `Purchase Price (Original)` (for example `7379 SEK`)
- `Exchange Rate` (for example `1 SEK = 0.11292 EUR (2014-01-03)`)
- `Source Email` (the Fastmail email id, readable with `fm-api read_email`)

Scratch work (harvest results, parsed items) stays outside the repo, since it contains email content.

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
- Archiving is a flag on the item (`archived: true`). Archived items are absent from default searches and lists, readable by id, and listed with `includeArchived=true`. Archive keeps the record, purchase details and attachments; delete removes them.
- Homebox attachments can't be imported or exported through CSV, so files are uploaded through the API after the records exist.
