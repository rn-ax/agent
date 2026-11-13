#!/usr/bin/env python3
"""agent-card-titles — keep the Claude Code background-agent view readable.

Every card gets titled  "<age> <model> · <what you actually asked>"  (e.g. "3h · fix the flaky
auth test"), and the list is ordered newest-interaction-first instead of by creation date.

Runs as a hook on three events (see install.py):
  UserPromptSubmit -> sets THIS session's title via hookSpecificOutput.sessionTitle
  Stop / SessionEnd -> sweeps every card in the project: re-ages chips + stamps sort keys

Why three events, and why it is built this way:

 - The fleet view renders `name` as the card label. `detail` doubles as the LIVE STATUS
   line and is overwritten constantly while a session works, so it is not a place a title
   can survive.
 - Sessions are daemon-backed and stay alive in blocked/done, and a live owner periodically
   rewrites its whole state.json from memory — silently dropping anything you inject.
   Writing `name` together with `nameSource: "user"` survives, because a watcher reads it
   back into the live session. `hookSpecificOutput.sessionTitle` is the officially
   supported path, but the CLI only honours it on UserPromptSubmit.
 - The age chip is RELATIVE, so it must be recomputed. A title set only at prompt-submit
   time would freeze at "now" forever; the Stop/SessionEnd sweep is what re-ages the list.

Safe by construction: additive fields only, never deletes or moves anything, never touches
a running session's card, and swallows every error (a hook must not fail the session).

Reads the hook JSON payload on stdin: { session_id, cwd, hook_event_name, prompt, ... }.
On UserPromptSubmit it prints ONE JSON object on stdout and nothing else — any other text
would be injected into your prompt as additional context.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ------------------------------------------------------------------ tunables

TITLE_MAX = 48    # label budget after the age chip. Raise for more context per card.
MAX_NAME = 200    # hard cap the CLI applies to a job name; longer names are truncated.
AGE_WIDTH = 3     # fixed column for the age, so the separators line up ("now", "99d").
                  # 100d+ overflows by one on purpose — those are rare and old.
GLYPH_WIDTH = 2   # cells reserved for the model glyph, so wide emoji and narrow text
                  # symbols (📜 vs ♫) leave the separator in the same place.
TERMINAL_STATES = ("done", "blocked", "failed")

# Which model last answered in that session, matched against ids like "claude-opus-5",
# "claude-opus-4-8", "claude-fable-5". First match wins, so order matters if ids overlap.
# A model with no entry here simply gets no chip — better a missing glyph than a wrong one.
# Entries are (re.compile(pattern), glyph).
MODEL_ICONS = []

# Only the last 64 KB of a transcript is read to find the model — assistant messages carry
# it on every turn, so the tail is plenty, and this keeps a full sweep cheap.
MODEL_TAIL_BYTES = 65536

# A larger window for finding your last prompt: one assistant turn can be far bigger than
# 64 KB, which would push the preceding human message out of the model-sized tail.
PROMPT_TAIL_BYTES = 262144

# ------------------------------------------------------------------ paths

IS_WINDOWS = sys.platform == "win32"


def claude_home():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def norm(p):
    """Normalise a project path for comparison only (never for reading from disk)."""
    s = re.sub(r"/+$", "", str(p or "").replace("\\", "/"))
    return s.lower() if IS_WINDOWS else s


def slug_for(cwd):
    """A project's transcript slug: the cwd with each ':' '\\' '/' replaced by '-'."""
    return re.sub(r"[:\\/]", "-", str(cwd or ""))


def transcript_path(s):
    slug = slug_for(s.get("cwd") or s.get("originCwd"))
    return claude_home() / "projects" / slug / ((s.get("sessionId") or "") + ".jsonl")


# ------------------------------------------------------------------ text helpers


def collapse(t):
    return re.sub(r"\s+", " ", str(t or "")).strip()


def clip(t, n):
    s = collapse(t)
    return s[: n - 1].rstrip() + "…" if len(s) > n else s


def cap(t, n):
    """Length-cap only. Unlike clip() this preserves runs of spaces, so it is what the final
    assembled label goes through — collapsing there would eat the alignment padding."""
    s = str(t or "")
    return s[: n - 1].rstrip() + "…" if len(s) > n else s


SMALL_TALK_RE = re.compile(
    r"^(wait|stop|retry|go|yes|no|ok|okay|nvm|never ?mind|continue|resume|option\b|[0-9]+\b"
    r"|thanks?|thx|cancel|abort|pause|hold on|proceed|done|next|again|do it|sure|yep|nope|k)\b"
)


def is_small_talk(t):
    """Short acknowledgements and control words that must never become a card's label."""
    s = str(t or "").strip().lower()
    return len(s) < 15 or bool(SMALL_TALK_RE.match(s))


