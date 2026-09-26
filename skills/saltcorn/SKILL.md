---
name: saltcorn
description: Use whenever the user asks for help with their Saltcorn instance — tables, views, the Tabulator grid plugin, API access, or anything about "saltcorn" explicitly. This is the accumulating knowledge base for how this user's Saltcorn instance is actually set up, so read it before assuming its architecture, access method, or view-building conventions from scratch.
---

# Saltcorn

This is the accumulating knowledge base for the user's self-hosted Saltcorn instance. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content.

## Instance

Self-hosted on TrueNAS (`truenas.lan`) as a **Custom App** (`custom_app: true` + a hand-written `custom_compose_config_string`, not a catalog app) — installed 2026-09-20. See the `truenas` skill's general custom-app playbook and `apps.md`'s Saltcorn section for the install incidents (Postgres 18 mount convention, the image's default command just printing CLI help and exiting unless `serve --addschema` is passed explicitly, `app.update` needing a follow-up `app.redeploy`).

Only reachable on the LAN so far — `http://truenas.lan:31399`. No public Cloudflare Tunnel route/Access app set up yet (unlike Windmill/Baserow/NocoDB).

API credentials live in `~/.config/saltcorn/env` (mode 600): `SALTCORN_BASE_URL`, `SALTCORN_TOKEN`. One token per user (resettable, invalidates the previous one).

## Why this exists alongside Baserow

Chosen after both NocoDB and Baserow turned out to gate basic spreadsheet features (unique-field constraints, row coloring) behind a paid Enterprise/Premium license even self-hosted. Saltcorn is MIT-licensed with genuinely no paid tier — structurally different from the open-core NocoDB/Baserow/Teable model, so there's no "will hit a paywall eventually" risk here. Don't assume this decision is final without checking current status — see the `home` skill's integration-threads section.

**Real tradeoff, not just polish**: Saltcorn's default views are not an inline-editable spreadsheet grid — "List" is read-only, "Edit" is one record at a time via a form. The **Tabulator plugin** (official, `saltcorn/tabulator`, shipped since v0.6.4 — mature, not experimental) adds a real inline-editable grid view template, and is what actually makes this comparable to Airtable/NocoDB/Baserow's UX. It must be activated (Settings → Plugins) before its view template appears in the "Create view" pattern dropdown.

## Table/field naming

Saltcorn has **no separate display label for a table** — the `name` given at creation is both the SQL identifier and what appears in the UI, unlike NocoDB/Baserow's separate internal-name-vs-display-name. A name with a space (e.g. "Cost claims") works but needs URL-encoding (`Cost%20claims`) in every API call from then on. Prefer `snake_case` or `PascalCase` table names from the start to avoid that friction permanently — renaming later just means editing the name field in the table's settings (the underlying SQL table is renamed along with it, data preserved).

## Scripting via `run-js`

`saltcorn run-js -f <script.js>` runs a script inside the instance, but it's **not** a full Node environment — it's `vm.runInNewContext` with a deliberately small sandbox. Confirmed available in that sandbox: `Table` (the class, already imported — no `import`/`require` works at all, both fail), `db` (raw DB access, includes helpers like `db.add_unique_constraint(tableName, [fieldNames])`), `console`, and whatever `getState().eval_context` contains (mostly formula-evaluation bindings, not model classes). **`Field` is not exposed** — there's no working way to `Field.create(...)` from a `run-js` script, and hand-replicating it via raw `db.query`/`db.insert` risks leaving `_sc_fields` metadata out of sync with the real SQL schema (Field.create does engine-specific DDL, default-value handling, and cache invalidation that's non-trivial to reproduce correctly). Table creation via `Table.create(name)` alone works fine from `run-js`; adding fields and building views needs the web UI instead.

## Related systems

See the `home` skill for the full topology map. Most relevant here:
- **Windmill** is the intended consumer of Saltcorn's data via its REST API (`GET/POST /api/<table_name>`, bearer token) — same integration shape as Baserow.
- **Baserow** is the other data-store candidate currently in play — see that skill for why it's not a clean win either.
