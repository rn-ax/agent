# Shopping for delivery to Åland

The user lives in Åland, which is outside the EU VAT and excise area. Goods sent between Åland and mainland Finland or any other EU country are customs-cleared, and VAT is charged at the border. A shop that charges Finnish VAT at checkout and also ships across the tax border means paying VAT twice (once to the shop, once on import), so a recommendation covers where the shop stands on this as well as price and spec.

Sources the user keeps current:

- [Customs regulations in Åland (Info Norden)](https://www.norden.org/en/info-norden/customs-regulations-aland) — the rules for private individuals: customs declaration, VAT, e-commerce, travellers' imports. The page returns 403 to `WebFetch`; `shop-browse <url> --text` reads it.
- [leverans.ax](https://leverans.ax/) — directory of shops that ship to Åland without double VAT. Each entry carries one of these labels:
  - **Skattegränsnummer** — the shop holds a tax-border number and settles VAT with Customs itself, so the buyer pays no extra VAT or customs fee.
  - **Momsfri försäljning** — the shop sells at 0 % VAT and the buyer clears the parcel through Customs and pays VAT there.
  - **Levererar till Åland** — ships to Åland; the VAT handling needs confirming with the shop.
  - **Via kontakt med kundtjänst** — the shop removes or refunds the VAT after customer service is contacted.

## Snapshot

`leverans-ax.json` (this skill's directory) is a committed snapshot of the whole directory: `{source, fetchedAt, pages, shops: [{name, category, label, vat, page}]}`. `label` is the leverans.ax wording and `vat` its normalized form: `tax-border-number`, `zero-vat`, `zero-vat-via-support`, `ioss`, `refund-via-support`, `delivers`.

```
jq -r '.shops[] | select(.name | test("ikea|amazon"; "i")) | [.name, .vat] | @tsv' leverans-ax.json
jq '.fetchedAt' leverans-ax.json
```

State the snapshot's `fetchedAt` date when quoting a shop's status. Refresh it with `leverans-ax-snapshot` (reads every page of the directory and rewrites the file; prints `{file, fetchedAt, count}`) when the snapshot is more than a few months old, when a shop is missing from it, or when the user says a listing changed. Commit the refreshed file.

A shop missing from the snapshot has unconfirmed Åland VAT handling; say "not listed on leverans.ax" and point to the shop's own delivery terms or customer service.

## Reading the directory live

`https://leverans.ax/alla-foretag/` lists every entry alphabetically, 15 per page, at `/alla-foretag/<n>/` (page 1 has no number). `https://leverans.ax/<category>/` filters by category (`hemelektronik`, `hem-hushall`, `bygg-renovering`, …) and the homepage shows only a sample. Pages render client-side; `shop-browse <url> --text` reads them, with each entry between the line `ⓘ Denna sida innehåller reklamlänkar` and the `Visa fler företag` button as a name, an optional category line and a label line. The site has no API or data file.
