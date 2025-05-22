"""
Error handling tests for the EnergyUnits library.

These tests verify that appropriate errors are raised for invalid operations
and that error messages are helpful and descriptive.
"""

import numpy as np
import pytest

from energyunits import Quantity
from energyunits.registry import registry


class TestRegistryErrors:
    def test_unknown_unit_errors(self):
        """Test errors for unknown units."""
        # Unknown unit in get_dimension
        with pytest.raises(ValueError) as excinfo:
            registry.get_dimension("unknown_unit")
        assert "Unknown unit: unknown_unit" in str(excinfo.value)

        # Unknown unit in get_conversion_factor
        with pytest.raises(ValueError) as excinfo:
            registry.get_conversion_factor("unknown_unit", "MWh")
        assert "Unknown unit: unknown_unit" in str(excinfo.value)

        with pytest.raises(ValueError) as excinfo:
            registry.get_conversion_factor("MWh", "unknown_unit")
        assert "Unknown unit: unknown_unit" in str(excinfo.value)

        # Unknown unit in get_corresponding_unit
        with pytest.raises(ValueError) as excinfo:
            registry.get_corresponding_unit("unknown_unit", "ENERGY")
        assert "Unknown unit: unknown_unit" in str(excinfo.value)

    def test_incompatible_unit_errors(self):
        """Test errors for incompatible unit conversions."""
        # Incompatible units in get_conversion_factor
        with pytest.raises(ValueError) as excinfo:
            registry.get_conversion_factor("MWh", "kg")
        assert "Incompatible units: MWh and kg" in str(excinfo.value)

        # Incompatible dimensions in convert_between_dimensions
        with pytest.raises(ValueError) as excinfo:
            registry.convert_between_dimensions(100, "MWh", "kg")
        assert "No conversion defined between ENERGY and MASS" in str(excinfo.value)

    def test_missing_substance_errors(self):
        """Test errors when substance is missing but required."""
        # Mass to volume conversion requires substance
        with pytest.raises(ValueError) as excinfo:
            registry.convert_between_dimensions(1000, "kg", "m3", substance=None)
        assert "Substance must be specified" in str(excinfo.value)

        # Volume to mass conversion requires substance
        with pytest.raises(ValueError) as excinfo:
            registry.convert_between_dimensions(1, "m3", "kg", substance=None)
        assert "Substance must be specified" in str(excinfo.value)

    def test_unknown_substance_errors(self):
        """Test errors for unknown substances."""
        # Unknown substance in convert_between_dimensions
        with pytest.raises(ValueError) as excinfo:
            registry.convert_between_dimensions(
                1000, "kg", "m3", substance="unknown_substance"
            )
        assert "Unknown substance: unknown_substance" in str(excinfo.value)


class TestQuantityErrors:
    def test_initialization_errors(self):
        """Test errors during Quantity initialization."""
        # Unknown unit
        with pytest.raises(ValueError) as excinfo:
            Quantity(100, "unknown_unit")
        assert "Unknown unit: unknown_unit" in str(excinfo.value)

    def test_conversion_errors(self):
        """Test errors in Quantity.to() method."""
        # Incompatible units
        energy = Quantity(100, "MWh")
        with pytest.raises(ValueError) as excinfo:
            energy.to("kg")
        assert "Cannot convert from MWh (ENERGY) to kg (MASS)" in str(excinfo.value)

        # Unknown target unit
        with pytest.raises(ValueError) as excinfo:
            energy.to("unknown_unit")
        assert "Unknown unit: unknown_unit" in str(excinfo.value)

    def test_duration_errors(self):
        """Test errors in for_duration and average_power methods."""
        # for_duration only applies to power
        energy = Quantity(100, "MWh")
        with pytest.raises(ValueError) as excinfo:
            energy.for_duration(hours=1)
        assert "for_duration only applies to power units" in str(excinfo.value)

        # average_power only applies to energy
        power = Quantity(100, "MW")
        with pytest.raises(ValueError) as excinfo:
            power.average_power(hours=1)
        assert "average_power only applies to energy units" in str(excinfo.value)

    def test_substance_errors(self):
        """Test errors related to substance handling."""
        # Energy content calculation requires substance
        energy = Quantity(100, "MWh")  # No substance
        with pytest.raises(ValueError) as excinfo:
            energy.energy_content()
        assert "Substance must be specified" in str(excinfo.value)

        # Heating value conversion requires substance
        energy = Quantity(100, "MWh")  # No substance
        with pytest.raises(ValueError) as excinfo:
            energy.to_lhv()
        assert "Substance must be specified" in str(excinfo.value)

        # Usable energy calculation requires substance
        biomass = Quantity(100, "t")  # No substance
        with pytest.raises(ValueError) as excinfo:
            biomass.usable_energy()
        assert "Substance must be specified" in str(excinfo.value)

        # Invalid moisture content
        biomass = Quantity(100, "t", "wood_pellets")
        with pytest.raises(ValueError) as excinfo:
            biomass.usable_energy(moisture_content=1.5)  # > 1.0
        assert "Moisture content must be between 0 and 1" in str(excinfo.value)

    def test_arithmetic_errors(self):
        """Test errors in arithmetic operations."""
        # Cannot add Quantity and non-Quantity
        energy = Quantity(100, "MWh")
        with pytest.raises(TypeError) as excinfo:
            energy + 50  # Not a Quantity
        assert "Cannot add Quantity and" in str(excinfo.value)

        # Multiplication between quantities not implemented
        energy1 = Quantity(100, "MWh")
        energy2 = Quantity(50, "MWh")
        with pytest.raises(NotImplementedError) as excinfo:
            energy1 * energy2
        assert "Multiplication between quantities not implemented" in str(excinfo.value)

    def test_emissions_calculation_errors(self):
        """Test errors in emissions calculations."""
        # Cannot calculate emissions for non-energy without substance
        mass = Quantity(100, "t")  # No substance
        with pytest.raises(ValueError) as excinfo:
            mass.calculate_emissions()
        assert "Cannot calculate emissions" in str(excinfo.value)

    def test_inflation_adjustment_errors(self):
        """Test errors in inflation adjustments."""
        # Reference year required
        cost = Quantity(100, "USD/kW")  # No reference_year
        with pytest.raises(ValueError) as excinfo:
            cost.adjust_inflation(target_year=2025)
        assert "Reference year not specified" in str(excinfo.value)
