# agent-card-titles

Make the Claude Code **background-agent view** readable.

By default the card list is titled with a vague auto-generated name and sorted by *creation*
date, so a session you resumed five minutes ago stays buried under ones you have not touched
in weeks. This retitles every card as `<age> <model> · <what you actually asked>` and sorts by **last
interaction**, newest on top.

```
before                                   after
─────────────────────────────────        ─────────────────────────────────────────────
flaky test investigation                 2h   ♫ · why does the checkout test only fail…
dark mode implementation                 16h 📜 · add dark mode to the settings page
database migration helper                3d  ✒️ · migrate the users table to Postgres…
api error handling                       12d    · /orders returns 500 when the cart is e…
```

Each card carries the age since you last touched it, a glyph for the model that answered
last (`♫` Opus, `📜` Fable, `✒️` Sonnet — configurable), and **your most recent request** in
your own words.

The label tracks the latest thing you asked, not the opening message, so a long-running
session reads as whatever it is doing now. Short acknowledgements ("yes", "go on", "commit
this") are skipped, so a card never degrades to a one-word label; if the tail holds nothing
substantive, it falls back to what the session opened with.

In the agent view, with cards sorted newest-first inside each group:

```
Needs input
  ✳ 2m   ♫ · why does the checkout test only fail in CI?
  ✳ 6d   ♫ · add dark mode to the settings page
  ✳ 18d  ♫ · migrate the users table to Postgres, keep the ids
  ✳ 30d ✒️ · rename the analytics events to the new scheme
  ✳ 45d    · investigate the memory leak in the image worker
  ✳ 52d    · document the deploy rollback procedure

Working
  ✳ 1m  📜 · draft the release notes for 2.4

Completed
  • now 📜 · fix the flaky auth test
  • 2h   ♫ · /orders returns 500 when the cart is empty
  • 3h   ♫ · add a retry to the webhook consumer
  • 4d   ♫ · bump the CI runner image to 22.04
  • 120d    · why is the bundle 400kb bigger after the upgrade?
```

The age sits in a fixed 3-wide column, the glyph in a 2-cell one, and a missing glyph becomes
blank — so the `·` separators line up even though 📜 and ✒️ are double-width emoji while ♫ is
a single-width text symbol. Ages past 99d overflow the column by one, which is rare enough
not to widen every card for.

The oldest cards carry no glyph: their transcript has been pruned, so there is no model left
to read. A glyph is omitted rather than guessed.

Two problems it fixes at once:

- **Vague titles.** The auto-namer summarises; the summary often loses the thing that would
  let you recognise the session. Your own words are a better label than a paraphrase.
- **Useless ordering.** There is no built-in "sort by last activity" — the fallback is
  `createdAt`, which is creation order, not recency.

## Requirements

Node.js (any recent version) and Claude Code. Works on Windows, macOS and Linux.

## Install

Put `agent-card-titles.js` and `install.js` in a folder you will keep, then:

```bash
node install.js --recompute
```

`--recompute` retitles every card you already have, so the view is useful immediately instead
of filling in as sessions end. Then **restart Claude Code** (or open `/hooks` once) — the
settings watcher only reloads files that existed when the session started.

That registers three hooks in `~/.claude/settings.json`. Re-running is safe: it never
double-registers, and it backs the file up to `settings.json.bak` first.

| Flag | Effect |
|---|---|
| `--recompute` | Retitle all existing cards immediately |
| `--uninstall` | Remove the hooks (card titles stay as they are) |
| `--dry-run` | Print the resulting settings.json without writing |
| `--home <dir>` | Operate on another `.claude` dir (default `$CLAUDE_CONFIG_DIR` or `~/.claude`) |
| `--node <path>` | Executable to run the hook with (default: the node running the installer) |

## Tuning

Both knobs live at the top of `agent-card-titles.js`. Re-run `node install.js --recompute`
to apply a change to cards you already have.

**`TITLE_MAX`** — label budget after the chips (default `48`). Raise it for more context per
card, lower it for a denser list.

**`AGE_WIDTH`** — width of the age column (default `3`, which covers everything up to `99d`;
`100d`+ overflows by one character, which is rare enough not to be worth a wider column for
every card). The age is padded on the right, never the left: the CLI sanitises a title with
`trim()`, so leading spaces are stripped and right-aligned digits would collapse.

**`GLYPH_WIDTH`** — cells reserved for the model glyph (default `2`). Emoji occupy two
terminal cells and text symbols one, so without this the separator would shift between a
`📜` row and a `♫` row. Padding sits *in front* of the glyph, right-aligning a narrow symbol
against the right edge of a wide emoji. If your terminal renders these differently, this is
the number to adjust.

**`MODEL_ICONS`** — which glyph marks the model that answered last:

```js
const MODEL_ICONS = [
  [/fable/i,  '📜'],
  [/opus/i,   '♫'],
  [/sonnet/i, '✒️'],
];
```

Matching is a regex against the model id (`claude-opus-5`, `claude-fable-5`, …), first match
wins, so version bumps keep working. A model with no entry gets no chip — better a missing
glyph than a wrong one. Add a row for any model you want marked.

A note on glyph choice: the card title is a plain string and the CLI strips every control
character from it, so **ANSI colour codes cannot be used** — the only colour available is
whatever the glyph itself carries from your emoji font. Text-class symbols (`♫ ≡ ★ ◆`) render
in your foreground colour at single width; emoji (`📜 ✒️`) render in colour but are
double-width in some terminals and single in others, which can disturb column alignment.

## How it works

Three hooks, because no single event can do the whole job:

| Event | Does |
|---|---|
| `UserPromptSubmit` | Sets **this** session's title via `hookSpecificOutput.sessionTitle`, using the prompt you just typed — it is not on disk yet, so it comes from the payload |
| `Stop` | Sweeps the project's cards: re-ages chips, stamps sort keys, and refreshes the running session's own label and model glyph |
| `SessionEnd` | Same sweep on `/stop`, for the session that is ending |

The `Stop` sweep deliberately includes the running session's own card. That is what catches a
model switch made mid-conversation: at prompt-submit time the new model has not answered yet,
so the glyph would lag a turn otherwise. Only `detail` is left alone for that card — it is the
live status line and belongs to the running session.

The awkward parts, so you can judge the approach:

- **The view renders `name`, not `detail`.** `detail` doubles as the live status line and is
  overwritten constantly while a session works, so a title cannot survive there.
- **A live session will clobber a direct write.** Sessions are daemon-backed and stay alive in
  `blocked`/`done`; the owner periodically rewrites its whole `state.json` from memory and
  silently drops injected fields. Writing `name` *together with* `nameSource: "user"` survives,
  because a watcher reads it back into the live session.
- **`sessionTitle` is the supported path, but only on `UserPromptSubmit`.** It is not honoured
  on `Stop` or `SessionEnd`, which is why the sweep exists as well.
- **The age chip is relative, so it must be recomputed.** A title set only at prompt-submit
  time would read `now` forever. The Stop/SessionEnd sweep re-ages every other card.

Sorting uses `sortOrder` / `stateSortOrder` — optional numeric fields on each card, where the
**largest** value renders at the top. The script stamps `Date.parse(lastInteraction)`.

## Safety

- Additive only: it writes `name`, `nameSource`, `detail`, `sortOrder`, `stateSortOrder` and
  nothing else. It never deletes, moves or renames a job, and never touches transcripts.
- Only this session's own card is touched while it runs; another running session's card is
  left alone, and its `detail` status line is never overwritten.
- Every error is swallowed — a failing hook must never break your session.
- Reversible: `--uninstall` removes the hooks, and clearing those five fields restores the
  CLI's own naming.
- It does **not** modify `updatedAt`, so it cannot distort the recency it sorts by (verified:
  timestamps are byte-identical before and after a sweep).

## Caveats

- The `UserPromptSubmit` hook runs on every prompt and costs one Node startup (~50–100 ms).
- It reads `~/.claude/jobs/*/state.json`, which is an internal file the CLI does not promise
  to keep stable. Verified against CLI 2.1.229. If a future version changes the shape, the
  script degrades to doing nothing rather than corrupting anything.
- Titles come from your prompts, so they are as descriptive as your first message was.

## License

MIT.
