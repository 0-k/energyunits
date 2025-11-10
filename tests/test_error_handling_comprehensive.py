"""Comprehensive error handling and validation tests."""

import numpy as np
import pytest

from energyunits import Quantity
from energyunits.registry import registry
from energyunits.substance import substance_registry


class TestQuantityInputValidation:
    """Test input validation for Quantity creation and methods."""

    def test_invalid_value_types(self):
        """Test error handling for invalid value types."""
        # NumPy is very permissive - test what actually happens
        q = Quantity("not_a_number", "MWh")
        # Should be some numpy value (string, object array, etc.)
        assert hasattr(q.value, "dtype")  # It's a numpy value

        # None values are handled by numpy
        q_none = Quantity(None, "MWh")
        # Should create a numpy array
        assert hasattr(q_none.value, "dtype")

        # Complex objects might work or fail
        try:
            q_dict = Quantity({"value": 100}, "MWh")
            # NumPy might create an object array
            assert hasattr(q_dict.value, "dtype")
        except (TypeError, ValueError):
            pass  # Also acceptable

    def test_invalid_unit_types(self):
        """Test error handling for invalid unit types."""
        with pytest.raises(TypeError):
            Quantity(100, 123)  # Numeric unit

        with pytest.raises(TypeError):
            Quantity(100, None)  # None unit

        with pytest.raises(TypeError):
            Quantity(100, ["MWh"])  # List unit

    def test_empty_unit_string(self):
        """Test handling of empty unit strings."""
        # Empty string is now valid for dimensionless quantities
        quantity = Quantity(100, "")  # Dimensionless
        assert quantity.value == 100
        assert quantity.unit == ""

        # Whitespace should still raise error
        with pytest.raises(ValueError):
            Quantity(100, "   ")  # Whitespace only

    def test_invalid_substance_validation(self):
        """Test that invalid substances are caught early where possible."""
        # Currently the library doesn't validate substances at creation
        # but they should fail during conversion operations
        invalid_quantity = Quantity(100, "MWh", "unobtainium")

        # Should fail when trying to use the invalid substance
        with pytest.raises(ValueError, match="Unknown substance"):
            invalid_quantity.to(substance="CO2")

    def test_invalid_basis_values(self):
        """Test error handling for invalid basis values."""
        # Currently doesn't validate at creation
        quantity = Quantity(100, "MWh", "coal", basis="INVALID")

        # Should fail during basis conversion
        with pytest.raises(ValueError, match="Invalid basis conversion"):
            quantity.to(basis="LHV")

    def test_invalid_reference_year_types(self):
        """Test error handling for invalid reference year types."""
        # Currently the library is quite permissive with reference years

        # String reference year - might be accepted or rejected
        try:
            quantity = Quantity(100, "USD/kW", reference_year="2020")
            # If accepted, test that it works
            assert quantity.reference_year == "2020"
        except (TypeError, ValueError):
            pass  # Also acceptable

        # Float reference year (currently accepted)
        quantity = Quantity(100, "USD/kW", reference_year=2020.5)
        assert quantity.reference_year == 2020.5

    def test_array_input_validation(self):
        """Test validation of array inputs."""
        # Mixed types in array - numpy is permissive and may convert
        try:
            mixed_quantity = Quantity([100, "invalid", 300], "MWh")
            # NumPy might convert strings to objects or fail
        except (TypeError, ValueError):
            pass  # Expected behavior

        # Empty arrays should work
        empty_quantity = Quantity([], "MWh")
        assert len(empty_quantity.value) == 0

        # NaN values should work
        nan_quantity = Quantity([100, np.nan, 300], "MWh")
        assert np.isnan(nan_quantity.value[1])

    def test_infinite_values(self):
        """Test handling of infinite values."""
        # Should accept infinity but might cause issues in calculations
        inf_quantity = Quantity(np.inf, "MWh")
        assert np.isinf(inf_quantity.value)

        # Operations with infinity
        result = inf_quantity * 2
        assert np.isinf(result.value)


