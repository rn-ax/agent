# Clas Ohlson (Finland)

Listed on [leverans.ax](https://leverans.ax/alla-foretag/2/) with a tax-border number (see `aland.md`).

Plain `curl` of any clasohlson.com URL, the search JSON endpoint included, receives a "Client Challenge" page; a real browser passes it. Use `shop-browse`.

## Search

```
shop-browse 'https://www.clasohlson.com/fi/search?text=paristolaturi' --text --links /p/
```

The page calls `/fi/search/getSearchResults?text=<terms>` for its results. In `.text`, each product is a block of lines: optional discount (`-43%`), rating, review count, category, title, blurb, current price (`19,99`), original price when discounted (`34,90`). Prices carry no currency sign (EUR incl. VAT). The cookie banner text precedes the results and can be ignored.

Product links are `/fi/<slug>/p/<article-number>` (for example `/p/39-2692`), available from `--links /p/`. The search page links to well over a thousand URLs, so filter with `/p/`.

Search is fuzzy: `akkulaturi` returns car-battery and power-tool chargers first, `paristolaturi` returns AA/AAA chargers.

## Multi-buy discounts

Clas Ohlson often runs a 15–20 % discount on all products when buying two. When the user wants two of an item, check whether such a campaign is running or likely soon, and weigh waiting for it against the current price. A product's own offer price (for example `-34%` on a tile) can already beat the multi-buy discount, so compare the two before advising to wait.
