"""Send one ad-hoc command over HA's websocket API and print the raw result.

For anything not reachable via the REST API -- HACS commands, renaming a
config entry (config_entries/update), or any other websocket-only command
-- this handles the connect/auth/send boilerplate that's otherwise easy to
reimplement slightly differently each time. For a repeated, multi-step
workflow worth its own script (see hacs_install.py), write a dedicated one
instead of chaining several ws-call invocations.

Usage: ws_call.py '<json payload, without "id">'

Reads HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN from the environment
(the ws-call wrapper script sources these from
~/.config/home-assistant/env before calling this).
"""

import asyncio
import json
import os
import sys

import websockets


async def main():
    if len(sys.argv) != 2:
        print('Usage: ws_call.py \'<json payload, without "id">\'', file=sys.stderr)
        raise SystemExit(1)
    payload = json.loads(sys.argv[1])

    token = os.environ["HOME_ASSISTANT_TOKEN"]
    base_url = os.environ["HOME_ASSISTANT_URL"]
    ws_scheme = "wss" if base_url.startswith("https") else "ws"
    host_part = base_url.split("://", 1)[1]
    uri = f"{ws_scheme}://{host_part}/api/websocket"

    async with websockets.connect(uri, max_size=50 * 1024 * 1024) as ws:
        await ws.recv()  # auth_required
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        auth_result = json.loads(await ws.recv())
        if auth_result.get("type") != "auth_ok":
            print("auth failed:", auth_result, file=sys.stderr)
            raise SystemExit(1)

        payload["id"] = 1
        await ws.send(json.dumps(payload))
        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout=30)
            data = json.loads(raw)
            if data.get("id") == 1:
                print(json.dumps(data, indent=2))
                return


asyncio.run(main())
