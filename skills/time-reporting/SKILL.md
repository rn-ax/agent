---
name: time-reporting
description: Use whenever the user asks to review Home Assistant computer activity logs, reconcile a workday with calendar evidence, estimate or record working hours by day, or manage non-working, sick, vacation, and flex days. Keep the review one local calendar day at a time and maintain the time report JSONL ledger in rn-agent.
---

# Time reporting

Use this skill to collaboratively reconstruct and maintain the user's day-by-day work time ledger from Home Assistant computer activity exports and the user's recollection. Activity is an imperfect clue, not proof of work or non-work: the user may be working away from the computer, including in phone meetings, or may be using the computer outside work. Present one day at a time and resolve uncertainties with the user before marking the date reviewed. Do not move to another date until the current date is resolved.

## Inputs and timezone

- The usual export is `~/Downloads/activity.csv`; use the path the user supplies when different.
- The relevant entity is `binary_sensor.slind_active` unless the user identifies another entity. Ignore other entities and non-state-change rows unless they help interpret the export.
- The optional work calendar feed URL is stored outside the repository in `~/.config/rn-agent/time-reporting-calendar-url` with mode `0600`. Never print or copy the URL into the repository. When calendar evidence is useful, run `uv run --script skills/time-reporting/refresh-calendar [--date YYYY-MM-DD]`; it fetches the feed, overwrites the private stable cache at `/private/tmp/rn-agent-time-reporting/calendar.ics`, and parses the requested day's events. The helper uses `icalendar` and `recurring-ical-events` to parse iCalendar and expand recurring events.
- The user has instructed that meetings in the selected work calendar are assumed accepted and attended unless the feed marks them canceled or the user corrects the assumption. Some ICS feeds omit RSVP fields; do not treat their absence as a declined response.
- The user does not work Saturdays or Sundays. Include weekend dates as `type: "non-working day"` with null start and end times. If the user later says they worked on a weekend, reconstruct that date normally.
- The reporting timezone is `Europe/Helsinki`, regardless of the computer's configured timezone. Parse explicit UTC offsets and `Z` as given, then convert each timestamp to `Europe/Helsinki`; do not relabel UTC values as local time. Use the local date after conversion to group activity. This also handles daylight saving transitions.
- Check the export's actual earliest and latest timestamps and entity coverage before claiming it covers a requested date range. If dates are missing, say so and ask for a more complete export when needed; never invent activity.
- When the user asks to inspect Chrome history for a specific interval, use `uv run --script skills/time-reporting/chrome-history --start '<ISO timestamp with offset>' --end '<ISO timestamp with offset>'`. The helper reads local macOS Chrome profiles in read-only mode, defaults to the Helsinki timezone, and searches only the inclusive requested window. It emits JSON grouped by profile and page, with visit timestamps and counts. URL query strings and fragments are omitted by default; use `--include-query` only when the user specifically needs them. Browser history confirms recorded visits, not that a tab stayed open or that a page was actively used for the whole interval. Do not write Chrome history analysis to the time-report JSONL.
- Before reviewing a date, group the relevant entity's entries by Helsinki local date and check the log's oldest and newest dates. The oldest date in the log is never eligible because prior state context is missing. A past date must be strictly between the oldest and newest dates. The newest date is eligible only when it is the current Helsinki date; treat that date as in progress and use the current time for an open end. Reject a past date that is the newest date in the log, and reject today if it is the oldest date.

## Review workflow

