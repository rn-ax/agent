---
name: paperless
description: Use whenever the user asks for help with their Paperless-ngx instance — upgrades (the v2 to v3 migration and the move to TrueNAS), documents that won't import or fail OCR ("PDF content stream is corrupt", Ghostscript PDF/A errors), the consume folder, the classifier, or anything about "paperless" explicitly. This is the accumulating knowledge base for how this user's Paperless is actually set up and behaves, so read it before assuming its architecture, upgrade state, or failure modes from scratch.
---

# Paperless-ngx

This is the accumulating knowledge base for the user's Paperless-ngx instance. Fill in each section as it's actually confirmed; don't guess or leave stale placeholder content. Dates are when something was confirmed; versions move on, so re-check anything old before relying on it.

**Related systems**: see the `truenas` skill — Paperless has moved to TrueNAS (see "TrueNAS deployment" below); the "Instance" section describes the previous Mac mini setup, which is kept stopped as a fallback. See the `home` skill for the topology map.

## Mentioning documents to the user

**Whenever a reply to the user mentions a Paperless document by id, write it as a link:** `[#10440](https://paper.rn.ax/documents/10440/details)`, not a bare `#10440`. Use the public host `paper.rn.ax` (the link is for the user's browser, not for API calls, which use the LAN address, see "API access"), and do it everywhere in a reply: lists, tables, summaries. It applies to messages to the user only; commit messages, PR text and these docs keep plain ids.

## Instance

**Superseded 2026-10-13: Paperless now runs on TrueNAS (see "TrueNAS deployment").** What follows describes the Mac mini instance, now stopped but intact.

Runs as the Docker container `paperless` on the Mac mini with hostname `server`, on port 14001 (`http://localhost:14001`). Everything operational lives in `~/Server/paperless`, which is not a git repository.

- `Makefile`: `make start | stop | restart | update`, plus `make snapshot` and `make snapshot-diff` (see "Snapshots"). `IMAGE` is **pinned to an explicit version tag** (it was `:latest` until 2026-10-12, which would have jumped straight to the newest release on the next `make update`); an upgrade step is "edit `IMAGE`, `make restart`".
- `data/`: SQLite database (`db.sqlite3`), classifier model (`classification_model.pickle`), search index, logs. Mounted into the container, **and not under `~/Paper`**, so a backup of `~/Paper` alone does not include the database.
- `~/Paper/media`, `~/Paper/consume`, `~/Paper/export`: documents, the consume folder, exporter output. Mounted into the container.
- `.env`: `PAPERLESS_FILENAME_FORMAT`, `PAPERLESS_OCR_LANGUAGES` (`swe fin eng`), `PAPERLESS_REDIS`, `PAPERLESS_SECRET_KEY`, `PAPERLESS_TIME_ZONE`, `PAPERLESS_URL`. Nothing else is set, so everything not listed is a Paperless default.
- **Database is SQLite**. Redis is a Homebrew service on the host (launchd `homebrew.mxcl.redis`), reached from the container at `redis://host.docker.internal:6379`; there is no Redis container.
- Credentials: none are recorded here.

## Upgrade state and procedure

Confirmed 2026-10-12: upgraded 2.20.10 to 2.20.15 to 3.0.5 to 3.1.3 to 3.3.0 (current), one step at a time, with a snapshot diff after each. The last three steps took about 2 minutes each to become healthy and the 3.1.3 and 3.3.0 steps changed nothing in the snapshot except versions, package versions, migration counts and index size. **Skipped v3.0.1** (its database migration is broken; fixed in 3.0.2) and **v3.2.0/3.2.1** (a bug that only bites with OCR `optimize` set to 2 or more; fixed in 3.3.0, and this instance doesn't set it, so skipping is caution rather than necessity). v3 can only be installed from exactly 2.20.15.

Per step, in order: stop the container, copy the database with `sqlite3 data/db.sqlite3 ".backup '<dest>'"` (copies WAL-mode databases correctly) plus the classifier model, check the copy with `pragma integrity_check`, pin `IMAGE`, `make restart`, wait for `healthy` (a v3 start with migrations took about 2 minutes), then check `docker logs` for errors, confirm the container ID is stable with 0 restarts, and take a snapshot and diff it against the previous one.

Things the migration guide (docs.paperless-ngx.com/migration-v3 — the site returns 403 to fetch tools; the same file is `docs/migration-v3.md` in the GitHub repo) doesn't spell out, all seen on this instance:
- Migration `documents.0016_sha256_checksums` recomputes every document's checksum from MD5 to SHA-256 by reading all files (about a minute for 9,300 documents). A stored checksum that didn't match its file under v2 is silently replaced with the file's current hash, so a v2 "checksum mismatch" sanity error disappears without the file being fixed. Take note of any mismatch before upgrading.
- The classifier model is deleted on the first v3 start (`ClassifierModelCorruptError ... deleting model file`). It retrains on the hourly schedule, or immediately with `docker exec paperless python3 manage.py document_create_classifier` (about 95 seconds).
- Task history is dropped (migration 0019), so all failed/stuck task counters reset to zero.
- The search index is rebuilt automatically on first start (smaller afterwards: 151 MB to 89 MB).
- SQLite switches to WAL journal mode, adding `db.sqlite3-wal` and `-shm` next to the database. Copy with `sqlite3 .backup`, not `cp`, unless the container is stopped.
- The sanity checker's output changed from log lines to a boxed table in v3; `snapshot.py` parses both.
- `PAPERLESS_ARCHIVE_FILE_GENERATION` was deliberately left at the v3 default (`auto`): archive PDFs are skipped for born-digital PDFs that already contain text. v2 always created one. This was a deliberate choice, not an oversight. `PAPERLESS_CONSUMER_DELETE_DUPLICATES` was likewise left at the v3 default (duplicates are consumed with a warning and show in the document's Duplicates tab).

## API access

Credentials live in the "Paperless" item in the "Agent" 1Password vault: `password` is the API token, the first URL is the LAN address of the TrueNAS app (`http://truenas.lan:30070/`) and the second is the public `https://paper.rn.ax/`. The public hostname is behind Cloudflare Access, so token calls use the LAN URL.

`pl-api` makes one authenticated request. `pl-tags` adds and removes tags on documents. The other scripts here share `paperless_lib.py`.

The API is preferred to `docker exec ... manage.py shell` over SSH. It needs no SSH session (the 1Password SSH agent approval lapses between agent calls), and bulk edits go through Paperless's own code, so the search index and audit history stay consistent.

## OCR quality scan

## OCR tags

The state of every document's OCR is a tag under the parent tag `agent-ocr`. Paperless is the only place this is recorded, so it is visible in the UI and the same from every machine.

| Tag | Meaning |
|---|---|
| `ocr-bad` | The scan found bad OCR; it waits to be fixed. This is the queue. |
| `ocr-fixed` | The agent rewrote the text from the page images; it waits for the user's review. |
| `ocr-ok` | The OCR is confirmed fine, by the user or because there is nothing to fix (a picture). Scans skip it. |
| `ocr-skipped` | The agent looked and could not or should not fix it, such as a drawing whose PDF is corrupt. It stays unresolved. |

A document moves one step at a time: `ocr-bad` to `ocr-fixed` when the agent has rewritten it, `ocr-fixed` to `ocr-ok` when the user has reviewed it, `ocr-bad` to `ocr-skipped` when the agent cannot fix it. A document the user fixes by hand goes straight to `ocr-ok`. Each change is one `pl-tags` call.

## OCR quality scan

`ocr-scan` scores the stored text of every document and lists the ones that fail, without changing anything. Its docstring has the heuristics and the rules that skip a document before scoring: inbox documents, documents already tagged under `agent-ocr`, and the "Pyssel / Teckning" type. A document without a tag is scored on every run, even when it passes.

The library mixes Swedish, Finnish and English, which is why the scan compares words with the library itself and not with a dictionary. The thresholds come from reading sample text, not from checking page images, so expect false positives, mostly noisy thermal receipts. Documents flagged `broken_encoding` have an embedded text layer with a wrong character table, so the stored text is shifted while the page looks fine (`VDU LQIRUPDWLRQHQ` is "information" with every character 29 off). Paperless keeps an existing text layer by default, so these need OCR from the image, with `ocrmypdf --force-ocr` or `PAPERLESS_OCR_MODE=force`.

Handing flagged documents over takes two steps:
1. `ocr-scan`, then read `flagged_ids` from its context.
2. `pl-tags --add ocr-bad` on those ids.

Re-OCR through Paperless itself is the **Reprocess** action in the UI, which creates `reprocess_document` tasks.

## Fixing OCR by reading the pages yourself

This is for documents with bad OCR and too much text for the user to retype by hand. The queue is the documents tagged `ocr-bad`. The method: render the pages, read them as images (the Read tool shows PNGs), transcribe, and write the text into the document's `content` field.

`ocr-pages` provides the mechanical steps, and the agent composes them:
1. `ocr-pages next` lists the documents still tagged `ocr-bad`, fewest pages first.
2. `ocr-pages prep` on a batch of ids backs up the current text and renders an overview of each page. Read the overviews first for the layout.
3. `ocr-pages strips`, `crop` and `rotate` zoom in on small or blurry text and turn sideways scans upright.
4. Write the transcription to a text file and run `ocr-pages put`, which replaces `content` and verifies it. It writes only the text.
5. `pl-tags --add ocr-fixed --remove ocr-bad` on the finished ids.
6. A document that cannot be fixed gets `pl-tags --add ocr-skipped --remove ocr-bad`, and the reason goes in the report to the user.

How to transcribe:
- Reading order, top to bottom, with a field label and its value on separate lines.
- Keep every language that is printed; the documents are often bilingual Swedish and Finnish.
- Keep diacritics, numbers, identifiers and dates exactly.
- Leave out background watermarks, barcodes and stray page-marker numbers, because they are not content.
- Re-crop at a higher dpi for any name, number or amount that is hard to read, and never guess one.
- Mark handwriting `[handskrivet]` and anything unreadable `[oläsligt]`. Where table rows do not line up, transcribe column by column and say so in the text.
- Standard boilerplate with a few smudged words can be resolved from context, and the user is told which words were inferred and which labels were normalised.
- Sums on the page are a check on the reading: a currency conversion, or marks adding up to a printed total.
- A receipt or slip is transcribed by its fields: the shop and address, date and time, the items with prices, totals and VAT, payment details, document numbers and any handwriting. The standard footer (return policy, opening hours, terminal slogans) and barcodes are left out, since nobody searches for them and they are most of a receipt's text.

What kinds of documents come up:
- Pictures with no text, such as a collage or a photograph, have nothing to fix and get `ocr-ok`. They are flagged `no_text` because they are typed as ordinary documents; typing them "Pyssel / Teckning" makes the scan skip them.
- Picture-only manuals have almost no text: part labels, step numbers, dimensions, reference numbers and a multilingual title block. Transcribe exactly that, start with a one-line marker such as `[Bruksanvisning med bilder, nästan ingen text]`, and do not describe the pictures.
- CAD drawings with hundreds of dimension labels, and PDFs that fail with poppler errors like `Unknown operator 'e+09'` (the corrupt-stream class above), are repaired mechanically with `analyze-pdf` and reprocessed, so they get `ocr-skipped` here.
- Reading is done by the main agent. Cheaper models misread amounts and identifiers plausibly, invent tables for handwritten sheets, and write hedges such as `(eller liknande)` into the text. A wrong, plausible number is worse than bad OCR.
- Plan for roughly 3,000 to 6,000 tokens per document, less for a single receipt. Reading several documents' images in one call and writing the files in the next keeps the number of calls low.

Only `content` changes, which is what Paperless searches. The archive PDF and its text layer are untouched, so searching inside the PDF viewer still sees the old text, and **running Reprocess afterwards overwrites the fixed text**. The old text stays in the backup (`$CLAUDE_JOB_DIR/tmp/paperless-ocr/ID/backup.json`) and in Paperless's own audit history for the document.

## Snapshots

`~/Server/paperless/snapshot.py` records the instance's state as JSON under `snapshots/`: versions, document counts and breakdowns, digests of titles/links/tags, config tables, migrations, task counts, file counts on disk plus any database rows whose files are missing, the sanity checker's results, and env var names (values only for a small non-secret allowlist). `make snapshot-diff OLD=... NEW=...` shows what changed. It is specific to this host and lives there, not in this skill. Expected differences across an upgrade: version and image fields, package versions, migration counts, and (across 2.20 to 3.0) the file-checksum digest, task tables and search index size.

## Consuming documents

- Only formats Paperless supports are consumed. `.zip`, `.pages` and `.md` files are logged as `Unknown file extension` and left in the consume folder indefinitely; move them elsewhere.
- A file that fails stays in the consume folder and is retried every time the container starts (seen on the 3.1.3 restart: two failing PDFs added two failed tasks).
- **The consume watcher can miss a file replaced in place.** Copying a repaired PDF over a same-named failed file produced no import; removing the file and creating it again did. When several files are recreated within a second of each other, one can be missed too, so recreate them one at a time and confirm each in `docker logs`.
- The classifier's suggestions (document type, correspondent, tags) are applied at consume time only, so documents consumed while the model was missing get none until the model exists and they're edited (the UI suggests values on a document's detail page; the bulk editor can set them for a selection). Documents consumed with a trained model got a type and correspondent automatically.
- Duplicates (same checksum) are consumed by default in v3 with a logged warning and appear in the Duplicates tab of the existing document. v2 rejected them and left the file behind.

## PDFs that Paperless rejects

**Workflow: analyze, then ask.** Run `analyze-pdf` (in this skill's directory; a uv script that installs pikepdf on first run, runs on the host, and is read-only) on the failing file. It prints JSON: a `summary` (pages, producer, encryption, text layer), a list of `findings` ordered by severity (each with `evidence`, the `ocrmypdf_impact` where known, and `possible_remedies`), and a `verdict` count. **Present the findings to the user in plain language and agree on what to do before changing any file** — the script deliberately never modifies or repairs anything, and every remedy changes what Paperless will store.
- `analyze-pdf FILE.pdf` checks the content streams (wrong operand counts for fixed-arity operators, tokens that aren't operators, unparseable streams), the structure (pikepdf/qpdf syntax check and open-time warnings, header offset, encryption, fillable forms, signature fields), and the text layer.
- `analyze-pdf FILE.pdf --probe-container paperless [--ocr-languages swe+fin+eng]` additionally copies the file into the container's `/tmp`, runs the container's own `ocrmypdf --skip-text --output-type pdfa` on it, reports exit code and output tail, and deletes the copy. This is the authoritative "would it be accepted" test and uses container CPU while it runs. Use it before proposing a fix and again on the fixed copy.
- Exit code is 0 whenever the analysis ran (findings don't change it), 2 if the file can't be opened.

**`InputFileError: PDF content stream is corrupt - this PDF is malformed`.** Confirmed cause for the two files that still failed on 3.0.5 (2026-10-12): the page content streams contain numbers written in exponent notation, e.g. `1 0 0 1 -1.0630028e+0 -1.13292e+09 cm`. PDF doesn't allow exponent notation (and some tokens look truncated, `e+0` where `e+09` was meant), so the tokenizer reads `-1.0630028e+0` as an unknown operator, which swallows the operands before it and leaves the following `cm` with too few; ocrmypdf then raises `ValueError: ObjectList must have 6 elements` from `ocrmypdf/pdfinfo/_contentstream.py` and Paperless wraps it as the message above. `analyze-pdf` reports this as `content_stream.exponent_notation_numbers` plus `content_stream.wrong_operand_count.cm`. Producers seen: macOS Quartz PDFContext and Haru Free PDF Library. Viewers such as poppler skip the whole broken instruction, and `pdfinfo` and `qpdf --check` don't look at content-stream semantics, so the file looks fine everywhere except in ocrmypdf. To see which error you have without the script, search `docker logs paperless` (or `data/log/paperless.log*`) for the filename and look for the `ValueError` line in the traceback.

**How the two files were fixed (with the user's go-ahead), as a recipe rather than a tool**: rewrite each page/form content stream without the broken instructions using pikepdf (`parse_content_stream`, drop instructions with the wrong operand count or an unknown operator, `unparse_content_stream`, assign the new stream back to the page's `Contents` or the form's stream), save as a new file, compare renders before and after (`pdftoppm -r 80 -png`, byte-compare the PNGs — they were pixel-identical, as expected since viewers already skip those instructions), and run the container probe on the result. Then recreate the file in the consume folder under the original filename (see the watcher caveat above). **Paperless stores the repaired file as the document's original**, not the user's original bytes, so keep the untouched original elsewhere (it went to `~/Server/paperless/backups/failed-pdfs-original/`). Both files then imported, and the classifier assigned a type and correspondent.

**`Ghostscript PDF/A rendering failed`** and **corrupt-stream errors that aren't the case above**: on 2.20.10 (ocrmypdf 16.12, pikepdf 10.0) 6 PDFs failed Ghostscript PDF/A rendering and 18 PDFs failed with the corrupt-stream error. After upgrading to 3.0.5 (ocrmypdf 17.4, pikepdf 10.2) all 6 Ghostscript failures and 16 of the 18 corrupt-stream failures imported without any change to the files; the 2 that remained were the exponent-notation case above. The ocrmypdf upgrade is the likely reason but was not isolated. One file's Ghostscript failure followed ocrmypdf's "This PDF has a fillable form" warning, which `analyze-pdf` reports as `structure.fillable_form`.

## Known baseline issues (2026-10-12)

Reported by the sanity checker and unrelated to upgrades: 49 documents with no OCR text, 2 orphaned files under `media/documents/{originals,archive}/Prov - tentamen/2023/`, and (until the SHA-256 migration) a checksum mismatch on document #1019 (stored MD5 `7e4e0bdee5bbc54474030c43b53fb638`; the file on disk hashed differently, cause unknown). The pre-v3 database copy kept in `~/Server/paperless/backups/pre-v3/` still has the original value.

## TrueNAS deployment

Confirmed 2026-10-13: Paperless-ngx 3.3.0 runs on TrueNAS as the **catalog app** `paperless-ngx` (community train, chart 1.6.60), app name `paperless`, web port 30070 (`http://truenas.lan:30070`). The Mac mini container is **stopped, not removed**, and its data (`~/Server/paperless/data`, `~/Paper/media`) is kept intact as a fallback until the user chooses to delete it; the Docker restart policy `unless-stopped` keeps it stopped across restarts. `paper.rn.ax` is a Cloudflare tunnel hostname that the user repointed from the Mac to the TrueNAS app (origin `http://192.168.1.142:30070`); `PAPERLESS_URL` is already `https://paper.rn.ax`. See the `truenas` skill for the app-install playbook and the `cloudflare` skill for tunnels.

- **Different from the Mac setup**: the catalog app bundles its own **PostgreSQL 18** container (`postgres`, internal network only, not a shared database) and its own Valkey on a temporary volume, so there is no SQLite and no use of the separate `redis` catalog app. The `SECRET_KEY` was carried over unchanged. `PAPERLESS_URL`, `PAPERLESS_FILENAME_FORMAT` and `PAPERLESS_OCR_LANGUAGES` (`swe fin eng`) are set through the app's `additional_envs`. Tika/Gotenberg and the trash directory are off, matching the Mac (the catalog defaults both to on). The Swedish and Finnish tesseract packs are installed by the container on every start, which delays the first healthy status by several minutes on this box.
- **Datasets** (user's Configuration/Logs convention): `Storage/Configuration/paperless/{media,consume,postgres}` (backed up; `postgres` is `999:999` with an ACL for `apps`) and `Storage/Logs/paperless/{data,export}` (regenerable: index, classifier model, logs; `export` is only the import source and can be emptied).
- **Run as UID/GID 1000, not the catalog's default 568.** The image's `paperless` user is 1000:1000. With `run_as` 568 the entrypoint's `usermod --uid 568` re-chowns the whole image source tree, each file forcing an overlayfs copy-up that waits for a ZFS transaction-group sync: it ran over 15 minutes at near-zero CPU (`/proc/<pid>/stack` shows `txg_wait_synced` under `ovl_copy_up`) and repeats whenever the container is recreated. Fix: `app.update paperless '{"values":{"run_as":{"user":1000,"group":1000}}}'` then `app.redeploy paperless`; the permissions container then chowns the mounts to 1000 and `apps` is given an ACL on `media` and `consume` so backups can read them.
- **Moving data = exporter then importer, not a file copy.** `document_exporter` on the Mac, copy the export to the `export` dataset (mounted in the container as `/usr/src/paperless/export` through `additional_storage`), then `docker exec -u paperless ... manage.py document_importer /usr/src/paperless/export` (about 5 minutes for 9,339 documents, plus the file copy). Run it detached (`docker exec -d`) with output to a log in the data dir.
- **Export traps seen on this library**:
  - The Mac volume `~/Paper` is **case-insensitive**, so documents whose exported names differ only in case (`KappAhl-archive.pdf` / `Kappahl-archive.pdf`, 14 documents) overwrite each other, and the importer then stops with "manifest file refers to ... which does not appear to be in the source directory". Export on a case-sensitive filesystem instead (inside the container, e.g. `/tmp/export`) and stream it out with `docker exec paperless tar -C /tmp/export -cf - . | ssh truenas 'sudo tar -xf - -C <export dataset>'`.
  - **Even on a case-sensitive filesystem the exporter silently overwrites files**: 59 pairs of documents (for example `Tre.pdf` and `Tre.jpg`) get the same exported archive PDF and thumbnail name, and the importer does not notice. `--use-filename-format` makes it worse (152 repeated names). Fix before importing: for each repeated `__exported_archive_name__` / `__exported_thumbnail_name__` in `manifest.json`, copy each document's real file (`Document.archive_path` / `thumbnail_path` from `manage.py shell`) to a unique name such as `<stem>__id<pk>.<ext>`, verify archive copies against `archive_checksum` (SHA-256), and patch the manifest. Check the result: no repeated names in the manifest, none missing on disk, and file count = references minus removed duplicates.
- **Importer needs an empty user table.** The app creates an `admin` and an `AnonymousUser` on first start, which collide with the exported users (`auth_user_username_key`). The load is transactional, so a failed import leaves nothing behind; delete the two with `User.objects.all().delete()` (the database is empty at that point) and rerun. The importer brings in the real `admin` with the old password hash, but not the system users `consumer` and `AnonymousUser` (3 users on the Mac, 1 on TrueNAS).
- **Verification used** (2026-10-13, all matched): document, correspondent, tag, type and saved-view counts; a row-by-row comparison of `id, title, checksum, archive_checksum, correspondent_id, document_type_id, storage_path_id, filename, archive_filename` between SQLite and PostgreSQL (do not `sort` on two machines with different locales; both queries `order by id`); tag, type, correspondent and saved-view names; media file count; and `document_sanity_checker` (0 errors, 0 warnings, the same 49 "no OCR data" notes as the Mac, about 5 minutes). One title differed: #10520 had a stray backspace control character on the Mac that the export dropped.
- **Counting export files**: a document exports as an original, a thumbnail and (unless v3 skipped it for a born-digital PDF) an archive PDF, plus `manifest.json` and `metadata.json`. 9,339 documents gave 27,982 referenced files, so 35 have no archive PDF.
- If login returns 403 behind the tunnel, set `PAPERLESS_TRUSTED_PROXIES` / `PAPERLESS_ALLAUTH_TRUSTED_PROXY_COUNT` via `additional_envs`, then `app.redeploy`.
- API v1 and API versions below 9 were removed in v3; nothing under `~/Server` called the API when checked, but clients outside it (phone apps, browser extensions) weren't.
- Not yet known: whether the TrueNAS backup tasks (see the `backup` skill) cover `Storage/Configuration/paperless`, and how the Mac-side `snapshot.py` should be adapted to read PostgreSQL (it opens `db.sqlite3` and a container named `paperless`).