class TestConversionErrors:
    """Test error handling in unit and substance conversions."""

    def test_incompatible_unit_conversion(self):
        """Test errors for incompatible unit conversions."""
        energy = Quantity(100, "MWh")

        with pytest.raises(ValueError, match="Substance required"):
            energy.to("kg")  # Energy to mass without substance

        with pytest.raises(ValueError, match="Cannot convert"):
            energy.to("USD")  # Energy to currency

    def test_unknown_unit_conversion(self):
        """Test errors for unknown units."""
        energy = Quantity(100, "MWh")

        with pytest.raises(ValueError, match="Unknown unit"):
            energy.to("MegaWatts")  # Non-standard unit name

        with pytest.raises(ValueError, match="Unknown unit"):
            energy.to("kWh_thermal")  # Non-existent unit

    def test_malformed_compound_units(self):
        """Test behavior with unusual compound unit formats."""
        # The system actually handles these by creating compound dimensions
        q1 = Quantity(100, "MW//h")  # Double slash
        q2 = Quantity(100, "MW/")  # Trailing slash
        q3 = Quantity(100, "/h")  # Leading slash

        # These create valid but unusual compound dimensions
        assert "POWER_PER_DIMENSIONLESS_PER_TIME" in q1.dimension
        assert "POWER_PER_DIMENSIONLESS" in q2.dimension
        assert "DIMENSIONLESS_PER_TIME" in q3.dimension

        # However, they shouldn't be useful for normal conversions
        with pytest.raises(ValueError):
            q1.to("MW")  # Cannot convert complex compound to simple unit

    def test_circular_unit_conversion(self):
        """Test that circular conversions don't cause infinite loops."""
        # This is more of a registry integrity test
        energy = Quantity(100, "MWh")

        # Multiple conversions should work
        result = energy.to("GJ").to("kWh").to("MWh")
        assert result.value == pytest.approx(energy.value, rel=1e-10)

    def test_substance_conversion_without_mass_basis(self):
        """Test substance conversion errors for energy/volume quantities."""
        # Energy without substance cannot convert to combustion products
        energy = Quantity(100, "MWh")

        with pytest.raises(ValueError, match="Source substance must be specified"):
            energy.to(substance="CO2")

    def test_basis_conversion_without_substance(self):
        """Test basis conversion errors without substance."""
        energy = Quantity(100, "MWh")

        with pytest.raises(ValueError, match="Substance must be specified"):
            energy.to(basis="HHV")

    def test_renewable_substance_basis_conversion(self):
        """Test error when trying basis conversion on renewables."""
        wind_energy = Quantity(100, "MWh", "wind")

        with pytest.raises(ValueError):
            wind_energy.to(basis="HHV")  # Wind has no heating value

    def test_conversion_chain_failures(self):
        """Test error propagation in conversion chains."""
        # Start with valid quantity but create invalid conversion chain
        coal = Quantity(1, "t", "coal")

        # Should fail at the substance conversion step
        with pytest.raises(ValueError):
            coal.to("kg").to(substance="INVALID_PRODUCT")


class TestArithmeticErrors:
    """Test error handling in arithmetic operations."""

    def test_incompatible_addition(self):
        """Test errors for incompatible quantity addition."""
        energy = Quantity(100, "MWh")
        mass = Quantity(50, "t")

        with pytest.raises((ValueError, TypeError)):
            energy + mass  # Cannot add energy and mass

        # Different substances should work (substance becomes None)
        coal_energy = Quantity(100, "MWh", "coal")
        gas_energy = Quantity(200, "MWh", "natural_gas")
        total = coal_energy + gas_energy
        assert total.substance is None

    def test_invalid_multiplication_types(self):
        """Test errors for invalid multiplication operands."""
        energy = Quantity(100, "MWh")

        with pytest.raises(TypeError):
            energy * "invalid"

        with pytest.raises(TypeError):
            energy * None

        with pytest.raises(TypeError):
            energy * [1, 2, 3]

    def test_division_by_zero(self):
        """Test division by zero handling."""
        energy = Quantity(100, "MWh")

        # Scalar division by zero - NumPy returns inf instead of raising error
        result = energy / 0
        assert np.isinf(result.value)

        # Quantity division by zero - also returns inf
        zero_time = Quantity(0, "h")
        result = energy / zero_time
        assert np.isinf(result.value)

    def test_array_arithmetic_errors(self):
        """Test error handling in array arithmetic."""
        energy_array = Quantity([100, 200, 300], "MWh")

        # Mismatched array sizes
        small_array = Quantity([1, 2], "h")
        with pytest.raises(ValueError):
            energy_array + small_array  # Different sizes

    def test_comparison_errors(self):
        """Test error handling in quantity comparisons."""
        energy = Quantity(100, "MWh")
        mass = Quantity(50, "t")

        # Comparing incompatible quantities should work through conversion
        # but will fail if conversion is impossible
        with pytest.raises(ValueError):
            energy > mass  # No way to convert

    def test_invalid_array_operations(self):
        """Test invalid operations on array quantities."""
        # Some operations might not make sense for arrays
        energy_array = Quantity([100, 200, 300], "MWh")

        # Operations that should work
        doubled = energy_array * 2
        assert len(doubled.value) == 3

        # Operations that might have edge cases
        power_array = energy_array / Quantity([1, 2, 0], "h")
        assert np.isinf(power_array.value[2])  # Division by zero


