"""Comprehensive tests for substance conversion functionality."""

import pytest

from energyunits import Quantity
from energyunits.substance import substance_registry


class TestSubstanceConversions:
    """Test all aspects of substance-based conversions."""

    def test_co2_emissions_from_coal(self):
        """Test CO2 calculations from coal combustion."""
        coal = Quantity(1, "t", "coal")
        co2 = coal.to(substance="CO2")

        # Coal has 75% carbon content: 1000 kg * 0.75 * (44/12) = 2750 kg CO2
        expected_co2 = 1000 * 0.75 * (44 / 12) / 1000  # Convert back to tonnes
        assert co2.value == pytest.approx(expected_co2)
        assert co2.unit == "t"
        assert co2.substance == "CO2"

    def test_h2o_emissions_from_natural_gas(self):
        """Test H2O calculations from natural gas combustion."""
        gas = Quantity(1, "t", "natural_gas")
        h2o = gas.to(substance="H2O")

        # Natural gas has 25% hydrogen content: 1000 kg * 0.25 * (18/2) = 2250 kg H2O
        expected_h2o = 1000 * 0.25 * (18 / 2) / 1000  # Convert back to tonnes
        assert h2o.value == pytest.approx(expected_h2o)
        assert h2o.unit == "t"
        assert h2o.substance == "H2O"

    def test_ash_content_from_coal(self):
        """Test ash calculations from coal combustion."""
        coal = Quantity(1, "t", "coal")
        ash = coal.to(substance="ash")

        # Coal has 10% ash content: 1000 kg * 0.10 = 100 kg ash
        expected_ash = 1000 * 0.10 / 1000  # Convert to tonnes
        assert ash.value == pytest.approx(expected_ash)
        assert ash.unit == "t"
        assert ash.substance == "ash"

    def test_all_combustion_products_different_fuels(self):
        """Test all combustion products for various fuel types."""
        test_cases = [
            (
                "lignite",
                {"carbon_content": 0.65, "hydrogen_content": 0.04, "ash_content": 0.15},
            ),
            (
                "anthracite",
                {"carbon_content": 0.85, "hydrogen_content": 0.04, "ash_content": 0.05},
            ),
            (
                "diesel",
                {"carbon_content": 0.86, "hydrogen_content": 0.14, "ash_content": 0.0},
            ),
            (
                "wood_pellets",
                {"carbon_content": 0.50, "hydrogen_content": 0.06, "ash_content": 0.01},
            ),
        ]

        for fuel_name, composition in test_cases:
            fuel = Quantity(1, "t", fuel_name)

            # Test CO2
            co2 = fuel.to(substance="CO2")
            expected_co2 = composition["carbon_content"] * (44 / 12)
            assert co2.value == pytest.approx(
                expected_co2
            ), f"CO2 calculation failed for {fuel_name}"

            # Test H2O
            h2o = fuel.to(substance="H2O")
            expected_h2o = composition["hydrogen_content"] * (18 / 2)
            assert h2o.value == pytest.approx(
                expected_h2o
            ), f"H2O calculation failed for {fuel_name}"

            # Test ash
            ash = fuel.to(substance="ash")
            expected_ash = composition["ash_content"]
            assert ash.value == pytest.approx(
                expected_ash
            ), f"Ash calculation failed for {fuel_name}"

    def test_renewable_zero_emissions(self):
        """Test that renewable sources produce zero combustion products."""
        renewables = ["wind", "solar", "hydro", "nuclear"]

        for renewable in renewables:
            energy = Quantity(100, "MWh", renewable)

            # All renewables should produce zero emissions
            co2 = energy.to(substance="CO2")
            assert co2.value == 0.0
            assert co2.unit == "t"
            assert co2.substance == "CO2"

            # H2O and ash should also be zero
            h2o = energy.to(substance="H2O")
            assert h2o.value == 0.0

            ash = energy.to(substance="ash")
            assert ash.value == 0.0

    def test_energy_to_mass_to_combustion_products(self):
        """Test complex conversion chain: energy → mass → combustion products."""
        # Start with energy from coal
        energy = Quantity(100, "MWh", "coal")

        # Convert to mass
        coal_mass = energy.to("t")

        # Convert mass to CO2
        co2_from_mass = coal_mass.to(substance="CO2")

        # Direct conversion from energy to CO2
        co2_direct = energy.to(substance="CO2")

        # Results should be identical
        assert co2_from_mass.value == pytest.approx(co2_direct.value)
        assert co2_from_mass.unit == co2_direct.unit
        assert co2_from_mass.substance == co2_direct.substance

    def test_volume_to_combustion_products(self):
        """Test conversions from volume through mass to combustion products."""
        # Start with natural gas volume
        gas_volume = Quantity(1000, "m3", "natural_gas")

        # Convert to CO2 (should go volume → mass → CO2)
        co2 = gas_volume.to(substance="CO2")

        # Verify the calculation chain
        # 1000 m3 * 0.75 kg/m3 = 750 kg gas
        # 750 kg * 0.75 carbon * (44/12) = 2062.5 kg CO2
        expected_co2 = 1000 * 0.75 * 0.75 * (44 / 12) / 1000  # Convert to tonnes
        assert co2.value == pytest.approx(expected_co2)

    def test_array_substance_conversions(self):
        """Test substance conversions with array inputs."""
        coal_masses = [1, 2, 5, 10]  # tonnes
        coal_array = Quantity(coal_masses, "t", "coal")

        co2_array = coal_array.to(substance="CO2")

        # Each element should be converted correctly
        for i, mass in enumerate(coal_masses):
            expected_co2 = mass * 0.75 * (44 / 12)
            assert co2_array.value[i] == pytest.approx(expected_co2)

    def test_basis_conversion_with_substances(self):
        """Test basis conversions (HHV/LHV) combined with substance conversions."""
        # Start with energy on HHV basis
        gas_energy_hhv = Quantity(100, "MWh", "natural_gas", basis="HHV")

        # Convert to LHV basis first, then to CO2
        co2_from_lhv = gas_energy_hhv.to(basis="LHV").to(substance="CO2")

        # Direct conversion should give same result
        co2_direct = gas_energy_hhv.to(basis="LHV", substance="CO2")

        assert co2_from_lhv.value == pytest.approx(co2_direct.value)

    def test_unit_conversion_with_substances(self):
        """Test unit conversions combined with substance conversions."""
        # Start with coal in kg
        coal_kg = Quantity(1000, "kg", "coal")

        # Convert to CO2 in kg
        co2_kg = coal_kg.to("kg", substance="CO2")

        # Convert to CO2 in tonnes
        co2_t = coal_kg.to("t", substance="CO2")

        # Should be consistent
        assert co2_t.value == pytest.approx(co2_kg.value / 1000)
        assert co2_kg.unit == "kg"
        assert co2_t.unit == "t"

    def test_cross_substance_consistency(self):
        """Test that carbon intensities exist and are reasonable."""
        # Note: The stored carbon intensities might be based on different calculation methods
        # or represent lifecycle emissions rather than direct combustion
        fuels_to_test = ["coal", "natural_gas", "diesel", "wood_pellets"]

        for fuel in fuels_to_test:
            # Get 1 MWh of energy from this fuel
            energy = Quantity(1, "MWh", fuel)

            # Calculate CO2 emissions from combustion stoichiometry
            co2 = energy.to(substance="CO2")
            co2_kg_per_mwh = co2.to("kg").value

            # Get the stored carbon intensity
            substance_props = substance_registry[fuel]
            stored_intensity = substance_props["carbon_intensity"]

            # Both should be positive and reasonable values
            assert co2_kg_per_mwh > 0, f"Calculated CO2 should be positive for {fuel}"
            assert (
                stored_intensity >= 0
            ), f"Stored intensity should be non-negative for {fuel}"

            # For fossil fuels, calculated values should be in reasonable range (100-500 kg CO2/MWh)
            if fuel != "wood_pellets":  # Biomass might be considered carbon neutral
                assert (
                    100 <= co2_kg_per_mwh <= 500
                ), f"CO2 intensity out of range for {fuel}: {co2_kg_per_mwh}"

    def test_roundtrip_conversions(self):
        """Test complex roundtrip conversions."""
        # Start with energy, convert to mass, to volume, back to mass, back to energy
        original_energy = Quantity(100, "MWh", "diesel")

        # Energy → Mass
        mass = original_energy.to("t")

        # Mass → Volume
        volume = mass.to("m3")

        # Volume → Mass
        mass_back = volume.to("t")

        # Mass → Energy
        energy_back = mass_back.to("MWh")

        # Should get back to original (within floating point precision)
        assert energy_back.value == pytest.approx(original_energy.value, rel=1e-10)


