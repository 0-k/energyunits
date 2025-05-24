"""
Inflation adjustment utilities for cost quantities.

This module provides inflation rate data and utilities for adjusting cost quantities
across different reference years using historical and projected inflation rates.
"""

import json
from typing import Dict, List, Optional, Tuple


class InflationRegistry:
    """
    Registry for inflation data with cached historical rates.

    Provides inflation adjustment capabilities for cost quantities using
    historical Consumer Price Index (CPI) data and projections for major currencies.

    Attributes:
        _inflation_data: Dictionary mapping currency codes to year-rate mappings
    """

    def __init__(self) -> None:
        """Initialize the inflation registry with default currency data."""
        self._inflation_data: Dict[str, Dict[int, float]] = {}
        self._load_default_data()

    def _load_default_data(self) -> None:
        """
        Load default inflation data for major currencies.

        Loads historical CPI-based inflation rates for USD and EUR,
        including actual rates through 2023 and projections through 2030.
        Sources: OECD, Federal Reserve, European Central Bank.
        """
        # CPI-based inflation rates (annual percentage changes)
        # Sources: OECD, Federal Reserve, European Central Bank
        self._inflation_data = {
            "USD": {
                2010: 1.50,  # Historical
                2011: 3.10,  # Historical
                2012: 2.07,  # Historical
                2013: 1.46,  # Historical
                2014: 0.12,  # Historical
                2015: 0.12,  # Historical
                2016: 1.26,  # Historical
                2017: 2.13,  # Historical
                2018: 2.44,  # Historical
                2019: 1.81,  # Historical
                2020: 1.23,  # 2020 actual
                2021: 4.70,  # 2021 actual
                2022: 8.00,  # 2022 actual
                2023: 4.12,  # 2023 actual
                2024: 3.15,  # 2024 estimated
                2025: 2.50,  # 2025 projected
                2026: 2.30,  # 2026 projected
                2027: 2.20,  # 2027 projected
                2028: 2.10,  # 2028 projected
                2029: 2.00,  # 2029 projected
                2030: 2.00,  # 2030 projected
            },
            "EUR": {
                2010: 1.60,  # Historical
                2011: 2.70,  # Historical
                2012: 2.50,  # Historical
                2013: 1.40,  # Historical
                2014: 0.40,  # Historical
                2015: 0.00,  # Historical
                2016: 0.20,  # Historical
                2017: 1.50,  # Historical
                2018: 1.80,  # Historical
                2019: 1.20,  # Historical
                2020: 0.30,  # 2020 actual
                2021: 2.60,  # 2021 actual
                2022: 8.40,  # 2022 actual
                2023: 5.40,  # 2023 actual
                2024: 2.80,  # 2024 estimated
                2025: 2.20,  # 2025 projected
                2026: 2.10,  # 2026 projected
                2027: 2.00,  # 2027 projected
                2028: 2.00,  # 2028 projected
                2029: 2.00,  # 2029 projected
                2030: 2.00,  # 2030 projected
            },
        }

    def get_cumulative_inflation_factor(
        self, currency: str, from_year: int, to_year: int
    ) -> float:
        """
        Calculate cumulative inflation factor between two years.

        Args:
            currency: Currency code (e.g., "USD", "EUR")
            from_year: Starting year
            to_year: Target year

        Returns:
            Cumulative inflation factor to multiply base year values

        Raises:
            ValueError: If currency not supported or years out of range
        """
        if currency not in self._inflation_data:
            raise ValueError(
                f"Currency '{currency}' not supported. Available: {list(self._inflation_data.keys())}"
            )

        currency_data = self._inflation_data[currency]

        if from_year == to_year:
            return 1.0

        # Determine direction of conversion
        if from_year > to_year:
            # Deflating - going backwards in time
            years_range = range(to_year + 1, from_year + 1)
            factor = 1.0
            for year in years_range:
                if year not in currency_data:
                    raise ValueError(f"No inflation data for {currency} in year {year}")
                annual_rate = (
                    currency_data[year] / 100.0
                )  # Convert percentage to decimal
                factor /= 1.0 + annual_rate  # Deflate
            return factor
        else:
            # Inflating - going forwards in time
            years_range = range(from_year + 1, to_year + 1)
            factor = 1.0
            for year in years_range:
                if year not in currency_data:
                    raise ValueError(f"No inflation data for {currency} in year {year}")
                annual_rate = (
                    currency_data[year] / 100.0
                )  # Convert percentage to decimal
                factor *= 1.0 + annual_rate  # Inflate
            return factor

    def get_available_years(self, currency: str) -> Tuple[int, int]:
        """
        Get the range of available years for a currency.

        Args:
            currency: Currency code (e.g., "USD", "EUR")

        Returns:
            Tuple of (min_year, max_year) for available data

        Raises:
            ValueError: If currency not supported
        """
        if currency not in self._inflation_data:
            raise ValueError(f"Currency '{currency}' not supported")

        years = list(self._inflation_data[currency].keys())
        return min(years), max(years)

    def get_supported_currencies(self) -> List[str]:
        """
        Get list of supported currencies.

        Returns:
            List of supported currency codes
        """
        return list(self._inflation_data.keys())

    def detect_currency_from_unit(self, unit: str) -> Optional[str]:
        """
        Attempt to detect currency from unit string.

        Args:
            unit: Unit string (e.g., "USD/kW", "EUR/MWh", "$/t")

        Returns:
            Currency code if detected, None otherwise
        """
        unit_upper = unit.upper()

        # Direct currency codes
        for currency in self._inflation_data:
            if currency in unit_upper:
                return currency

        # Dollar sign handling
        if "$" in unit or "DOLLAR" in unit_upper:
            return "USD"

        return None

    def load_custom_data(self, file_path: str) -> None:
        """
        Load custom inflation data from JSON file.

        Args:
            file_path: Path to JSON file containing inflation data
                      Format: {"currency": {"year": rate, ...}, ...}

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        with open(file_path, "r") as f:
            custom_data = json.load(f)

        for currency, year_data in custom_data.items():
            if currency not in self._inflation_data:
                self._inflation_data[currency] = {}
            self._inflation_data[currency].update(year_data)


# Global inflation registry instance
inflation_registry = InflationRegistry()
