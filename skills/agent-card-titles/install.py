#!/usr/bin/env python3
"""Installer for agent-card-titles.

  python3 install.py              register the hooks
  python3 install.py --recompute  register, then retitle every existing card right away
  python3 install.py --uninstall  remove the hooks (leaves card titles as they are)
  python3 install.py --dry-run    print the resulting settings.json without writing

Options:
  --home <dir>    operate on a different .claude directory (default: $CLAUDE_CONFIG_DIR
                  or ~/.claude). Handy for testing against a scratch copy.
  --python <path> executable to run the hook with (default: the Python running this script).

Idempotent: re-running never double-registers. settings.json is backed up before write.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOOK_FILE = Path(__file__).resolve().parent / "agent-card-titles.py"
# File names a registration may invoke; the Node implementation's name is included so that
# installing over a registration made by it replaces that one.
HOOK_NAMES = ("agent-card-titles.py", "agent-card-titles.js")
EVENTS = ("UserPromptSubmit", "Stop", "SessionEnd")
STATUS = {
    "UserPromptSubmit": "Titling session card...",
    "Stop": "Reordering agent cards...",
    "SessionEnd": "Stamping agent card...",
}

# ------------------------------------------------------------------ args

parser = argparse.ArgumentParser(description="Install the agent-card-titles hooks.")
parser.add_argument("--uninstall", action="store_true")
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--recompute", action="store_true")
parser.add_argument("--python", default=sys.executable)
parser.add_argument("--home", default=os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude"))
args = parser.parse_args()

home = Path(args.home)
settings_file = home / "settings.json"

# ------------------------------------------------------------------ helpers


def read_settings():
    if not settings_file.exists():
        return {}
    raw = settings_file.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError as e:
        sys.exit(f"! {settings_file} is not valid JSON — fix it first.\n  {e}")


def is_ours(hook):
    """Ours if it invokes a file named agent-card-titles.py, wherever it lives."""
    hay = " ".join([str(hook.get("command", "")), *map(str, hook.get("args") or [])])
    return any(name in hay for name in HOOK_NAMES)


def strip_ours(settings):
    removed = 0
    hooks = settings.get("hooks") or {}

    for event in list(hooks):
        if not isinstance(hooks[event], list):
            continue

        for group in hooks[event]:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                continue
            before = len(group["hooks"])
            group["hooks"] = [h for h in group["hooks"] if not is_ours(h)]
            removed += before - len(group["hooks"])

        # Drop groups we emptied, and the event key if nothing else uses it.
        hooks[event] = [g for g in hooks[event] if isinstance(g, dict) and isinstance(g.get("hooks"), list) and g["hooks"]]
        if not hooks[event]:
            del hooks[event]

    return removed


def add_ours(settings):
    hooks = settings.setdefault("hooks", {})

    for event in EVENTS:
        groups = hooks.setdefault(event, [])

        entry = {
            "type": "command",
            "command": args.python,   # exec form: spawned directly, never through a shell,
            "args": [str(HOOK_FILE)],  # so Windows backslashes and spaces survive untouched
            "statusMessage": STATUS[event],
        }

        # Reuse a matcher-less group if there is one, so we do not fragment the file.
        group = next((g for g in groups if isinstance(g, dict) and not g.get("matcher") and isinstance(g.get("hooks"), list)), None)
        if group:
            group["hooks"].append(entry)
        else:
            groups.append({"hooks": [entry]})


def backup():
    if not settings_file.exists():
        return None
    dest = settings_file.with_name(settings_file.name + ".bak")
    shutil.copyfile(settings_file, dest)
    return dest


def recompute_all():
    """Retitle every existing card, in every project, without waiting for a hook to fire."""
    jobs_root = home / "jobs"

    try:
        ids = os.listdir(jobs_root)
    except OSError:
        print("no jobs directory — nothing to recompute")
        return

    projects = {}
    for job_id in ids:
        try:
            s = json.loads((jobs_root / job_id / "state.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        cwd = s.get("originCwd") or s.get("cwd") if isinstance(s, dict) else None
        if cwd:
            projects[str(cwd).lower()] = cwd

    for cwd in projects.values():
        # A session id that matches no job, so no card is skipped as "live".
        payload = json.dumps({
            "hook_event_name": "Stop",
            "session_id": "00000000-0000-0000-0000-000000000000",
            "cwd": cwd,
        })
        try:
            subprocess.run([args.python, str(HOOK_FILE)], input=payload, text=True, timeout=30, check=True)
        except (subprocess.SubprocessError, OSError) as e:
            print(f"  ! {cwd}: {e}")

    print(f"recomputed {len(ids)} card(s) across {len(projects)} project(s)")


# ------------------------------------------------------------------ main

if not HOOK_FILE.exists():
    sys.exit(f"! {HOOK_FILE.name} not found next to install.py ({HOOK_FILE})")

settings = read_settings()
removed = strip_ours(settings)
if not args.uninstall:
    add_ours(settings)

output = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"

if args.dry_run:
    print(output)
    sys.exit(0)

home.mkdir(parents=True, exist_ok=True)
saved = backup()
settings_file.write_text(output, encoding="utf-8")

print("Uninstalled." if args.uninstall else "Installed.")
print(f"  settings : {settings_file}" + (f"  (backup: {saved.name})" if saved else ""))
if removed:
    print(f"  replaced : {removed} existing registration(s)")
if not args.uninstall:
    print(f"  hook     : {HOOK_FILE}\n  events   : {', '.join(EVENTS)}")

if args.recompute and not args.uninstall:
    recompute_all()

if not args.uninstall:
    print("\nRestart Claude Code (or open /hooks once) to load the hooks.")
