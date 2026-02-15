"""Tests for complex conversion chains and multi-step operations."""

import numpy as np
import pytest

from energyunits import Quantity


class TestComplexConversionChains:
    """Test complex multi-step conversion chains."""

    def test_energy_mass_volume_roundtrip(self):
        """Test roundtrip conversion: energy → mass → volume → mass → energy."""
        # Start with energy from diesel
        original_energy = Quantity(100, "MWh", "diesel")

        # Convert to mass
        diesel_mass = original_energy.to("t")

        # Convert to volume
        diesel_volume = diesel_mass.to("m3")

        # Convert back to mass
        mass_back = diesel_volume.to("t")

        # Convert back to energy
        energy_back = mass_back.to("MWh")

        # Should get back to original (within floating point precision)
        assert energy_back.value == pytest.approx(original_energy.value, rel=1e-10)
        assert energy_back.unit == original_energy.unit
        assert energy_back.substance == original_energy.substance

    def test_basis_unit_substance_chain(self):
        """Test conversion chain involving basis, unit, and substance conversions."""
        # Start with coal energy on HHV basis
        coal_energy_hhv = Quantity(1000, "MWh", "coal", basis="HHV")

        # Convert to LHV basis
        coal_energy_lhv = coal_energy_hhv.to(basis="LHV")

        # Convert to different energy unit
        coal_energy_gj = coal_energy_lhv.to("GJ")

        # Convert to mass
        coal_mass = coal_energy_gj.to("t")

        # Convert to combustion products
        co2_emissions = coal_mass.to(substance="CO2")
        h2o_emissions = coal_mass.to(substance="H2O")
        ash_content = coal_mass.to(substance="ash")

        # Verify all conversions worked
        assert coal_energy_lhv.basis == "LHV"
        assert coal_energy_gj.unit == "GJ"
        assert coal_mass.unit == "t"
        assert co2_emissions.substance == "CO2"
        assert h2o_emissions.substance == "H2O"
        assert ash_content.substance == "ash"

        # Values should be reasonable
        assert co2_emissions.value > 0
        assert h2o_emissions.value > 0
        assert ash_content.value > 0

    def test_cross_fuel_conversion_chain(self):
        """Test conversion chains involving different fuel types."""
        # Start with natural gas volume
        gas_volume = Quantity(1000, "m3", "natural_gas")

        # Convert to mass
        gas_mass = gas_volume.to("t")

        # Convert to energy
        gas_energy = gas_mass.to("MWh")

        # Calculate CO2 emissions
        gas_co2 = gas_energy.to(substance="CO2")

        # Compare with equivalent coal energy
        coal_energy = Quantity(gas_energy.value, "MWh", "coal")
        coal_co2 = coal_energy.to(substance="CO2")

        # Coal should produce more CO2 than natural gas for same energy
        assert coal_co2.value > gas_co2.value

    def test_unit_scaling_chain(self):
        """Test conversion chains across different unit scales."""
        # Start with small energy amount
        energy_kwh = Quantity(100, "kWh", "coal")

        # Scale up through different units
        energy_mwh = energy_kwh.to("MWh")
        energy_gwh = energy_mwh.to("GWh")
        energy_twh = energy_gwh.to("TWh")

        # Convert to different energy units
        energy_gj = energy_twh.to("GJ")
        energy_mj = energy_gj.to("MJ")
        energy_j = energy_mj.to("J")

        # Scale back down
        energy_kj = energy_j.to("kJ")
        energy_mj_back = energy_kj.to("MJ")
        energy_gj_back = energy_mj_back.to("GJ")
        energy_kwh_back = energy_gj_back.to("kWh")

        # Should get back to original
        assert energy_kwh_back.value == pytest.approx(energy_kwh.value, rel=1e-8)

    def test_power_energy_time_conversions(self):
        """Test complex conversions involving power, energy, and time."""
        # Start with power capacity
        power_capacity = Quantity(500, "MW", "coal")

        # Convert to energy over different time periods
        energy_1h = power_capacity * Quantity(1, "h")
        energy_24h = power_capacity * Quantity(24, "h")
        energy_1yr = power_capacity * Quantity(8760, "h")

        # Convert to different power units using compound units
        power_rate_1 = Quantity(500, "MWh/h")  # Same as 500 MW
        power_rate_2 = Quantity(
            500 / 60, "MWh/min"
        )  # Same as 500 MW (500 MWh/hour = 500/60 MWh/min)

        # Convert compound units to simple power units
        power_1 = power_rate_1.to("MW")
        power_2 = power_rate_2.to("MW")

        assert power_1.value == pytest.approx(500)
        assert power_2.value == pytest.approx(500)

    def test_array_conversion_chains(self):
        """Test conversion chains with array inputs."""
        # Array of different fuel masses
        fuel_masses = [100, 200, 500, 1000]  # tonnes

        # Test each fuel type
        for fuel_type in ["coal", "natural_gas", "diesel"]:
            fuel_array = Quantity(fuel_masses, "t", fuel_type)

            # Convert to energy
            energy_array = fuel_array.to("MWh")

            # Convert to CO2 emissions
            co2_array = fuel_array.to(substance="CO2")

            # Check that arrays have correct length
            assert len(energy_array.value) == len(fuel_masses)
            assert len(co2_array.value) == len(fuel_masses)

            # Check that values increase with mass
            assert np.all(np.diff(energy_array.value) > 0)
            assert np.all(np.diff(co2_array.value) > 0)

    def test_monetary_conversion_chains(self):
        """Test conversion chains involving monetary units and inflation."""
        # Capital cost with reference year
        capex_2020 = Quantity(1200, "USD/kW", reference_year=2020)

        # Adjust for inflation
        capex_2025 = capex_2020.to(reference_year=2025)

        # Convert to different currency units (conceptually)
        capex_per_mw = capex_2025.to("USD/MW")

        # Calculate total cost for a project
        project_capacity = Quantity(100, "MW")
        total_cost_before_year = capex_per_mw * project_capacity

        # Create total cost with reference year
        total_cost = Quantity(total_cost_before_year.value, "USD", reference_year=2025)

        # Adjust to different year
        total_cost_2030 = total_cost.to(reference_year=2030)

        assert capex_2025.reference_year == 2025
        assert total_cost.unit == "USD"
        assert total_cost_2030.reference_year == 2030

    def test_mixed_substance_operations(self):
        """Test operations with different substances."""
        # Different fuel energies
        coal_energy = Quantity(100, "MWh", "coal")
        gas_energy = Quantity(200, "MWh", "natural_gas")
        oil_energy = Quantity(150, "MWh", "oil")

        # Add them (substance metadata is dropped when mixing, but preserved from
        # the last addition since coal+gas drops to None, then None+oil keeps oil)
        total_energy = coal_energy + gas_energy + oil_energy
        assert total_energy.value == 450

        # Calculate individual emissions and sum
        coal_co2 = coal_energy.to(substance="CO2")
        gas_co2 = gas_energy.to(substance="CO2")
        oil_co2 = oil_energy.to(substance="CO2")

        total_co2 = coal_co2 + gas_co2 + oil_co2
        assert total_co2.substance == "CO2"  # All same substance
        assert total_co2.value == pytest.approx(
            coal_co2.value + gas_co2.value + oil_co2.value
        )

    def test_renewable_vs_fossil_comparison(self):
        """Test conversion chains comparing renewable and fossil energy."""
        # Same amount of energy from different sources
        energy_amount = 1000  # MWh

        sources = ["wind", "solar", "coal", "natural_gas"]
        emissions = {}

        for source in sources:
            energy = Quantity(energy_amount, "MWh", source)
            co2 = energy.to(substance="CO2")
            emissions[source] = co2.value

        # Renewables should have zero emissions
        assert emissions["wind"] == 0
        assert emissions["solar"] == 0

        # Fossil fuels should have positive emissions
        assert emissions["coal"] > 0
        assert emissions["natural_gas"] > 0

        # Coal should typically have higher emissions than gas
        assert emissions["coal"] > emissions["natural_gas"]

    def test_precision_preservation_in_chains(self):
        """Test that precision is preserved through long conversion chains."""
        # Start with a precise value
        precise_value = 123.456789
        energy = Quantity(precise_value, "MWh", "diesel")

        # Long conversion chain
        result = (
            energy.to("GJ")
            .to("t")
            .to("m3")
            .to("kg")
            .to("t")
            .to("MWh")
            .to("kWh")
            .to("MWh")
        )

        # Should preserve precision reasonably well
        assert result.value == pytest.approx(precise_value, rel=1e-10)

    def test_conversion_with_combined_parameters(self):
        """Test conversions with multiple parameters at once."""
        # Start with coal energy on HHV basis
        coal_hhv = Quantity(100, "MWh", "coal", basis="HHV")

        # Single conversion with multiple parameters
        coal_lhv_gj = coal_hhv.to("GJ", basis="LHV")

        # Should be equivalent to step-by-step conversion
        coal_lhv = coal_hhv.to(basis="LHV")
        coal_lhv_gj_step = coal_lhv.to("GJ")

        assert coal_lhv_gj.value == pytest.approx(coal_lhv_gj_step.value)
        assert coal_lhv_gj.basis == "LHV"
        assert coal_lhv_gj.unit == "GJ"

    def test_error_propagation_in_chains(self):
        """Test that errors propagate correctly through conversion chains."""
        # Start with valid quantity
        energy = Quantity(100, "MWh", "coal")

        # Chain that should fail at some point
        try:
            # This should work
            mass = energy.to("t")

            # This should fail - invalid combustion product
            invalid_product = mass.to(substance="NOx")

            assert False, "Should have raised an error"
        except ValueError:
            pass  # Expected

    def test_chained_arithmetic_and_conversions(self):
        """Test combinations of arithmetic operations and conversions."""
        # Power plants with different fuels
        coal_plant = Quantity(500, "MW", "coal")
        gas_plant = Quantity(300, "MW", "natural_gas")

        # Operating hours
        hours = Quantity(8760, "h")

        # Calculate annual generation
        coal_generation = coal_plant * hours
        gas_generation = gas_plant * hours

        # Total generation
        total_generation = coal_generation + gas_generation

        # Convert to different units
        total_twh = total_generation.to("TWh")

        # Calculate emissions from each plant
        coal_co2 = coal_generation.to(substance="CO2")
        gas_co2 = gas_generation.to(substance="CO2")
        total_co2 = coal_co2 + gas_co2

        # Calculate emission intensity
        emission_intensity = total_co2 / total_generation

        # Should have reasonable units and values
        assert total_twh.unit == "TWh"
        assert emission_intensity.unit == "t/MWh"
        assert emission_intensity.value > 0


