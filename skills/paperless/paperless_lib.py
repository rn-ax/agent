"""Shared pieces of the paperless scripts: the report context and the Paperless API client.

Context: a script builds one when it starts, adds a step for everything it does, and prints it as
one JSON document on stdout when it exits, on success and on failure alike (see the
writing-skills skill). `Failure` is the expected way for a script to stop with a clear message.

Api: credentials come from PAPERLESS_URL and PAPERLESS_TOKEN, else from the "Paperless" item in
the "Agent" 1Password vault (first URL = LAN address, password = API token), like pl-api.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


class Failure(Exception):
    """A script stops with this to report what failed; detail keys are added to the context's error."""

    def __init__(self, message, **detail):
        super().__init__(message)
        self.detail = detail


class Context:
    def __init__(self, script, **args):
        self.data = {"script": script, "args": args, "steps": []}

    def step(self, name, **data):
        self.data["steps"].append({"step": name, **data})

    def set(self, **data):
        self.data.update(data)

    def _last_step(self):
        return self.data["steps"][-1]["step"] if self.data["steps"] else "start"

    def run(self, fn):
        """Call fn(self); always print the context; exit 0, or 1 with an `error` in the context."""
        code = 0
        try:
            fn(self)
        except Failure as e:
            self.data["error"] = {"after_step": self._last_step(), "message": str(e), **e.detail}
            code = 1
        except Exception as e:  # anything unexpected still reports how far the script got
            self.data["error"] = {"after_step": self._last_step(), "type": type(e).__name__, "message": str(e)}
            code = 1
        finally:
            print(json.dumps(self.data, ensure_ascii=False))
        sys.exit(code)


def credentials():
    url, token = os.environ.get("PAPERLESS_URL"), os.environ.get("PAPERLESS_TOKEN")
    if url and token:
        return url.rstrip("/"), token
    wrapper = os.path.expanduser("~/tasks/op-service-account")
    out = subprocess.run([wrapper, "item", "get", "Paperless", "--vault", "Agent", "--format", "json", "--reveal"],
                         capture_output=True, text=True)
    if out.returncode:
        raise Failure("could not read the Paperless item from 1Password", stderr=out.stderr.strip()[:300])
    item = json.loads(out.stdout)
    token = token or next(f["value"] for f in item["fields"] if f["id"] == "password")
    url = url or item["urls"][0]["href"]
    return url.rstrip("/"), token


class Api:
    def __init__(self):
        self.url, self.token = credentials()

    def _request(self, method, path, body=None):
        return urllib.request.Request(
            self.url + "/api" + path, method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Authorization": f"Token {self.token}", "Accept": "application/json; version=9",
                     "Content-Type": "application/json"})

    def request(self, method, path, body=None):
        try:
            with urllib.request.urlopen(self._request(method, path, body), timeout=180) as r:
                return json.loads(r.read() or "null")
        except urllib.error.HTTPError as e:
            raise Failure(f"{method} {path} answered HTTP {e.code}", status=e.code, response=e.read()[:300].decode("utf-8", "replace"))
        except urllib.error.URLError as e:
            raise Failure(f"{method} {path} could not reach Paperless", reason=str(e.reason))

    def get(self, path):
        return self.request("GET", path)

    def download(self, path, dest):
        try:
            with urllib.request.urlopen(self._request("GET", path), timeout=300) as r, open(dest, "wb") as f:
                size = 0
                for chunk in iter(lambda: r.read(1 << 20), b""):
                    f.write(chunk)
                    size += len(chunk)
            return size
        except urllib.error.HTTPError as e:
            raise Failure(f"GET {path} answered HTTP {e.code}", status=e.code)

    def tag(self, name):
        found = self.get("/tags/?" + urllib.parse.urlencode({"name__iexact": name, "page_size": 5}))["results"]
        if not found:
            known = [t["name"] for t in self.get("/tags/?page_size=1000")["results"]]
            raise Failure(f"no tag named {name!r}", known_tags=known)
        return found[0]

    def documents(self, query, fields):
        """All documents matching a query string, following pages; returns the list."""
        out, page = [], 1
        while True:
            qs = f"{query}&" if query else ""
            data = self.get(f"/documents/?{qs}page={page}&page_size=100&ordering=id&fields={fields}")
            out += data["results"]
            if not data.get("next"):
                return out
            page += 1