NOISE_RES = [re.compile(p, re.I) for p in (
    r"^\[Request interrupted",
    r"^\[Image",
    r"^Caveat: The messages below were generated",
    r"^This session is being continued from a previous conversation",
    r"^Base directory for this skill:",
    r"^Launching skill:",
    r"^Result of calling the .* tool",
)]


def is_noise(s):
    """Injected or system content that is not a genuine human prompt."""
    if not s:
        return True
    return s.startswith("<") or any(r.match(s) for r in NOISE_RES)


def human_text(line):
    """Plain human text from one transcript JSONL line; '' if not a substantive user message."""
    try:
        o = json.loads(line)
    except ValueError:
        return ""
    if not isinstance(o, dict) or o.get("type") != "user" or not o.get("message"):
        return ""

    c = o["message"].get("content")
    if isinstance(c, str):
        parts = [c]
    elif isinstance(c, list):
        parts = [str(x.get("text") or "") for x in c if isinstance(x, dict) and x.get("type") == "text"]
    else:
        parts = []

    kept = [p for p in (p.strip() for p in parts) if not is_noise(p)]
    s = collapse(" ".join(kept))
    return "" if is_noise(s) else s


def first_meaningful(s):
    """What the session is about: prefer the immutable `intent`, else the first real human message."""
    intent = str(s.get("intent") or "").strip()
    if intent and not is_small_talk(intent):
        return intent

    try:
        with open(transcript_path(s), encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                t = human_text(line)
                if t and not is_small_talk(t):
                    return t
    except OSError:
        pass  # transcript missing or unreadable

    return intent


def last_meaningful(s):
    """The most recent real thing you asked, scanning the transcript tail backwards.
    Small talk is skipped, so a card never ends up labelled "yes" or "go on"."""
    try:
        text = read_tail(transcript_path(s), PROMPT_TAIL_BYTES)
    except OSError:
        return ""

    for line in reversed(text.split("\n")):
        if not line.strip():
            continue
        t = human_text(line)
        if t and not is_small_talk(t):
            return t

    return ""


def label_text(s, typed):
    """The card's text: what you asked most recently, falling back to what the session opened
    with when the tail holds nothing substantive (all small talk, or transcript pruned)."""
    fresh = collapse(typed)
    if fresh and not is_small_talk(fresh):
        return fresh
    return last_meaningful(s) or first_meaningful(s)


# ------------------------------------------------------------------ model chip


def read_tail(file, max_bytes):
    """Read up to the last max_bytes of a file, for a bounded tail scan of a large transcript."""
    with open(file, "rb") as f:
        size = f.seek(0, os.SEEK_END)
        n = min(size, max_bytes)
        f.seek(size - n)
        return f.read(n).decode("utf-8", errors="replace")


def model_icon(s):
    """Icon for the model that answered most recently in this session.
    '<synthetic>' marks CLI-generated messages, not a real model — skip it."""
    try:
        text = read_tail(transcript_path(s), MODEL_TAIL_BYTES)
    except OSError:
        return ""

    for line in reversed(text.split("\n")):
        if not line.strip():
            continue
        try:
            o = json.loads(line)
        except ValueError:
            continue

        msg = o.get("message") if isinstance(o, dict) else None
        model = msg.get("model") if isinstance(msg, dict) else None
        if not model or model == "<synthetic>":
            continue

        return next((glyph for pattern, glyph in MODEL_ICONS if pattern.search(model)), "")

    return ""


# ------------------------------------------------------------------ the label


def display_width(g):
    """Rough terminal display width of a glyph. Emoji-presentation characters occupy two cells,
    text-class symbols one — so a set that mixes them (📜 emoji, ♫ text) would otherwise push
    the separator around. Not exhaustive Unicode width handling; it covers the glyphs a model
    chip realistically uses."""
    if not g:
        return 0
    if "️" in g:  # variation selector forces emoji presentation
        return 2
    return 2 if ord(g[0]) >= 0x1F300 else 1  # pictographs and above are wide


def glyph_cell(g):
    """The glyph padded to a fixed cell. Padding sits in FRONT so a narrow text symbol lines up
    with the right edge of a wide emoji, which is what actually reads as aligned."""
    return " " * max(0, GLYPH_WIDTH - display_width(g)) + (g or "")


EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def parse_ts_ms(ts):
    """Epoch milliseconds of an ISO timestamp string, or None if it is not one."""
    if not isinstance(ts, str):
        return None
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt - EPOCH) // timedelta(milliseconds=1)


def now_ms():
    return (datetime.now(timezone.utc) - EPOCH) // timedelta(milliseconds=1)


def iso_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def ago(ts):
    """Very short relative age: "now", "5m", "3h", "12d", "2y". Never wider than AGE_WIDTH —
    days roll over to years so an ancient card cannot blow the column out to "1000d"."""
    ms = parse_ts_ms(ts)
    if ms is None:
        return ""
    diff = now_ms() - ms
    if diff < 0:
        return ""

    minutes = diff // 60000
    if minutes < 1:
        return "now"
    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    if hours < 24:
        return f"{hours}h"

    days = hours // 24
    if days < 365:
        return f"{days}d"
    return f"{days // 365}y"


