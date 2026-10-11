---
name: email
description: Use whenever the user asks about their email — finding or reading a message, their mailbox folders, sending identities/aliases, which domain's mail goes where (rn.ax, rutinerad.com), calendar or contacts in Fastmail, or anything about "fastmail" explicitly. This is the accumulating knowledge base for how this user's home email is set up and how an agent reads it, so read it before assuming providers, routing, or access method from scratch.
---

# Email

How the user's home email is set up and how an agent reads it. This repo is public, so addresses, message content, and mailbox counts stay out of this file; look them up live with `fm-api`.

**Related systems**: `cloudflare` covers the Email Routing and Worker deploy side of `rutinerad.com`; `windmill` covers the flows that mail triggers; `home` has the topology map.

## Mail setup

Two domains with different roles:

- **`rn.ax`** is the real personal mail, hosted on Fastmail (the apex MX points at Fastmail). The Fastmail account has a wildcard sending identity for `*@rn.ax`, so any local-part at the domain is usable as a from-address. Outgoing personal mail uses `d@rn.ax` as the sender by default; any other `@rn.ax` address works equally well when the context calls for it.
- **`rutinerad.com`** is a side-project domain handled by Cloudflare Email Routing. One catch-all rule sends every message to the `windmill-mail-router` Worker, which turns the recipient's local-part into a Windmill flow call; see `windmill` for the addressing convention. No mailbox sits behind it.

Older addresses that end up in the same Fastmail mailbox. These are legacy: any account that can move to an `rn.ax` address is moved, so new signups and address changes use `rn.ax`.

- **A `me.com` address**, tied to the user's iCloud account (the Apple ID side). Mail sent to it is forwarded to Fastmail, and Fastmail also has it as a sending identity.
- **A Gmail address**, forwarded to Fastmail.
- **A default identity on a Fastmail-owned domain** (`sent.com`).

`list_identities` shows the current sending identities; the Gmail address is receive-only and does not appear there.

## Per-service addresses

Every service the user signs up for gets its own address at `rn.ax`, named after the service (for example `spotify@rn.ax`), and that address is the account email at the service. This gives two properties:

- **Leak attribution**: mail arriving at `<service>@rn.ax` from a sender unrelated to that service shows which service leaked or sold the address.
- **Targeted blocking**: a leaked address can be blocked on its own while every other address keeps working. Blocking is configured in Fastmail; the read-only token cannot change rules.

`search_email` with `query: "to:<service>@rn.ax"` lists everything received at one address (an address with no mail returns an empty result). New signups use the same pattern: the lowercase service name as the local part.

Fastmail uses **folders** (each message lives in one folder; `search_email` reports a `folder` object). Standard role folders exist (Inbox, Archive, Drafts, Sent, Spam, Trash, Snoozed, Templates). Archive is the long-term store. Custom folders include `Auto` and `Later`, plus a `[Mailbox]` tree with `Later`, `To Buy`, `To Read` and `To Watch`. `list_folders` returns the live tree with folder ids.

## Agent access

API credentials live in the "Fastmail" item in the "Agent" 1Password vault: `password` = the token. The token is scoped to Fastmail's **MCP service with read-only data access**.

The MCP endpoint is `https://api.fastmail.com/mcp` (streamable HTTP, JSON-RPC, `Authorization: Bearer <token>`). Fastmail's JMAP session endpoint answers 401 `JMAP request for session without JMAP enabled` to this token, so reading goes through MCP.

Use `fm-api <tool> [json-args]` (this skill's own directory) for a call: it performs the MCP handshake, calls one tool, and prints the tool's text result (JSON for the list/search/read tools). `fm-api --tools` lists the available tools. Like `wm-api` and `hb-api`, it goes through `~/tasks/op-service-account`, so it needs that machine's `op-service-account-agent` Keychain entry set up first.

Available tools (all read-only):

| Tool | Use |
|---|---|
| `search_email` | Gmail-style `query` (e.g. `from:…`), `limit`, `cursor`; omit `query` for the newest mail. Returns summaries with `id` and `threadId`; when `hasMore` is true, pass `nextCursor` back as `cursor` |
| `read_email` | Full message by `id`; quoted reply history is stripped unless `includeQuotedText` is true |
| `read_thread` | Every message in a thread by `threadId`, quoted history stripped |
| `read_attachment` | Attachment text by `emailId` + `blobId` (from `read_email`); long text pages via `offset`; `format: "original"` returns images/PDFs |
| `list_folders`, `list_identities` | Mailbox tree with ids and roles; sending identities |
| `search_contacts`, `search_org_contacts` | Personal address book; shared directory |
| `search_events`, `list_calendars` | Calendar events in an `after`/`before` range; calendar ids |
| `search_notes`, `read_note` | Fastmail notes |

A token without write scope has no `send_email`, `draft_email` or event-editing tools; sending or changing anything needs a new token with write access, created in Fastmail under Settings → Privacy & Security → Integrations.
