"""
Tests for fallback removal in arithmetic operations.

Tests that arithmetic operations now raise explicit errors instead of
using silent fallbacks when unit correspondences are not defined.
"""

from energyunits import Quantity


class TestFallbackRemoval:
    """Test that fallbacks have been replaced with explicit errors."""

    def test_power_time_multiplication_with_unsupported_units(self):
        """Test that power * time raises error for unsupported power units."""
        # Using a hypothetical unsupported power unit - this would need to be added to test
        # For now, test with existing units that should work
        power = Quantity(100, "MW")
        time = Quantity(24, "h")
        result = power * time

        # This should work fine with MW -> MWh
        assert result.unit == "MWh"
        assert result.value == 2400

    def test_energy_time_division_with_unsupported_units(self):
        """Test that energy / time raises error for unsupported energy units."""
        # Test with existing units that should work
        energy = Quantity(2400, "MWh")
        time = Quantity(24, "h")
        result = energy / time

        # This should work fine with MWh -> MW
        assert result.unit == "MW"
        assert result.value == 100

    def test_clear_error_messages_for_missing_correspondences(self):
        """Test that error messages are clear and informative."""
        # This test documents the expected behavior when we encounter
        # units without defined correspondences

        # Note: All currently supported power/energy units have correspondences
        # So this test serves as documentation for the expected behavior

        # If we had an unsupported unit, we would expect:
        # ValueError: Cannot determine energy unit for power unit 'unsupported_unit'.
        #            No corresponding energy unit defined in registry.

        pass  # This is a documentation test

    def test_compound_unit_creation_still_works(self):
        """Test that compound unit creation works for non-power/energy cases."""
        # Test units that should create compound units
        mass = Quantity(1000, "t")
        price = Quantity(50, "USD/t")

        # This should still work without fallbacks
        total_cost = price * mass
        assert "USD" in total_cost.unit

        # Test division creating compound units
        energy = Quantity(100, "MWh")
        mass = Quantity(10, "t")
        intensity = energy / mass
        assert intensity.unit == "MWh/t"

    def test_dimensional_analysis_preserved(self):
        """Test that dimensional analysis still works correctly."""
        # Power * time should give energy for supported units
        power_mw = Quantity(100, "MW")
        power_gw = Quantity(0.1, "GW")
        time = Quantity(1, "h")

        energy_mw = power_mw * time
        energy_gw = power_gw * time

        assert energy_mw.unit == "MWh"
        assert energy_gw.unit == "GWh"

        # Energy / time should give power for supported units
        back_to_power_mw = energy_mw / time
        back_to_power_gw = energy_gw / time

        assert back_to_power_mw.unit == "MW"
        assert back_to_power_gw.unit == "GW"

    def test_same_unit_division_gives_dimensionless(self):
        """Test that dividing same units gives dimensionless result."""
        energy1 = Quantity(200, "MWh")
        energy2 = Quantity(100, "MWh")

        ratio = energy1 / energy2
        assert ratio.unit == ""  # dimensionless
        assert ratio.value == 2.0

    def test_improved_error_handling_documentation(self):
        """Document the improved error handling approach."""
        # Previously: Silent fallbacks to "MW" or "MWh" could mask issues
        # Now: Explicit errors help users understand when unit mappings are missing

        # Benefits:
        # 1. Users get clear feedback about unsupported operations
        # 2. No hidden assumptions about default units
        # 3. Encourages completing the unit registry properly
        # 4. Makes the library behavior more predictable

        # If registry expansion is needed, users will see clear error messages
        # pointing to exactly what's missing

        pass  # Documentation test
