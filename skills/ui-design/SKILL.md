---
name: ui-design
description: Use whenever designing, building or changing a user interface for any of the user's apps, whatever the framework (SvelteKit, Windmill apps, Home Assistant dashboards, anything with a screen), and when reviewing a screenshot of one. Holds the principles every interface follows, above all that mobile and desktop are both primary.
---

# UI design

**Related systems**: `sveltekit` (daisyUI and Tailwind in the rn-ax apps), `windmill` (Windmill apps and their table conventions), `playwright` (screenshots at both sizes).

## Mobile and desktop are both primary

Every interface is used on a phone and on a desktop browser, and works well on both. Neither is a fallback for the other: a page is designed for a phone-sized screen and a wide one at the same time, and checked at both before it counts as done.

### On mobile

- Show only what the user needs at that moment. Information that is secondary is left out of lists and rows, or moved behind a tap, so a row stays readable at phone width.
- Elements take the width of the screen and rearrange as it narrows: a row of buttons wraps or stacks, side-by-side columns become one column in an order that puts the most important thing first, long text wraps or is cut with the full text one tap away.
- Large or optional sections collapse and expand, so the page does not become a long scroll of everything at once.
- Touch targets are large enough to hit, and nothing sits where it covers content that has to be reached, such as a fixed label over the bottom of a form.

### On desktop

- The layout uses the width of the screen: content is laid out in wider columns, a list and its detail sit side by side, and a form's fields use the room they have, so the page does not become a narrow strip in the middle of a wide screen.
- Information that was left out of a phone's row is shown, since there is room for it.

### The same page at every size

One page serves both. Its structure is a layout that reflows between the sizes, and the same content, actions and URLs exist at each size. A feature is built once and shown differently, never built twice.

## Labels about the app itself

A label that says something about the app, such as its version and when it was deployed, is small, subdued text at the bottom right of the end of the page, in the page's flow after the content. It scrolls with the page, so it covers nothing at any size.

The version label reads `v2026.11.15.73 (3s ago)`: the version, then how long ago it was deployed as a compact age (`3s`, `5m`, `2h`, `4d`), and hovering it shows the exact date and time of the deploy in the user's time zone. The age comes from the time the deploy recorded, so nothing else is stored for it, and an app running without a deploy time (a local preview) shows the version alone. Every app shows it the same way.

## Tables

- Every table opens in its natural order, and every column sorts, by the value and not by the text shown (an ISO time, a number). A table paged by the backend sorts and filters there, so a sort orders every row and not only the page on screen.
- Filters are checkboxes in a bar above the table, one per filter, labelled by what they narrow to; a ticked filter narrows the list and several narrow it together. A choice of one value (an event type) is a select in the same bar.
- A time reads as how long ago it was (`5 minutes ago`), with the exact date and time on hover, and its column sorts by the time itself.

## Dark layouts

An app that is always dark sets its theme once, on the document root, and every part of every component is checked in it, not only the parts that were themed on purpose.

- A component library ships light colours as its defaults, often as the fallbacks of its CSS variables, and styles its native controls (a page-size select, scrollbars, checkboxes, date pickers) by a colour scheme that defaults to light. A table with only some of its colours themed looks dark in its rows and light in its pagination, its select and its scrollbars. Set every colour variable the library reads, and set its colour scheme to dark.
- Check the theme against the library's own stylesheet, not by eye: a test lists the colour variables the stylesheet falls back to a light colour for and fails when the app does not set one. A library upgrade that adds a colour then fails a test, not a page.
- A rule that targets a library's class names is checked against the installed version. Names change between major versions (`rdt_Table` in react-data-table-component 7, `rdt_table` in 8), and a rule for a class that does not exist matches nothing and reports no error, so a test lists the classes the app styles and checks that the installed stylesheet has them.

## Checking

Look at the page at a phone width and at a desktop width. In the rn-ax apps the Playwright screenshot tests run a `mobile` and a `desktop` project over the same pages, so a layout that fails at one size shows up as a screenshot that needs to be looked at.
