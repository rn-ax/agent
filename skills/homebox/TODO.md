# Homebox inventory: remaining work

Work still open on the home inventory, grouped by theme. Rules for how items are chosen and recorded live in `SKILL.md`; this file lists what is left to do.

## Paperless

- [ ] Create a `paperless` skill: where it runs, the API wrapper, the token in 1Password, how documents are tagged. It currently runs on the home server Mac mini.
- [ ] Go through the manuals stored in Paperless and upload the useful ones to Homebox as `manual` attachments on the right item (Swedish or English only, named like `User Manual (English)`).
- [ ] Go through the invoices and receipts in Paperless to find items the mail sweep missed (shops that send no email, in-store purchases, older years).
- [ ] Migrate Paperless to TrueNAS.

## Remaining purchase sources

- [ ] AliExpress: about 70 paid orders; most are small, so triage by order value first.
- [ ] Amazon.com (USD) orders from 2022-2023: the order emails carry totals only, so read the shipping notices for item names.
- [ ] Blocket listing receipts (2008-2013): vehicles, a workstation and furniture that were put up for sale. Record the items as archived with the `sold` fields filled in where the sale is known.
- [ ] PayPal receipts: list the merchants and pick out product shops that sent no order email.
- [ ] Bank and card statements, for purchases that left no email at all.
- [ ] IKEA online orders from 2024 (Finnish shop): the items were never read.
- [ ] Elgiganten receipts from 2015 and 2020: the attachments cannot be read; ask what was bought.
- [ ] Webhallen games, figures and toys: decide whether any category is in scope.
- [ ] Gifts and items with no purchase record: ask the user for the list and add them.

## Computers and disks

- [ ] Inventory the disks and parts in each machine (TrueNAS server, Synology NAS, the Mac minis and laptops), matching serials to purchase emails; record replaced parts as archived children.
- [ ] Place the parked computer parts (older Webhallen and Dustin purchases) in the computers they belonged to, or archive them.
- [ ] Fill in serial number, configuration and purchase details for the machines recorded as skeletons.
- [ ] Fix SSH access to the home server (confirm the host key, install the key) and read its hardware report.
- [ ] Link the Raspberry Pi 5 record and the legacy Mac mini record to the planned Home Assistant move.

## Homebox housekeeping

- [ ] Move everything out of the `Home` placeholder location into real rooms, then remove the placeholder.
- [ ] Choose one tag scheme: Homebox's default capitalised tags or the lowercase ones in use, and merge the two sets.
- [ ] Define entity types and templates for the main categories so new items start with the right fields.
- [ ] Decide whether employer-owned items belong in the inventory.
- [ ] Add photos, and print asset-ID labels or QR codes for the physical items that benefit.
- [ ] Fill in warranty expiry dates where the purchase email or receipt states them.
- [ ] Set up the yearly inventory: a scheduled maintenance entry per category, with a notifier.
- [ ] Turn off open registration once the household accounts exist; consider OIDC.
- [ ] Back up Homebox: a regular export plus a ZFS snapshot policy for its data directory.
- [ ] Items still waiting for delivery get added when they arrive.

## Manuals and specs

- [ ] For each item, fetch the manual or spec sheet from the vendor, read it with `file-reader`, attach it, and fill the exact specs and the product-page link into the item's fields.
- [ ] Keep to the manual rule: Swedish or English, one comprehensive document per item, no environmental or compliance sheets.

## Data quality

- [ ] Confirm the VAT handling of online purchases against real customs or delivery bills for a sample of orders.
- [ ] Items whose price assumed VAT inclusion (marked in their `VAT` field) get checked when a receipt turns up.
- [ ] Look for duplicate orders (identical order placed twice, only one fulfilled) in each new shop before listing items.
- [ ] Re-check items whose delivered model differed from the ordered one.
