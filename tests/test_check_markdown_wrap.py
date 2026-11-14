import io
import json

import pytest


@pytest.fixture
def hook(load_script):
    return load_script("hooks/check-markdown-wrap.py")


def run_hook(hook, monkeypatch, capsys, payload):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    hook.main()
    return capsys.readouterr().out


def test_three_consecutive_medium_lines_are_a_wrapped_paragraph(hook):
    # given prose hard-wrapped at about 70 characters
    content = "\n".join(["word " * 14] * 3)

    # when the content is scanned
    run = hook.find_wrapped_run(content)

    # then the wrapped lines are returned
    assert run == [("word " * 14)] * 3


@pytest.mark.parametrize(
    "content",
    [
        "short line\n" * 5,
        ("word " * 14 + "\n") * 2,
        "# " + "h" * 70 + "\n" + "- " + "i" * 70 + "\n" + "> " + "q" * 70,
        "```\n" + ("c" * 70 + "\n") * 4 + "```",
        "x" * 150 + "\n" + "y" * 150 + "\n" + "z" * 150,
    ],
    ids=["short lines", "only two long lines", "structural lines", "code block", "unwrapped paragraphs"],
)
def test_content_without_a_wrapped_paragraph_is_accepted(hook, content):
    # given content with no run of three wrapped prose lines
    # when the content is scanned
    run = hook.find_wrapped_run(content)

    # then nothing is found
    assert run is None


def test_write_of_a_wrapped_markdown_file_is_denied(hook, monkeypatch, capsys):
    # given a Write of wrapped prose to a markdown file
    payload = {"tool_name": "Write", "tool_input": {"file_path": "notes.md", "content": "\n".join(["word " * 14] * 3)}}

    # when the hook runs
    out = run_hook(hook, monkeypatch, capsys, payload)

    # then the call is denied with the reason
    decision = json.loads(out)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "hard-wrapped" in decision["permissionDecisionReason"]


def test_edit_checks_the_new_string(hook, monkeypatch, capsys):
    # given an Edit whose new_string is wrapped prose
    payload = {"tool_name": "Edit", "tool_input": {"file_path": "notes.md", "new_string": "\n".join(["word " * 14] * 3)}}

    # when the hook runs
    out = run_hook(hook, monkeypatch, capsys, payload)

    # then the call is denied
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_wrapped_prose_in_a_non_markdown_file_is_ignored(hook, monkeypatch, capsys):
    # given a Write of wrapped prose to a python file
    payload = {"tool_name": "Write", "tool_input": {"file_path": "notes.py", "content": "\n".join(["word " * 14] * 3)}}

    # when the hook runs
    out = run_hook(hook, monkeypatch, capsys, payload)

    # then nothing is printed
    assert out == ""