class TestConversionChainConsistency:
    """Test consistency across different conversion pathways."""

    def test_multiple_path_consistency(self):
        """Test that different conversion paths give same result."""
        coal = Quantity(1000, "kg", "coal")

        # Path 1: kg → t → CO2
        path1 = coal.to("t").to(substance="CO2")

        # Path 2: kg → CO2 → t
        path2 = coal.to(substance="CO2").to("t")

        # Should give same result
        assert path1.value == pytest.approx(path2.value)

    def test_order_independence(self):
        """Test that conversion order doesn't matter for commutative operations."""
        coal_hhv = Quantity(100, "MWh", "coal", basis="HHV")

        # Path 1: basis then unit
        result1 = coal_hhv.to(basis="LHV").to("GJ")

        # Path 2: unit then basis
        result2 = coal_hhv.to("GJ").to(basis="LHV")

        # Should give same result
        assert result1.value == pytest.approx(result2.value)
        assert result1.unit == result2.unit
        assert result1.basis == result2.basis

    def test_arithmetic_conversion_commutativity(self):
        """Test that arithmetic and conversion operations commute where expected."""
        energy1 = Quantity(100, "MWh", "coal")
        energy2 = Quantity(200, "MWh", "coal")

        # Path 1: add then convert
        sum_then_convert = (energy1 + energy2).to("GJ")

        # Path 2: convert then add
        convert_then_add = energy1.to("GJ") + energy2.to("GJ")

        # Should give same result
        assert sum_then_convert.value == pytest.approx(convert_then_add.value)

    def test_scaling_consistency(self):
        """Test that scaling operations are consistent."""
        base_energy = Quantity(1, "MWh", "coal")

        # Scale by 1000 then convert
        large_mwh = base_energy * 1000
        large_gwh = large_mwh.to("GWh")

        # Convert then scale
        base_gwh = base_energy.to("GWh")
        large_gwh_alt = base_gwh * 1000

        assert large_gwh.value == pytest.approx(large_gwh_alt.value)

    def test_inverse_operation_consistency(self):
        """Test that inverse operations cancel out."""
        original = Quantity(123.456, "MWh", "diesel", basis="LHV")

        # Apply operation and its inverse
        converted = original.to("GJ").to("MWh")

        assert converted.value == pytest.approx(original.value, rel=1e-12)
        assert converted.unit == original.unit
        assert converted.substance == original.substance
        assert converted.basis == original.basis