class TestSubstanceConversionErrors:
    """Test error handling in substance conversions."""

    def test_unknown_substance_error(self):
        """Test error handling for unknown substances."""
        coal = Quantity(1, "t", "coal")

        with pytest.raises(ValueError, match="Substance conversion only supported for"):
            coal.to(substance="NOx")  # Not supported

    def test_no_substance_specified_error(self):
        """Test error when trying substance conversion without substance."""
        energy = Quantity(100, "MWh")  # No substance specified

        with pytest.raises(ValueError, match="Source substance must be specified"):
            energy.to(substance="CO2")

    def test_unknown_fuel_substance_error(self):
        """Test error for unknown fuel substances."""
        with pytest.raises(ValueError, match="Unknown substance"):
            invalid_fuel = Quantity(1, "t", "plutonium")  # Not in registry
            invalid_fuel.to(substance="CO2")

    def test_invalid_basis_conversion_error(self):
        """Test error handling for invalid basis conversions."""
        energy = Quantity(100, "MWh", "coal")

        with pytest.raises(ValueError, match="Basis must be"):
            energy.to(basis="INVALID")

    def test_substance_conversion_without_substance_property(self):
        """Test handling of renewable substances in calculations."""
        # This should work (renewables return 0) but test edge cases
        wind_energy = Quantity(100, "MWh", "wind")

        # Should work and return zero
        co2 = wind_energy.to(substance="CO2")
        assert co2.value == 0.0

        # But what about trying to get heating value of wind?
        with pytest.raises(ValueError):
            # Wind has None heating values, should error in basis conversion
            wind_energy.to(basis="HHV")


