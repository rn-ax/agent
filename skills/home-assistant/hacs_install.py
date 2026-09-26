"""Register a GitHub repo as a HACS custom repository and install it.

HACS doesn't expose this over HA's REST API -- it's carried over HA's
websocket API as HACS-specific command types. See this skill's SKILL.md
for the background; this is the parameterized version of the script used
to install ha-inteno-router.

Usage: hacs_install.py <owner/repo> <category>
  category is HACS's lowercase category name, e.g. "integration".

Reads HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN from the environment
(the hacs-install wrapper script sources these from
~/.config/home-assistant/env before calling this).
"""

import asyncio
import json
import os
import sys

import websockets


async def send(ws, msg_id, payload):
    payload["id"] = msg_id
    await ws.send(json.dumps(payload))
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout=30)
        data = json.loads(raw)
        if data.get("id") == msg_id:
            return data


async def main():
    if len(sys.argv) != 3:
        print("Usage: hacs_install.py <owner/repo> <category>", file=sys.stderr)
        raise SystemExit(1)
    full_name, category = sys.argv[1], sys.argv[2]

    token = os.environ["HOME_ASSISTANT_TOKEN"]
    base_url = os.environ["HOME_ASSISTANT_URL"]
    ws_scheme = "wss" if base_url.startswith("https") else "ws"
    host_part = base_url.split("://", 1)[1]
    uri = f"{ws_scheme}://{host_part}/api/websocket"

    async with websockets.connect(uri, max_size=50 * 1024 * 1024) as ws:
        hello = json.loads(await ws.recv())
        print("server:", hello)
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth_result = json.loads(await ws.recv())
        if auth_result.get("type") != "auth_ok":
            print("auth failed:", auth_result, file=sys.stderr)
            raise SystemExit(1)

        msg_id = 1
        add_result = await send(ws, msg_id, {
            "type": "hacs/repositories/add",
            "repository": full_name,
            "category": category,
        })
        print("add_repository:", json.dumps(add_result))
        msg_id += 1

        list_result = await send(ws, msg_id, {
            "type": "hacs/repositories/list",
            "categories": [category],
        })
        msg_id += 1
        repos = list_result.get("result", [])
        match = [r for r in repos if r.get("full_name", "").lower() == full_name.lower()]
        if not match:
            print(f"'{full_name}' not found in HACS list after add -- stopping.", file=sys.stderr)
            raise SystemExit(1)
        print("repository state:", json.dumps(match[0], indent=2))

        repo_id = match[0]["id"]
        download_result = await send(ws, msg_id, {
            "type": "hacs/repository/download",
            "repository": repo_id,
        })
        print("download:", json.dumps(download_result))

        print("Restart Home Assistant (homeassistant.restart service) and run "
              "wait-ready before checking the result -- HACS's own state is "
              "transiently stale for a few seconds right after a restart.")


asyncio.run(main())
