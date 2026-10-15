# Reviews and product research

Shop pages give live price, stock and specs (see `sites/`). Independent reviews come from the sources below. The user trusts Wirecutter; add further sources here as the user names them.

## Wirecutter (nytimes.com/wirecutter)

Independent, tested "best X" guides; the user considers it quite trustworthy and it is the first stop for a product category it covers.

Reachability (checked 2026-10-16):

- `WebSearch` rejects `nytimes.com` as a domain, and `WebFetch` refuses `www.nytimes.com`.
- `shop-browse` and plain `curl` get an empty page and a 403 from its bot protection.
- A real browser session passes: use Claude in Chrome or the built-in browser when their tools are present (the `anthropic-skills:chrome-browser` and `anthropic-skills:built-in-browser` skills describe them).
- Otherwise ask the user to paste the relevant section or the picks and say that Wirecutter could not be read.

A guide is dated; state the update date shown on it when quoting a pick, and check that the pick is still sold by a shop that delivers to Åland (see `aland.md`) before recommending it.

## When Wirecutter has no guide for the category

Say so, and use the shops' own specs and ratings (shown on Clas Ohlson, IKEA and Amazon.de result pages) as weaker signals. Keep these labelled as shop ratings and not as independent tests.
