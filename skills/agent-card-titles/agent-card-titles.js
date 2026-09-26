#!/usr/bin/env node
/**
 * agent-card-titles — keep the Claude Code background-agent view readable.
 *
 * Every card gets titled  "<age> <model> · <what you actually asked>"  (e.g. "3h · fix the flaky
 * auth test"), and the list is ordered newest-interaction-first instead of by creation date.
 *
 * Runs as a hook on three events (see install.js):
 *   UserPromptSubmit -> sets THIS session's title via hookSpecificOutput.sessionTitle
 *   Stop / SessionEnd -> sweeps every card in the project: re-ages chips + stamps sort keys
 *
 * Why three events, and why it is built this way:
 *
 *  - The fleet view renders `name` as the card label. `detail` doubles as the LIVE STATUS
 *    line and is overwritten constantly while a session works, so it is not a place a title
 *    can survive.
 *  - Sessions are daemon-backed and stay alive in blocked/done, and a live owner periodically
 *    rewrites its whole state.json from memory — silently dropping anything you inject.
 *    Writing `name` together with `nameSource: "user"` survives, because a watcher reads it
 *    back into the live session. `hookSpecificOutput.sessionTitle` is the officially
 *    supported path, but the CLI only honours it on UserPromptSubmit.
 *  - The age chip is RELATIVE, so it must be recomputed. A title set only at prompt-submit
 *    time would freeze at "now" forever; the Stop/SessionEnd sweep is what re-ages the list.
 *
 * Safe by construction: additive fields only, never deletes or moves anything, never touches
 * a running session's card, and swallows every error (a hook must not fail the session).
 *
 * Reads the hook JSON payload on stdin: { session_id, cwd, hook_event_name, prompt, ... }.
 * On UserPromptSubmit it prints ONE JSON object on stdout and nothing else — any other text
 * would be injected into your prompt as additional context.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

// ------------------------------------------------------------------ tunables

const TITLE_MAX = 48;   // label budget after the age chip. Raise for more context per card.
const MAX_NAME = 200;   // hard cap the CLI applies to a job name; longer names are truncated.
const AGE_WIDTH = 3;    // fixed column for the age, so the separators line up ("now", "99d").
                        // 100d+ overflows by one on purpose — those are rare and old.
const GLYPH_WIDTH = 2;  // cells reserved for the model glyph, so wide emoji and narrow text
                        // symbols (📜 vs ♫) leave the separator in the same place.
const TERMINAL_STATES = ['done', 'blocked', 'failed'];

// Which model last answered in that session, matched against ids like "claude-opus-5",
// "claude-opus-4-8", "claude-fable-5". First match wins, so order matters if ids overlap.
// A model with no entry here simply gets no chip — better a missing glyph than a wrong one.
const MODEL_ICONS = [];

// Only the last 64 KB of a transcript is read to find the model — assistant messages carry
// it on every turn, so the tail is plenty, and this keeps a full sweep cheap.
const MODEL_TAIL_BYTES = 65536;

// A larger window for finding your last prompt: one assistant turn can be far bigger than
// 64 KB, which would push the preceding human message out of the model-sized tail.
const PROMPT_TAIL_BYTES = 262144;

// ------------------------------------------------------------------ paths

const isWindows = process.platform === 'win32';

function claudeHome() {
  return process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
}

// Normalise a project path for comparison only (never for reading from disk).
function norm(p) {
  const s = String(p || '').replace(/\\/g, '/').replace(/\/+$/, '');
  return isWindows ? s.toLowerCase() : s;
}

// A project's transcript slug: the cwd with each ':' '\' '/' replaced by '-'.
function slugFor(cwd) {
  return String(cwd || '').replace(/[:\\/]/g, '-');
}

function transcriptPath(s) {
  const slug = slugFor(s.cwd || s.originCwd);
  return path.join(claudeHome(), 'projects', slug, (s.sessionId || '') + '.jsonl');
}

// ------------------------------------------------------------------ text helpers

function collapse(t) {
  return String(t || '').replace(/\s+/g, ' ').trim();
}

function clip(t, n) {
  const s = collapse(t);
  return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s;
}

// Length-cap only. Unlike clip() this preserves runs of spaces, so it is what the final
// assembled label goes through — collapsing there would eat the alignment padding.
function cap(t, n) {
  const s = String(t || '');
  return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s;
}

// Short acknowledgements and control words that must never become a card's label.
function isSmallTalk(t) {
  const s = String(t || '').trim().toLowerCase();
  if (s.length < 15) return true;
  return /^(wait|stop|retry|go|yes|no|ok|okay|nvm|never ?mind|continue|resume|option\b|[0-9]+\b|thanks?|thx|cancel|abort|pause|hold on|proceed|done|next|again|do it|sure|yep|nope|k)\b/.test(s);
}

// Injected or system content that is not a genuine human prompt.
function isNoise(s) {
  if (!s) return true;
  return s.startsWith('<')
    || /^\[Request interrupted/i.test(s)
    || /^\[Image/i.test(s)
    || /^Caveat: The messages below were generated/i.test(s)
    || /^This session is being continued from a previous conversation/i.test(s)
    || /^Base directory for this skill:/i.test(s)
    || /^Launching skill:/i.test(s)
    || /^Result of calling the .* tool/i.test(s);
}

// Plain human text from one transcript JSONL line; '' if not a substantive user message.
function humanText(line) {
  let o;
  try { o = JSON.parse(line); } catch { return ''; }
  if (o.type !== 'user' || !o.message) return '';

  const c = o.message.content;
  const parts = typeof c === 'string' ? [c]
    : Array.isArray(c) ? c.filter((x) => x && x.type === 'text').map((x) => String(x.text || ''))
    : [];

  const kept = parts.map((p) => p.trim()).filter((p) => !isNoise(p));
  const s = collapse(kept.join(' '));
  return isNoise(s) ? '' : s;
}

// What the session is about: prefer the immutable `intent`, else the first real human message.
function firstMeaningful(s) {
  const intent = String(s.intent || '').trim();
  if (intent && !isSmallTalk(intent)) return intent;

  try {
    for (const line of fs.readFileSync(transcriptPath(s), 'utf8').split('\n')) {
      if (!line.trim()) continue;
      const t = humanText(line);
      if (t && !isSmallTalk(t)) return t;
    }
  } catch { /* transcript missing or unreadable */ }

  return intent;
}