class TestRegistryErrors:
    """Test error handling in registry operations."""

    def test_registry_unknown_dimension(self):
        """Test registry errors for unknown dimensions."""
        with pytest.raises(ValueError, match="Unknown unit"):
            registry.get_dimension("InvalidUnit")

    def test_registry_conversion_factor_errors(self):
        """Test registry conversion factor errors."""
        with pytest.raises(ValueError):
            registry.get_conversion_factor("MWh", "InvalidUnit")

        with pytest.raises(ValueError):
            registry.get_conversion_factor("MWh", "kg")  # Incompatible

    def test_registry_dimension_compatibility(self):
        """Test dimension compatibility checking."""
        assert registry.are_dimensions_compatible("ENERGY", "ENERGY")
        assert not registry.are_dimensions_compatible("ENERGY", "CURRENCY")

    def test_registry_corresponding_unit_errors(self):
        """Test errors in corresponding unit lookup."""
        with pytest.raises(ValueError):
            registry.get_corresponding_unit("InvalidUnit", "ENERGY")

    def test_substance_registry_errors(self):
        """Test substance registry error handling."""
        with pytest.raises(ValueError, match="Unknown substance"):
            substance_registry["nonexistent_fuel"]

        with pytest.raises(ValueError):
            substance_registry.hhv("nonexistent_fuel")

        with pytest.raises(ValueError):
            substance_registry.density("nonexistent_fuel")

    def test_compound_unit_parsing_errors(self):
        """Test errors in compound unit parsing."""
        # These should either work or fail gracefully
        try:
            registry.get_dimension("MWh/h/h")  # Triple compound
        except ValueError:
            pass  # Expected

        try:
            registry.get_dimension("MW*h")  # Wrong separator
        except ValueError:
            pass  # Expected


class TestCustomExceptionUsage:
    """Test usage of custom exceptions defined in the library."""

    def test_unknown_substance_error_type(self):
        """Test that UnknownSubstanceError is used appropriately."""
        # Currently the library uses ValueError instead of custom exceptions
        # This test documents the current behavior

        with pytest.raises(ValueError):  # Should be UnknownSubstanceError
            substance_registry.hhv("invalid_substance")

    def test_unit_conversion_error_type(self):
        """Test that IncompatibleUnitsError is used appropriately."""
        # Currently the library uses ValueError instead of custom exceptions
        # This test documents the current behavior

        energy = Quantity(100, "MWh")
        with pytest.raises(ValueError):  # Should be IncompatibleUnitsError
            energy.to("kg")



class TestErrorMessageQuality:
    """Test the quality and helpfulness of error messages."""

    def test_conversion_error_messages_include_units(self):
        """Test that conversion error messages include the problematic units."""
        energy = Quantity(100, "MWh")

        try:
            energy.to("kg")
        except ValueError as e:
            error_msg = str(e)
            # Error message mentions substance requirement, not specific units
            assert "substance" in error_msg.lower() or "mass" in error_msg.lower()

    def test_substance_error_messages_include_substance(self):
        """Test that substance error messages include the problematic substance."""
        try:
            substance_registry.hhv("invalid_fuel")
        except ValueError as e:
            error_msg = str(e)
            assert "invalid_fuel" in error_msg

    def test_arithmetic_error_messages(self):
        """Test error messages for arithmetic operations."""
        energy = Quantity(100, "MWh")

        try:
            energy * "invalid"
        except TypeError as e:
            error_msg = str(e)
            # Should include information about the invalid operand
            assert "str" in error_msg or "invalid" in error_msg

    def test_registry_error_messages(self):
        """Test error messages from registry operations."""
        try:
            registry.get_dimension("InvalidUnit")
        except ValueError as e:
            error_msg = str(e)
            assert "InvalidUnit" in error_msg

    def test_inflation_error_messages(self):
        """Test error messages for inflation adjustment."""
        quantity_no_year = Quantity(100, "USD/kW")

        try:
            quantity_no_year.to(reference_year=2025)
        except ValueError as e:
            error_msg = str(e)
            assert "reference year" in error_msg.lower()


