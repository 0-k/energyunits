"""
Unit tests for the UnitRegistry class.

These tests verify the core functionality of the registry including unit conversions,
dimension relationships, and the handling of compound units.
"""

import numpy as np
import pytest

from energyunits.registry import registry
from energyunits.substance import substance_registry


class TestUnitRegistry:

    def test_basic_unit_conversions(self):
        """Test basic unit conversion factors."""
        # Energy units
        assert registry.get_conversion_factor("MWh", "GJ") == pytest.approx(3.6)
        assert registry.get_conversion_factor("GJ", "MWh") == pytest.approx(0.277778)
        assert registry.get_conversion_factor("kWh", "MWh") == pytest.approx(0.001)
        assert registry.get_conversion_factor("MWh", "kWh") == pytest.approx(1000)

        # Power units
        assert registry.get_conversion_factor("MW", "kW") == pytest.approx(1000)
        assert registry.get_conversion_factor("GW", "MW") == pytest.approx(1000)

        # Mass units
        assert registry.get_conversion_factor("kg", "t") == pytest.approx(0.001)
        assert registry.get_conversion_factor("t", "kg") == pytest.approx(1000)

        # Volume units
        assert registry.get_conversion_factor("L", "m3") == pytest.approx(0.001)
        assert registry.get_conversion_factor("barrel", "m3") == pytest.approx(0.159)

        # Time units
        assert registry.get_conversion_factor("min", "h") == pytest.approx(1 / 60)
        assert registry.get_conversion_factor("h", "s") == pytest.approx(3600)

    def test_large_unit_conversions(self):
        """Test conversions between very large and small units."""
        # Very large energy units
        assert registry.get_conversion_factor("TWh", "kWh") == pytest.approx(1e9)
        assert registry.get_conversion_factor("PJ", "MJ") == pytest.approx(1e9)
        assert registry.get_conversion_factor("EJ", "GJ") == pytest.approx(1e9)

        # Very small energy units
        assert registry.get_conversion_factor("J", "GJ") == pytest.approx(1e-9)
        assert registry.get_conversion_factor("Wh", "MWh") == pytest.approx(1e-6)

        # Large mass units
        assert registry.get_conversion_factor("Mt", "kg") == pytest.approx(1e9)
        assert registry.get_conversion_factor("g", "t") == pytest.approx(1e-6)

    def test_compound_unit_conversions(self):
        """Test conversions between compound units."""
        # Energy prices
        assert registry.get_conversion_factor("USD/MWh", "USD/GJ") == pytest.approx(
            0.277778
        )
        assert registry.get_conversion_factor("EUR/GJ", "EUR/MWh") == pytest.approx(3.6)

        # Different currencies
        # For example USD/MWh to EUR/MWh would convert USD to EUR
        price_factor = registry.get_conversion_factor("USD/MWh", "EUR/MWh")
        currency_factor = registry.get_conversion_factor("USD", "EUR")
        assert price_factor == pytest.approx(currency_factor)
        assert price_factor == pytest.approx(1 / 1.08)

        # Energy intensity
        assert registry.get_conversion_factor("MWh/t", "GJ/t") == pytest.approx(3.6)

    def test_dimension_relationships(self):
        """Test conversions between related dimensions."""
        # Energy to Power - 24 MWh over 24 hours = 1 MW
        result = registry.convert_between_dimensions(24, "MWh", "MW", hours=24)
        assert result == pytest.approx(1.0)

        # Power to Energy - 10 MW for 5 hours = 50 MWh
        result = registry.convert_between_dimensions(10, "MW", "MWh", hours=5)
        assert result == pytest.approx(50.0)

        # Test various units
        result = registry.convert_between_dimensions(1, "GW", "GWh", hours=1)
        assert result == pytest.approx(1.0)

        result = registry.convert_between_dimensions(2.4, "TWh", "TW", hours=24)
        assert result == pytest.approx(0.1)

    def test_substance_based_conversions(self):
        """Test substance-specific conversions between mass and volume."""
        # Create temporary test data in the substance registry if needed
        if "water" not in substance_registry._substances:
            substance_registry._substances["water"] = {
                "name": "Water",
                "density": 1000,  # kg/m3
                "hhv": 0,
                "lhv": 0,
                "carbon_intensity": 0,
                "moisture_content": 0,
            }

        # Mass to volume for water (1000 kg = 1 m3)
        result = registry.convert_between_dimensions(
            1000, "kg", "m3", substance="water"
        )
        assert result == pytest.approx(1.0, rel=1e-2)

        # Volume to mass for water (2 m3 = 2000 kg)
        result = registry.convert_between_dimensions(2, "m3", "kg", substance="water")
        assert result == pytest.approx(2000.0, rel=1e-2)

        # Test with natural gas
        # Natural gas density ≈ 0.75 kg/m3
        # 750 kg of natural gas ≈ 1000 m3
        result = registry.convert_between_dimensions(
            750, "kg", "m3", substance="natural_gas"
        )
        assert result == pytest.approx(1000.0, rel=0.1)

        # Test with different units
        # 1 t of LNG ≈ 2.22 m3 (using density of 450 kg/m3)
        result = registry.convert_between_dimensions(1, "t", "m3", substance="lng")
        assert result == pytest.approx(1000 / 450, rel=0.1)

    def test_corresponding_units(self):
        """Test getting corresponding units in related dimensions."""
        # Power to Energy
        assert registry.get_corresponding_unit("MW", "ENERGY") == "MWh"
        assert registry.get_corresponding_unit("kW", "ENERGY") == "kWh"
        assert registry.get_corresponding_unit("GW", "ENERGY") == "GWh"

        # Energy to Power
        assert registry.get_corresponding_unit("MWh", "POWER") == "MW"
        assert registry.get_corresponding_unit("kWh", "POWER") == "kW"
        assert registry.get_corresponding_unit("GWh", "POWER") == "GW"

    def test_are_dimensions_compatible(self):
        """Test the dimension compatibility check."""
        # Same dimension is always compatible
        assert registry.are_dimensions_compatible("ENERGY", "ENERGY") == True
        assert registry.are_dimensions_compatible("POWER", "POWER") == True

        # Related dimensions
        assert registry.are_dimensions_compatible("ENERGY", "POWER") == True
        assert registry.are_dimensions_compatible("POWER", "ENERGY") == True
        assert registry.are_dimensions_compatible("MASS", "VOLUME") == True
        assert registry.are_dimensions_compatible("VOLUME", "MASS") == True

        # Energy system conversions (NEW in this version!)
        assert registry.are_dimensions_compatible("ENERGY", "MASS") == True
        assert registry.are_dimensions_compatible("MASS", "ENERGY") == True
        assert registry.are_dimensions_compatible("ENERGY", "VOLUME") == True
        assert registry.are_dimensions_compatible("VOLUME", "ENERGY") == True

        # Truly unrelated dimensions
        assert registry.are_dimensions_compatible("ENERGY", "CURRENCY") == False
        assert registry.are_dimensions_compatible("POWER", "CURRENCY") == False
        assert registry.are_dimensions_compatible("MASS", "TIME") == False
