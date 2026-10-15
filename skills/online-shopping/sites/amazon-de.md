# Amazon.de

Not listed on [leverans.ax](https://leverans.ax/) (see `aland.md`); delivery to Åland and its VAT handling are confirmed at checkout with an Åland address.

## Search

```
shop-browse 'https://www.amazon.de/s?k=eneloop+ladeger%C3%A4t+AA+AAA' --text --links /dp/
```

Headless Chromium loads the results page. Product links are `/<slug>/dp/<ASIN>`; drop everything after `?` and keep the ASIN. Each product appears twice in `--links` (title link and an `Optionen anzeigen` link). In `.text`, prices are lines such as `9,29 €`, and sponsored rows are mixed with organic results, so match each price to its title from the text around it before quoting. Search in German (`Ladegerät`, `Akkus`) for the best results.
