"""Shared helpers for loading custom data into the registries."""

import json
import math
import os
from collections.abc import Mapping
from typing import List, Union

from .exceptions import DefinitionConflictError

#: A JSON file path or an already parsed mapping.
DataSource = Union[str, "os.PathLike[str]", Mapping]

_MAX_LISTED = 10


def _plain(value):
    """Copy of nested data with mappings as dicts and sequences as lists (like parsed JSON)."""
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def read_source(source: DataSource) -> dict:
    """Return the data of a JSON file path, or a copy of a mapping (read-only views included)."""
    if isinstance(source, Mapping):
        return _plain(source)
    if isinstance(source, (str, os.PathLike)):
        with open(source, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"{os.fspath(source)}: the top level must be a JSON object")
        return data
    raise TypeError(f"Expected a file path or a mapping, got {type(source).__name__}")


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def same_value(a, b) -> bool:
    """Equality that tolerates float round-off and treats lists and tuples alike."""
    if is_number(a) and is_number(b):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0)
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        return a.keys() == b.keys() and all(same_value(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(same_value(x, y) for x, y in zip(a, b))
    return a == b


def raise_conflicts(what: str, conflicts: List[str]) -> None:
    """Raise :class:`DefinitionConflictError` listing ``conflicts`` (if any)."""
    if not conflicts:
        return
    listed = conflicts[:_MAX_LISTED]
    if len(conflicts) > _MAX_LISTED:
        listed.append(f"... and {len(conflicts) - _MAX_LISTED} more")
    noun = "definition conflicts" if len(conflicts) == 1 else "definitions conflict"
    raise DefinitionConflictError(
        f"Cannot load {what}: {len(conflicts)} {noun} with existing data (bundled or loaded earlier):\n  "
        + "\n  ".join(listed)
        + "\nNothing was loaded. Use new names (for example with a prefix such as 'mylib_'), or pass "
        "overwrite=True to replace the existing definitions for the whole Python process."
    )
