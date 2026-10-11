---
name: online-shopping
description: Use whenever a task needs live product data from an online shop — current price, stock, product specs, or searching a retailer's catalogue (e.g. "check verkkokauppa", "is X in stock", "what does Y cost", comparing components to buy). This is the accumulating knowledge base for how each shop the user buys from can actually be read by an agent, so read it before fetching a shop page from scratch. Currently covers Verkkokauppa.com.
---

# Online shopping

How to read live price, stock and catalogue data from the shops this user buys from. Each shop gets a file under `sites/`; add a new shop there, with a row in the table below.

| Shop | Notes | Fast path |
|---|---|---|
| Verkkokauppa.com (Finland) | `sites/verkkokauppa.md` | `verkkokauppa-product <pid>...` returns price and stock as JSON |

## Reading a shop, cheapest method first

1. **The shop's own JSON API.** Modern storefronts load product data from a JSON endpoint; calling it with `curl` returns exact price and stock with no rendering. Find the endpoints by loading one page in headless Chromium and listing the JSON responses (see the browser recipe below), then call them directly.
2. **Headless Chromium via Playwright.** For pages that render client-side, or to discover endpoints. Install into a scratch directory (`npm i playwright && npx playwright install chromium`; the browser download is cached under `~/Library/Caches/ms-playwright`).
3. **Claude in Chrome / the built-in browser** when their tools are present in the session.

`WebFetch` and plain `curl` of a storefront page return the pre-render shell, with placeholder titles and `0,00` prices, so treat any such result as empty. `WebSearch` snippets of product pages can be weeks out of date and can list products the shop no longer carries; use them to find product URLs and ids, and read price and stock from the shop itself.

## Browser recipe

```js
import { chromium } from 'playwright';
const browser = await chromium.launch();
const ctx = await browser.newContext({ locale: 'fi-FI', userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36' });
const page = await ctx.newPage();
page.on('response', r => { if (/json/.test(r.headers()['content-type'] || '')) console.log(r.status(), r.url()); });
await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
await page.waitForTimeout(2000); // late XHRs after networkidle
```

Run it from the scratch directory that holds `node_modules/playwright` (module resolution is relative to the script). Job-scoped scratch lives in `$CLAUDE_JOB_DIR/tmp`.

## Reporting results

State the date the data was read, since price and stock change within days. Quote prices in the shop's own currency with VAT as shown to consumers, and say when an item is sold out, because a listed price on a sold-out item is not a price the user can pay.
