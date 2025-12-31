"""Tests for year-dependent currency conversions."""

import warnings
import pytest
from energyunits import Quantity
from energyunits.exchange_rate import exchange_rate_registry


class TestYearDependentExchangeRates:
    """Test exchange rate registry functionality."""

    def test_get_exchange_rate_for_specific_year(self):
        """Test getting exchange rate for a specific year."""
        # EUR was stronger in 2010 vs 2023
        rate_2010 = exchange_rate_registry.get_exchange_rate("EUR", 2010)
        rate_2023 = exchange_rate_registry.get_exchange_rate("EUR", 2023)

        assert rate_2010 == pytest.approx(1.3257, rel=1e-4)
        assert rate_2023 == pytest.approx(1.0813, rel=1e-4)
        assert rate_2010 > rate_2023  # EUR was stronger in 2010

    def test_brexit_impact_on_gbp(self):
        """Test that Brexit (2016) shows in GBP rates."""
        rate_2015 = exchange_rate_registry.get_exchange_rate("GBP", 2015)
        rate_2017 = exchange_rate_registry.get_exchange_rate("GBP", 2017)

        # GBP dropped significantly after Brexit referendum
        assert rate_2015 > rate_2017
        assert rate_2015 == pytest.approx(1.5286, rel=1e-4)
        assert rate_2017 == pytest.approx(1.2886, rel=1e-4)

    def test_jpy_depreciation(self):
        """Test JPY depreciation in recent years."""
        rate_2020 = exchange_rate_registry.get_exchange_rate("JPY", 2020)
        rate_2024 = exchange_rate_registry.get_exchange_rate("JPY", 2024)

        # JPY weakened significantly 2020-2024
        assert rate_2020 > rate_2024

    def test_usd_always_one(self):
        """Test USD is always 1.0 (base currency)."""
        assert exchange_rate_registry.get_exchange_rate("USD", 2010) == 1.0
        assert exchange_rate_registry.get_exchange_rate("USD", 2024) == 1.0
        assert exchange_rate_registry.get_exchange_rate("USD", None) == 1.0

    def test_missing_year_error(self):
        """Test error when requesting unavailable year."""
        with pytest.raises(ValueError, match="No exchange rate data for EUR in year 2009"):
            exchange_rate_registry.get_exchange_rate("EUR", 2009)

    def test_unsupported_currency_error(self):
        """Test error for unsupported currency."""
        with pytest.raises(ValueError, match="Currency 'AUD' not supported"):
            exchange_rate_registry.get_exchange_rate("AUD", 2020)

    def test_default_to_most_recent_year(self):
        """Test that None year defaults to most recent."""
        rate_none = exchange_rate_registry.get_exchange_rate("EUR", None)
        rate_2025 = exchange_rate_registry.get_exchange_rate("EUR", 2025)

        assert rate_none == rate_2025


class TestCurrencyConversionWithoutInflation:
    """Test pure currency conversions (no inflation adjustment)."""

    def test_simple_currency_conversion_eur_to_usd(self):
        """Test EUR to USD conversion without year specified."""
        cost_eur = Quantity(100, "EUR")
        cost_usd = cost_eur.to("USD")

        # Should use most recent rate (2025: 1.08)
        assert cost_usd.value == pytest.approx(100 * 1.08, rel=1e-2)
        assert cost_usd.unit == "USD"

    def test_currency_conversion_with_explicit_year(self):
        """Test currency conversion uses specified reference year."""
        cost_eur = Quantity(100, "EUR", reference_year=2010)
        cost_usd = cost_eur.to("USD")

        # Should use 2010 rate (1.3257)
        assert cost_usd.value == pytest.approx(100 * 1.3257, rel=1e-2)
        assert cost_usd.unit == "USD"

    def test_compound_unit_currency_conversion(self):
        """Test currency conversion in compound units."""
        price_eur = Quantity(50, "EUR/MWh", reference_year=2020)
        price_usd = price_eur.to("USD/MWh")

        # Should use 2020 rate (1.1422)
        assert price_usd.value == pytest.approx(50 * 1.1422, rel=1e-2)
        assert price_usd.unit == "USD/MWh"

    def test_roundtrip_currency_conversion(self):
        """Test USD->EUR->USD roundtrip."""
        original = Quantity(100, "USD", reference_year=2020)
        eur = original.to("EUR")
        back_to_usd = eur.to("USD")

        assert back_to_usd.value == pytest.approx(100, rel=1e-6)


