"""Exchange rate utilities for currency conversions with year-dependent rates."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from ._warnings import warn
from .exceptions import MissingDataError

_DATA_DIR = Path(__file__).parent / "data"


class ExchangeRateRegistry:
    """Registry of historical annual average exchange rates.

    All rates are expressed as: 1 unit of currency = X USD.

    A module-level instance is available as
    :data:`energyunits.exchange_rate.exchange_rate_registry`.
    """

    def __init__(self) -> None:
        self._load_defaults()

    def _load_defaults(self) -> None:
        self._exchange_rate_data: Dict[str, Dict[int, float]] = {"USD": {}}
        with open(_DATA_DIR / "exchange_rates.json", encoding="utf-8") as f:
            self._ingest(json.load(f))

    def reset(self) -> None:
        """Discard custom data and reload the bundled defaults."""
        self._load_defaults()

    def load_exchange_rates(self, file_path: str) -> None:
        """Load custom exchange rates (USD per unit) from a JSON file.

        Format: ``{"AUD": {"2020": 0.69, ...}, ...}``.
        """
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        self._ingest(data)

    def _ingest(self, data: dict) -> None:
        for currency, year_data in data.items():
            if currency.startswith("_") or currency == "USD":
                continue
            rates = self._exchange_rate_data.setdefault(currency, {})
            for year, rate in year_data.items():
                rate = float(rate)
                if rate <= 0:
                    raise ValueError(f"Exchange rate for {currency} in {year} must be positive")
                rates[int(year)] = rate

    def has_currency(self, currency: str) -> bool:
        """True if year-dependent rates are available for ``currency``."""
        return currency == "USD" or bool(self._exchange_rate_data.get(currency))

    def get_exchange_rate(self, currency: str, year: Optional[int] = None) -> float:
        """Exchange rate of a currency (USD per unit) in a given year.

        Args:
            currency: Currency code (e.g. ``"EUR"``).
            year: Year of the annual average rate. ``None`` uses the most recent
                year available. Years after the most recent available year use
                the most recent rate and emit a warning.

        Raises:
            MissingDataError: if the currency is not supported or the year is
                before the first available year.
        """
        if currency == "USD":
            return 1.0
        rates = self._exchange_rate_data.get(currency)
        if not rates:
            raise MissingDataError(
                f"Currency '{currency}' not supported for historical exchange rates. "
                f"Supported: {self.get_supported_currencies()}"
            )
        first, last = min(rates), max(rates)
        if year is None:
            return rates[last]
        year = int(year)
        if year in rates:
            return rates[year]
        if year > last:
            warn(
                f"No exchange rate data for {currency} in year {year}; using the {last} rate "
                f"(most recent available)."
            )
            return rates[last]
        raise MissingDataError(
            f"No exchange rate data for {currency} in year {year}. Available years: {first}-{last}"
        )

    def convert_currency(
        self,
        value: float,
        from_currency: str,
        to_currency: str,
        year: Optional[int] = None,
    ) -> float:
        """Convert an amount between currencies using the rates of one year."""
        if from_currency == to_currency:
            return value
        from_rate = self.get_exchange_rate(from_currency, year)
        to_rate = self.get_exchange_rate(to_currency, year)
        return value * from_rate / to_rate

    def get_conversion_factor(self, from_currency: str, to_currency: str, year: Optional[int] = None) -> float:
        """Factor such that ``amount_to = amount_from * factor``."""
        return self.convert_currency(1.0, from_currency, to_currency, year)

    def unit_correction_factor(self, from_unit: str, to_unit: str, year: Optional[int] = None) -> float:
        """Correction applied on top of the static registry factor for a currency change.

        The unit registry converts currencies with static (most recent) rates.
        This returns ``(year_rate / static_rate) ** exponent`` for a conversion
        between units that contain one currency each, so that the combined
        factor uses the exchange rate of ``year``. Returns 1.0 when no currency
        change is involved or no year-dependent data is available.
        """
        from .registry import registry

        source = registry.currency_terms(from_unit)
        target = registry.currency_terms(to_unit)
        if len(source) != 1 or len(target) != 1:
            return 1.0
        (_, source_code, source_exp), (_, target_code, target_exp) = source[0], target[0]
        if source_code == target_code or source_exp != target_exp:
            return 1.0
        if not (self.has_currency(source_code) and self.has_currency(target_code)):
            return 1.0
        if not (registry.has_unit(source_code) and registry.has_unit(target_code)):
            return 1.0
        static = registry.get_conversion_factor(source_code, target_code)
        dynamic = self.get_conversion_factor(source_code, target_code, year)
        return (dynamic / static) ** source_exp

    def get_supported_currencies(self) -> List[str]:
        """Currencies with exchange rate data (always includes USD)."""
        return sorted(code for code in self._exchange_rate_data if self.has_currency(code))

    def get_available_years(self, currency: str) -> Optional[tuple]:
        """First and last year with data for ``currency`` (``None`` for USD)."""
        rates = self._exchange_rate_data.get(currency)
        if not rates:
            return None
        return min(rates), max(rates)

    def detect_currency_from_unit(self, unit: str) -> Optional[str]:
        """Detect the currency code contained in a unit string (e.g. ``"EUR/MWh"`` -> ``"EUR"``)."""
        from .inflation import _currency_from_string
        from .registry import registry

        try:
            terms = registry.currency_terms(unit)
        except (TypeError, ValueError):
            return _currency_from_string(unit, self.get_supported_currencies())
        return terms[0][1] if terms else None

    def is_currency(self, unit: str) -> bool:
        """True if ``unit`` is a pure currency unit (not compound like ``USD/MWh``)."""
        from .registry import registry

        try:
            terms = registry.parse_unit(unit)
        except (TypeError, ValueError):
            return False
        return len(terms) == 1 and terms[0][1] == 1 and registry.currency_of(terms[0][0]) is not None

    def warn_currency_inflation_combination(self) -> None:
        """Warn about the convention used when combining currency and inflation conversions."""
        warn(
            "Combining currency conversion with inflation adjustment involves economic assumptions. "
            "This library uses the convention: INFLATE FIRST (in original currency), THEN CONVERT "
            "(using target year exchange rate). Example: 50 EUR (2015) -> 2024 USD inflates EUR to 2024, "
            "then converts using the 2024 EUR/USD rate. This approximates purchasing power parity but "
            "may not reflect actual financial returns."
        )


exchange_rate_registry = ExchangeRateRegistry()
