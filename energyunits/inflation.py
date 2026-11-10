"""Inflation adjustment utilities for cost quantities."""

import json
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import List, Optional, Tuple

from ._loading import (  # noqa: F401  (re-exported for backwards compatibility)
    DataSource,
    _currency_from_string,
    _year,
    merge_annual_series,
    parse_annual_series,
    raise_conflicts,
    read_source,
)
from .exceptions import MissingDataError

_DATA_DIR = Path(__file__).parent / "data"


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
        """First and last reference year that can be converted for a currency.

        Raises:
            MissingDataError: if there is no inflation data for the currency.
        """
        years = sorted(self._inflation_data.get(currency, ()))
        if not years:
            raise MissingDataError(f"No inflation data for currency '{currency}'")
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
