"""Exchange rate utilities for currency conversions with year-dependent rates."""

import json
import warnings
from pathlib import Path
from typing import Optional


class ExchangeRateRegistry:
    """Registry for historical exchange rate data.

    Provides year-dependent exchange rates for currency conversions.
    All rates are expressed as: 1 unit of currency = X USD.
    """

    def __init__(self):
        self._exchange_rate_data = {}
        self._load_defaults()

    def _load_defaults(self):
        """Load default exchange rate data from JSON."""
        data_path = Path(__file__).parent / "data" / "exchange_rates.json"
        with open(data_path) as f:
            data = json.load(f)

        # Convert string years to integers, skip metadata fields
        self._exchange_rate_data = {
            currency: {int(year): rate for year, rate in years.items()}
            for currency, years in data.items()
            if not currency.startswith("_")
        }

        # USD is always 1.0 for any year (base currency)
        self._exchange_rate_data["USD"] = {}

    def load_exchange_rates(self, file_path: str):
        """Load custom exchange rate data from JSON file."""
        with open(file_path) as f:
            data = json.load(f)

        for currency, year_data in data.items():
            # Skip metadata fields
            if currency.startswith("_"):
                continue

            if currency not in self._exchange_rate_data:
                self._exchange_rate_data[currency] = {}

            # Convert string years to integers
            self._exchange_rate_data[currency].update(
                {int(year): rate for year, rate in year_data.items()}
            )

    def get_exchange_rate(self, currency: str, year: Optional[int] = None) -> float:
        """Get exchange rate for a currency in a specific year.

        Args:
            currency: Currency code (EUR, GBP, JPY, CNY)
            year: Year for exchange rate. If None, uses most recent available.

        Returns:
            Exchange rate (1 currency unit = X USD)

        Raises:
            ValueError: If currency not supported or year not available
        """
        if currency == "USD":
            return 1.0

        if currency not in self._exchange_rate_data:
            raise ValueError(
                f"Currency '{currency}' not supported for historical exchange rates. "
                f"Supported: {self.get_supported_currencies()}"
            )

        currency_data = self._exchange_rate_data[currency]

        if year is None:
            # Use most recent year available
            year = max(currency_data.keys())

        if year not in currency_data:
            available_years = sorted(currency_data.keys())
            raise ValueError(
                f"No exchange rate data for {currency} in year {year}. "
                f"Available years: {available_years[0]}-{available_years[-1]}"
            )

        return currency_data[year]

    def convert_currency(
        self,
        value: float,
        from_currency: str,
        to_currency: str,
        year: Optional[int] = None
    ) -> float:
        """Convert amount from one currency to another using rates from a specific year.

        Args:
            value: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            year: Year for exchange rate. If None, uses most recent available.

        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return value

        # Convert to USD as intermediate
        from_rate = self.get_exchange_rate(from_currency, year)
        to_rate = self.get_exchange_rate(to_currency, year)

        # value * (from_rate USD/from_currency) / (to_rate USD/to_currency)
        return value * from_rate / to_rate

    def get_conversion_factor(
        self,
        from_currency: str,
        to_currency: str,
        year: Optional[int] = None
    ) -> float:
        """Get conversion factor between two currencies for a specific year.

        Returns the factor such that: amount_to = amount_from * factor
        """
        return self.convert_currency(1.0, from_currency, to_currency, year)

    def get_supported_currencies(self):
        """Get list of supported currencies."""
        return ["USD"] + list(self._exchange_rate_data.keys())

    def detect_currency_from_unit(self, unit: str) -> Optional[str]:
        """Detect currency from unit string.

        Args:
            unit: Unit string (e.g., "USD", "EUR/MWh", "USD/kW")

        Returns:
            Currency code if detected, None otherwise
        """
        unit_upper = unit.upper()

        # Check for explicit currency codes
        for currency in self.get_supported_currencies():
            if currency in unit_upper:
                return currency

        # Check for $ symbol
        if "$" in unit or "DOLLAR" in unit_upper:
            return "USD"

        return None

    def is_currency(self, unit: str) -> bool:
        """Check if a unit is a pure currency (not compound like USD/MWh)."""
        return unit in self.get_supported_currencies()

    def warn_currency_inflation_combination(self):
        """Issue warning about currency conversion + inflation adjustment path dependency."""
        warnings.warn(
            "Combining currency conversion with inflation adjustment involves economic assumptions. "
            "This library uses the convention: INFLATE FIRST (in original currency), THEN CONVERT (using target year exchange rate). "
            "Example: 50 EUR (2015) → 2024 USD inflates EUR to 2024, then converts using 2024 EUR/USD rate. "
            "This approximates purchasing power parity but may not reflect actual financial returns. "
            "For precise financial analysis, use dedicated economic/forex tools.",
            UserWarning,
            stacklevel=3
        )


exchange_rate_registry = ExchangeRateRegistry()
