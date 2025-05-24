"""Updated tests for inflation adjustment functionality using historical data."""

import numpy as np
import pytest

from energyunits import Quantity


class TestInflationAdjustment:
    """Test inflation adjustment functionality with historical data."""

    def test_basic_inflation_adjustment(self):
        """Test basic inflation adjustment with historical rates."""
        capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
        capex_2022 = capex_2020.to(reference_year=2022)

        # 2021: 4.70%, 2022: 8.00%
        expected = 1000 * 1.047 * 1.08
        assert capex_2022.value == pytest.approx(expected, rel=1e-3)
        assert capex_2022.reference_year == 2022

    def test_backward_adjustment(self):
        """Test deflation to past years."""
        capex_2022 = Quantity(
            1130.76, "USD/kW", reference_year=2022
        )  # 1000 * 1.047 * 1.08
        capex_2020 = capex_2022.to(reference_year=2020)

        assert capex_2020.value == pytest.approx(1000, rel=1e-2)
        assert capex_2020.reference_year == 2020

    def test_same_year_no_change(self):
        """Test that same year returns unchanged value."""
        capex = Quantity(1000, "USD/kW", reference_year=2020)
        capex_same = capex.to(reference_year=2020)

        assert capex_same.value == 1000
        assert capex_same.reference_year == 2020

    def test_eur_currency(self):
        """Test EUR inflation adjustment."""
        cost_2020 = Quantity(800, "EUR/kW", reference_year=2020)
        cost_2022 = cost_2020.to(reference_year=2022)

        # EUR: 2021: 2.60%, 2022: 8.40%
        expected = 800 * 1.026 * 1.084
        assert cost_2022.value == pytest.approx(expected, rel=1e-3)

    def test_array_values(self):
        """Test inflation with array values."""
        values = np.array([1000, 1500, 2000])
        costs = Quantity(values, "USD/kW", reference_year=2020)
        costs_2021 = costs.to(reference_year=2021)

        expected = values * 1.047  # 2021: 4.70%
        assert np.allclose(costs_2021.value, expected, rtol=1e-3)

    def test_compound_units(self):
        """Test inflation with compound units."""
        price = Quantity(50, "USD/MWh", reference_year=2020)
        price_2021 = price.to(reference_year=2021)

        expected = 50 * 1.047
        assert price_2021.value == pytest.approx(expected, rel=1e-3)

    def test_new_to_method(self):
        """Test the new .to(reference_year=) method."""
        capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
        capex_2022 = capex_2020.to(reference_year=2022)

        expected = 1000 * 1.047 * 1.08
        assert capex_2022.value == pytest.approx(expected, rel=1e-3)
        assert capex_2022.reference_year == 2022


class TestInflationErrors:
    """Test error handling for inflation adjustment."""

    def test_no_reference_year(self):
        """Test error when no reference year specified."""
        quantity = Quantity(1000, "USD/kW")  # No reference year

        with pytest.raises(ValueError, match="Reference year not specified"):
            quantity.to(reference_year=2025)

    def test_unsupported_currency(self):
        """Test error for unsupported currency."""
        quantity = Quantity(1000, "JPY/kW", reference_year=2020)

        with pytest.raises(ValueError, match="Cannot detect currency"):
            quantity.to(reference_year=2025)

    def test_year_out_of_range(self):
        """Test error for years outside data range."""
        quantity = Quantity(1000, "USD/kW", reference_year=2020)

        with pytest.raises(ValueError, match="No inflation data"):
            quantity.to(reference_year=2050)

    def test_non_currency_unit(self):
        """Test error for non-currency units."""
        energy = Quantity(100, "MWh", reference_year=2020)

        with pytest.raises(ValueError, match="Cannot detect currency"):
            energy.to(reference_year=2025)


class TestInflationMath:
    """Test mathematical properties of inflation adjustment."""

    def test_round_trip_consistency(self):
        """Test that forward and backward adjustments are consistent."""
        original = Quantity(1000, "USD/kW", reference_year=2020)

        # Forward to 2025, then back to 2020
        forward = original.to(reference_year=2025)
        back = forward.to(reference_year=2020)

        assert back.value == pytest.approx(1000, rel=1e-10)

    def test_transitive_property(self):
        """Test that A→B→C equals A→C."""
        original = Quantity(1000, "USD/kW", reference_year=2020)

        # Direct: 2020 → 2022
        direct = original.to(reference_year=2022)

        # Indirect: 2020 → 2021 → 2022
        step1 = original.to(reference_year=2021)
        step2 = step1.to(reference_year=2022)

        assert step2.value == pytest.approx(direct.value, rel=1e-10)

    def test_additive_years(self):
        """Test that sequential year adjustments work correctly."""
        cost_2020 = Quantity(1000, "USD/kW", reference_year=2020)

        # Method 1: Direct adjustment
        cost_2023_direct = cost_2020.to(reference_year=2023)

        # Method 2: Year by year
        cost_2021 = cost_2020.to(reference_year=2021)
        cost_2022 = cost_2021.to(reference_year=2022)
        cost_2023_steps = cost_2022.to(reference_year=2023)

        assert cost_2023_steps.value == pytest.approx(cost_2023_direct.value, rel=1e-10)