def short_title(s, recency, typed=None):
    """"3h  ♫ · fix the flaky auth test" — age, the model that last answered, then the ask.

    The age is padded to a fixed width and a missing glyph becomes a space, so the '·'
    separator lines up down the list. Padding goes AFTER the age, never before: the CLI
    sanitises a title with trim(), so any leading space would be stripped and right-aligned
    digits would collapse. Column alignment is still approximate across mixed glyphs, since
    emoji are double-width in some terminals and text symbols are single."""
    what = clip(label_text(s, typed), TITLE_MAX)
    if not what:
        return ""

    age = ago(recency)
    if not age:
        return what

    return age.ljust(AGE_WIDTH) + " " + glyph_cell(model_icon(s)) + " · " + what


# ------------------------------------------------------------------ events


def emit_title(payload, live_short):
    """UserPromptSubmit: the only event whose output can set the session title."""
    job_file = claude_home() / "jobs" / live_short / "state.json"

    try:
        s = json.loads(job_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        s = {}
    if not isinstance(s, dict):
        s = {}

    # Submitting a prompt IS the interaction, so the chip is "now" by definition here, and
    # the prompt being submitted is the freshest possible label — it is not in the transcript
    # on disk yet, so it has to come from the payload.
    title = cap(short_title(s, iso_now(), payload.get("prompt")), MAX_NAME)
    if not title:
        return

    out = json.dumps(
        {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "sessionTitle": title}},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    sys.stdout.buffer.write(out.encode("utf-8"))


def sweep(cwd, live_session, live_short):
    """Stop / SessionEnd: re-age and re-sort every card belonging to this project.

    The running session's OWN card is included: that is what keeps the label on your latest
    prompt and the glyph on the model actually answering, even if you switch model mid
    conversation. Only its `detail` is left alone — that field is the live status line and
    belongs to the running session."""
    jobs_root = claude_home() / "jobs"

    try:
        ids = os.listdir(jobs_root)
    except OSError:
        return

    for job_id in ids:
        file = jobs_root / job_id / "state.json"

        try:
            s = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(s, dict) or norm(s.get("originCwd") or s.get("cwd")) != cwd:
            continue

        # Another project's still-running session is left alone; ours is always refreshed.
        is_self = job_id == live_short or s.get("sessionId") == live_session
        if not is_self and s.get("state") not in TERMINAL_STATES:
            continue

        if not is_self and s.get("state") == "done":
            recency = s.get("firstTerminalAt") or s.get("updatedAt")
        else:
            recency = s.get("updatedAt") or iso_now()

        key = parse_ts_ms(recency)
        if key is None:
            continue

        changed = False

        # (a) recency sort. The view puts the LARGEST value on top; with no value it falls back
        # to createdAt, which is why old-but-recently-resumed sessions otherwise stay buried.
        if s.get("sortOrder") != key or s.get("stateSortOrder") != key:
            s["sortOrder"] = key
            s["stateSortOrder"] = key
            changed = True

        label = short_title(s, recency)
        if not label:
            continue

        # (b) the live status line, so a finished card stops showing its last tool message.
        # Skipped for the running session — that field is its own to write.
        if not is_self and s.get("detail") != label:
            s["detail"] = label
            changed = True

        # (c) the visible card title. nameSource 'user' pins it — an 'auto' name is regenerated
        # by the CLI and would silently drop the stamp.
        name = cap(label, MAX_NAME)
        if s.get("name") != name or s.get("nameSource") != "user":
            s["name"] = name
            s["nameSource"] = "user"
            changed = True

        if not changed:
            continue
        try:
            file.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass


def main(raw):
    # A hook always delivers valid JSON with `cwd`. If it does not parse we cannot identify
    # the project or exclude the live card, so bail rather than guess.
    try:
        payload = json.loads(raw)
    except ValueError:
        return
    if not isinstance(payload, dict) or not payload.get("cwd"):
        return

    cwd = norm(payload["cwd"])
    if not cwd:
        return

    live_session = str(payload.get("session_id") or "")
    live_short = live_session.split("-")[0]
    event = str(payload.get("hook_event_name") or "")

    if event == "UserPromptSubmit":
        if live_short:
            emit_title(payload, live_short)
        return  # titling only — the card sweep belongs to Stop/SessionEnd

    # On SessionEnd (/stop, exit, clear) this session is going away, so its own card is no
    # longer live and is the one the user just left — stamp it too.
    sweep(cwd, live_session, live_short)


if __name__ == "__main__":
    try:
        main(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
    except Exception:
        pass  # a hook must never fail the session
