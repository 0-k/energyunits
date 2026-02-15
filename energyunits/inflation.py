"""Inflation adjustment utilities for cost quantities."""

import json
from pathlib import Path
from typing import Optional


class InflationRegistry:
    """Registry for inflation data with historical rates."""

    def __init__(self):
        self._inflation_data = {}
        self._load_defaults()

    def _load_defaults(self):
        """Load default inflation data from JSON."""
        data_path = Path(__file__).parent / "data" / "inflation.json"
        with open(data_path) as f:
            data = json.load(f)

        # Convert string years to integers, skip metadata fields
        self._inflation_data = {
            currency: {int(year): rate for year, rate in years.items()}
            for currency, years in data.items()
            if not currency.startswith("_")
        }

    def load_inflation(self, file_path: str):
        """Load custom inflation data from JSON file."""
        with open(file_path) as f:
            data = json.load(f)

        for currency, year_data in data.items():
            # Skip metadata fields
            if currency.startswith("_"):
                continue

            if currency not in self._inflation_data:
                self._inflation_data[currency] = {}

            # Convert string years to integers
            self._inflation_data[currency].update(
                {int(year): rate for year, rate in year_data.items()}
            )

    def get_cumulative_inflation_factor(
        self, currency: str, from_year: int, to_year: int
    ) -> float:
        """Calculate cumulative inflation factor between two years."""
        if currency not in self._inflation_data:
            raise ValueError(f"Currency '{currency}' not supported")

        currency_data = self._inflation_data[currency]

        if from_year == to_year:
            return 1.0

        if from_year > to_year:
            # Deflating
            years_range = range(to_year + 1, from_year + 1)
            factor = 1.0
            for year in years_range:
                if year not in currency_data:
                    raise ValueError(f"No inflation data for {currency} in year {year}")
                factor /= 1.0 + (currency_data[year] / 100.0)
            return factor
        else:
            # Inflating
            years_range = range(from_year + 1, to_year + 1)
            factor = 1.0
            for year in years_range:
                if year not in currency_data:
                    raise ValueError(f"No inflation data for {currency} in year {year}")
                factor *= 1.0 + (currency_data[year] / 100.0)
            return factor

    def get_supported_currencies(self):
        """Get list of supported currencies."""
        return list(self._inflation_data.keys())

    def detect_currency_from_unit(self, unit: str) -> Optional[str]:
        """Detect currency from unit string."""
        # Split compound units into components for exact matching
        components = unit.upper().replace("/", " ").split()

        for currency in self._inflation_data:
            if currency in components:
                return currency

        if "$" in unit or "DOLLAR" in unit.upper():
            return "USD"

        return None


inflation_registry = InflationRegistry()
