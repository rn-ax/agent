# Homebox inventory: remaining work

Work still open on the home inventory, grouped by theme. Rules for how items are chosen and recorded live in `SKILL.md`; this file lists what is left to do.

## Paperless

- [ ] Create a `paperless` skill: where it runs, the API wrapper, the token in 1Password, how documents are tagged. It currently runs on the home server Mac mini.
- [ ] Go through the manuals stored in Paperless and upload the useful ones to Homebox as `manual` attachments on the right item (Swedish or English only, named like `User Manual (English)`).
- [ ] Go through the invoices and receipts in Paperless to find items the mail sweep missed (shops that send no email, in-store purchases, older years).
- [ ] Migrate Paperless to TrueNAS.

## Remaining purchase sources

- [ ] Read the website order histories of the shops covered only by mail (Amazon.de, Amazon.com, Amazon.co.uk, Multitronic, Dustin Home, Apple Store, Clas Ohlson, IKEA, Elgiganten; Verkkokauppa is done from 2020-10 on, so only earlier orders remain, if any) to close gaps in the mail coverage. Update the coverage table in `SKILL.md` as each is done.

- [x] AliExpress: the order history is analysed through 2026-10-11 and the barcode scanner is recorded.
- [ ] Amazon.com (USD) orders from 2022-2023: the order and shipping emails carry totals only (no item names); go through the order history on the Amazon site.
- [x] Blocket listing receipts (2008-2013) are recorded as archived items; the guitar is still owned.
- [x] PayPal receipts reviewed: software, services, books and tiny accessories only; nothing to record.
- [x] Bank e-invoice notices and Klarna invoices reviewed: they name no items. Real bank or card statements (not in the mailbox) are the only remaining source for purchases with no email.
- [x] IKEA online orders from 2024 are recorded.
- [x] Elgiganten receipts are recorded (an air conditioner was returned; an iPad Air 2, a Ring Chime and an Arlo Pro 2 set were kept).
- [ ] Webhallen games, figures and toys: decide whether any category is in scope.
- [ ] Gifts and items with no purchase record: ask the user for the list and add them.

## Computers and disks

- [x] Disks in the TrueNAS server and the Synology NAS are recorded with serials and firmware. Four Synology drives still lack a purchase record.
- [ ] Place the parked computer parts (older Webhallen and Dustin purchases) in the computers they belonged to, or archive them.
- [ ] Fill in serial number, configuration and purchase details for the machines recorded as skeletons.
- [ ] Fix SSH access to the home server (confirm the host key, install the key) and read its hardware report.
- [ ] Link the Raspberry Pi 5 record and the legacy Mac mini record to the planned Home Assistant move.

## Homebox housekeeping

- [ ] Move everything out of the `Home` placeholder location into real rooms, then remove the placeholder.
- [x] Tags follow Homebox's Title Case defaults (37 tags).
- [ ] Define entity types and templates for the main categories so new items start with the right fields.
- [ ] Add photos, and print asset-ID labels or QR codes for the physical items that benefit.
- [ ] Fill in warranty expiry dates where the purchase email or receipt states them.
- [ ] Set up the yearly inventory: a scheduled maintenance entry per category, with a notifier.
- [ ] Turn off open registration once the household accounts exist; consider OIDC.
- [ ] Back up Homebox: a regular export plus a ZFS snapshot policy for its data directory.
- [ ] Items tagged `Ordered`: remove the tag and the `Expected Delivery` field when they arrive.

## Network identity

- [ ] Record the MAC address of every network-connected device (computers, phones, tablets, TVs and AV gear, routers and access points, smart-home hubs and sensors, printers, consoles, cameras) in a `MAC Address` custom field, so a device can be found on the network from its inventory record.
  - Sources: the Synology SRM router's client list (the `SYNO.Core.NGFW.Traffic.Device` API and related client/DHCP APIs are the place to look; method names are undocumented, see the `home-network` skill), the Inteno gateway's `router.network clients`, and each device's own settings or system report.
  - Match router entries to inventory records by hostname, IP and manufacturer prefix (OUI), and confirm each match with the user before writing it.
  - Extend `hb-needs-info` with a MAC-address check for devices tagged as network-connected, so missing ones are flagged for follow-up.

## Manuals and specs

- [ ] For each item, fetch the manual or spec sheet from the vendor, read it with `file-reader`, attach it, and fill the exact specs and the product-page link into the item's fields.
- [ ] Keep to the manual rule: Swedish or English, one comprehensive document per item, no environmental or compliance sheets.

## Data quality

- [ ] Work through the items tagged `Needs Info` (serial numbers, model numbers, purchase details), then re-run `hb-needs-info`.

- [ ] Confirm the VAT handling of online purchases against real customs or delivery bills for a sample of orders.
- [ ] Items whose price assumed VAT inclusion (marked in their `VAT` field) get checked when a receipt turns up.
- [ ] Look for duplicate orders (identical order placed twice, only one fulfilled) in each new shop before listing items.
- [ ] Re-check items whose delivered model differed from the ordered one.
