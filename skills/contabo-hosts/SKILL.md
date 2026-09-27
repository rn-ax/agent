---
name: contabo-hosts
description: Use whenever a task touches the two Contabo VPS boxes (contabo-1/contabo-2) — provisioning them, GitHub Actions or Gitea Actions self-hosted runners, their Cloudflare WARP/Tunnel setup, or anything about deciding whether a private rn-ax repo's CI should run there instead of GitHub-hosted runners. This is the accumulating knowledge base for how these boxes are actually set up, so read it before assuming their connectivity, runner conventions, or IaC from scratch.
---

# Contabo hosts

Two Contabo Debian VPS boxes (`contabo-1` / `contabo-2`, Cloud VPS 6 tier — 6 cores / 12GB RAM / ~200GB disk each) that run self-hosted CI runners and a handful of small self-hosted apps. Public IPs `169.58.173.62` (contabo-1) / `169.58.173.63` (contabo-2) — see `~/Projects/rn-infra/inventory/hosts.yml` for the source of truth if these ever change.

**SSH**: `~/.ssh/config` has a per-host `Host contabo-N` block (just `HostName <ip>`) plus a shared `Host contabo-*` wildcard (`User deploy`, `IdentityFile`, `IdentitiesOnly`). Plain `ssh contabo-1`/`ssh contabo-2` logs in as `deploy`; `ssh root@contabo-N` for root (only needed for first bootstrap).

**IaC**: `~/Projects/rn-infra` (Ansible). See that repo's own `AGENTS.md` for layout/bootstrapping/secrets conventions — this file covers operational knowledge about what's actually running, which is a different concern from the IaC's own structure.

## Connectivity to the home LAN

Both boxes run Cloudflare WARP as an unattended Zero Trust client (`cloudflare_warp` role), enrolled via `mdm.xml` MDM parameters. The Zero Trust org's Split Tunnel Include already routes `192.168.1.142` (TrueNAS's LAN IP) directly by IP — so both boxes can reach TrueNAS's LAN services with no separate tunnel/service-token setup needed. WARP doesn't resolve `.lan` hostnames itself, so the role pins `truenas.lan` to that IP in `/etc/hosts`.

