"""Test smart compound unit cancellation with dimensional matching."""

import pytest

from energyunits import Quantity


class TestSmartCompoundUnitCancellation:
    """Test automatic unit conversion for compound unit multiplication."""

    def test_power_units_different_scales(self):
        """USD/kW × MW should auto-convert and cancel."""
        capex = Quantity(1500, "USD/kW")
        capacity = Quantity(500, "MW")

        result = capex * capacity

        assert result.value == pytest.approx(750_000_000)
        assert result.unit == "USD"

    def test_power_units_reverse_order(self):
        """MW × USD/kW should also work (order independence)."""
        capacity = Quantity(500, "MW")
        capex = Quantity(1500, "USD/kW")

        result = capacity * capex

        assert result.value == pytest.approx(750_000_000)
        assert result.unit == "USD"

    def test_mass_units_different_scales(self):
        """USD/kg × t should auto-convert and cancel."""
        price_per_kg = Quantity(0.05, "USD/kg")
        mass_tonnes = Quantity(100, "t")

        result = price_per_kg * mass_tonnes

        assert result.value == pytest.approx(5000)
        assert result.unit == "USD"

    def test_mass_units_with_substance(self):
        """USD/kg × t with substance should preserve substance."""
        price_per_kg = Quantity(0.05, "USD/kg")
        coal_mass = Quantity(100, "t", "coal")

        result = price_per_kg * coal_mass

        assert result.value == pytest.approx(5000)
        assert result.unit == "USD"
        assert result.substance == "coal"

    def test_energy_units_different_scales(self):
        """EUR/MWh × GWh should auto-convert and cancel."""
        price = Quantity(50, "EUR/MWh")
        energy = Quantity(2, "GWh")

        result = price * energy

        assert result.value == pytest.approx(100_000)
        assert result.unit == "EUR"

    def test_energy_units_reverse_order(self):
        """GWh × EUR/MWh should also work."""
        energy = Quantity(2, "GWh")
        price = Quantity(50, "EUR/MWh")

        result = energy * price

        assert result.value == pytest.approx(100_000)
        assert result.unit == "EUR"

    def test_time_units_different_scales(self):
        """GWh/min × min should cancel (already worked, but verify)."""
        power_rate = Quantity(100, "GWh/min")
        time = Quantity(30, "min")

        result = power_rate * time

        assert result.value == pytest.approx(3000)
        assert result.unit == "GWh"

    def test_exact_match_still_works(self):
        """USD/t × t should still work without conversion."""
        price = Quantity(50, "USD/t")
        mass = Quantity(100, "t", "coal")

        result = price * mass

        assert result.value == pytest.approx(5000)
        assert result.unit == "USD"
        assert result.substance == "coal"

    def test_multiple_scale_differences(self):
        """Test with extreme scale differences."""
        # USD/W × GW (6 orders of magnitude difference)
        price = Quantity(0.001, "USD/W")
        capacity = Quantity(1, "GW")

        result = price * capacity

        assert result.value == pytest.approx(1_000_000)
        assert result.unit == "USD"

    def test_currency_conversion_with_scale(self):
        """Test different currencies with unit scale differences."""
        # EUR/kW × MW
        capex_eur = Quantity(1200, "EUR/kW")
        capacity = Quantity(100, "MW")

        result = capex_eur * capacity

        assert result.value == pytest.approx(120_000_000)
        assert result.unit == "EUR"

    def test_volume_units_different_scales(self):
        """USD/L × m3 should auto-convert and cancel."""
        price_per_liter = Quantity(1.5, "USD/L")
        volume_m3 = Quantity(2, "m3")

        result = price_per_liter * volume_m3

        # 2 m3 = 2000 L, so 1.5 * 2000 = 3000
        assert result.value == pytest.approx(3000)
        assert result.unit == "USD"

    def test_no_conversion_when_not_needed(self):
        """Test that exact matches don't trigger unnecessary conversions."""
        price = Quantity(100, "USD/MWh")
        energy = Quantity(10, "MWh")

        result = price * energy

        assert result.value == pytest.approx(1000)
        assert result.unit == "USD"

    def test_reference_year_cleared_when_not_matching(self):
        """Test that reference year is cleared when other operand has none."""
        capex = Quantity(1500, "USD/kW", reference_year=2020)
        capacity = Quantity(500, "MW")  # No reference year

        result = capex * capacity

        assert result.value == pytest.approx(750_000_000)
        assert result.unit == "USD"
        # Reference year is cleared because capacity has no reference year
        assert result.reference_year is None

    def test_with_inflation_adjustment(self):
        """Test smart cancellation works with inflated quantities."""
        capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
        capex_2025 = capex_2020.to(reference_year=2025)
        capacity = Quantity(500, "MW")

        result = capex_2025 * capacity

        # Should be > 500M due to inflation
        assert result.value > 500_000_000
        assert result.unit == "USD"
        # Reference year is cleared because capacity has no reference year
        assert result.reference_year is None


class TestSmartCancellationEdgeCases:
    """Test edge cases and limitations of smart cancellation."""

    def test_arrays_with_smart_cancellation(self):
        """Test that smart cancellation works with arrays."""
        prices = Quantity([1000, 1500, 2000], "USD/kW")
        capacity = Quantity(500, "MW")

        result = prices * capacity

        assert result.value[0] == pytest.approx(500_000_000)
        assert result.value[1] == pytest.approx(750_000_000)
        assert result.value[2] == pytest.approx(1_000_000_000)
        assert result.unit == "USD"

    def test_scalar_array_multiplication(self):
        """Test scalar with array using smart cancellation."""
        capacity = Quantity(500, "MW")
        prices = Quantity([1000, 1500, 2000], "USD/kW")

        result = capacity * prices

        assert len(result.value) == 3
        assert result.value[0] == pytest.approx(500_000_000)
        assert result.unit == "USD"
