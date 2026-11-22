import importlib.machinery
import importlib.util
import subprocess

import pytest

from conftest import REPO

SCRIPT = "skills/standard-diagram/render-diagram"


@pytest.fixture
def mod():
    """Import the extension-less script."""
    loader = importlib.machinery.SourceFileLoader("render_diagram", str(REPO / SCRIPT))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader("render_diagram", loader))
    loader.exec_module(module)
    return module


def run(*args):
    return subprocess.run([REPO / SCRIPT, *args], capture_output=True, text=True)


@pytest.mark.parametrize("args", [[], ["--png"], ["a.schematex", "b.schematex"], ["a.schematex", "--out-dir"], ["a.schematex", "--bogus"]])
def test_bad_arguments_are_a_usage_error(args):
    # given arguments that omit the DSL file, repeat it or carry an unknown or incomplete flag

    # when the script runs
    result = run(*args)

    # then it exits 2 with the usage line and prints no context
    assert result.returncode == 2
    assert "Usage: render-diagram" in result.stderr
    assert result.stdout == ""


def test_missing_file_fails_with_a_context(tmp_path):
    # given a path that is not a file

    # when the script runs
    result = run(str(tmp_path / "nothing.schematex"))

    # then it exits 1 and the context names the failed step
    assert result.returncode == 1
    assert '"error"' in result.stdout


def test_page_escapes_title_and_source(mod):
    # given a title and DSL source containing markup characters
    page = mod.build_page("A <b> & C", "<svg></svg>", "x: y <z> & w")

    # when the page is built

    # then the title and source are escaped and the drawing is inlined
    assert "<title>A &lt;b&gt; &amp; C</title>" in page
    assert "x: y &lt;z&gt; &amp; w" in page
    assert "<figure><svg></svg></figure>" in page
    assert "<html" not in page and "<body" not in page


@pytest.mark.parametrize(
    "source, expected",
    [("breadboard\ntitle: IR transmit stage\nparts", "IR transmit stage"), ("breadboard\nparts", "fallback")],
)
def test_title_comes_from_the_dsl_or_the_fallback(mod, source, expected):
    # given DSL with and without a title line

    # when the title is read
    title = mod.dsl_title(source, "fallback")

    # then the title line wins, otherwise the fallback is used
    assert title == expected
