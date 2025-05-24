"""Comprehensive tests for inflation adjustment functionality."""

import pytest
import numpy as np

from energyunits import Quantity


class TestInflationAdjustment:
    """Test inflation adjustment functionality comprehensively."""

    def test_basic_inflation_adjustment(self):
        """Test basic inflation adjustment with 2% annual rate."""
        # Start with a cost in 2020
        capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
        
        # Adjust to 2025 (5 years)
        capex_2025 = capex_2020.adjust_inflation(2025)
        
        # Expected: 1000 * (1.02)^5 = 1104.08
        expected_value = 1000 * (1.02 ** 5)
        assert capex_2025.value == pytest.approx(expected_value)
        assert capex_2025.unit == "USD/kW"
        assert capex_2025.reference_year == 2025

    def test_backward_inflation_adjustment(self):
        """Test inflation adjustment to past years (deflation)."""
        # Start with a cost in 2025
        capex_2025 = Quantity(1104.08, "USD/kW", reference_year=2025)
        
        # Adjust back to 2020 (5 years back)
        capex_2020 = capex_2025.adjust_inflation(2020)
        
        # Expected: 1104.08 / (1.02)^5 ≈ 1000
        expected_value = 1104.08 / (1.02 ** 5)
        assert capex_2020.value == pytest.approx(expected_value, rel=1e-4)
        assert capex_2020.reference_year == 2020

    def test_same_year_adjustment(self):
        """Test adjustment to the same year (should return unchanged)."""
        capex = Quantity(1000, "USD/kW", reference_year=2020)
        capex_same = capex.adjust_inflation(2020)
        
        # Should return the same object or identical values
        assert capex_same.value == capex.value
        assert capex_same.unit == capex.unit
        assert capex_same.reference_year == capex.reference_year
        
        # Should be the same object (optimization)
        assert capex_same is capex

    def test_large_time_differences(self):
        """Test inflation adjustment over large time periods."""
        # Test 50 years forward
        cost_1980 = Quantity(100, "USD/MWh", reference_year=1980)
        cost_2030 = cost_1980.adjust_inflation(2030)
        
        # 50 years at 2%: 100 * (1.02)^50 ≈ 269.16
        expected_value = 100 * (1.02 ** 50)
        assert cost_2030.value == pytest.approx(expected_value)
        
        # Test 100 years forward
        cost_1920 = Quantity(10, "USD/kW", reference_year=1920)
        cost_2020 = cost_1920.adjust_inflation(2020)
        
        # 100 years at 2%: 10 * (1.02)^100 ≈ 72.44
        expected_value = 10 * (1.02 ** 100)
        assert cost_2020.value == pytest.approx(expected_value)

    def test_array_inflation_adjustment(self):
        """Test inflation adjustment with array inputs."""
        costs = [100, 200, 500, 1000]
        capex_array = Quantity(costs, "USD/kW", reference_year=2020)
        
        # Adjust to 2025
        adjusted_array = capex_array.adjust_inflation(2025)
        
        inflation_factor = (1.02 ** 5)
        for i, original_cost in enumerate(costs):
            expected = original_cost * inflation_factor
            assert adjusted_array.value[i] == pytest.approx(expected)

    def test_different_currency_units(self):
        """Test inflation adjustment with different currency units."""
        test_cases = [
            ("USD", 1000),
            ("EUR", 850),
            ("GBP", 750),
            ("JPY", 110000),
        ]
        
        for currency, amount in test_cases:
            cost = Quantity(amount, f"{currency}/kW", reference_year=2020)
            adjusted = cost.adjust_inflation(2025)
            
            expected = amount * (1.02 ** 5)
            assert adjusted.value == pytest.approx(expected)
            assert adjusted.unit == f"{currency}/kW"

    def test_compound_units_inflation(self):
        """Test inflation adjustment with complex compound units."""
        # O&M costs per MWh per year
        om_cost = Quantity(50, "USD/MWh/a", reference_year=2020)
        om_2030 = om_cost.adjust_inflation(2030)
        
        expected = 50 * (1.02 ** 10)
        assert om_2030.value == pytest.approx(expected)
        assert om_2030.unit == "USD/MWh/a"

    def test_inflation_preserves_other_attributes(self):
        """Test that inflation adjustment preserves substance and basis."""
        cost = Quantity(100, "USD/t", substance="coal", basis="HHV", reference_year=2020)
        adjusted = cost.adjust_inflation(2025)
        
        assert adjusted.substance == "coal"
        assert adjusted.basis == "HHV"
        assert adjusted.unit == "USD/t"
        assert adjusted.reference_year == 2025

    def test_chained_inflation_adjustments(self):
        """Test multiple consecutive inflation adjustments."""
        cost_2010 = Quantity(500, "USD/kW", reference_year=2010)
        
        # Chain: 2010 → 2015 → 2020 → 2025
        cost_2015 = cost_2010.adjust_inflation(2015)
        cost_2020 = cost_2015.adjust_inflation(2020)
        cost_2025 = cost_2020.adjust_inflation(2025)
        
        # Should be same as direct adjustment
        cost_2025_direct = cost_2010.adjust_inflation(2025)
        
        assert cost_2025.value == pytest.approx(cost_2025_direct.value, rel=1e-10)

    def test_inflation_with_unit_conversions(self):
        """Test inflation adjustment combined with unit conversions."""
        # Start with USD/kW, adjust inflation, then convert to USD/MW
        cost_kw = Quantity(1000, "USD/kW", reference_year=2020)
        
        # Method 1: Inflate then convert
        cost_2025_kw = cost_kw.adjust_inflation(2025)
        cost_2025_mw = cost_2025_kw.to("USD/MW")
        
        # Method 2: Convert then inflate
        cost_mw = cost_kw.to("USD/MW")
        cost_2025_mw_alt = cost_mw.adjust_inflation(2025)
        
        # Results should be identical
        assert cost_2025_mw.value == pytest.approx(cost_2025_mw_alt.value)

    def test_roundtrip_inflation_adjustment(self):
        """Test roundtrip inflation adjustments (forward and back)."""
        original = Quantity(1000, "USD/kW", reference_year=2020)
        
        # Forward to 2030 and back to 2020
        forward = original.adjust_inflation(2030)
        back = forward.adjust_inflation(2020)
        
        # Should get back to original value (within floating point precision)
        assert back.value == pytest.approx(original.value, rel=1e-12)
        assert back.reference_year == 2020

    def test_extreme_inflation_scenarios(self):
        """Test extreme inflation scenarios for numerical stability."""
        # Very small amounts
        tiny_cost = Quantity(0.001, "USD/kWh", reference_year=2020)
        tiny_adjusted = tiny_cost.adjust_inflation(2025)
        assert tiny_adjusted.value > 0
        
        # Very large amounts
        huge_cost = Quantity(1e9, "USD", reference_year=2020)
        huge_adjusted = huge_cost.adjust_inflation(2025)
        assert huge_adjusted.value > huge_cost.value
        
        # Zero amounts
        zero_cost = Quantity(0, "USD/kW", reference_year=2020)
        zero_adjusted = zero_cost.adjust_inflation(2025)
        assert zero_adjusted.value == 0

    def test_inflation_mathematical_properties(self):
        """Test mathematical properties of inflation adjustment."""
        cost = Quantity(1000, "USD/kW", reference_year=2020)
        
        # Test that inflation is multiplicative
        cost_2025 = cost.adjust_inflation(2025)
        cost_2030 = cost.adjust_inflation(2030)
        
        # Ratio should equal the inflation factor for the difference
        ratio = cost_2030.value / cost_2025.value
        expected_ratio = (1.02 ** 5)  # 2030 - 2025 = 5 years
        assert ratio == pytest.approx(expected_ratio)


