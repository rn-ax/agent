# Multitronic.fi

Finnish electronics retailer. Listed on [leverans.ax](https://leverans.ax/hemelektronik/) with a tax-border number (see `aland.md`).

## Search

The search page is driven by the URL fragment; a `?q=` query string returns an empty page.

```
shop-browse 'https://www.multitronic.fi/fi/search/results#lang=fi&c=search&keywords=eneloop' --text --links /fi/products/ --wait 6000
```

`--wait 6000` gives the client-side render time to finish. The page loads no JSON API that `--json` can see, so read the rendered text. In `.text`, each result is the product title line followed by its price line (`35,90€`), a delivery estimate (`Arvioitu toimitus: 21.10. - 22.10.`) and an availability line (`Saatavilla toimittajalta` for supplier stock). A short parse that pairs each title with the price line below it is enough.

Product links are `/fi/products/<id>/<slug>`, available from `--links /fi/products/`.

Search is broad: `akkulaturi` returns mostly power-tool chargers, so name the product family (`eneloop`, `paristolaturi`) for AA/AAA.
