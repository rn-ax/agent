# Shopping for delivery to Åland

The user lives in Åland, which is outside the EU VAT and excise area. Goods sent between Åland and mainland Finland or any other EU country are customs-cleared, and VAT is charged at the border. A shop that charges Finnish VAT at checkout and also ships across the tax border means paying VAT twice (once to the shop, once on import), so a recommendation covers where the shop stands on this as well as price and spec.

Sources the user keeps current:

- [Customs regulations in Åland (Info Norden)](https://www.norden.org/en/info-norden/customs-regulations-aland) — the rules for private individuals: customs declaration, VAT, e-commerce, travellers' imports. The page returns 403 to `WebFetch`; `shop-browse <url> --text` reads it.
- [leverans.ax](https://leverans.ax/) — directory of shops that ship to Åland without double VAT. Each entry carries one of these labels:
  - **Skattegränsnummer** — the shop holds a tax-border number and settles VAT with Customs itself, so the buyer pays no extra VAT or customs fee.
  - **Momsfri försäljning** — the shop sells at 0 % VAT and the buyer clears the parcel through Customs and pays VAT there.
  - **Levererar till Åland** — ships to Åland; the VAT handling needs confirming with the shop.
  - **Via kontakt med kundtjänst** — the shop removes or refunds the VAT after customer service is contacted.

## Using the directory

`https://leverans.ax/alla-foretag/` lists every entry alphabetically, 15 per page, at `/alla-foretag/<n>/` (page 1 has no number; the list ends at page 9). `https://leverans.ax/<category>/` filters by category (`hemelektronik`, `hem-hushall`, `bygg-renovering`, …). The pages render client-side; read each with `shop-browse <url> --text` and take the entries between the line `ⓘ Denna sida innehåller reklamlänkar` and the `Visa fler företag` button, where each entry is a name, an optional category line and a label line. The site has no API or data file, and the homepage and category pages show only a sample, so search all nine pages before concluding a shop is missing.

Before saying a shop is not listed, check every page. A shop missing from all pages has unconfirmed Åland VAT handling; say "not listed on leverans.ax" and point to the shop's own delivery terms or customer service.

## Status of shops with a site file

| Shop | leverans.ax (read 2026-10-15) |
|---|---|
| Multitronic | Skattegränsnummer: no extra VAT or customs |
| Clas Ohlson | Skattegränsnummer: no extra VAT or customs |
| IKEA | Skattegränsnummer: no extra VAT or customs |
| Verkkokauppa.com | Momsfri försäljning: 0 % VAT at checkout, VAT paid at Åland customs |
| Amazon | Momsfri försäljning: 0 % VAT at checkout, VAT paid at Åland customs (the entry names Amazon without a country domain) |
