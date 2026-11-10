"""Exchange rate utilities for currency conversions with year-dependent rates."""

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

from ._loading import (
    DataSource,
    _currency_from_string,
    merge_annual_series,
    parse_annual_series,
    raise_conflicts,
    read_source,
)
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
        self._lock = threading.RLock()
        self._load_defaults()

    def _load_defaults(self) -> None:
        with open(_DATA_DIR / "exchange_rates.json", encoding="utf-8") as f:
            self._ingest(json.load(f), overwrite=False, replace_all=True)

    def reset(self) -> None:
        """Discard custom data and reload the bundled defaults.

        This affects every user of the registry in the process; it is meant for
        scripts and tests, not for libraries.
        """
        self._load_defaults()

    def load_exchange_rates(self, source: DataSource, overwrite: bool = False) -> None:
        """Load custom exchange rates (USD per unit) from a JSON file or a mapping.

        Format: ``{"AUD": {"2020": 0.69, ...}, ...}``. Entries for USD are ignored.
        New currencies and years are added; replacing a bundled rate needs
        ``overwrite=True``. A new currency also needs a currency unit (see
        :meth:`UnitRegistry.load_units`).

        Raises:
            DefinitionConflictError: if a rate differs from existing data.
            ValueError: if the data is malformed (nothing is loaded).
        """
        self._ingest(read_source(source), overwrite=overwrite)

    def _ingest(self, data: dict, overwrite: bool, replace_all: bool = False) -> None:
        data = {currency: years for currency, years in data.items() if currency != "USD"}
        rates = parse_annual_series(
            data, "Exchange rate", lambda rate: rate > 0, "must be positive (USD per unit)"
        )
        with self._lock:
            conflicts: List[str] = []
            current = {"USD": {}} if replace_all else self._exchange_rate_data
            merged = merge_annual_series(current, rates, "exchange rate", conflicts)
            if not overwrite:
                raise_conflicts("exchange rates", conflicts)
            self._exchange_rate_data = merged

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

    def get_conversion_factor(
        self, from_currency: str, to_currency: str, year: Optional[int] = None
    ) -> float:
        """Factor such that ``amount_to = amount_from * factor``."""
        return self.convert_currency(1.0, from_currency, to_currency, year)

    def unit_correction_factor(self, from_unit: str, to_unit: str, year: Optional[int] = None) -> float:
        """Correction applied on top of the static registry factor for a currency change.

        The unit registry converts currencies with static (most recent) rates.
        For every currency whose exponent differs between the two units this
        multiplies by ``(year_rate / static_rate) ** exponent``, so the combined
        factor uses the exchange rates of ``year`` (also for units with several
        currencies such as ``EUR/kUSD``). Currencies without year-dependent data
        keep their static rate. Returns 1.0 when no currency changes.
        """
        from .registry import registry

        exponents: Dict[str, int] = {}
        for _, code, exp in registry.currency_terms(from_unit):
            exponents[code] = exponents.get(code, 0) + exp
        for _, code, exp in registry.currency_terms(to_unit):
            exponents[code] = exponents.get(code, 0) - exp
        correction = 1.0
        for code, exp in exponents.items():
            if exp == 0 or code == "USD" or not self.has_currency(code) or not registry.has_unit(code):
                continue
            static = registry.get_conversion_factor(code, "USD")
            correction *= (self.get_exchange_rate(code, year) / static) ** exp
        return correction

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
