import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def load_script():
    """Import a repo script by its path relative to the repo root, whatever its file name."""

    def load(relative_path):
        path = REPO / relative_path
        spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return load