class TestInflationAdjustmentErrors:
    """Test error handling in inflation adjustment."""

    def test_missing_reference_year_error(self):
        """Test error when reference year is not specified."""
        cost = Quantity(1000, "USD/kW")  # No reference year
        
        with pytest.raises(ValueError, match="Reference year not specified"):
            cost.adjust_inflation(2025)

    def test_invalid_target_year_types(self):
        """Test error handling for invalid target year types."""
        cost = Quantity(1000, "USD/kW", reference_year=2020)
        
        # Test non-numeric types
        with pytest.raises(TypeError):
            cost.adjust_inflation("2025")
        
        # Float years actually work in the current implementation
        # This might be changed in the future for stricter validation
        result = cost.adjust_inflation(2025.0)
        assert result.reference_year == 2025.0

    def test_extreme_year_values(self):
        """Test handling of extreme year values."""
        cost = Quantity(1000, "USD/kW", reference_year=2020)
        
        # Very large year differences might cause overflow
        try:
            # This might overflow but should handle gracefully
            extreme_future = cost.adjust_inflation(4020)  # 2000 years
            assert extreme_future.value > 0  # Should not be NaN or infinity
        except OverflowError:
            # Acceptable to raise overflow for extreme cases
            pass
        
        # Very negative years
        try:
            extreme_past = cost.adjust_inflation(20)  # 2000 years ago
            assert extreme_past.value > 0  # Should not be negative or zero
        except (OverflowError, ZeroDivisionError):
            # Acceptable to raise errors for extreme cases
            pass

    def test_non_currency_unit_warning(self):
        """Test that inflation adjustment works on any unit (might want to warn in future)."""
        # Currently the library allows inflation adjustment on any unit
        # This might be changed in the future to only allow currency units
        energy = Quantity(100, "MWh", reference_year=2020)
        
        # Should work (for now) but might want to warn users
        adjusted = energy.adjust_inflation(2025)
        assert adjusted.value == pytest.approx(100 * (1.02 ** 5))

    def test_negative_costs_inflation(self):
        """Test inflation adjustment with negative costs (credits)."""
        # Negative costs might represent credits or subsidies
        credit = Quantity(-100, "USD/kW", reference_year=2020)
        adjusted_credit = credit.adjust_inflation(2025)
        
        # Should maintain the negative sign
        expected = -100 * (1.02 ** 5)
        assert adjusted_credit.value == pytest.approx(expected)
        assert adjusted_credit.value < 0


