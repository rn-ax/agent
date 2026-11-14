---
name: trotter
description: Use whenever the user wants places, visits, trips or transportation recorded in trotter, asks what trotter holds, or needs an agent to enter or change trotter data (a trip, a restaurant, a hotel stay, a flight or ferry, ratings, tags). Holds how to reach trotter's API, the data model and field formats, and the steps for entering a trip.
---

# trotter

trotter records visits to places, grouped into trips with the transportation between places. The repo is `rn-ax/trotter` (its `spec/` is the authority on behaviour), and it runs as the TrueNAS app `trotter`, a single PocketBase on `http://truenas.machine.rn.ax:31001` with its data in `Storage/Configuration/trotter/pb_data` (backed up with the rest of `Configuration`).

**Related systems**: `pocketbase` (how the backend behaves), `truenas` (where it runs and its data), `spec-driven-dev` (how changes to trotter are made).

## Reaching the API

`trotter-api <method> <path> [curl-args...]` (this skill's own directory) adds the base URL and signs in, nothing else, so every request is the agent's decision. It reads the "Trotter" item in the "Agent" 1Password vault (url, username, password); `TROTTER_URL`, `TROTTER_EMAIL` and `TROTTER_PASSWORD` override it, and `TROTTER_AUTH_COLLECTION` is `users` for the owner's login (the default) or `_superusers` for an administrator.

Everything requires a signed-in login. Changes made by an administrator are recorded in the history log under `admin`, and those made by the owner's login under the user, so an agent's work is told apart when it has a login of its own.

## Data

Records are plain PocketBase collections, `/api/collections/<name>/records`. Every list is small enough to fetch whole (`perPage=500`).

- **places**: `name`, `type` (`food`, `lodging`, `airport`, `station`, `harbor`, `home`, `other`), and optionally a lookup snapshot, `source` (`nominatim`), `source_id`, `latitude`, `longitude`, which are given all together or not at all and never change afterwards. Names are not unique, and a new place is always a new record, so look for an existing one before creating.
- **visits**: `place`, `start` (required), `end` (optional), `rating` (1 to 5, left out when unrated), `tags` (a list of words of lowercase letters, digits and hyphens, no repeats, without a `#`), `trip` (optional, fixed when the visit is created).
- **trips**: no fields. A trip is shown by what it holds, so create it with `{}` and then give visits and transportations its id.
- **transportations**: `trip`, `from_place`, `to_place`, `mode` (`car`, `flight`, `train`, `ferry`, `bus`), `departure`, `arrival` (all required, the arrival not before the departure), `name` (optional, such as a vessel's).
- **auditlog**: read-only history of changes to places and visits.

Times are the clock time at the place, written as if they were UTC: `2026-11-08 22:25:00.000Z` for 22:25 on 8 November. Nothing records a timezone.

A place that has visits or transportations cannot be deleted, a trip that has either cannot be deleted, and a visit cannot be moved to another trip; each answers 400 or 404.

## Place lookup

`GET /api/places/search?q=<text>` asks OpenStreetMap (Nominatim) for candidates and answers a list of `{name, display_name, type, source, source_id, latitude, longitude}`. It allows one real search per second, caches repeats, and answers 429 when called too fast, so wait and retry. Create the place with the candidate's `source`, `source_id`, `latitude` and `longitude`, the name the user knows it by, and the trotter `type`. A place with no good candidate is created by name and type alone and has no location.

## Entering a trip

The account of a trip is a list of places visited, stays, meals and moves. Each write is one request, and the agent checks the answer before the next.

1. Read what already exists: `places`, `trips` and `visits` (`perPage=500`), so nothing is entered twice.
2. For each place not yet there, look it up, choose the candidate whose `display_name` matches what the user described (the right district and city), and create the place. Report the candidates chosen, and the places created by name only.
3. Create the trip with `{}`, then each visit and transportation with its `trip`.
4. Times the user did not give (a meal's clock time, a check-in) are estimated by the agent and reported as estimates, since every visit and transportation needs them.
5. Read the trip back (`trip = "<id>"` as the filter, with `expand=place` or `expand=from_place,to_place`) and compare it with the account, item by item, before reporting it done.

A change to a record is an `update` of that record; to correct a mistake in a trip, update the record, and delete a visit or transportation only when it should not exist.
