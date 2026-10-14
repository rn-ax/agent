---
name: backup
description: Use whenever a task touches backups of the user's home systems — what gets backed up, where copies live, the backup server (the M1 Mac mini with its drive enclosure), TrueNAS snapshot/replication/Cloud Sync tasks, Time Machine for the Macs, offsite copies, restore tests, or "is X backed up". This is the living design and status document for the user's backup solution, so read it before proposing or changing any backup mechanism, and update it in the same pass as any decision or change.
---

# Backup

The design and status of the user's home backup solution. It is built iteratively: each section says whether it records something **confirmed** on the live systems or something **planned**, and moves from planned to confirmed once it is set up and a restore has been tested. Keep new findings and decisions here as they happen.

Open work is listed in `TODO.md` next to this file; an item leaves that list when it is done, and what it established moves into this file.

**Related systems**: see the `home` skill for the topology map. `truenas` holds the pools and datasets being backed up, `homebox` records the physical hardware (the backup server, the drive enclosure and the disks), `home-assistant` and `paperless` hold data worth protecting, and `email` covers the mailbox that holds purchase history.

## Principles

- **3-2-1**: three copies, on two kinds of storage, one of them offsite.
- **No hardware RAID dependency**: every disk in the backup enclosure is an ordinary independent disk that reads in any dock or adapter, so a failed enclosure costs nothing but the enclosure.
- **History**: a backup keeps earlier versions (snapshots, Time Machine, a versioned repository), so a deleted or corrupted file stays recoverable after the next run.
- **Encrypted offsite**: data leaves the house encrypted client-side, with the key kept in the password manager.
- **Monitored**: every job reports success to a health-check service, so a silent failure becomes an alert.
- **Tested**: a restore of a sample file from each copy runs on a schedule; an untested backup is recorded as unverified.

## What exists today (confirmed 2026-10-13)

TrueNAS (`truenas.lan`):

- `Storage` pool: **RAIDZ1 over four 8 TB disks** (single-disk redundancy), about 29 TiB raw and 82% full. It holds the configuration, the data and the important media.
- Three further pools (`Misc-63`, `Misc-102`, `Misc-204`), each a single disk with one `Movies` dataset. They hold the media the user accepts losing, so they have no redundancy and no backup by design.
- The system disk (the boot SSD, `boot-pool`) has no backup. If it dies the TrueNAS install and its configuration go with it; see open decision 6.
- Scrubs run on every pool and report no errors.
- No periodic snapshot tasks and no replication tasks exist. The snapshots that are present come from the Apps system.
- One Cloud Sync task pushes `Storage/Books` to Dropbox hourly in SYNC mode, which mirrors deletions to the remote copy. Its credentials live in TrueNAS and the cloud account.
- Healthcheck cron jobs ping an external health-check service every five minutes for TrueNAS and the media apps.

Elsewhere: no Time Machine destination or Mac backup is documented yet, and no restore test has been recorded.

## Backup scope

`Storage` datasets by size (approximate, 2026-10-13):

| Dataset | Size | Tier |
|---|---|---|
| `Configuration` | 24 GB | Irreplaceable: app configuration and databases |
| `Homebridge`, `Backup`, `Books`, `Music`, `Talks`, `Audiobooks` | under 50 GB each | Irreplaceable or hard to replace; confirm per dataset |
| `Downloads`, `ix-apps`, `ix-applications` | 60–170 GB each | Regenerable; decide per dataset |
| `Movies`, `TV` | 8.9 TB and 8.2 TB | A subset is important (hard to get); the rest is replaceable. The subset is **not yet defined** |
| `Misc-*` pools | 18 TB in total | Replaceable; excluded |

Everything in `Storage` apart from `Movies` and `TV` is under about 0.5 TB, so the irreplaceable tier fits on one backup disk several times over. The size of the "important media" subset decides the capacity plan.

## Backup server (planned)

The M1 Mac mini `server.lan` is the backup server, with a Deltaco SI-1359RUS3 5-bay enclosure (recorded in Homebox) attached over USB 3.0.

- The enclosure runs in **Clear RAID** mode so every bay is an independent disk. Its manual says only the failed disk is affected when one dies; it has no sleep mode in this mode.
- Open check: the vendor lists a 15 TB maximum (5 × 3 TB), so the behaviour of larger disks in this unit is untested. Test a larger disk before moving data.
- Open check: confirm that Clear RAID shows each disk separately over USB before relying on it.
- Mac backups use Time Machine over SMB (a shared folder on the Mac mini with "Share as a Time Machine backup destination"), one volume or quota per Mac. The Mac mini's own disk is cloned to a separate backup disk with SuperDuper or Carbon Copy Cloner.
- TrueNAS data reaches the Mac mini through rsync over SSH or a versioned tool (restic or Kopia). ZFS replication needs ZFS on the receiving side.

## Offsite (planned, undecided)

A scheduled job on the Mac mini sends an encrypted, versioned copy of the irreplaceable tier (and the important-media subset if it fits) to remote storage. Candidates: object storage (Backblaze B2, Cloudflare R2, Hetzner Storage Box), rotating physical disks from the enclosure's hot-swap trays, or a machine at another site. The deciding inputs are upload speed, the size of the offsite set and the preferred provider. The existing Dropbox sync of `Books` stays until the offsite job covers it.

## Open decisions

1. Which movies and TV shows are "important" and how to mark them (a dataset split, a folder, or a list).
2. Per-dataset tiering for `Homebridge`, `Backup`, `Downloads` and the Apps datasets.
3. Offsite provider and the upload speed available.
4. Whether TrueNAS pushes to the Mac mini or the Mac mini pulls from TrueNAS.
5. Snapshot schedule and retention on `Storage`.
6. How to back up the TrueNAS system disk (the boot SSD) so a dead disk costs a reinstall and a config restore, not the configuration itself.

## Log

- 2026-10-13: Skill created from the design discussion. TrueNAS pool layout, existing tasks and the Cloud Sync job confirmed live.
