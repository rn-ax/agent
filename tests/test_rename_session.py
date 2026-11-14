import io
import json

import pytest


@pytest.fixture
def hook(load_script):
    return load_script("hooks/rename-session.py")


def assistant_line(*texts):
    blocks = [{"type": "text", "text": t} for t in texts]
    return json.dumps({"type": "assistant", "message": {"content": blocks}})


def run_hook(hook, monkeypatch, capsys, transcript):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"transcript_path": str(transcript)})))
    hook.main()
    return capsys.readouterr().out


def test_marker_in_the_last_assistant_reply_sets_the_session_title(hook, monkeypatch, capsys, tmp_path):
    # given a transcript whose last assistant reply carries a rename marker
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(assistant_line("old <!--rename: First title -->") + "\n" + assistant_line("done <!--rename:  Second title  -->") + "\n")

    # when the hook runs
    out = run_hook(hook, monkeypatch, capsys, transcript)

    # then the title from the last marker is returned
    assert json.loads(out)["hookSpecificOutput"] == {"hookEventName": "UserPromptSubmit", "sessionTitle": "Second title"}


def test_title_is_cut_to_the_maximum_length(hook, monkeypatch, capsys, tmp_path):
    # given a marker with a title longer than the maximum
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(assistant_line("<!--rename: " + "a" * 150 + " -->") + "\n")

    # when the hook runs
    out = run_hook(hook, monkeypatch, capsys, transcript)

    # then the title is cut to the maximum
    assert json.loads(out)["hookSpecificOutput"]["sessionTitle"] == "a" * hook.MAX_TITLE_LEN


def test_reply_without_a_marker_prints_nothing(hook, monkeypatch, capsys, tmp_path):
    # given a transcript whose last reply has no marker, after an earlier reply that had one
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(assistant_line("<!--rename: Old -->") + "\n" + assistant_line("plain reply") + "\n")

    # when the hook runs
    out = run_hook(hook, monkeypatch, capsys, transcript)

    # then nothing is printed
    assert out == ""


def test_malformed_transcript_lines_are_skipped(hook, tmp_path):
    # given a transcript with a broken line before a valid reply
    transcript = tmp_path / "t.jsonl"
    transcript.write_text("not json\n" + assistant_line("hello", "world") + "\n")

    # when the last assistant text is read
    text = hook.last_assistant_text(transcript)

    # then the text blocks of the valid reply are joined
    assert text == "hello\nworld"


def test_missing_transcript_prints_nothing(hook, monkeypatch, capsys, tmp_path):
    # given a transcript path that does not exist
    # when the hook runs
    out = run_hook(hook, monkeypatch, capsys, tmp_path / "missing.jsonl")

    # then nothing is printed
    assert out == ""
