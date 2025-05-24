"""
Tests for runtime registry extensibility.

Tests the ability to add, modify, and remove units and substances
from the registries at runtime.
"""

import pytest

from energyunits import Quantity
from energyunits.registry import registry
from energyunits.substance import substance_registry


class TestUnitRegistryExtensibility:
    """Test unit registry extensibility features."""

    def test_add_new_unit(self):
        """Test adding a new unit to the registry."""
        # Add horsepower using the user-friendly method
        registry.add_unit_with_reference("hp", "POWER", 0.746, "kW")  # 1 hp = 0.746 kW

        # Test the new unit works
        power_hp = Quantity(100, "hp")
        power_kw = power_hp.to("kW")

        assert power_kw.value == pytest.approx(74.6)
        assert power_kw.unit == "kW"

        # Test unit info
        info = registry.get_unit_info("hp")
        assert info["unit"] == "hp"
        assert info["dimension"] == "POWER"
        assert info["conversion_factor"] == pytest.approx(0.000746, rel=1e-4)
        assert not info["is_base_unit"]

    def test_add_unit_with_correspondence(self):
        """Test adding units with power/energy correspondence."""
        # Add hp and hp·h with correspondence
        registry.add_unit_with_reference("hp", "POWER", 0.746, "kW")
        registry.add_unit_with_reference("hp·h", "ENERGY", 0.746, "kWh")
        registry.add_corresponding_unit("hp", "hp·h")

        # Test arithmetic operations work
        power = Quantity(10, "hp")
        time = Quantity(2, "h")
        energy = power * time

        assert energy.unit == "hp·h"
        assert energy.value == 20

    def test_add_custom_dimension(self):
        """Test adding a completely new dimension."""
        # Add individual units first for compound unit support
        registry.add_unit_with_reference("lb", "MASS", 0.454, "kg")  # 1 lb = 0.454 kg
        registry.add_unit_with_reference("gal", "VOLUME", 3.785, "L")  # 1 gal = 3.785 L

        # Test that we can create compound quantities
        mass = Quantity(8.34, "lb")
        volume = Quantity(1.0, "gal")
        density = mass / volume  # This creates lb/gal

        # Test conversion to metric
        mass_kg = mass.to("kg")
        volume_l = volume.to("L")

        assert mass_kg.value == pytest.approx(3.78, rel=1e-2)
        assert volume_l.value == pytest.approx(3.785, rel=1e-2)

    def test_list_and_search_units(self):
        """Test listing and filtering units."""
        # Add test units
        registry.add_unit_with_reference("therm", "ENERGY", 105.5, "MJ")

        # List all units
        all_units = registry.list_units()
        assert "therm" in all_units
        assert all_units["therm"] == "ENERGY"

        # List energy units only
        energy_units = registry.list_units("ENERGY")
        assert "therm" in energy_units
        assert "MW" not in energy_units  # MW is power, not energy

    def test_remove_unit(self):
        """Test removing a unit from the registry."""
        # Add and then remove a unit
        registry.add_unit_with_reference("test_unit", "ENERGY", 1.0, "MJ")

        # Verify it exists
        assert "test_unit" in registry.list_units()

        # Remove it
        registry.remove_unit("test_unit")

        # Verify it's gone
        assert "test_unit" not in registry.list_units()

        # Should raise error if we try to use it
        with pytest.raises(ValueError, match="Unknown unit"):
            Quantity(100, "test_unit")

    def test_cannot_remove_base_unit(self):
        """Test that base units cannot be removed."""
        with pytest.raises(ValueError, match="Cannot remove base unit"):
            registry.remove_unit("MW")  # MW is base unit for POWER

    def test_registry_validation(self):
        """Test registry validation functionality."""
        # Get validation results
        issues = registry.validate_registry()

        # Should be no issues with default registry
        assert len(issues["missing_conversion_factors"]) == 0
        assert len(issues["orphaned_correspondences"]) == 0
        assert len(issues["missing_base_units"]) == 0

    def test_unit_arithmetic_with_custom_units(self):
        """Test that arithmetic operations work with custom units."""
        # Add British thermal units
        registry.add_unit_with_reference(
            "BTU", "ENERGY", 1.055, "kJ"
        )  # 1 BTU = 1.055 kJ
        registry.add_unit_with_reference(
            "BTU/h", "POWER", 0.293, "W"
        )  # 1 BTU/h ≈ 0.293 W
        registry.add_corresponding_unit("BTU/h", "BTU")

        # Test power * time = energy
        heating_rate = Quantity(10000, "BTU/h")
        time = Quantity(8, "h")
        energy = heating_rate * time

        assert energy.unit == "BTU"
        assert energy.value == 80000

        # Test conversion to standard units
        energy_mj = energy.to("MJ")
        assert energy_mj.value == pytest.approx(84.4, rel=1e-2)

    def test_error_handling(self):
        """Test error cases for unit registry extension."""
        # Test missing required parameters
        with pytest.raises(TypeError):
            registry.add_unit("bad_unit", "ENERGY")

        # Test removing non-existent unit
        with pytest.raises(ValueError, match="not found"):
            registry.remove_unit("non_existent_unit")

        # Test getting info for non-existent unit
        with pytest.raises(ValueError, match="not found"):
            registry.get_unit_info("non_existent_unit")