class TestPerformanceInChains:
    """Test performance characteristics of conversion chains."""

    def test_large_array_conversion_chains(self):
        """Test conversion chains with large arrays."""
        # Large array of values
        large_array = np.random.rand(1000) * 100 + 50  # 50-150 range
        coal_array = Quantity(large_array, "t", "coal")

        # Chain of conversions
        energy_array = coal_array.to("MWh")
        co2_array = coal_array.to(substance="CO2")
        energy_gj = energy_array.to("GJ")

        # Should handle large arrays efficiently
        assert len(energy_array.value) == len(large_array)
        assert len(co2_array.value) == len(large_array)
        assert len(energy_gj.value) == len(large_array)

    def test_nested_conversion_efficiency(self):
        """Test that nested conversions don't cause exponential slowdown."""
        # Start with base quantity
        base = Quantity(100, "MWh", "coal")

        # Many nested conversions
        result = base
        units = ["GJ", "MJ", "kJ", "J", "kJ", "MJ", "GJ", "MWh"]

        for unit in units:
            result = result.to(unit)

        # Should complete in reasonable time and preserve value
        assert result.value == pytest.approx(base.value, rel=1e-10)

    def test_memory_efficiency_in_chains(self):
        """Test that conversion chains don't cause memory leaks."""
        # This is a basic test - comprehensive memory testing would need profiling
        base_energy = Quantity(100, "MWh", "coal")

        # Create many temporary quantities in a chain
        for i in range(100):
            temp = base_energy.to("GJ").to("MJ").to("GJ").to("MWh")
            assert temp.value == pytest.approx(base_energy.value)
