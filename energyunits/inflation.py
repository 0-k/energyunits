"""Inflation adjustment utilities for cost quantities."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
        self._load_defaults()

    def _load_defaults(self) -> None:
        self._inflation_data: Dict[str, Dict[int, float]] = {}
        self._projected_from: Dict[str, int] = {}
        with open(_DATA_DIR / "inflation.json", encoding="utf-8") as f:
            self._ingest(json.load(f))

    def reset(self) -> None:
        """Discard custom data and reload the bundled defaults."""
        self._load_defaults()

    def load_inflation(self, file_path: str) -> None:
        """Load custom inflation rates from a JSON file.

        Format: ``{"USD": {"2031": 2.1, ...}, ...}``. An optional
        ``"_metadata": {"projected_from": {"USD": 2031}}`` entry marks the first
        projected (non-historical) year per currency.
        """
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        self._ingest(data)

    def _ingest(self, data: dict) -> None:
        for currency, year_data in data.items():
            if currency.startswith("_"):
                continue
            rates = self._inflation_data.setdefault(currency, {})
            rates.update({int(year): float(rate) for year, rate in year_data.items()})
        metadata = data.get("_metadata", {})
        for currency, year in metadata.get("projected_from", {}).items():
            self._projected_from[currency] = int(year)

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
