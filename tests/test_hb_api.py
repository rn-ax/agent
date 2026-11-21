import subprocess

import pytest

from conftest import REPO

HB_API = REPO / "skills/homebox/hb-api"


def run(*args):
    return subprocess.run([HB_API, *args], capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["GET", "/groups"],
        ["--inventory"],
        ["--inventory", "other", "GET", "/groups"],
        ["--inventory", "diy"],
        ["--inventory", "diy", "GET"],
    ],
)
def test_call_without_a_known_inventory_and_a_method_and_path_is_a_usage_error(args):
    # given a call that omits or misnames the inventory, or lacks a method or path

    # when it runs
    result = run(*args)

    # then it exits 2 with the usage line, before any credential is read or request sent
    assert result.returncode == 2
    assert "Usage: hb-api --inventory household|diy" in result.stderr