// The most recent real thing you asked, scanning the transcript tail backwards.
// Small talk is skipped, so a card never ends up labelled "yes" or "go on".
function lastMeaningful(s) {
  let text;
  try { text = readTail(transcriptPath(s), PROMPT_TAIL_BYTES); } catch { return ''; }

  const lines = text.split('\n');
  for (let i = lines.length - 1; i >= 0; i--) {
    if (!lines[i].trim()) continue;
    const t = humanText(lines[i]);
    if (t && !isSmallTalk(t)) return t;
  }

  return '';
}

// The card's text: what you asked most recently, falling back to what the session opened
// with when the tail holds nothing substantive (all small talk, or transcript pruned).
function labelText(s, typed) {
  const fresh = collapse(typed);
  if (fresh && !isSmallTalk(fresh)) return fresh;
  return lastMeaningful(s) || firstMeaningful(s);
}

// ------------------------------------------------------------------ model chip

// Read up to the last maxBytes of a file, for a bounded tail scan of a large transcript.
function readTail(file, maxBytes) {
  const fd = fs.openSync(file, 'r');
  try {
    const size = fs.fstatSync(fd).size;
    const len = Math.min(size, maxBytes);
    const buf = Buffer.alloc(len);
    fs.readSync(fd, buf, 0, len, size - len);
    return buf.toString('utf8');
  } finally { fs.closeSync(fd); }
}

// Icon for the model that answered most recently in this session.
// '<synthetic>' marks CLI-generated messages, not a real model — skip it.
function modelIcon(s) {
  let text;
  try { text = readTail(transcriptPath(s), MODEL_TAIL_BYTES); } catch { return ''; }

  const lines = text.split('\n');
  for (let i = lines.length - 1; i >= 0; i--) {
    if (!lines[i].trim()) continue;

    let o;
    try { o = JSON.parse(lines[i]); } catch { continue; }

    const model = o && o.message && o.message.model;
    if (!model || model === '<synthetic>') continue;

    const hit = MODEL_ICONS.find(([re]) => re.test(model));
    return hit ? hit[1] : '';
  }

  return '';
}

// ------------------------------------------------------------------ the label

// Rough terminal display width of a glyph. Emoji-presentation characters occupy two cells,
// text-class symbols one — so a set that mixes them (📜 emoji, ♫ text) would otherwise push
// the separator around. Not exhaustive Unicode width handling; it covers the glyphs a model
// chip realistically uses.
function displayWidth(g) {
  if (!g) return 0;
  if (g.includes('️')) return 2;          // variation selector forces emoji presentation
  return g.codePointAt(0) >= 0x1F300 ? 2 : 1;  // pictographs and above are wide
}

// The glyph padded to a fixed cell. Padding sits in FRONT so a narrow text symbol lines up
// with the right edge of a wide emoji, which is what actually reads as aligned.
function glyphCell(g) {
  return ' '.repeat(Math.max(0, GLYPH_WIDTH - displayWidth(g))) + (g || '');
}

// Very short relative age: "now", "5m", "3h", "12d", "2y". Never wider than AGE_WIDTH —
// days roll over to years so an ancient card cannot blow the column out to "1000d".
function ago(ts) {
  const diff = Date.now() - Date.parse(ts);
  if (!Number.isFinite(diff) || diff < 0) return '';

  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'now';
  if (minutes < 60) return minutes + 'm';

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return hours + 'h';

  const days = Math.floor(hours / 24);
  if (days < 365) return days + 'd';
  return Math.floor(days / 365) + 'y';
}

