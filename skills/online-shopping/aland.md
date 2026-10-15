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

`https://leverans.ax/alla-foretag/` lists every entry and `https://leverans.ax/<category>/` filters by category (`hemelektronik`, `hem-hushall`, `bygg-renovering`, …). The page renders client-side; read it with `shop-browse <url> --text`. The site has no API or data file.

A shop's absence from the directory means its Åland VAT handling is unconfirmed. It does not mean the shop refuses Åland deliveries, so say "not listed on leverans.ax" and point to the shop's own delivery terms or customer service.

## Status of shops with a site file

| Shop | leverans.ax (read 2026-10-15) |
|---|---|
| Multitronic | Skattegränsnummer: no extra VAT or customs |
| Verkkokauppa.com, Clas Ohlson, IKEA, Amazon.de | not listed |
