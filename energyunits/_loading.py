"""Shared helpers for loading custom data into the registries."""

import json
import math
import numbers
import os
from collections.abc import Mapping
from typing import Dict, List, Optional, Union

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
    """True for real numbers, including NumPy scalars, but not for booleans."""
    if isinstance(value, bool) or type(value).__name__ in ("bool_", "bool"):
        return False
    return isinstance(value, numbers.Real)


def is_comment(key) -> bool:
    """Keys starting with ``_`` are comments or metadata in all data files."""
    return isinstance(key, str) and key.startswith("_")


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


def _currency_from_string(unit: str, currencies) -> Optional[str]:
    """Fallback currency detection for strings that are not valid unit expressions."""
    components = unit.upper().replace("/", " ").replace("*", " ").replace("·", " ").split()
    for currency in currencies:
        if currency in components:
            return currency
    if "$" in unit or "DOLLAR" in unit.upper():
        return "USD"
    return None


def _year(value, where: str) -> int:
    try:
        year = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{where}: invalid year {value!r}") from None
    if isinstance(value, bool) or str(year) != str(value).strip():
        raise ValueError(f"{where}: invalid year {value!r}")
    return year


def parse_annual_series(data: dict, what: str, valid, requirement: str) -> Dict[str, Dict[int, float]]:
    """Validate ``{"CUR": {"2020": value, ...}}`` data (keys starting with ``_`` are skipped)."""
    series: Dict[str, Dict[int, float]] = {}
    for currency, year_data in data.items():
        if is_comment(currency):
            continue
        if not isinstance(currency, str) or not currency or currency != currency.strip():
            raise ValueError(f"Invalid currency code {currency!r} in {what}")
        if not isinstance(year_data, Mapping):
            raise ValueError(f"{what} for {currency} must map years to values")
        if not year_data:
            raise ValueError(f"{what} for {currency} must contain at least one year")
        values = {}
        for year, value in year_data.items():
            where = f"{what} for {currency}"
            year = _year(year, where)
            if not is_number(value) or not math.isfinite(value) or not valid(value):
                raise ValueError(f"{where} in {year} {requirement}, got {value!r}")
            values[year] = float(value)
        series[currency] = values
    return series


def merge_annual_series(current: Dict[str, Dict[int, float]], new, what: str, conflicts: List[str]) -> dict:
    """Copy of ``current`` with ``new`` merged in; differing existing values are reported in ``conflicts``."""
    merged = {currency: dict(years) for currency, years in current.items()}
    for currency, years in new.items():
        target = merged.setdefault(currency, {})
        for year, value in years.items():
            if year in target and not math.isclose(target[year], value, rel_tol=1e-12):
                conflicts.append(f"{what} {currency} {year}: {target[year]!r} -> {value!r}")
            target[year] = value
    return merged