class TestSubstanceRegistryExtensibility:
    """Test substance registry extensibility features."""

    def test_add_custom_substance(self):
        """Test adding a custom substance."""
        # Add a custom coal type
        substance_registry.add_substance(
            "my_coal",
            {
                "name": "High-Grade Coal",
                "hhv": 32.0,  # MJ/kg
                "lhv": 30.5,
                "density": 900,  # kg/m3
                "carbon_intensity": 380,  # kg CO2/MWh
                "carbon_content": 0.85,
                "ash_content": 0.05,
            },
        )

        # Test using the custom substance
        coal = Quantity(1000, "kg", substance="my_coal")
        energy = coal.to("MWh", basis="LHV")

        assert energy.value == pytest.approx(8.47, rel=1e-2)  # 30.5 MJ/kg ≈ 8.47 kWh/kg

    def test_update_existing_substance(self):
        """Test updating properties of existing substance."""
        # Add a substance first
        substance_registry.add_substance(
            "test_fuel",
            {
                "hhv": 25.0,
                "lhv": 23.0,
                "density": 700,
                "carbon_intensity": 300,
                "carbon_content": 0.70,
            },
        )

        # Update it
        substance_registry.update_substance(
            "test_fuel", {"hhv": 26.0, "carbon_intensity": 320}
        )

        # Verify updates
        info = substance_registry.get_substance_info("test_fuel")
        assert info["hhv"] == 26.0
        assert info["carbon_intensity"] == 320
        assert info["lhv"] == 23.0  # Should remain unchanged

    def test_substance_search(self):
        """Test searching for substances by criteria."""
        # Add test substances
        substance_registry.add_substance(
            "high_carbon_fuel",
            {
                "hhv": 30.0,
                "lhv": 28.0,
                "density": 800,
                "carbon_intensity": 400,
                "carbon_content": 0.90,
            },
        )
        substance_registry.add_substance(
            "low_carbon_fuel",
            {
                "hhv": 20.0,
                "lhv": 18.0,
                "density": 600,
                "carbon_intensity": 200,
                "carbon_content": 0.60,
            },
        )

        # Search for high-carbon fuels
        high_carbon = substance_registry.search_substances(carbon_content__gt=0.8)
        assert "high_carbon_fuel" in high_carbon
        assert "low_carbon_fuel" not in high_carbon

        # Search by HHV range
        mid_hhv = substance_registry.search_substances(hhv__range=(25, 35))
        assert "high_carbon_fuel" in mid_hhv
        assert "low_carbon_fuel" not in mid_hhv

    def test_substance_validation(self):
        """Test substance validation."""
        # Add valid substance
        substance_registry.add_substance(
            "valid_fuel",
            {
                "hhv": 25.0,
                "lhv": 23.0,
                "density": 800,
                "carbon_intensity": 300,
                "carbon_content": 0.75,
                "hydrogen_content": 0.05,
                "ash_content": 0.10,
            },
        )

        validation = substance_registry.validate_substance("valid_fuel")
        assert validation["valid"] is True
        assert len(validation["issues"]) == 0

        # Add invalid substance (LHV > HHV)
        substance_registry.add_substance(
            "invalid_fuel",
            {
                "hhv": 20.0,
                "lhv": 25.0,
                "density": 800,  # LHV > HHV!
                "carbon_intensity": 300,
                "carbon_content": 0.75,
            },
        )

        validation = substance_registry.validate_substance("invalid_fuel")
        assert validation["valid"] is False
        assert "LHV cannot be greater than HHV" in validation["issues"]

    def test_substance_removal(self):
        """Test removing substances."""
        # Add and remove substance
        substance_registry.add_substance(
            "temp_fuel",
            {
                "hhv": 25.0,
                "lhv": 23.0,
                "density": 800,
                "carbon_intensity": 300,
                "carbon_content": 0.75,
            },
        )

        assert "temp_fuel" in substance_registry.list_substances()

        substance_registry.remove_substance("temp_fuel")

        assert "temp_fuel" not in substance_registry.list_substances()

    def test_substance_with_custom_units(self):
        """Test using custom substances with custom units."""
        # Add custom substance and units
        substance_registry.add_substance(
            "my_biomass",
            {
                "hhv": 18.0,
                "lhv": 16.5,
                "density": 400,
                "carbon_intensity": 0,  # Carbon neutral
                "carbon_content": 0.0,  # No carbon content for CO2 calculation
            },
        )

        registry.add_unit_with_reference("ton", "MASS", 1000, "kg")  # US short ton

        # Test conversions
        biomass = Quantity(2, "ton", substance="my_biomass")
        energy = biomass.to("MWh", basis="LHV")
        co2 = biomass.to("t", substance="CO2")

        assert energy.value == pytest.approx(9.17, rel=1e-2)
        assert co2.value == 0  # Carbon neutral

    def test_error_handling_substances(self):
        """Test error cases for substance registry."""
        # Missing required properties
        with pytest.raises(ValueError, match="Missing required property"):
            substance_registry.add_substance(
                "bad_substance",
                {
                    "hhv": 25.0
                    # Missing other required properties
                },
            )

        # Update non-existent substance
        with pytest.raises(ValueError, match="not found"):
            substance_registry.update_substance("non_existent", {"hhv": 30})

        # Remove non-existent substance
        with pytest.raises(ValueError, match="not found"):
            substance_registry.remove_substance("non_existent")


