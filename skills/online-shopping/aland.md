# Shopping for delivery to Åland

The user lives in Åland, which is outside the EU VAT and excise area. Goods sent between Åland and mainland Finland or any other EU country are customs-cleared, and VAT is charged at the border. A shop that charges Finnish VAT at checkout and also ships across the tax border means paying VAT twice (once to the shop, once on import), so a recommendation covers where the shop stands on this as well as price and spec.

Sources the user keeps current:

- [Customs regulations in Åland (Info Norden)](https://www.norden.org/en/info-norden/customs-regulations-aland) — the rules for private individuals: customs declaration, VAT, e-commerce, travellers' imports. The page returns 403 to `WebFetch`; `shop-browse <url> --text` reads it.
- [leverans.ax](https://leverans.ax/) — directory of shops that ship to Åland without double VAT. Each entry carries one of these labels:
  - **Skattegränsnummer** — the shop holds a tax-border number and settles VAT with Customs itself, so the buyer pays no extra VAT or customs fee.
  - **Momsfri försäljning** — the shop sells at 0 % VAT and the buyer clears the parcel through Customs and pays VAT there.
  - **Levererar till Åland** — ships to Åland; the VAT handling needs confirming with the shop.
  - **Via kontakt med kundtjänst** — the shop removes or refunds the VAT after customer service is contacted.

## Using leverans.ax

leverans.ax is a refreshable list of shops that sell to Åland, and the first place to look when choosing where to buy. It is not comprehensive (the user adds shops that are missing) and not fully accurate: it lists AliExpress as customs-cleared with IOSS, which no longer works, so treat AliExpress as a shop that does not deliver to Åland VAT-free. A shop's label is a starting point to confirm at checkout.

Amazon is the one Amazon site that sells to Åland without VAT: amazon.de. The leverans.ax entry "Amazon" refers to it.

Prices are compared with VAT included. A tax-free shop's checkout price carries no VAT, and the user then pays Finnish VAT (25.5 %) at Åland customs, so the price to compare with a Finnish shop's price is the tax-free charge multiplied by 1.255, plus any customs or handling fee. Amazon.de listings show the German VAT-inclusive price, and the VAT-free charge at checkout is the listing price divided by 1.19.

`leverans-ax-snapshot` reads every page of the directory and prints `{source, fetchedAt, pages, knownChecked, new, removed, shops: [{name, category, label, vat, page}]}` as JSON on stdout (progress on stderr). `label` is leverans.ax's wording and `vat` its normalized form: `tax-border-number`, `zero-vat`, `zero-vat-via-support`, `ioss`, `refund-via-support`, `delivers`.

`leverans-ax-known.txt` records the shops the user has been told about (first line `# checked <date>`, then one name per line). `new` and `removed` in the script's output are the differences against it.

When recommending where to buy, and `knownChecked` in the file's header is more than a month old, run `leverans-ax-snapshot`, tell the user which shops are `new` or `removed`, then run it again with `--accept` to record them and commit the updated file. State the `fetchedAt` date when quoting a shop's status.

Shops the user buys from have a note under `sites/` with what the store is and its leverans.ax label; shops without one are only in the directory. Create a `sites/<shop>.md` when the user starts considering a shop.

## Reading the directory live

`https://leverans.ax/alla-foretag/` lists every entry alphabetically, 15 per page, at `/alla-foretag/<n>/` (page 1 has no number). `https://leverans.ax/<category>/` filters by category (`hemelektronik`, `hem-hushall`, `bygg-renovering`, …) and the homepage shows only a sample. Pages render client-side; `shop-browse <url> --text` reads them, with each entry between the line `ⓘ Denna sida innehåller reklamlänkar` and the `Visa fler företag` button as a name, an optional category line and a label line. The site has no API or data file.
