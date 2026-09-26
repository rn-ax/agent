---
name: agent-card-titles
description: Use when the user wants their Claude Code background-agent (FleetView) card list to be readable - retitling cards as "<age> <model> · <what they asked>" and sorting by last interaction instead of creation date. Triggers on "my agent list is unreadable", "sort agents by recent", "rename agent cards", "install/uninstall/tune agent-card-titles".
---

# agent-card-titles

Source: https://gist.github.com/builder-main/6304a866420369935e2f4443ac586f21

Installs and manages a hook that retitles Claude Code background-agent cards as
`<age> <model> · <what the user actually asked>` and sorts them newest-interaction-first.

**This skill installs automation; it is not the automation.** The retitling happens on hook
events the harness fires (`UserPromptSubmit`, `Stop`, `SessionEnd`) — Claude is not in the
loop at that moment. So the work here is always: edit `settings.json`, run the installer,
verify. Never try to "do" the retitling conversationally.

## Where things live

- Hook script and installer: this skill's directory (`scripts/` if bundled, else alongside).
- Registration: `~/.claude/settings.json` (or `$CLAUDE_CONFIG_DIR/settings.json`).
- Card data: `~/.claude/jobs/<id>/state.json`.

## Install

```bash
node install.js --recompute
```

Then tell the user to **restart Claude Code or open `/hooks` once** — the settings watcher
only reloads files that existed at session start, so a fresh registration will not fire until
then. Do not report the install as working before that happens.

## Common requests

| Request | Do |
|---|---|
| "install it" | `node install.js --recompute` |
| "remove it" | `node install.js --uninstall` |
| "titles too long/short" | Edit `TITLE_MAX` in `agent-card-titles.js`, then `node install.js --recompute` |
| "refresh all cards now" | `node install.js --recompute` |
| "show me what it'd change" | `node install.js --dry-run` |
| "it isn't working" | See Troubleshooting |

## Troubleshooting

Check in this order:

1. **Hooks registered?** Read `~/.claude/settings.json` and confirm three entries whose
   `args` contain `agent-card-titles.js`. If absent, the installer never ran.
2. **Session restarted?** Newly added hooks do not fire in an already-running session.
3. **Script healthy?** `node --check agent-card-titles.js`, then feed it a payload directly:
   ```bash
   echo '{"hook_event_name":"UserPromptSubmit","session_id":"<id>","cwd":"<project>"}' | node agent-card-titles.js
   ```
   It must print exactly one JSON object with `hookSpecificOutput.sessionTitle`. Any other
   stdout text would be injected into the user's prompt as context.
4. **Card not updating?** Cards in state `working` are skipped on purpose — the script does
   not fight a running session for its own card.

## Things that look like bugs but are not

- **A card reads `now` and will not age.** Expected between sweeps: `UserPromptSubmit` can
  only ever write `now`. The `Stop`/`SessionEnd` sweep re-ages it.
- **A direct edit to `state.json` disappears.** Live daemon-backed sessions rewrite the whole
  file from memory. Only `name` written together with `nameSource: "user"` survives, because a
  watcher reads it back. Do not "fix" this by writing harder — use the installer's path.
- **`sessionTitle` ignored on Stop/SessionEnd.** The CLI honours it only on
  `UserPromptSubmit`. That is why both mechanisms exist.

## Before claiming success

Verify, do not assume: read back `settings.json`, and confirm at least one card in
`~/.claude/jobs/*/state.json` has a `name` matching `^(now|\d+[mhd])( \S+)? · ` (the optional
middle group is the model glyph, absent when the transcript is gone or the model is unmapped).
