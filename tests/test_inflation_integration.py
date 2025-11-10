"""
Tests for inflation adjustment integration in unified .to() method.
"""

import numpy as np
import pytest

from energyunits import Quantity
from energyunits.inflation import inflation_registry


class TestInflationIntegration:
    """Test inflation adjustment through the unified .to() method."""

    def test_basic_inflation_adjustment(self):
        """Test basic inflation adjustment from 2020 to 2025."""
        capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
        capex_2025 = capex_2020.to(reference_year=2025)

        # Should be inflated from 2020 to 2025
        assert capex_2025.reference_year == 2025
        assert capex_2025.value > 1000  # Should be higher due to inflation
        assert capex_2025.unit == "USD/kW"
        assert capex_2025.substance == capex_2020.substance
        assert capex_2025.basis == capex_2020.basis

    def test_deflation_adjustment(self):
        """Test deflation (going backwards in time)."""
        capex_2025 = Quantity(1200, "EUR/MW", reference_year=2025)
        capex_2020 = capex_2025.to(reference_year=2020)

        # Should be deflated from 2025 to 2020
        assert capex_2020.reference_year == 2020
        assert capex_2020.value < 1200  # Should be lower due to deflation
        assert capex_2020.unit == "EUR/MW"

    def test_same_year_no_change(self):
        """Test that same year conversion returns identical value."""
        capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
        capex_2020_again = capex_2020.to(reference_year=2020)

        assert capex_2020_again.value == 1000
        assert capex_2020_again.reference_year == 2020

    def test_currency_detection(self):
        """Test automatic currency detection from various unit formats."""
        test_cases = [
            ("USD/kW", "USD"),
            ("EUR/MWh", "EUR"),
            ("$/t", "USD"),
            ("€/kg", None),  # Euro symbol not supported yet
        ]

        for unit, expected_currency in test_cases:
            detected = inflation_registry.detect_currency_from_unit(unit)
            assert detected == expected_currency

    def test_combined_conversions(self):
        """Test inflation adjustment combined with unit conversion."""
        capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
        capex_2025_mw = capex_2020.to("USD/MW", reference_year=2025)

        # Should convert both unit and apply inflation
        assert capex_2025_mw.unit == "USD/MW"
        assert capex_2025_mw.reference_year == 2025
        assert (
            capex_2025_mw.value > 1000000
        )  # USD/MW is 1000x larger than USD/kW, plus inflation

    def test_error_handling(self):
        """Test error cases for inflation adjustment."""
        # No reference year specified
        quantity_no_year = Quantity(1000, "USD/kW")
        with pytest.raises(ValueError, match="Reference year not specified"):
            quantity_no_year.to(reference_year=2025)

        # Unsupported currency
        quantity_unsupported = Quantity(1000, "JPY/kW", reference_year=2020)
        with pytest.raises(ValueError, match="Cannot detect currency"):
            quantity_unsupported.to(reference_year=2025)

    def test_array_values(self):
        """Test inflation adjustment with array values."""
        values = np.array([1000, 1500, 2000])
        capex_2020 = Quantity(values, "USD/kW", reference_year=2020)
        capex_2025 = capex_2020.to(reference_year=2025)

        assert isinstance(capex_2025.value, np.ndarray)
        assert len(capex_2025.value) == 3
        assert np.all(capex_2025.value > values)  # All should be inflated

    def test_inflation_method_consistency(self):
        """Test that inflation adjustment is consistent."""
        capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)

        # Test the unified .to() method
        result = capex_2020.to(reference_year=2025)

        assert result.value > 1000  # Should be inflated
        assert result.reference_year == 2025
        assert result.unit == "USD/kW"


class TestInflationRegistry:
    """Test the inflation registry functionality."""

    def test_get_cumulative_factor_forward(self):
        """Test forward inflation calculation."""
        # USD from 2020 to 2021: 1.23% to 4.70%
        factor = inflation_registry.get_cumulative_inflation_factor("USD", 2020, 2021)
        expected = 1.047  # 4.7% inflation in 2021
        assert abs(factor - expected) < 0.001

    def test_get_cumulative_factor_backward(self):
        """Test backward (deflation) calculation."""
        factor = inflation_registry.get_cumulative_inflation_factor("USD", 2021, 2020)
        expected = 1.0 / 1.047  # Inverse of 4.7% inflation
        assert abs(factor - expected) < 0.001

    def test_get_cumulative_factor_same_year(self):
        """Test same year returns 1.0."""
        factor = inflation_registry.get_cumulative_inflation_factor("USD", 2020, 2020)
        assert factor == 1.0

    def test_multi_year_calculation(self):
        """Test calculation across multiple years."""
        # USD 2020 to 2022: 1.23% -> 4.70% -> 8.00%
        factor = inflation_registry.get_cumulative_inflation_factor("USD", 2020, 2022)
        expected = 1.047 * 1.08  # Compound 2021 and 2022 rates
        assert abs(factor - expected) < 0.001

    def test_unsupported_currency(self):
        """Test error for unsupported currency."""
        with pytest.raises(ValueError, match="Currency 'JPY' not supported"):
            inflation_registry.get_cumulative_inflation_factor("JPY", 2020, 2021)

    def test_year_out_of_range(self):
        """Test error for year out of range."""
        with pytest.raises(ValueError, match="No inflation data"):
            inflation_registry.get_cumulative_inflation_factor("USD", 2020, 2050)

    def test_get_supported_currencies(self):
        """Test getting supported currencies."""
        currencies = inflation_registry.get_supported_currencies()
        assert "USD" in currencies
        assert "EUR" in currencies

