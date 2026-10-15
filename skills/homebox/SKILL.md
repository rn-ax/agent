---
name: homebox
description: Use whenever the user asks about their home inventory — what they own, specs/manuals/warranty for an item, adding or updating an item, or anything about "homebox" explicitly. This is the accumulating knowledge base for how this user's Homebox instance is set up and how to talk to its API, so read it before assuming access method, API shape, or inventory conventions from scratch.
---

# Homebox

The user's home inventory: everything they own (loosely defined), with exact specs, links to relevant pages, and PDF manuals, searchable by an agent.

**Related systems**: Homebox runs as an app on TrueNAS — see the `truenas` skill for the install playbook and "TrueNAS deployment" below for this app's install notes; `home` has the topology map.

## Instance

Runs as the `homebox` app from TrueNAS's `community` catalog train. The browser URL is `https://home.rn.ax`, published through Cloudflare Access, and it is the base for every link to a Homebox resource (`https://home.rn.ax/item/<entity id>`, `/location/<id>`). The API wrappers talk to the LAN address `http://truenas.lan:30149`.

API credentials live in the "Homebox" item in the "Agent" 1Password vault: `password` = API token, the **website** URL = base URL. The URL sits in the item's `urls` array rather than `fields`, so it needs `item get --format json | jq -r '.urls[0].href'`.

