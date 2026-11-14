import pytest


@pytest.fixture
def titles(load_script):
    return load_script("skills/agent-card-titles/agent-card-titles.py")


@pytest.mark.parametrize(
    "text, limit, expected",
    [
        ("  fix   the\nbug ", 20, "fix the bug"),
        ("a" * 10, 5, "aaaa…"),
        ("", 5, ""),
    ],
    ids=["whitespace collapsed", "long text clipped", "empty"],
)
def test_clip_collapses_whitespace_and_limits_length(titles, text, limit, expected):
    # given a text and a limit
    # when it is clipped
    clipped = titles.clip(text, limit)

    # then the result is collapsed and within the limit
    assert clipped == expected


@pytest.mark.parametrize("text", ["yes", "ok thanks a lot for that", "continue with the plan please", "12"])
def test_acknowledgements_are_small_talk(titles, text):
    # given a short acknowledgement or control word
    # when it is classified
    small_talk = titles.is_small_talk(text)

    # then it can not become a card label
    assert small_talk is True


def test_a_real_request_is_not_small_talk(titles):
    # given a genuine request
    # when it is classified
    small_talk = titles.is_small_talk("fix the flaky auth test in the login flow")

    # then it is kept as a label
    assert small_talk is False


def test_project_slug_replaces_path_separators(titles):
    # given a project path
    # when its transcript slug is built
    slug = titles.slug_for("/Users/test/Projects/agent")

    # then each separator becomes a dash
    assert slug == "-Users-test-Projects-agent"


@pytest.mark.parametrize(
    "diff_ms, expected",
    [
        (30_000, "now"),
        (5 * 60_000, "5m"),
        (3 * 3_600_000, "3h"),
        (12 * 86_400_000, "12d"),
        (400 * 86_400_000, "1y"),
    ],
)
def test_age_is_the_shortest_relative_unit(titles, monkeypatch, diff_ms, expected):
    # given the current time is fixed
    monkeypatch.setattr(titles, "now_ms", lambda: 10_000_000_000_000)
    monkeypatch.setattr(titles, "parse_ts_ms", lambda ts: 10_000_000_000_000 - diff_ms)

    # when the age of a timestamp is formatted
    age = titles.ago("any")

    # then the largest fitting unit is used
    assert age == expected


def test_age_of_a_future_timestamp_is_empty(titles, monkeypatch):
    # given a timestamp after the current time
    monkeypatch.setattr(titles, "now_ms", lambda: 1_000)
    monkeypatch.setattr(titles, "parse_ts_ms", lambda ts: 2_000)

    # when the age is formatted
    age = titles.ago("any")

    # then there is no age
    assert age == ""