// "3h  ♫ · fix the flaky auth test" — age, the model that last answered, then the ask.
//
// The age is padded to a fixed width and a missing glyph becomes a space, so the '·'
// separator lines up down the list. Padding goes AFTER the age, never before: the CLI
// sanitises a title with trim(), so any leading space would be stripped and right-aligned
// digits would collapse. Column alignment is still approximate across mixed glyphs, since
// emoji are double-width in some terminals and text symbols are single.
function shortTitle(s, recency, typed) {
  const what = clip(labelText(s, typed), TITLE_MAX);
  if (!what) return '';

  const age = ago(recency);
  if (!age) return what;

  return age.padEnd(AGE_WIDTH) + ' ' + glyphCell(modelIcon(s)) + ' · ' + what;
}

// ------------------------------------------------------------------ events

// UserPromptSubmit: the only event whose output can set the session title.
function emitTitle(payload, liveShort) {
  const jobFile = path.join(claudeHome(), 'jobs', liveShort, 'state.json');

  let s;
  try { s = JSON.parse(fs.readFileSync(jobFile, 'utf8')); } catch { s = {}; }

  // Submitting a prompt IS the interaction, so the chip is "now" by definition here, and
  // the prompt being submitted is the freshest possible label — it is not in the transcript
  // on disk yet, so it has to come from the payload.
  const title = cap(shortTitle(s, new Date().toISOString(), payload.prompt), MAX_NAME);
  if (!title) return;

  process.stdout.write(JSON.stringify({
    hookSpecificOutput: { hookEventName: 'UserPromptSubmit', sessionTitle: title },
  }));
}

// Stop / SessionEnd: re-age and re-sort every card belonging to this project.
//
// The running session's OWN card is included: that is what keeps the label on your latest
// prompt and the glyph on the model actually answering, even if you switch model mid
// conversation. Only its `detail` is left alone — that field is the live status line and
// belongs to the running session.
function sweep(cwd, liveSession, liveShort) {
  const jobsRoot = path.join(claudeHome(), 'jobs');

  let ids;
  try { ids = fs.readdirSync(jobsRoot); } catch { return; }

  for (const id of ids) {
    const file = path.join(jobsRoot, id, 'state.json');

    let s;
    try { s = JSON.parse(fs.readFileSync(file, 'utf8')); } catch { continue; }
    if (norm(s.originCwd || s.cwd) !== cwd) continue;

    // Another project's still-running session is left alone; ours is always refreshed.
    const isSelf = (id === liveShort || s.sessionId === liveSession);
    if (!isSelf && !TERMINAL_STATES.includes(s.state)) continue;

    const recency = (!isSelf && s.state === 'done')
      ? (s.firstTerminalAt || s.updatedAt)
      : (s.updatedAt || new Date().toISOString());

    const key = Date.parse(recency);
    if (!Number.isFinite(key)) continue;

    let changed = false;

    // (a) recency sort. The view puts the LARGEST value on top; with no value it falls back
    // to createdAt, which is why old-but-recently-resumed sessions otherwise stay buried.
    if (s.sortOrder !== key || s.stateSortOrder !== key) {
      s.sortOrder = key;
      s.stateSortOrder = key;
      changed = true;
    }

    const label = shortTitle(s, recency);
    if (!label) continue;

    // (b) the live status line, so a finished card stops showing its last tool message.
    // Skipped for the running session — that field is its own to write.
    if (!isSelf && s.detail !== label) {
      s.detail = label;
      changed = true;
    }

    // (c) the visible card title. nameSource 'user' pins it — an 'auto' name is regenerated
    // by the CLI and would silently drop the stamp.
    const name = cap(label, MAX_NAME);
    if (s.name !== name || s.nameSource !== 'user') {
      s.name = name;
      s.nameSource = 'user';
      changed = true;
    }

    if (!changed) continue;
    try { fs.writeFileSync(file, JSON.stringify(s, null, 2)); } catch { /* ignore */ }
  }
}

function main(input) {
  // A hook always delivers valid JSON with `cwd`. If it does not parse we cannot identify
  // the project or exclude the live card, so bail rather than guess.
  let payload;
  try { payload = JSON.parse(input); } catch { return; }
  if (!payload || typeof payload !== 'object' || !payload.cwd) return;

  const cwd = norm(payload.cwd);
  if (!cwd) return;

  const liveSession = String(payload.session_id || '');
  const liveShort = liveSession.split('-')[0];
  const event = String(payload.hook_event_name || '');

  if (event === 'UserPromptSubmit') {
    if (liveShort) emitTitle(payload, liveShort);
    return; // titling only — the card sweep belongs to Stop/SessionEnd
  }

  // On SessionEnd (/stop, exit, clear) this session is going away, so its own card is no
  // longer live and is the one the user just left — stamp it too.
  sweep(cwd, liveSession, liveShort);
}

let buffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (d) => { buffer += d; });
process.stdin.on('end', () => {
  try { main(buffer); } catch { /* a hook must never fail the session */ }
});