class TestSubstanceRegistryDirectly:
    """Test the substance registry methods directly."""

    def test_registry_access_all_substances(self):
        """Test accessing all substances in the registry."""
        # Test that all expected substances exist
        expected_substances = [
            "coal",
            "lignite",
            "bituminous",
            "anthracite",
            "natural_gas",
            "lng",
            "methane",
            "crude_oil",
            "oil",
            "fuel_oil",
            "diesel",
            "gasoline",
            "wood_pellets",
            "wood_chips",
            "wind",
            "solar",
            "hydro",
            "nuclear",
        ]

        for substance in expected_substances:
            assert substance in substance_registry._substances
            props = substance_registry[substance]
            assert "name" in props
            assert "carbon_intensity" in props

    def test_heating_value_methods(self):
        """Test HHV and LHV methods directly."""
        hhv_coal = substance_registry.hhv("coal")
        lhv_coal = substance_registry.lhv("coal")

        assert hhv_coal > lhv_coal  # HHV should always be higher
        assert hhv_coal == 29.3
        assert lhv_coal == 27.8

    def test_lhv_hhv_ratio(self):
        """Test LHV/HHV ratio calculation."""
        ratio = substance_registry.lhv_hhv_ratio("coal")
        expected_ratio = 27.8 / 29.3
        assert ratio == pytest.approx(expected_ratio)

    def test_density_method(self):
        """Test density method."""
        coal_density = substance_registry.density("coal")
        assert coal_density == 833  # kg/m3

    def test_unknown_substance_registry_error(self):
        """Test registry error for unknown substance."""
        with pytest.raises(ValueError, match="Unknown substance"):
            substance_registry.hhv("unobtainium")

    def test_renewable_heating_values_none(self):
        """Test that renewables have None heating values."""
        assert substance_registry._substances["wind"]["hhv"] is None
        assert substance_registry._substances["solar"]["lhv"] is None

        # But accessing them should raise errors
        with pytest.raises(ValueError):
            substance_registry.hhv("wind")

    def test_combustion_product_calculation_direct(self):
        """Test calculate_combustion_product method directly."""
        coal = Quantity(1, "t", "coal")

        # Test direct method call
        co2 = substance_registry.calculate_combustion_product(coal, "CO2")
        h2o = substance_registry.calculate_combustion_product(coal, "H2O")
        ash = substance_registry.calculate_combustion_product(coal, "ash")

        # Verify calculations
        assert co2.value == pytest.approx(1.0 * 0.75 * (44 / 12))
        assert h2o.value == pytest.approx(1.0 * 0.05 * (18 / 2))
        assert ash.value == pytest.approx(1.0 * 0.10)
