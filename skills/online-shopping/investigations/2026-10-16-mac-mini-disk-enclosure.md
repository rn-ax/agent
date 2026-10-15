# Disk enclosure for the Mac mini M1 (backup server)

Investigated 2026-10-16. Prices are EUR as shown to a consumer on that date.

## Request and requirements

Replace the Deltaco SI-1359RUS3 5-bay enclosure planned for the Mac mini `server.lan` (another session noted it is old and unreliable; the vendor lists a 15 TB maximum and large disks are untested in it). Requirements the user gave:

- At least 2 bays; more if the extra cost is small.
- USB 3 (5–10 Gbps) to the Mac mini M1.
- Every disk independent (JBOD), with no hardware RAID dependency, as in the `backup` skill's design.
- Big modern 3.5" disks.

## Sources used

- Shops read with `shop-browse`: Multitronic (search and product pages), Verkkokauppa (search, `verkkokauppa-product`), Amazon.de (search and product pages).
- Vendor/retailer spec text on the Multitronic product pages.
- TerraMaster support forum threads and a retailer summary of the ICY BOX spec, found with `WebSearch`.
- Not readable: Wirecutter (see `reviews.md`), so no independent review of any candidate was available. Ratings below are shop ratings.

## Candidates

| Product | Bays | Mode | Multitronic | Amazon.de (delivery to Åland shown) |
|---|---|---|---|---|
| TerraMaster D4-320 | 4 × 3.5"/2.5" SATA | JBOD only, no hardware RAID | 349,90 € | from 188,99 € |
| TerraMaster D2-320 | 2 | RAID 0/1/JBOD selectable | 199,90 € | from 125,99 € |
| TerraMaster D6-320 | 6 | No RAID | 442,90 € | from 296,99 € |
| TerraMaster D8 Hybrid | 4 SATA + 4 NVMe | RAID 0/1/JBOD/single | 338,90 € | — |
| ICY BOX IB-3740-C31 | 4 | JBOD | 282,90 € | not found |
| ICY BOX IB-3640SU3 (Verkkokauppa) | 4, USB 3.0/eSATA | — | 160,99 € at Verkkokauppa | — |

Notes:

- D4-320: USB 3.2 Gen 2 (10 Gbps), 120 mm temperature-controlled fan around 21 dB, 72 W supply, tool-free hot-swap bays, up to 88 TB stated, filesystems include APFS and Mac OS Extended. The Multitronic text says it acts as a single-disk enclosure with no hardware RAID. Amazon.de rating 4.2/5 (387) on one listing and 4.4/5 (161) on another.
- ICY BOX IB-3740-C31: USB 3.2 Gen 2 with UASP, aluminium and plastic housing with fan; retailers state up to 10 TB per bay, which is below the disk sizes this backup design is likely to use.
- ICY BOX IB-3640SU3 at Verkkokauppa is the same generation as the Deltaco it would replace, so it was excluded.
- Multitronic prices include Finnish VAT; the page offers an "ALV 0 %" view.
- Amazon.de pages show "Liefern nach Ålandinseln" and the variant selector gives the "from" prices above; the buy-box price of each listing was not readable with `shop-browse`, so confirm it at checkout.

## Findings on Mac compatibility

The TerraMaster forum (forum.terra-master.com) sits behind a Cloudflare challenge that `WebFetch` and `shop-browse` cannot pass. The user pasted the main thread, "[Help] D4-320 sleep issue on Mac" (19–23 Sep 2025), and the findings come from it plus `WebSearch` summaries of other threads.

- **The thread.** An M1 Mac user ran four Seagate IronWolf 8 TB disks as a macOS (Apple) software RAID 1 array in a TerraMaster D5-300C and then a D4-320, and saw five drive failures or degraded-array events in about a year. They believe the enclosure sleeps the disks against the Mac's power settings, which they could not change. TerraMaster support replied that the enclosure's sleep state depends on the Mac, noted "it seems you are using the built-in software RAID on your Mac", suggested trying without RAID, and later stopped investigating when the user declined. The reporter disputes the RAID explanation but gave no evidence beyond the same symptom on two enclosures. The user concludes the complaint is about macOS software RAID, not the enclosure, and will not use RAID.
- **Second post, same thread (19 Jun 2026).** A Mac mini M4 user ran two 16 TB disks as macOS software RAID 1 in a D4-320 and lost both disks after short use. They suspect the Apple RAID presents a virtual device that the system's sleep settings apply to, with no passthrough to the physical disks, so the D4-320 falls back to its own aggressive default of spinning down after about 60 seconds without use. Their workaround is a script reading 1 MB of a random file every 30 seconds (cached reads do not keep the disks awake). TerraMaster support replied that the enclosure follows the system into hibernation and pointed to the same sleep-settings post (t=3840). This is the reporter's theory, not a confirmed cause. It extends the problem reports from the M1 to an M4 Mac.
- **What that implies for single disks.** The D4-320 has no RAID of any kind built in. Disk sleep in that mode is controlled by the host operating system, so with independent disks the likely effect of sleep is a wake-up delay on first access, with no array to degrade. This is an inference from the threads, not something a source states. The reported 60-second idle spin-down still applies to single disks: with infrequent access (a nightly backup job) it is harmless, while steady sporadic access (hourly Time Machine, SMB browsing) would cycle the disks often, which disk sleep settings or a keep-alive read can prevent.
- **SMART.** The reporter's macOS `smartctl` returned "SMART Status: Not Supported" for all four disks through the D4-320, so disk health monitoring through the enclosure may need a different SMART pass-through setting; untested.
- **Sleep fixes on offer.** TerraMaster's FAQ (forum topic t=3840) lists the D4-320 among models with slow access or disks failing to wake and advises disabling disk sleep in macOS; support also suggested a script that reads the volume at intervals to keep it active.
- **macOS 15.4+.** A forum report says disks in a D4-320 on an M1 MacBook Pro do not mount after a reboot, or are ejected when the lid closes. The lid case does not apply to a Mac mini; the mount-after-reboot case does.
- A short USB cable (or an active hub) is advised for small-form-factor Macs with weak USB signal.
- No Mac-specific reviews were found for the ICY BOX IB-3740-C31.

## Recommendation (given to the user)

1. TerraMaster D4-320: the best fit for 4 independent disks, large-disk support and price.
2. ICY BOX IB-3740-C31 at Multitronic (282,90 €): JBOD alternative with no sleep-cycling reports found, but the 10 TB per bay spec limits it.
3. TerraMaster D2-320 (125,99 € at Amazon.de, 199,90 € at Multitronic): two bays only.

Where to buy: Amazon.de is the cheapest and ships to Åland without VAT at checkout, with customs clearance on the Åland side (see `aland.md`); Multitronic costs more but needs no customs handling.

## Open questions

- Whether `smartctl` can read SMART data from disks in the D4-320 on macOS (the thread's reporter got "Not Supported"), since the backup design benefits from disk health checks.
- Buy-box price and exact VAT/customs cost of the Amazon.de D4-320 for an Åland address.
- Whether disks in the D4-320 mount reliably after a reboot on the Mac mini's current macOS and stay awake with disk sleep turned off (`pmset`); test with one disk before moving data, as the `backup` skill already requires for the Deltaco.
