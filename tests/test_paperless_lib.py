import json

import pytest


@pytest.fixture
def lib(load_script):
    return load_script("skills/paperless/paperless_lib.py")


def test_successful_run_prints_the_context_and_exits_zero(lib, capsys):
    # given a script that records a step
    ctx = lib.Context("example", id=42)

    # when it runs to completion
    with pytest.raises(SystemExit) as exit_info:
        ctx.run(lambda c: c.step("fetched", count=3))

    # then the context is printed with the step and the exit code is 0
    assert exit_info.value.code == 0
    assert json.loads(capsys.readouterr().out) == {
        "script": "example",
        "args": {"id": 42},
        "steps": [{"step": "fetched", "count": 3}],
    }


def test_failure_is_reported_in_the_context_and_exits_one(lib, capsys):
    # given a script that fails after a step
    def fn(c):
        c.step("fetched")
        raise lib.Failure("no tag", known_tags=["a"])

    # when it runs
    with pytest.raises(SystemExit) as exit_info:
        lib.Context("example").run(fn)

    # then the error names the last step and carries the detail
    assert exit_info.value.code == 1
    assert json.loads(capsys.readouterr().out)["error"] == {"after_step": "fetched", "message": "no tag", "known_tags": ["a"]}


def test_unexpected_exception_is_reported_with_its_type(lib, capsys):
    # given a script that raises before any step
    def fn(c):
        raise ValueError("boom")

    # when it runs
    with pytest.raises(SystemExit) as exit_info:
        lib.Context("example").run(fn)

    # then the error names the start and the exception type
    assert exit_info.value.code == 1
    assert json.loads(capsys.readouterr().out)["error"] == {"after_step": "start", "type": "ValueError", "message": "boom"}


def test_credentials_come_from_the_environment(lib, monkeypatch):
    # given both credentials in the environment
    monkeypatch.setenv("PAPERLESS_URL", "http://paperless.test/")
    monkeypatch.setenv("PAPERLESS_TOKEN", "token-1")

    # when credentials are read
    url, token = lib.credentials()

    # then the url has no trailing slash
    assert (url, token) == ("http://paperless.test", "token-1")
