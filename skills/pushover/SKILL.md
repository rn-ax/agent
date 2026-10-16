---
name: pushover
description: Use whenever a task sends a notification to the user's phone — alerting, "notify me when X finishes", wiring a service's notifications, or anything about "pushover" explicitly. Pushover is the user's main notification channel, so read this before choosing how to notify, adding a new sender, or looking up the Pushover keys.
---

# Pushover

This is the accumulating knowledge base for the user's Pushover setup. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content.

**Related systems**: Uptime Kuma (`uptime-kuma` skill) and Healthchecks.io (`healthchecks` skill) both alert through Pushover; the `home` skill maps the rest.

## Role

Pushover delivers most of the user's notifications to their phone. Anything that needs the user's attention (an outage, a finished job, a failed automation) notifies through Pushover.

## Credentials

The "Pushover" item in the "Agent" 1Password vault holds:
- `username` — the user's User Key (identifies the recipient).
- `email` — the user's Pushover email address; mail sent to it becomes a notification, which suits a system that can only send email.
- one concealed field per **application token**, named after the sender (currently `Uptime Kuma`). Pushover shows the application's name and icon on each notification, so each sender gets its own application and its own field.

A new sender gets a new application at pushover.net (the user creates it), and its token is added to the item as a field named after the sender.

## Sending: `pushover-send`

`pushover-send -a <app> [-t <title>] [-p <priority>] [-u <url>] <message>` (this skill's directory) reads the User Key and the named application's token from the item and posts to the Pushover API, keeping both off the command line. `-a` names the field holding the sender's token; the JSON reply has `"status":1` on success.

Priorities: `-2` silent (appears in the app only), `-1` quiet, `0` normal (default), `1` high (bypasses the user's quiet hours), `2` emergency (repeats every 60 seconds for an hour until acknowledged). Reserve `1` and `2` for outages; test with `-2` so the phone stays quiet.

## Consumers

- **Uptime Kuma** — a notification named `Pushover`, default-enabled and attached to every monitor, using the `Uptime Kuma` application token.
- **Healthchecks.io** — a Pushover integration on its channel, so a missed ping reaches the phone.
