---
name: ui-design
description: Use whenever designing, building or changing a user interface for any of the user's apps, whatever the framework (SvelteKit, Windmill apps, Home Assistant dashboards, anything with a screen), and when reviewing a screenshot of one. Holds the principles every interface follows, above all that mobile and desktop are both primary.
---

# UI design

**Related systems**: `sveltekit` (daisyUI and Tailwind in the rn-ax apps), `windmill` (Windmill apps), `playwright` (screenshots at both sizes).

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

A label that says something about the app, such as its version and build time, is small, subdued text at the bottom right of the end of the page, in the page's flow after the content. It scrolls with the page, so it covers nothing at any size.

## Checking

Look at the page at a phone width and at a desktop width. In the rn-ax apps the Playwright screenshot tests run a `mobile` and a `desktop` project over the same pages, so a layout that fails at one size shows up as a screenshot that needs to be looked at.