1. Read the ledger at `data/time-reports.jsonl` if it exists. It has one JSON object per local calendar date. When correcting a date, replace that date's line; do not append a duplicate.
2. Determine the requested date. For a date range, start from the most recent date requested and move backward, one date per user confirmation. Skip dates already resolved only if the user asks to continue past them.
3. Parse the CSV with a CSV parser. Sort state changes chronologically after converting timestamps to Helsinki local time. Pair `on` with the next `off` as observed computer-active intervals. Identify gaps and incomplete edges, but do not automatically treat them as breaks or work. If the export begins while the entity is already `on`, the start is unknown. If the current date has no recorded end, use the current time in `Europe/Helsinki` as the provisional end and refresh it to the current time on each later turn until the user approves the report. For a past date, an open interval has an unknown end; do not invent one.
4. Present the date, source coverage, computer-active intervals and gaps in Helsinki local time, and any open or truncated interval. Split gaps around attended calendar meetings and other work away from the computer. Ask about uncertain gaps, computer use outside work, and actual start and finish; the user's corrections override sensor evidence. Apply the break rules below and resolve the timeline with the user.
5. For a work day, calculate the single Kellokortti entry using the calculation below. Show the evidence timeline first, then the entry on its own line with the expected credited hours for confirmation. For a non-working, sick, vacation, or flex day, confirm the classification explicitly; never infer it from an empty activity log.
6. Only after the user approves the period or classification, add or replace that date with `uv run --script skills/time-reporting/update-report --date YYYY-MM-DD --type TYPE [--start HH:MM --end HH:MM]`. Never save a draft. The helper validates and atomically updates the ledger, then refreshes and verifies the Übersicht badge. If badge refresh fails after the ledger write, report that the date was saved but the badge update failed; rerun the same command to repair the badge.
7. Show the saved record, then automatically present the next earlier date for review. Stop at the requested earliest date or when the export has no further eligible date under the coverage rules; explain any coverage gap.

## Break merging

After accounting for calendar meetings and user-confirmed work away from the computer, merge adjacent candidate breaks when the intervening computer-active interval is at most 10 minutes, inclusive. Repeat across consecutive qualifying intervals so a chain becomes one candidate break. The merged break spans from the first break's start to the last break's end, including the intervening computer activity. Never merge across an attended meeting or other user-confirmed work, even if it lasts 10 minutes or less; the user's corrections override sensor-based merging.

Apply the 30-minute threshold only after merging, using exact timestamps rather than rounded display times. For example, inactivity from 12:00–12:20 and 12:30–12:45 merges into a 45-minute candidate break, including the 10-minute computer-active interval. An intervening activity interval longer than 10 minutes keeps breaks separate. Ignore merged or standalone breaks shorter than 30 minutes. Show the merged spans and included computer activity in the timeline and confirm that they were non-working before deducting their full duration.

## Kellokortti calculation

Report one continuous period. Under the user's observed Kellokortti configuration, the entered span automatically loses 30 minutes for lunch (08:00–16:00 credits 7.5 hours). Compensate for that deduction once per work day, after subtracting actual qualifying breaks, including lunch:

```text
net work = actual finish − actual start − confirmed deductible breaks
entry start = actual start
entry end = actual finish − confirmed deductible breaks + 30 minutes
```

Round the entry start and entry end to the nearest half hour only after this calculation. Expected credited hours equal the rounded entry span minus Kellokortti's 30-minute deduction. The entry end is a reporting adjustment, not the actual finish. Do not subtract gaps the user confirms were work or include computer use the user confirms was outside work.

For an actual 08:00–16:00 day:

| Confirmed deductible breaks | Kellokortti entry | Credited hours |
| --- | --- | --- |
| None | 08:00–16:30 | 8 |
| 30-minute lunch | 08:00–16:00 | 7.5 |
| 60 minutes in total | 08:00–15:30 | 7 |

These examples assume the automatic deduction applies. If Kellokortti shows a different deduction for a particular entry, reconcile it before approval rather than applying the compensation twice.

## Ledger format

Store records in `data/time-reports.jsonl`, one compact JSON object per confirmed date, with only these fields:

```json
{"date":"2026-11-06","start_time":"08:00","end_time":"16:00","type":"work"}
```

`date` is the Helsinki local date. `start_time` and `end_time` are the approved Kellokortti entry's local clock times in `HH:mm` format; use `null` for non-working, sick, vacation, or flex days. `type` is `work`, `non-working day`, `sick`, `vacation`, or `flex`. Keep analysis and supporting evidence in the conversation. Approval means the report is persisted; do not add a reported status, notes, or other fields to the JSONL record.
