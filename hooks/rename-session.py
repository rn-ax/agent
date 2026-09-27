#!/usr/bin/env python3
"""UserPromptSubmit hook: rename the session when the last assistant reply
carries a `<!--rename: TITLE -->` marker.

Only SessionStart/UserPromptSubmit hooks can set sessionTitle (not Stop), so
the rename always lands one message late -- see
https://github.com/anthropics/claude-code/issues/29355#issuecomment-4926999826
"""
import json
import re
import sys

MARKER_RE = re.compile(r"<!--\s*rename:\s*(.+?)\s*-->")
MAX_TITLE_LEN = 100


def last_assistant_text(path):
    text = ""
    with open(path) as f:
        for line in f:
            try:
                entry = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if entry.get("type") != "assistant":
                continue
            blocks = (entry.get("message") or {}).get("content") or []
            text = "\n".join(
                b.get("text", "") for b in blocks
                if isinstance(b, dict) and b.get("type") == "text"
            )
    return text


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    transcript_path = hook_input.get("transcript_path")
    if not transcript_path:
        return
    try:
        text = last_assistant_text(transcript_path)
    except OSError:
        return
    match = MARKER_RE.search(text)
    if not match:
        return
    title = match.group(1).strip()[:MAX_TITLE_LEN]
    if not title:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "sessionTitle": title,
        }
    }))


if __name__ == "__main__":
    main()
