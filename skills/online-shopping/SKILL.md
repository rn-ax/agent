---
name: online-shopping
description: Use whenever a task needs live product data from an online shop — current price, stock, product specs, or searching a retailer's catalogue (e.g. "check verkkokauppa", "is X in stock", "what does Y cost", comparing products to buy) — and whenever recommending where to buy something, since the user lives in Åland and a shop's delivery and VAT handling there decides whether it is usable. This is the accumulating knowledge base for how each shop the user buys from can actually be read by an agent, so read it before fetching a shop page from scratch. Covers Verkkokauppa.com, Multitronic, Clas Ohlson, IKEA and Amazon.de.
---

# Online shopping

How to read live price, stock and catalogue data from the shops this user buys from. Each shop gets a file under `sites/`; add a new shop there, with a row in the table below.

| Shop | Notes | Fast path |
|---|---|---|
| Verkkokauppa.com (Finland) | `sites/verkkokauppa.md` | `verkkokauppa-product <pid>...` returns price and stock as JSON |
| Multitronic.fi (Finland) | `sites/multitronic.md` | `shop-browse` on the fragment-based search URL |
| Clas Ohlson (Finland) | `sites/clasohlson.md` | `shop-browse` search page (plain `curl` is blocked) |
| IKEA (Finland) | `sites/ikea.md` | `shop-browse` search page |
| Amazon.de | `sites/amazon-de.md` | `shop-browse` search page |

Other shops the user considers have a note under `sites/` too (`head -3 sites/*.md` shows what each store is).

For product research, `reviews.md` lists the review sources the user trusts (Wirecutter first) and whether each can be read.

## Åland

The user lives in Åland, outside the EU VAT area, so every recommendation of where to buy states the shop's status for Åland delivery. `aland.md` holds the rules, the [Info Norden customs page](https://www.norden.org/en/info-norden/customs-regulations-aland), the [leverans.ax](https://leverans.ax/) directory of shops that ship to Åland without double VAT, and how to read and refresh the directory with `leverans-ax-snapshot`. Prefer shops that sell to Åland, and treat the directory as a starting point: it is incomplete and sometimes wrong.

## Reading a shop, cheapest method first

1. **The shop's own JSON API.** Modern storefronts load product data from a JSON endpoint; calling it with `curl` returns exact price and stock with no rendering. `shop-browse <url> --json` lists the JSON responses a page loads, which is how endpoints are found. Call them directly when they answer plain `curl`.
2. **`shop-browse`.** Headless Chromium for client-rendered pages and for shops that challenge plain `curl`.
3. **Claude in Chrome / the built-in browser** when their tools are present in the session.

`WebFetch` and plain `curl` of a storefront page return the pre-render shell, with placeholder titles and `0,00` prices, so treat any such result as empty. `WebSearch` snippets of product pages can be weeks out of date and can list products the shop no longer carries; use them to find product URLs and ids, and read price and stock from the shop itself.

## `shop-browse`

`shop-browse <url> [--links <href-substring>] [--json] [--text] [--wait <ms>]` (this skill's directory) loads the page in headless Chromium with a Finnish locale and prints one JSON object: `{url, title, links?, json?, text?}`.

- `--links <substr>` returns the page's anchors whose href contains `<substr>` as `[{text, href}]`; `""` returns all of them.
- `--json` returns the JSON responses the page loaded as `[{status, url}]`.
- `--text` returns the body's `innerText`, which is where prices are read on shops whose result tiles carry them.
- `--wait <ms>` adds time after network idle for late requests (default 2000).

Playwright and Chromium install into `~/.cache/online-shopping` on first use (one run at a time; a parallel first run races the install). Progress goes to stderr, so `2>/dev/null` keeps stdout clean for `jq`. Searches for several shops can run in parallel afterwards.

## Investigations

A request to find the right product for a need (as opposed to one price or stock lookup) is an investigation. Check `investigations/` for earlier work on the same product before starting. Keep a markdown file `investigations/<date>-<slug>.md` for each investigation and write it during the work, not afterwards: the request and requirements, the sources used and the ones that could not be read, the candidates with shop, price, date and Åland status, the findings, the recommendation given and the open questions. If the requirements are not clear enough to narrow the candidates, ask the user first.

When the user says they ordered something, read the confirmation from their email (the `email` skill; search the product name), add the outcome (shop, price paid, expected delivery) to the investigation file, and create a Homebox record per item with the `Ordered` tag and the `Expected Delivery` field, specs, product images and manuals (the `homebox` skill). Order numbers and delivery addresses stay in Homebox and out of this public repo.

## Reporting results

State the date the data was read, since price and stock change within days. Quote prices in the shop's own currency with VAT as shown to consumers, and say when an item is sold out, because a listed price on a sold-out item is not a price the user can pay.
