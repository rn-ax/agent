# IKEA (Finland)

Listed on [leverans.ax](https://leverans.ax/alla-foretag/4/) with a tax-border number (see `aland.md`).

## Search

```
shop-browse 'https://www.ikea.com/fi/fi/search/?q=paristolaturi' --text --links /p/
```

In `.text`, each result is a small block: optional badge (`Myydyin`, `Uutuus`), product name (`STENKOL / LADDA`), descriptor line, price (`11,99`; multipacks read `9,99/4 kpl`), then the rating. The page header states the result count, and `Näytetään N tulosta yhteensä N` marks the end of the list.

Product links are `/fi/fi/p/<slug>-<id>/`. The search backend is `sik.search.blue.cdtapps.com` and the cart is `prod.cart.caas.selling.ingka.com`; the search endpoint returned an empty body to a bare `curl`, so use the browser.

## Product naming

LADDA is the rechargeable-cell line (AA 1 900 mAh and 2 450 mAh, AAA 750 mAh) and STENKOL, LITOSFÄR are chargers. `STENKOL / LADDA` is the charger bundled with four cells, `STENKOL` alone is the charger. The LADDA cells are rebadged Eneloop cells made by FDK.
