# Amazon.de

Amazon.de is the Amazon site that sells to Åland without VAT (leverans.ax lists it as "Amazon", 0 % VAT sales; see `aland.md`). The user confirms the other Amazon sites do not.

## Ordering to Åland

An order placed on 2026-10-15 for delivery to Åland showed each line at its price including 19 % German VAT, and an order total equal to the line sum divided by 1,19, so Amazon.de removes the German VAT at checkout. Finnish VAT is then paid at Åland customs (see `aland.md`). The delivery estimate for in-stock tools and electronics was about five weeks (21 November for an order on 15 October), so Amazon.de suits planned purchases and not urgent ones. Order-confirmation emails come from `bestellbestaetigung@amazon.de` to the user's `amazon@rn.ax` address.

## Search

```
shop-browse 'https://www.amazon.de/s?k=eneloop+ladeger%C3%A4t+AA+AAA' --text --links /dp/
```

Headless Chromium loads the results page. Product links are `/<slug>/dp/<ASIN>`; drop everything after `?` and keep the ASIN. Each product appears twice in `--links` (title link and an `Optionen anzeigen` link). In `.text`, prices are lines such as `9,29 €`, and sponsored rows are mixed with organic results, so match each price to its title from the text around it before quoting. Search in German (`Ladegerät`, `Akkus`) for the best results.
