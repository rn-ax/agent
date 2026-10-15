# Verkkokauppa.com

Finnish electronics retailer. The storefront is a client-rendered single-page app, so all product data arrives through JSON APIs after the page loads.

## Product price and stock: `verkkokauppa-product`

`verkkokauppa-product <pid>...` (this skill's directory) takes product ids and prints a JSON array of `{pid, name, price, previousPrice, inStock, soldOut, url}`. `price` is EUR including VAT. `previousPrice` is the price before the latest change and can be lower than `price`. An unknown pid is silently absent from the output.

The script calls two endpoints that need no authentication and accept several comma-separated ids per request:

- `https://product.service.verkkokauppa.com/fi/api/v1/product?filter[pid]=<id>,<id>` — JSON:API document; each article carries `price.current`, `price.original`, `name`, `href`, brand, bullet points, description and active campaigns. Curl needs `-g` so the brackets are not treated as a glob.
- `https://product.service.verkkokauppa.com/fi/api/v1/availability?pids=<id>,<id>` — per pid: `flags.isSoldOut`, `stocks.shipment.isPurchasable` and `stock`, plus per-pickup-location stock under `stocks.pickup`.

## Product ids and URLs

A product URL is `/fi/product/<pid>/<slug>`. The pid alone resolves (`/fi/product/975140` loads the page), so ids taken from search snippets or lists are enough. Links in search results carry a long `#list=...` tracking fragment that can be dropped.

## Search needs a browser

`https://www.verkkokauppa.com/fi/search?query=<terms>` renders results client-side and there is no unauthenticated search endpoint. Load it with `shop-browse '<url>' --links /product/`: the link text is the product title and the href holds the pid. Result tiles contain no price, so collect the pids and pass them to `verkkokauppa-product`.

Search is fuzzy and returns related products and accessories when the exact item no longer exists (a query for a discontinued GPU returns current-generation cards). Check that returned titles match the query before concluding the item is stocked.

## Endpoints that do not work

`web-api.service.verkkokauppa.com/search` answers `204` with an empty body, and `web-api-cdn.service.verkkokauppa.com` does not connect.

## Page-scraping fallback

When the product API is unavailable, a rendered product page shows the consumer price after the text `Hintatiedot Alv 25,5 % Hinta <price> €`. Other euro amounts on the page (financing instalments, shipping, accessories) are not the product price, so anchor on `Hinta` and avoid taking the first euro figure.