class TestCurrencyWithInflationCombined:
    """Test the special case: currency conversion + inflation adjustment."""

    def test_inflate_then_convert_convention(self):
        """Test that inflate-first-then-convert convention is used."""
        # 50 EUR/MWh in 2015 → USD/MWh in 2024
        cost_eur_2015 = Quantity(50, "EUR/MWh", reference_year=2015)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cost_usd_2024 = cost_eur_2015.to("USD/MWh", reference_year=2024)

            # Check warning was issued
            assert len(w) == 1
            assert "economic assumptions" in str(w[0].message).lower()
            assert "inflate first" in str(w[0].message).lower()

        # Manual calculation: inflate EUR 2015→2024, then convert
        # EUR inflation 2016-2024: ~20% cumulative (approximate)
        # Then convert using 2024 EUR/USD rate (1.085)
        # Expected: 50 * 1.20 * 1.085 = ~65.1

        assert cost_usd_2024.value > 50  # Should be higher
        assert cost_usd_2024.value < 100  # Sanity check
        assert cost_usd_2024.unit == "USD/MWh"
        assert cost_usd_2024.reference_year == 2024

    def test_path_dependency_example(self):
        """Test the user's original example showing path dependency."""
        # 50 EUR in 2015 → USD in 2024
        original = Quantity(50, "EUR", reference_year=2015)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = original.to("USD", reference_year=2024)
            assert len(w) == 1  # Warning issued

        # The library uses: inflate EUR 2015→2024, then convert EUR→USD at 2024 rate
        # This is deterministic and documented
        assert result.unit == "USD"
        assert result.reference_year == 2024

    def test_two_step_vs_one_step_consistency(self):
        """Test that two-step manual process matches one-step."""
        # Original: 100 EUR in 2015
        original = Quantity(100, "EUR", reference_year=2015)

        # One step: combined conversion with warning suppression
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            one_step = original.to("USD", reference_year=2024)

        # Two step: inflate first, then convert
        inflated = original.to(reference_year=2024)  # Still EUR, but 2024
        two_step = inflated.to("USD")  # Convert using 2024 rate

        # Should be identical (within floating point)
        assert one_step.value == pytest.approx(two_step.value, rel=1e-10)
        assert one_step.unit == two_step.unit
        assert one_step.reference_year == two_step.reference_year

    def test_warning_only_on_currency_plus_inflation(self):
        """Test warning only issued when both currency and year change."""
        # No warning for just currency
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Quantity(100, "EUR", reference_year=2020).to("USD")
            assert len(w) == 0  # No warning (same year)

        # No warning for just inflation
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Quantity(100, "EUR", reference_year=2020).to(reference_year=2024)
            assert len(w) == 0  # No warning (same currency)

        # Warning for both
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Quantity(100, "EUR", reference_year=2020).to("USD", reference_year=2024)
            assert len(w) == 1  # Warning issued

    def test_historical_rate_changes_matter(self):
        """Test that using different years gives different results."""
        # 100 EUR converted to USD in different years
        eur_2010 = Quantity(100, "EUR", reference_year=2010)
        eur_2023 = Quantity(100, "EUR", reference_year=2023)

        usd_2010 = eur_2010.to("USD")
        usd_2023 = eur_2023.to("USD")

        # 2010 rate (1.3257) vs 2023 rate (1.0813)
        assert usd_2010.value == pytest.approx(132.57, rel=1e-2)
        assert usd_2023.value == pytest.approx(108.13, rel=1e-2)
        assert usd_2010.value > usd_2023.value  # EUR was stronger in 2010


class TestExchangeRateRegistry:
    """Test the exchange rate registry utility functions."""

    def test_convert_currency(self):
        """Test currency conversion helper."""
        result = exchange_rate_registry.convert_currency(100, "EUR", "USD", 2020)
        assert result == pytest.approx(100 * 1.1422, rel=1e-4)

    def test_get_conversion_factor(self):
        """Test getting conversion factor."""
        factor = exchange_rate_registry.get_conversion_factor("EUR", "USD", 2020)
        assert factor == pytest.approx(1.1422, rel=1e-4)

    def test_detect_currency_from_unit(self):
        """Test currency detection from unit strings."""
        assert exchange_rate_registry.detect_currency_from_unit("USD") == "USD"
        assert exchange_rate_registry.detect_currency_from_unit("EUR/MWh") == "EUR"
        assert exchange_rate_registry.detect_currency_from_unit("GBP/kW") == "GBP"
        assert exchange_rate_registry.detect_currency_from_unit("$/kWh") == "USD"
        assert exchange_rate_registry.detect_currency_from_unit("MWh") is None

    def test_is_currency(self):
        """Test pure currency detection."""
        assert exchange_rate_registry.is_currency("USD") is True
        assert exchange_rate_registry.is_currency("EUR") is True
        assert exchange_rate_registry.is_currency("USD/MWh") is False
        assert exchange_rate_registry.is_currency("MWh") is False

    def test_supported_currencies(self):
        """Test getting supported currency list."""
        currencies = exchange_rate_registry.get_supported_currencies()
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "GBP" in currencies
        assert "JPY" in currencies
        assert "CNY" in currencies


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_currency_conversion_without_reference_year(self):
        """Test currency conversion when no reference year set."""
        # Should use most recent rate
        cost = Quantity(100, "EUR")  # No reference year
        converted = cost.to("USD")

        # Should use 2025 rate
        assert converted.value == pytest.approx(100 * 1.08, rel=1e-2)

    def test_same_currency_no_conversion_needed(self):
        """Test converting to same currency is no-op."""
        cost = Quantity(100, "USD", reference_year=2020)
        same = cost.to("USD")

        assert same.value == 100
        assert same.unit == "USD"
        assert same.reference_year == 2020

    def test_array_values_currency_conversion(self):
        """Test currency conversion with array values."""
        costs = Quantity([100, 200, 300], "EUR", reference_year=2020)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            converted = costs.to("USD", reference_year=2024)

        assert len(converted.value) == 3
        assert all(converted.value > [100, 200, 300])  # All increased

    def test_cross_currency_direct_conversion(self):
        """Test EUR to GBP (not through explicit USD)."""
        cost_eur = Quantity(100, "EUR", reference_year=2020)
        cost_gbp = cost_eur.to("GBP")

        # EUR to GBP via USD: 100 * 1.1422 / 1.2837
        expected = 100 * 1.1422 / 1.2837
        assert cost_gbp.value == pytest.approx(expected, rel=1e-3)
