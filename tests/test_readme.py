"""Execute the Python examples in README.md and check their documented output.

Every ``print(...)  # expected`` line in a README code block must print exactly
``expected``. Text after two spaces in the comment is treated as an annotation,
e.g. ``# 4000.00 h  (full-load hours)``.
"""

import contextlib
import io
import re
import warnings
from pathlib import Path

import pytest

from energyunits import EnergyUnitsWarning

README = Path(__file__).resolve().parents[1] / "README.md"
_BLOCK_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)
_PRINT_RE = re.compile(r"^\s*print\(.*\)\s+#\s(?P<expected>.*)$")


def _blocks():
    if not README.exists():  # e.g. when running tests from an installed sdist without README
        return []
    text = README.read_text(encoding="utf-8")
    blocks = []
    for match in _BLOCK_RE.finditer(text):
        line = text[: match.start()].count("\n") + 2
        blocks.append(pytest.param(match.group(1), id=f"README.md:{line}"))
    return blocks


def _expected_outputs(code):
    expected = []
    for line in code.splitlines():
        if line.strip().startswith("print("):
            match = _PRINT_RE.match(line)
            expected.append(match.group("expected").split("  ")[0].strip() if match else None)
    return expected


@pytest.mark.parametrize("code", _blocks())
def test_readme_example(code, tmp_path, monkeypatch):
    if "import pandas" in code:
        pytest.importorskip("pandas")
    monkeypatch.chdir(tmp_path)
    output = io.StringIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", EnergyUnitsWarning)
        with contextlib.redirect_stdout(output):
            exec(compile(code, str(README), "exec"), {"__name__": "__readme__"})

    printed = output.getvalue().splitlines()
    expected = _expected_outputs(code)
    assert len(printed) == len(expected), printed
    for actual, documented in zip(printed, expected):
        if documented is not None:
            assert actual == documented


def test_readme_has_examples():
    assert len(_blocks()) >= 10
