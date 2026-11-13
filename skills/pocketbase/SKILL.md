---
name: pocketbase
description: Use whenever building, changing, testing or packaging an app on PocketBase — collections and migrations, JS hooks (`*.pb.js`), relations and cascade deletes, serving a static frontend, authentication from a client, Docker images, or integration tests against a real PocketBase. Holds how PocketBase behaves where its documentation is easy to misread, as established building rn-ax apps.
---

# PocketBase

Facts here were established on PocketBase 0.40.5, the version the apps pin in `mise.toml`.

**Related systems**: `sveltekit` (the frontend these apps serve), `truenas` (where the image runs), `spec-driven-dev` (how the apps are specified and shipped).

## Migrations

- Applied migrations are tracked by filename. A schema change is a new migration file, and an edit to an applied file never reaches a database that has already run it.
- A schema change made through the API or the admin UI writes a migration file when automigrate is on. An image and its test servers run with `--automigrate=false`, so the next start does not apply a file nobody wrote.
- A collection created in a migration has no `created` or `updated` field unless the migration declares `autodate` fields.
- A relation without cascade delete makes PocketBase refuse to delete a record that a required relation still references, and it answers 400. A cascading relation deletes the referencing records.
- PocketBase stores an unset number as 0, and 0 is also a valid value. A hook that must tell them apart checks which fields the request sent.

## JS hooks

- Hooks are JavaScript run by PocketBase's embedded engine, so there is no TypeScript, no Node and no build step. Editors get PocketBase's types from `/// <reference path="../pb_data/types.d.ts" />`.
- Only files ending in `.pb.js` in the hooks directory load automatically. Any other file is a helper.
- Handlers run in isolated runtimes. Shared code is loaded with `require(`${__hooks}/file.js`)` inside the handler, and state shared between requests lives in `$app.store()`.
- A request hook that writes an extra record together with the change runs the save and the extra write in one transaction: it sets `e.app` to the transaction's app, calls `e.next()` once, saves the extra record with that app, and restores `e.app`. A change whose extra record cannot be saved is then rolled back.
- An app that serves a single-page frontend answers undefined `/api/*` routes with 404 from a hook, so the frontend's fallback to `index.html` never answers an API call.

## Authentication from a client

- A token the server no longer accepts still looks valid in the browser. A list request with it answers 200 with nothing in it, because an invalid token counts as no token.
- A client checks the session once at startup with `authRefresh()` and signs out locally on any 401.

## Serving a frontend

PocketBase serves a static build from its public directory (`--publicDir`), so the image holds no Node or Bun.

## Tests

- Integration and end-to-end suites start a real PocketBase on an empty temporary data directory with the app's migrations and hooks, and create a superuser with `superuser upsert --dir`.
- The same integration suite runs against the built Docker image to cover packaging.
- A container on a Linux host cannot reach a service on its host through the firewall. Image tests point external lookups at an address nothing listens on and skip the tests that need answers.
