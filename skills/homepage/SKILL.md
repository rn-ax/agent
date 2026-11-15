---
name: homepage
description: Use whenever an app is installed, renamed, moved to another port or removed on TrueNAS, because every app with a web UI gets a tile on the landing page; also whenever the user asks about the landing page, "homepage", gethomepage, or how the apps are listed in one place. This is the knowledge base for how the user's Homepage is set up and how an agent adds an app to it, so read it before editing its config or installing an app.
---

# Homepage

The landing page for the apps running on TrueNAS: [Homepage](https://gethomepage.dev/) as a launcher of links, grouped, with an icon per app. Live data about the house belongs to Home Assistant, so the page has no widgets.

**Related systems**: Homepage runs on TrueNAS (see the `truenas` skill for the install playbook and dataset conventions). The repo follows `spec-driven-dev`. A new app also gets a monitor (`uptime-kuma`). The `home` skill maps the whole stack.

## Instance

The page shows only app tiles. `bookmarks.yaml` and `widgets.yaml` are empty files in the repo, because Homepage fills any config file it does not find with sample bookmarks and widgets.

The page is at `http://truenas.machine.rn.ax:30054`, on the home network only; it has no Cloudflare tunnel hostname. It is the catalog app `homepage` (community train), running as UID 1000 without the Docker socket, with `HOMEPAGE_ALLOWED_HOSTS` set to `truenas.machine.rn.ax:30054`. Every tile is declared in the YAML, so the container has no view of other containers.

The configuration lives in the private repo `rn-ax/homepage` (local clone `~/Projects/rn-homepage`), whose `spec/` holds the acceptance criteria and whose `AGENTS.md` holds the delivery details. The config dataset `Storage/Configuration/homepage/config` receives the repo's `config/` through an S3 push; the repo is the source of truth, and a file edited on the dataset is overwritten by the next deploy.

## Adding an app to the page

An app with a web UI gets a tile as part of being installed on TrueNAS.

1. Open the repo's `config/services.yaml`.
2. Add `Name: {href, icon, description}` to the group that fits, or add a group when none fits. Groups say what an app does (`Media`, `Downloads`, `Music and books`, `Planning and tracking`, `Household`, `System`); the project an app belongs to plays no part. `href` is `http://truenas.machine.rn.ax:<port>` with the app's published port (`tn-api app.query '[["id","=","<app>"]]'` shows it under `portals`), or an `https://` URL. A Windmill app has `http://truenas.machine.rn.ax:30155/apps/get/p/f/apps/<folder>` (`wm-api GET /apps/list` lists the folders), so a new Windmill app gets its tile too. An app whose name does not say what it does gets a one-line `description`. `icon` is a name from [dashboard-icons](https://github.com/homarr-labs/dashboard-icons) and is left out when none exists.
3. Run `mise run test`. It enforces the rules of `spec/entries.md`: a unique name, a group, and an allowed `href`.
4. Open the pull request with the `agent-code-pusher` flow. The repo's CI merges it once the build passes and deploys the merged commit, so there is nothing to merge or deploy by hand.

A change to an app's name or port edits its entry, and removing an app removes its entry.

A new rule about what the page shows is a new acceptance criterion in the repo's `spec/`, proposed to the user before any code, per `spec-driven-dev`.

## How the files get there

The gateway is the catalog app `versitygw` (S3 API on port 30157, users in `Storage/Configuration/versitygw/iam`). Its posix backend serves each subdirectory of its root as a bucket, and the Homepage config dataset is mounted into it as the bucket `homepage`, so an S3 push writes the files Homepage reads. The CI user holds the `user` role and owns that one bucket. Homepage reloads its YAML when a file changes.

Another app whose files should arrive the same way gets its own mount into the gateway, its own bucket owner and its own CI user, created with `versitygw admin` inside the container (`create-user`, then `change-bucket-owner`); `AGENTS.md` of the repo lists the exact flags that matter. The gateway has no separate admin port, so the admin API answers on the S3 port.