class TestIntegratedExtensibility:
    """Test integrated use of extended registries."""

    def test_complete_custom_system(self):
        """Test a complete custom unit/substance system."""
        # Add British thermal system
        registry.add_unit_with_reference("BTU", "ENERGY", 1.055, "kJ")
        registry.add_unit_with_reference("lb", "MASS", 0.454, "kg")
        # Note: BTU/lb is a compound unit that will be handled automatically

        # Add custom coal with BTU-based properties
        substance_registry.add_substance(
            "us_coal",
            {
                "name": "US Coal (BTU basis)",
                "hhv": 26.8,  # MJ/kg (≈ 11,500 BTU/lb)
                "lhv": 25.6,
                "density": 833,
                "carbon_intensity": 340,
                "carbon_content": 0.75,
            },
        )

        # Test the complete system
        coal_mass = Quantity(2000, "lb", substance="us_coal")  # 1 ton
        coal_energy = coal_mass.to("BTU", basis="LHV")
        coal_co2 = coal_mass.to("lb", substance="CO2")

        # Verify reasonable values
        assert coal_energy.value > 20e6  # Should be > 20 million BTU
        assert coal_co2.value > 2000  # Should produce more than 2000 lb CO2

    def test_extensibility_persistence(self):
        """Test that extensions persist across operations."""
        # Add custom units
        registry.add_unit_with_reference("custom_energy", "ENERGY", 2.0, "MJ")
        substance_registry.add_substance(
            "custom_fuel",
            {
                "hhv": 30.0,
                "lhv": 28.0,
                "density": 800,
                "carbon_intensity": 350,
                "carbon_content": 0.80,
            },
        )

        # Use them in multiple operations
        fuel1 = Quantity(100, "kg", substance="custom_fuel")
        fuel2 = Quantity(200, "kg", substance="custom_fuel")

        total_fuel = fuel1 + fuel2
        total_energy = total_fuel.to("custom_energy", basis="LHV")

        assert total_fuel.value == 300
        assert total_energy.unit == "custom_energy"

        # Should still work after other operations
        energy_per_kg = total_energy / total_fuel
        assert energy_per_kg.unit == "custom_energy/kg"
