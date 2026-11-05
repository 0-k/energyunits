"""Inflation adjustment utilities for cost quantities."""

import json
import math
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ._loading import DataSource, is_number, raise_conflicts, read_source
from .exceptions import MissingDataError

_DATA_DIR = Path(__file__).parent / "data"


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
        if isinstance(currency, str) and currency.startswith("_"):
            continue
        if not isinstance(currency, str) or not currency or currency != currency.strip():
            raise ValueError(f"Invalid currency code {currency!r} in {what}")
        if not isinstance(year_data, Mapping):
            raise ValueError(f"{what} for {currency} must map years to values")
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


class InflationRegistry:
    """Registry of annual consumer price inflation rates per currency.

    The rate stored for year ``Y`` is the change of the annual average price
    index from ``Y - 1`` to ``Y`` in percent. Converting a value from
    ``reference_year=2015`` to ``2024`` therefore multiplies by
    ``prod(1 + rate[Y] / 100 for Y in 2016..2024)``.

    A module-level instance is available as
    :data:`energyunits.inflation.inflation_registry`.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._load_defaults()

    def _load_defaults(self) -> None:
        with open(_DATA_DIR / "inflation.json", encoding="utf-8") as f:
            self._ingest(json.load(f), overwrite=False, replace_all=True)

    def reset(self) -> None:
        """Discard custom data and reload the bundled defaults.

        This affects every user of the registry in the process; it is meant for
        scripts and tests, not for libraries.
        """
        self._load_defaults()

    def load_inflation(self, source: DataSource, overwrite: bool = False) -> None:
        """Load custom inflation rates from a JSON file or a mapping.

        Format: ``{"USD": {"2031": 2.1, ...}, ...}`` (percent per year). An optional
        ``"_metadata": {"projected_from": {"USD": 2031}}`` entry marks the first
        projected (non-historical) year per currency; omit it when only adding
        years to a bundled currency.

        New currencies and years are added. Replacing a bundled value (for
        example a projected year with an actual rate) needs ``overwrite=True``.

        Raises:
            DefinitionConflictError: if a rate or ``projected_from`` year differs from existing data.
            ValueError: if the data is malformed (nothing is loaded).
        """
        self._ingest(read_source(source), overwrite=overwrite)

    def _ingest(self, data: dict, overwrite: bool, replace_all: bool = False) -> None:
        rates = parse_annual_series(data, "Inflation rate", lambda rate: rate > -100, "must be above -100 %")
        metadata = data.get("_metadata", {})
        projected = metadata.get("projected_from", {}) if isinstance(metadata, Mapping) else None
        if not isinstance(projected, Mapping):
            raise ValueError("_metadata.projected_from must map currencies to years")
        projected = {currency: _year(year, "projected_from") for currency, year in projected.items()}
        with self._lock:
            conflicts: List[str] = []
            current = {} if replace_all else self._inflation_data
            merged = merge_annual_series(current, rates, "inflation rate", conflicts)
            projected_from = {} if replace_all else dict(self._projected_from)
            for currency, year in projected.items():
                if currency in projected_from and projected_from[currency] != year:
                    conflicts.append(f"projected_from {currency}: {projected_from[currency]} -> {year}")
                projected_from[currency] = year
            if not overwrite:
                raise_conflicts("inflation data", conflicts)
            self._inflation_data, self._projected_from = merged, projected_from

    def get_cumulative_inflation_factor(self, currency: str, from_year: int, to_year: int) -> float:
        """Cumulative price change factor from ``from_year`` to ``to_year``.

        Raises:
            MissingDataError: if the currency or a required year is not available.
        """
        if currency not in self._inflation_data:
            raise MissingDataError(
                f"Currency '{currency}' not supported for inflation adjustment. "
                f"Supported: {self.get_supported_currencies()}"
            )
        if from_year == to_year:
            return 1.0
        rates = self._inflation_data[currency]
        start, end = sorted((int(from_year), int(to_year)))
        factor = 1.0
        for year in range(start + 1, end + 1):
            if year not in rates:
                first, last = self.get_available_years(currency)
                raise MissingDataError(
                    f"No inflation data for {currency} in year {year} "
                    f"(reference years {first}-{last} are supported)."
                )
            factor *= 1.0 + rates[year] / 100.0
        return factor if to_year > from_year else 1.0 / factor

    def get_available_years(self, currency: str) -> Tuple[int, int]:
        """First and last reference year that can be converted for a currency."""
        years = sorted(self._inflation_data[currency])
        return years[0] - 1, years[-1]

    def uses_projection(self, currency: str, from_year: int, to_year: int) -> bool:
        """True if converting between the two years relies on projected rates."""
        first_projected = self._projected_from.get(currency)
        if first_projected is None or from_year == to_year:
            return False
        return max(from_year, to_year) >= first_projected

    def get_projected_from(self, currency: str) -> Optional[int]:
        """First year for which the rate of ``currency`` is a projection (or ``None``)."""
        return self._projected_from.get(currency)

    def get_supported_currencies(self) -> List[str]:
        """Currencies with inflation data."""
        return list(self._inflation_data)

    def detect_currency_from_unit(self, unit: str) -> Optional[str]:
        """Detect the currency (with inflation data) contained in a unit string."""
        from .registry import registry

        try:
            terms = registry.currency_terms(unit)
        except (TypeError, ValueError):
            return _currency_from_string(unit, self._inflation_data)
        for _, code, _ in terms:
            if code in self._inflation_data:
                return code
        return None


inflation_registry = InflationRegistry()
