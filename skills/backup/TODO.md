# Backup: remaining work

Work still open on the backup solution, grouped by theme. The design, principles and confirmed state live in `SKILL.md`; this file lists what is left to do. Remove an item when it is done and move what it established into `SKILL.md`.

## Scope decisions

- [ ] Movies and TV on `Storage` (8.9 TB and 8.2 TB): decide which titles are important (hard to get) and how to mark them (a dataset split, a folder, or a list), then size that subset. Deferred for now.
- [ ] Tier the small `Storage` datasets (`Homebridge`, `Backup`, `Books`, `Music`, `Talks`, `Audiobooks`) as irreplaceable or replaceable.
- [ ] Decide whether `Downloads`, `ix-apps` and `ix-applications` are backed up or rebuilt.
- [ ] Decide the role of the Synology DS1813+: a backup source with data worth keeping, or retired once its data has moved.
- [ ] Decide whether other sources belong in the plan: the Fastmail mailbox, GitHub repositories, the Cloudflare configuration, a password-manager export.
- [x] The TrueNAS pools, existing tasks and the Cloud Sync job are documented in `SKILL.md`.

## Backup server

- [ ] Attach the TerraMaster D4-320 to the Mac mini `server.lan` over USB 3.2 and check that every bay shows up as its own disk and that the disks mount again after a reboot of the Mac mini.
- [ ] Run a long self-test (`smartctl -t long`) on the first disk (WD Red 3 TB) through the enclosure and record the result and the final SMART counters.
- [ ] Choose which disks serve as data, backup and spare, and format them.
- [ ] Record what the Mac mini `server.lan` runs today (Paperless among others) and which of that data is a backup source.
- [ ] Enable Remote Login and File Sharing on the Mac mini, create the Time Machine share and set a quota per Mac.
- [ ] Test the sleep design on the D4-320: set `pmset disksleep`, confirm with `smartctl -n standby` that an unmounted disk reaches standby, and that it wakes and remounts for a job.
- [ ] Record the D4-320 and its disks (the first is serial `WD-WMC1T2678849`) in Homebox, mark the malfunctioning Deltaco SI-1359RUS3 as faulty there, and fill in the Mac mini's configuration.

## TrueNAS

- [ ] Create periodic snapshot tasks and a retention policy for `Storage` (none exist).
- [ ] Choose the transport to the backup server: rsync over SSH, or a versioned tool (restic or Kopia), and whether TrueNAS pushes or the Mac mini pulls.
- [ ] Back up app databases through dumps or snapshots so the copies are consistent; copying live database files from `Configuration` risks a corrupt copy.
- [ ] Save a TrueNAS system configuration export (System, General) on a schedule and include it in the backup set.
- [ ] Move the Books-to-Dropbox sync into the new plan once the offsite job covers it, then retire it.
- [ ] Re-authorise the Dropbox Cloud Sync connection (credential rotation).

## Macs and other sources

- [ ] List the Macs to protect and set up Time Machine on each against the Mac mini share.
- [ ] Clone the Mac mini's own disk to a separate backup disk with SuperDuper or Carbon Copy Cloner.
- [ ] Find where Home Assistant stores its backups and include them in the backup set (the Pi 5 has no redundancy).
- [ ] Include the Paperless data, Homebox, Windmill and the other app configuration under `Configuration` in the TrueNAS backup set.

## Offsite

- [ ] Measure the upload speed available at home.
- [ ] Choose the provider or method: object storage, rotating physical disks or a machine at another site.
- [ ] Choose the tool (restic, Kopia, Arq or rclone) and set up client-side encryption with the key in the password manager.
- [ ] Define the offsite set (the irreplaceable tier, plus the important media if it fits) and run the first upload.

## Monitoring and verification

- [ ] Give every backup job a health-check ping, and alert on a missed run through Home Assistant or Windmill.
- [ ] Schedule a sample restore from each copy and record the result.
- [ ] Add a SMART check to every backup job (fail on non-zero reallocated, pending or offline-uncorrectable counts) and a monthly long self-test of each backup disk.
- [ ] Write a restore runbook for each source (TrueNAS dataset, Mac, Home Assistant).

## Skill upkeep

- [ ] Move each planned section of `SKILL.md` to confirmed as it is set up and a restore is tested.