class TestInflationAdjustmentIntegration:
    """Test inflation adjustment integration with other features."""

    def test_inflation_with_substance_conversions(self):
        """Test inflation adjustment combined with substance conversions."""
        # Start with coal mass
        coal_mass = Quantity(1, "t", substance="coal", reference_year=2020)
        
        # Convert to CO2 emissions (preserves reference year)
        co2_2020 = coal_mass.to(substance="CO2")
        
        # Now test with inflated coal cost
        fuel_cost_2020 = Quantity(50, "USD/t", substance="coal", reference_year=2020)
        fuel_cost_2025 = fuel_cost_2020.adjust_inflation(2025)
        
        # Should preserve reference year and substance
        assert fuel_cost_2025.reference_year == 2025
        assert fuel_cost_2025.substance == "coal"
        
        # CO2 calculation should still work
        coal_mass_2025 = Quantity(1, "t", substance="coal", reference_year=2025)
        co2_2025 = coal_mass_2025.to(substance="CO2")
        
        # CO2 amounts should be the same regardless of reference year
        assert co2_2025.value == pytest.approx(co2_2020.value)

    def test_inflation_with_basis_conversions(self):
        """Test inflation adjustment with basis conversions."""
        fuel_cost_hhv = Quantity(30, "USD/MWh", substance="natural_gas", 
                                basis="HHV", reference_year=2020)
        
        # Adjust inflation first, then convert basis
        cost_2025_hhv = fuel_cost_hhv.adjust_inflation(2025)
        cost_2025_lhv = cost_2025_hhv.to(basis="LHV")
        
        # Reference year should be preserved
        assert cost_2025_lhv.reference_year == 2025
        assert cost_2025_lhv.basis == "LHV"

    def test_inflation_with_array_operations(self):
        """Test inflation adjustment with array operations."""
        costs_2020 = [100, 200, 300, 500]
        cost_array = Quantity(costs_2020, "USD/kW", reference_year=2020)
        
        # Adjust inflation
        cost_array_2025 = cost_array.adjust_inflation(2025)
        
        # Add another cost array
        additional_costs = Quantity([50, 100, 150, 200], "USD/kW", reference_year=2025)
        total_costs = cost_array_2025 + additional_costs
        
        # Should work correctly
        assert total_costs.reference_year == 2025  # Or None due to different years

    def test_lcoe_calculation_with_inflation(self):
        """Test a realistic LCOE calculation with inflation adjustments."""
        # Capital costs in 2020
        capex_2020 = Quantity(1200, "USD/kW", reference_year=2020)
        
        # Project starts in 2025, so adjust capital costs
        capex_2025 = capex_2020.adjust_inflation(2025)
        
        # O&M costs in 2025
        om_2025 = Quantity(40, "USD/kW/a", reference_year=2025)
        
        # Example LCOE calculation (simplified)
        # Convert capex to energy basis
        capacity_factor = 0.35
        lifetime_energy = 20 * 365 * 24 * capacity_factor  # 20 years, kWh/kW
        
        capex_per_kwh = capex_2025.value / lifetime_energy
        om_per_kwh = om_2025.value / (365 * 24 * capacity_factor)
        
        lcoe = capex_per_kwh + om_per_kwh
        
        assert lcoe > 0
        assert capex_2025.reference_year == 2025

    def test_currency_conversion_with_inflation(self):
        """Test combining currency conversion with inflation (if implemented)."""
        # This is a placeholder for future currency conversion features
        usd_cost = Quantity(1000, "USD/kW", reference_year=2020)
        
        # Inflate to 2025
        usd_2025 = usd_cost.adjust_inflation(2025)
        
        # In the future, might want to combine with currency conversion
        # For now, just ensure inflation works with different currencies
        eur_cost = Quantity(850, "EUR/kW", reference_year=2020)
        eur_2025 = eur_cost.adjust_inflation(2025)
        
        assert usd_2025.unit == "USD/kW"
        assert eur_2025.unit == "EUR/kW"
        assert usd_2025.reference_year == 2025
        assert eur_2025.reference_year == 2025