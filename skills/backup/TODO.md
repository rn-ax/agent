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

- [ ] Attach the Deltaco enclosure to the Mac mini `server.lan` over USB 3.0 and set it to Clear RAID with the power off.
- [ ] Test with a spare disk that Clear RAID shows every disk separately over USB.
- [ ] Test a disk larger than 3 TB in the enclosure (the vendor lists a 15 TB maximum for five bays).
- [ ] Choose which disks serve as data, backup and spare, and format them.
- [ ] Record what the Mac mini `server.lan` runs today (Paperless among others) and which of that data is a backup source.
- [ ] Enable Remote Login and File Sharing on the Mac mini, create the Time Machine share and set a quota per Mac.
- [ ] Decide on sleep and power settings for an always-on backup server; Clear RAID gives the enclosure no sleep mode.
- [ ] Record the quantity and the serial number of the enclosure in Homebox (the user has more than one) and fill in the Mac mini's configuration there.
- [x] The enclosure is identified (Deltaco SI-1359RUS3) and recorded in Homebox with its manual and photos.

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
- [ ] Find out whether SMART data is readable through the enclosure's USB bridge, and monitor disk health if it is.
- [ ] Write a restore runbook for each source (TrueNAS dataset, Mac, Home Assistant).

## Skill upkeep

- [ ] Link the skill into `~/.claude/skills/backup` once the pull request is merged.
- [ ] Move each planned section of `SKILL.md` to confirmed as it is set up and a restore is tested.
