#!/usr/bin/env python3
"""PreToolUse hook: block Write/Edit calls that manually hard-wrap markdown
prose. Three or more consecutive prose lines that all fall in a narrow
length band (60-100 chars) is the signature of a wrapped paragraph, as
opposed to natural single-line paragraphs left for the renderer to soft-wrap.
Structural lines (headers, list items, blockquotes, tables, code fences,
horizontal rules) are excluded, since those are expected to be short.
"""

import json
import re
import sys

MIN_LINE_LEN = 60
MAX_LINE_LEN = 100
MIN_RUN = 3

LIST_ITEM_RE = re.compile(r"^\s*([-*+]|\d+\.)\s+")
HR_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")


def is_structural(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("#"):
        return True
    if stripped.startswith(">"):
        return True
    if stripped.count("|") >= 2:
        return True
    if LIST_ITEM_RE.match(line):
        return True
    if HR_RE.match(stripped):
        return True
    return False


def find_wrapped_run(content: str) -> list[str] | None:
    lines = content.split("\n")
    run: list[str] = []
    in_code_block = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            run = []
            continue
        if in_code_block:
            continue
        if is_structural(line):
            run = []
            continue
        if MIN_LINE_LEN <= len(line) <= MAX_LINE_LEN:
            run.append(line)
            if len(run) >= MIN_RUN:
                return run
        else:
            run = []
    return None


def main() -> None:
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path.endswith(".md"):
        return

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    else:
        return

    run = find_wrapped_run(content)
    if run is None:
        return

    example = run[0]
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Looks like manually hard-wrapped markdown: {len(run)} "
                        f"consecutive lines all {MIN_LINE_LEN}-{MAX_LINE_LEN} chars "
                        f"long (e.g. {len(example)} chars: {example!r}). Write "
                        "paragraphs as one continuous line and let the renderer "
                        "soft-wrap -- only break lines for actual structure "
                        "(new paragraphs, list items, code)."
                    ),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