**Confirmed live (2026-09-27)**: `curl http://truenas.lan:30155/api/version` (Windmill's LAN endpoint) returns `200` directly from both boxes, no proxy or extra auth needed. This means **any self-hosted-runner job on these boxes has a direct path to TrueNAS-hosted services** — a GitHub-hosted runner does not, and has to go the long way through whatever public/Access-gated hostname the service exposes.

The `windmill` skill previously described Contabo→TrueNAS job-execution connectivity as "planned, not yet built" with a separate TCP-application-plus-service-token plan for reaching Postgres specifically — that note was stale. The general WARP private-network route already covers it; no dedicated Postgres-specific Access application has been (or needs to be) built for this.

`git-internal.rn.ax:30022` (a Gitea-specific hostname `gitea_runner` also depends on) is being torn down in favor of routing to `truenas.lan` directly — don't build new dependencies on `git-internal.rn.ax`.

## Runners: two independent systems

Both boxes run **two separate runner stacks side by side**, unrelated to each other:

- **Gitea Actions** (`act_runner`, role `gitea_runner`) — Docker-executor based, jobs run in containers (`catthehacker/ubuntu:act-*` images — act_runner's own fallback image is missing Node.js, which is why labels are registered with an explicit `:docker://` image rather than left bare). Capacity 4 concurrent jobs per box, sized against `monocoque`'s actual CI weight (see `inventory/group_vars/runners/vars.yml`'s comments for the reasoning).
- **GitHub Actions self-hosted runner** (native process, not containerized — role `github_runner`) — this is the one relevant to "should this repo's CI run on Contabo" questions. See below.

## GitHub Actions runner convention: repo-scoped, not org-level

**The `github_runner` Ansible role's own defaults describe org-level registration** (`github_runner_org_url: https://github.com/rn-ax`, single label `contabo`) — **this is stale and does not match reality.** An org-level runner hit a confirmed bug where it silently stops accepting jobs from the queue while still reporting online (see the `github` skill's "Self-hosted runner: stuck job dispatch" section for the full incident writeup and the escalating fixes tried). The fix that actually worked was converting to a **repo-level** runner on the same host, and every runner actually running on these boxes today is repo-scoped, registered by hand rather than through this Ansible role as currently written. The role's org-level defaults should eventually be updated to match, but as of 2026-09-27 they haven't been — don't trust `roles/github_runner`'s own comments about scope.

**Currently registered** (one instance per repo per box, each in its own install directory since each is a separate `config.sh` registration):

| Repo | Install dir | Labels |
|---|---|---|
| `rn-ax/monocoque` | `/opt/github-runner` | `self-hosted, Linux, X64, contabo` |
| `rn-ax/windmill` | `/opt/github-runner-windmill` | `self-hosted, Linux, X64, contabo` |
| `rn-ax/actions` | `/opt/github-runner-actions` | `self-hosted, Linux, X64, contabo` — **repo is archived, so this runner is currently a no-op**; GitHub blocks Actions execution entirely on archived repos (job stays `queued` forever with zero job records, eventually auto-cancelled — this was the actual root cause of that repo's `mirror-base-images.yml` failures, not a runner problem) |

All run as the same `github-runner` system user (uid/gid consistent across boxes), installed via the vendor's own `svc.sh` as a systemd service named `actions.runner.<org>-<repo>.<hostname>.service`.

**To register a new repo's runner** (on each box that should carry it):
```sh
TOKEN=$(gh api -X POST repos/rn-ax/<repo>/actions/runners/registration-token --jq .token)
ssh contabo-N "sudo mkdir -p /opt/github-runner-<repo> && sudo chown github-runner:github-runner /opt/github-runner-<repo> && sudo -u github-runner bash -c 'cd /opt/github-runner-<repo> && curl -fsSL -o runner.tar.gz https://github.com/actions/runner/releases/download/v<version>/actions-runner-linux-x64-<version>.tar.gz && tar xzf runner.tar.gz && rm runner.tar.gz'"
ssh contabo-N "sudo -u github-runner bash -c 'cd /opt/github-runner-<repo> && ./config.sh --url https://github.com/rn-ax/<repo> --token $TOKEN --name contabo-N --labels contabo --unattended --replace'"
ssh contabo-N "sudo bash -c 'cd /opt/github-runner-<repo> && ./svc.sh install github-runner && ./svc.sh start'"
```
The registration token is repo-scoped (different endpoint from the org one), expires in ~1h, and is reusable for registering the same repo on multiple boxes within that window. The runner binary self-updates on first connect (observed 2.336.0 → 2.337.0 automatically) — don't chase pinning the exact version.

**Policy: private rn-ax repos default to self-hosted Contabo runners, not GitHub-hosted.** Public repos get free GitHub-hosted minutes and have no reason to move; private repos meter Actions minutes with no such allowance, and Contabo capacity sits idle otherwise. A private repo whose CI needs to reach a home-LAN service (TrueNAS, Windmill, etc.) gets this doubly for free — direct LAN reachability instead of a Cloudflare Access proxy workaround. See the `github` skill for the org-conventions section this policy lives in.

## Resource headroom

As of 2026-09-27: ~85–106GB disk free and ~9GB RAM available on each box even with `act_runner` (capacity 4) plus three native GitHub runner instances running. Light CI workloads (deploy pushes, image mirrors, app builds) fit comfortably; re-check headroom before adding anything heavier (e.g. a fourth or fifth repo's runner, or raising `gitea_runner_capacity`).

## Known documentation gap

`rn-infra`'s `AGENTS.md` and the `cloudflare_warp`/`gitea_runner` roles' own comments point Gitea-runner-specific operational knowledge (registration token retrieval, naming vs. the `rutinerad-mini`/`Server`/`TrueNAS` Gitea runners, troubleshooting) at `~/.claude/skills/gitea/references/contabo-runner-operations.md` — **that skill does not exist on this machine.** Either it was never created, or it exists only on a different machine/session and never synced here. This file (`contabo-hosts`) covers the GitHub-Actions-runner side of things instead; the Gitea-side operational detail those references promise is still genuinely undocumented if it's ever needed.

## Related systems

See the `home` skill for the full topology map. `rn-infra` is the IaC source of truth for these boxes. The `github` skill covers the stuck-org-runner incident and general org CI conventions. `truenas`/`windmill` cover the services these boxes now have a confirmed direct path to.