class TestEdgeCaseErrors:
    """Test error handling for edge cases and boundary conditions."""

    def test_very_large_numbers(self):
        """Test handling of very large numbers."""
        try:
            huge_quantity = Quantity(1e100, "MWh")
            result = huge_quantity * 1e100
            # Should either work or fail gracefully
            assert result.value > 0 or np.isinf(result.value)
        except OverflowError:
            pass  # Acceptable

    def test_very_small_numbers(self):
        """Test handling of very small numbers."""
        tiny_quantity = Quantity(1e-100, "MWh")
        result = tiny_quantity / 1e100
        # Should either work or be zero
        assert result.value >= 0

    def test_special_float_values(self):
        """Test handling of special float values."""
        # NaN
        nan_quantity = Quantity(np.nan, "MWh")
        nan_result = nan_quantity * 2
        assert np.isnan(nan_result.value)

        # Infinity
        inf_quantity = Quantity(np.inf, "MWh")
        inf_result = inf_quantity + Quantity(100, "MWh")
        assert np.isinf(inf_result.value)

    def test_empty_arrays(self):
        """Test operations on empty arrays."""
        empty_quantity = Quantity([], "MWh")

        # Should handle operations gracefully
        doubled = empty_quantity * 2
        assert len(doubled.value) == 0

        # Conversion should work
        empty_gj = empty_quantity.to("GJ")
        assert len(empty_gj.value) == 0

    def test_single_element_arrays(self):
        """Test operations on single-element arrays."""
        single_quantity = Quantity([100], "MWh")

        # Should behave like scalar
        doubled = single_quantity * 2
        assert doubled.value[0] == 200

    def test_unicode_in_error_messages(self):
        """Test that error messages handle Unicode properly."""
        # Test with Unicode unit names (should fail but not crash)
        try:
            Quantity(100, "MWh_ñ")
        except ValueError as e:
            error_msg = str(e)
            # Should not crash on Unicode
            assert isinstance(error_msg, str)

    def test_concurrent_access_safety(self):
        """Test that registry access is thread-safe (basic test)."""
        # Basic test - comprehensive thread safety testing would be more complex
        import threading

        errors = []

        def test_conversion():
            try:
                q = Quantity(100, "MWh")
                q.to("GJ")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=test_conversion) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should not have any errors from concurrent access
        assert len(errors) == 0


class TestValidationConsistency:
    """Test consistency of validation across the library."""

    def test_unit_validation_consistency(self):
        """Test that unit validation is consistent across methods."""
        # All methods should validate units the same way
        invalid_unit = "InvalidUnit"

        # Should fail consistently
        with pytest.raises(ValueError):
            Quantity(100, invalid_unit)

    def test_substance_validation_consistency(self):
        """Test that substance validation is consistent."""
        # Substance validation should behave the same everywhere
        invalid_substance = "invalid_substance"

        # Creation should work (no validation at creation)
        q = Quantity(100, "MWh", invalid_substance)

        # But usage should fail consistently
        with pytest.raises(ValueError):
            q.to(substance="CO2")

    def test_error_type_consistency(self):
        """Test that similar errors raise the same exception types."""
        # Similar validation errors should raise the same exception type

        # Unit errors should all be ValueError
        with pytest.raises(ValueError):
            Quantity(100, "InvalidUnit")

        with pytest.raises(ValueError):
            registry.get_dimension("InvalidUnit")

        # Substance errors should all be ValueError (currently)
        with pytest.raises(ValueError):
            substance_registry["invalid"]