Use `hb-api <method> <path> [curl-args...]` (this skill's own directory) for an authenticated call. `<path>` is relative to `<base_url>/api/v1`, e.g. `hb-api GET '/entities?q=mac&pageSize=5'`. Like `wm-api`, it goes through `~/tasks/op-service-account`, so it needs that machine's `op-service-account-agent` Keychain entry set up first. Multipart uploads (`-F`) work: the wrapper only sets a JSON content type when no `-F` is passed.

## API shape (v0.26)

The live OpenAPI spec is at `<base_url>/swagger/doc.json` (UI at `/swagger/index.html`); read it rather than guessing routes.

This version names things differently from older Homebox docs and blog posts:
- Inventory records are **entities** (`/entities`), not items. Locations are entities too, distinguished by `/entity-types`; `/entities/tree` returns the hierarchy.
- Labels are **tags** (`/tags`).
- `/entities/fields` and `/entities/fields/values` list the custom field names and values already in use — check these before inventing a new custom field name, so specs stay consistent across items.
- Attachments: `POST /entities/{id}/attachments` uploads a file (`-F file=@… -F type=photo|manual|attachment|warranty -F name=…`; `-F primary=true` makes a photo the item's main image). Links to manuals and product pages go in the `Documentation` custom field as markdown; `POST /entities/{id}/attachments/external` answered 400 to `{title, url, type}`.
- Creating a record takes two calls: `POST /entities` with `name`, `parentId`, `entityTypeId`, `tagIds` and `quantity` returns the new `id`, then `PUT /entities/{id}` with that `id` in the body fills in the built-in fields and the whole `fields` array (`type: "text"`, `name`, `textValue`). `purchaseDate` is sent as RFC 3339 (`2026-10-15T00:00:00Z`).
- A custom field value of about 580 characters made the `PUT` fail with HTTP 500 `Unknown Error` while 383 characters were accepted, so long specs are split across several fields (`Tech Specs`, `Performance`, `Compatibility`, `Environment`, `Dimensions`).
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
- **Tags** follow Homebox's own defaults: Title Case names for broad categories (`Appliances`, `Electronics`, `Servers`, `IOT`, plus `Computers`, `Storage`, `Audio`, `AV`, `Displays`, `Kitchen`, `Tools` and so on), kept to a small set that is reused rather than one tag per product type. Smart-home devices are `IOT`, homelab and server hardware is `Servers`, and powered household devices are `Appliances`.
- **Status and person tags** use the same style: `Ordered`, `Needs Info`, `Employer Owned`, and one tag per household member named after them.
- **Attachments** use the type that matches the file (`manual`, `warranty`, `photo` or `attachment`); see "Documents worth attaching" for what to include.
- **Description** is markdown and holds the one-line "what is this and what is it for".
- **Records stand alone.** A record holds facts about the item: specs, purchase, serial, firmware, location and notes on its state. Skills, agents and tooling stay out of it. Knowledge about operating or integrating a device (pairing steps, device settings, entity names, how it behaves) lives in the skill for that system, and the skill points to the record by asset ID.

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

An order that has been placed but not delivered yet is recorded straight away with the `Ordered` tag and an `Expected Delivery` field; the tag and field are removed when it arrives. An order that never shipped is dropped. A repeated identical order placed minutes or days apart is checked for fulfilment emails ("finns att hämta", "shipped"): when only one was fulfilled it is a single item, and when both were, the user is asked how many they received.

Employer-owned items the user has in their possession (a work laptop, a work phone) are recorded too, with the `Employer Owned` tag and a note saying so; their price stays empty when the employer paid.

Things that belong to another household member carry a person tag (their first name, in Title Case) and sit among the rest of the inventory.

## Following up on missing information

The `Needs Info` tag marks live items that lack information worth chasing, and the item's `Missing Info` field lists what: serial number (whole devices only, not peripherals or internal parts), model number (not furniture or board games), purchase date, and purchase price (not gifts or employer-owned items). `hb-needs-info` (this skill's directory) sets and clears the tag and field across the inventory and is safe to re-run; `--dry-run` shows what would change. Filter by the tag in Homebox, or `hb-api GET '/entities?tags=<tag id>'`, to work through the follow-ups, then run the script again to clear the completed ones.

A kit that combines individual products is recorded as those products, never as a single kit item: a starter kit of bulbs and a remote becomes the bulbs and the remote, each with its own quantity. The kit's price is divided evenly over its pieces and the `Part Of Kit` and `Kit Price Split` fields say so.

## Purchase history coverage

Each shop has two possible sources. Order mails are easy to scan but can have gaps (notifications that were never configured, mails that were deleted or filtered, items missing from the text). A shop's own order-history page is complete: it lists every order, so a website pass closes the gaps a mail pass leaves.

A later sweep starts after the dates below, so only newer orders need reading: search the mailbox with `fm-api` for newer mail, and ask for a fresh order-history capture (a window capture of the page, since a full-page capture stops at 16,384 px).

| Shop | Order mails | Website order history |
|---|---|---|
| Webhallen | Read through 2026-08 | Complete through 2026-10-11 |
| AliExpress | Name no items before 2025 | Complete through 2026-10-11 |
| Amazon.de | Read through 2026-09-23 | Not read |
| Amazon.com (USD) | Totals only, no item names | Not read |
| Amazon.co.uk | Read through 2019-12 (two orders) | Not read |
| Multitronic (Åland and Oy) | Read through 2026-04-07 | Not read |
| Dustin Home | Read through 2013-12 (the last order) | Not read |
| Apple Store | Read through 2016-10 | Not read |
| Clas Ohlson (Finnish shop) | Read through 2026-01-06 | Not read |
| Verkkokauppa.com | Read through 2026-06-18 | Complete from 2020-10-01 through 2026-10-11 (CSV export "Ostoraportti" with serial numbers and warranty months); earlier orders not read |
| IKEA | Store receipts through 2026-08-09, online orders through 2024-11-11 | Not read |
| Elgiganten | Read through 2026-06-22 | Not read |
| Blocket | Listing receipts through 2013-09 | Not read |

Reviewed with nothing to record: PayPal receipts (software, services, tiny accessories), Klarna invoices, and bank e-invoice notices (they name no merchants or items).

Small purchases are skipped: AliExpress items under about 10 EUR, bare electronic components, clothing and costumes, utensils and consumables, and LEGO sets.

A shop's order-history export is the preferred source when one exists: Verkkokauppa's CSV lists every order with brand, product code, serial or IMEI, and warranty months. Its prices exclude VAT for deliveries to Åland, so Finnish VAT is added by purchase date. Returned items and orders the user did not keep are left out, and serial numbers in the export are matched to devices already in Homebox.

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

Every product added after the initial mass migration gets a complete record in the same pass: full specs in the built-in and custom fields, every document from "Documents worth attaching" (the manual above all), product photos, links to the vendor and shop pages, and the purchase facts. The thin records the migration created (purchase facts only) are filled in the same way whenever an item is touched. An order recorded straight away with the `Ordered` tag gets the complete record at that moment too, with `Expected Delivery` taken from the shop's estimate.

1. Read what exists: `GET /tags`, `GET /entities/fields`, `GET /entities/tree`.
2. Collect exact specs from an authoritative source — a command on the device itself (`system_profiler SPHardwareDataType`, `lscpu`, `dmidecode`, `lsblk -o NAME,MODEL,SERIAL`) or the vendor's spec page. A product sold in several hardware revisions (the same name with different resolutions or chips) gets the specs of the revision the shop lists, with the other revisions named in `Tech Specs`. Vendors keep manuals in a download center (Reolink's `reolink.com/download-center/` links one PDF per camera family) and product images on their product page; shops publish a gallery on the product page, and the images that show the product itself (not marketing graphics) are the photos to attach. For a discontinued product, a retailer listing still carries the spec table, and its CDN often serves a product image and a PDF (Inet's `cdn.inet.se/product/...` and `cdn.inet.se/pdf/<article>_0.pdf`); a PDF labelled "product sheet" can turn out to be the full manual. The shop's own receipt (see "Importing from purchase emails") gives the article number that links the device to its listing, and a label on the device ties the two together.
3. `POST /entities` with `name`, `parentId`, `quantity` and `tagIds`; the create call accepts only these basics.
4. `GET /entities/{id}`, merge the specs into the body (`tagIds` from `tags`, `parentId` from `parent`, plus `fields`), and `PUT /entities/{id}`. PUT replaces the whole record, so send the full body.
5. Attach the documents worth keeping and the product photos (`-F type=photo`): `hb-api POST /entities/{id}/attachments -F file=@x.pdf -F type=manual -F name='Title'`.
6. `GET /entities/{id}` and check the result; for a batch, check `GET /entities?pageSize=50` too.

## Behaviour worth knowing

- Locations take asset IDs from the same sequence as items, so IDs are not contiguous across items.
- Item search matches serial numbers and asset IDs (`q=%23000-012` finds asset `000-012`).
- Uploads are capped by `HBOX_WEB_MAX_UPLOAD_SIZE` (MB), which defaults to 10. This instance sets it to 100 so full-size manuals fit; an over-limit upload fails with `Connection reset by peer` or `failed to parse multipart form`.
- Archiving is a flag on the item (`archived: true`). Archived items are absent from default searches and lists, readable by id, and listed with `includeArchived=true`. Archive keeps the record, purchase details and attachments; delete removes them.
- Homebox attachments can't be imported or exported through CSV, so files are uploaded through the API after the records exist.
- Phone photos in HEIC are converted before upload with `sips -s format jpeg -Z 1600 in.HEIC --out out.jpg`, which keeps them small and viewable in Homebox.
- A custom field's text value holds at most 500 characters; a longer value makes `PUT /entities/{id}` answer `500 Unknown Error`. Long procedures are split over several fields (for example `Setup` and `Rebuild And Recovery`).
- `PUT /entities/{id}` applies its field list as it goes: a field with an `id` is updated, a field without one is created, and a field left out of the list is deleted. A request that fails partway keeps the changes made before the failure (duplicate field names are the visible sign), so after any error `GET` the entity and tidy it by sending the list again. The update body needs only the `EntityUpdate` keys (`name`, `description`, `notes`, `manufacturer`, `modelNumber`, purchase fields, `quantity`, `parentId`, `tagIds`, `fields`), with each existing field reduced to `id`, `name`, `type`, `textValue`.

## TrueNAS deployment

Installed 2026-10-11 from the `community` catalog train via `app.create` (app name `homebox`, compose project `ix-homebox`), published on port `30149`. See the `homebox` skill for the API and inventory conventions.

- The container runs as `568:568` (`apps:apps`) with one persistent mount, `/data`, bound to `Storage/Configuration/homebox/data` as a host path. No ACL grant is needed.
- The catalog's `values.storage` accepts only `data`; passing `additional_storage` fails validation with `values.storage.additional_storage: Field was not expected`.
- `values.homebox.api_key_pepper` is required and must stay stable across restarts; rotating it invalidates every issued API key. The generated value went to a dated credentials file on `~/Desktop` per the standing install convention.
- The web UI allows open registration (`allowRegistration: true` in `/api/v1/status`) until disabled.
- `HBOX_WEB_MAX_UPLOAD_SIZE=100` is set through `values.homebox.additional_envs` (the default is 10 MB, too small for PDF manuals). Changing it goes through `app.update` with the full `app.config` values minus the `ix_*` keys, followed by `app.redeploy`.
