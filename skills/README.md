# Skills

This directory is the source of truth for the skills linked into `~/.claude/skills`. Agent-facing workflows live in each skill's `SKILL.md`; this page records extra setup and access requirements.

| Skill | Extra tool | Local configuration or access |
| --- | --- | --- |
| `time-reporting` | `uv` | Optional read-only Outlook calendar feed URL in `~/.config/rn-agent/time-reporting-calendar-url`, mode `0600`; the refresh helper needs access to `outlook.office365.com`. Approved reports also refresh the Übersicht badge at `~/.config/ubersicht/badges/time-reporting.json`. Chrome history summaries read local Chrome History databases in read-only mode. |

The calendar URL and downloaded ICS file contain private calendar data. Keep the URL outside the repository and use the helper's private cache under `/private/tmp/rn-agent-time-reporting/`.
