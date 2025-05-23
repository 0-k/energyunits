"""
Integration tests for the EnergyUnits library.

These tests focus on realistic scenarios that combine multiple features
to model energy systems and complex workflows.
"""

import numpy as np
import pytest

from energyunits import Quantity


class TestEnergySystemModels:
    def test_power_plant_workflow(self):
        """Test modeling a complete power plant workflow."""
        # Plant capacity
        plant_capacity = Quantity(1000, "MW", "coal")

        # Annual energy generation
        capacity_factor = 0.85  # 85% capacity factor
        hours_per_year = 8760

        # FIXED: Use for_duration to properly convert MW to MWh, then convert to GWh
        annual_generation_mwh = (
            plant_capacity.for_duration(hours=hours_per_year) * capacity_factor
        )
        annual_generation = annual_generation_mwh.to("GWh")

        # Alternative calculation using for_duration
        daily_generation = plant_capacity.for_duration(hours=24) * capacity_factor
        annual_generation_alt_mwh = daily_generation * 365
        annual_generation_alt = annual_generation_alt_mwh.to("GWh")

        # Values should match
        assert annual_generation.value == pytest.approx(annual_generation_alt.value)
        assert annual_generation.unit == "GWh"
        assert annual_generation.value == pytest.approx(
            7446
        )  # 1000 * 0.85 * 8760 / 1000

        # Fuel consumption
        # First get energy content of coal
        coal_unit = Quantity(1, "t", "coal")
        coal_energy = coal_unit.to("MWh")  # In MWh

        # Calculate required coal
        annual_generation_mwh = annual_generation.to("MWh")
        coal_required = annual_generation_mwh.value / coal_energy.value
        coal_quantity = Quantity(coal_required, "t", "coal")

        # The value depends on the exact heating value in the database
        # But we can check it's in a reasonable range
        assert coal_quantity.value > 0
        assert coal_quantity.unit == "t"

        # CO2 emissions
        emissions = annual_generation_mwh.to(substance="CO2").to("t")

        assert emissions.unit == "t"
        assert emissions.substance == "CO2"
        # Emissions factor depends on the substance database
        assert emissions.value > 0

    def test_renewable_energy_scenario(self):
        """Test modeling a renewable energy scenario."""
        # Wind farm capacity
        wind_capacity = Quantity(200, "MW", "wind")

        # Solar farm capacity
        solar_capacity = Quantity(100, "MW", "solar")

        # Combined capacity
        total_capacity = Quantity(wind_capacity.value + solar_capacity.value, "MW")

        # Generation with different capacity factors
        wind_cf = 0.35  # 35% capacity factor
        solar_cf = 0.25  # 25% capacity factor

        # Annual generation
        wind_generation = wind_capacity.for_duration(hours=8760) * wind_cf
        solar_generation = solar_capacity.for_duration(hours=8760) * solar_cf

        # Total generation
        total_generation = wind_generation + solar_generation

        assert wind_generation.value == pytest.approx(200 * 8760 * 0.35)
        assert solar_generation.value == pytest.approx(100 * 8760 * 0.25)
        assert total_generation.value == pytest.approx(
            (200 * 8760 * 0.35) + (100 * 8760 * 0.25)
        )

        # CO2 emissions (should be very low or zero for renewables)
        wind_emissions = wind_generation.to(substance="CO2")
        solar_emissions = solar_generation.to(substance="CO2")

        # Renewables typically have zero direct emissions
        assert wind_emissions.value == pytest.approx(0)
        assert solar_emissions.value == pytest.approx(0)

    def test_energy_storage_scenario(self):
        """Test modeling an energy storage scenario."""
        # Battery storage capacity
        battery_capacity = Quantity(100, "MWh")

        # Charging power
        charging_power = Quantity(25, "MW")

        # Time to fully charge
        hours_to_charge = battery_capacity.value / charging_power.value
        assert hours_to_charge == pytest.approx(4)  # 100 MWh / 25 MW = 4 h

        # Energy charged in 2 hours
        energy_2h = charging_power.for_duration(hours=2)
        assert energy_2h.value == pytest.approx(50)  # 25 MW * 2 h = 50 MWh

        # Battery state of charge (50%)
        state_of_charge = energy_2h.value / battery_capacity.value
        assert state_of_charge == pytest.approx(0.5)  # 50 MWh / 100 MWh = 50%

        # Discharging at 20 MW
        discharging_power = Quantity(20, "MW")

        # Time to fully discharge from 50%
        hours_to_discharge = (
            state_of_charge * battery_capacity.value
        ) / discharging_power.value
        assert hours_to_discharge == pytest.approx(2.5)  # 50 MWh / 20 MW = 2.5 h

    def test_energy_cost_calculations(self):
        """Test energy cost calculations and inflation adjustments."""
        # Electricity price
        price_2020 = Quantity(50, "USD/MWh", reference_year=2020)

        # Adjust for inflation
        price_2025 = price_2020.adjust_inflation(target_year=2025)

        # With 2% annual inflation
        inflation_factor = (1.02) ** 5  # 5 years
        assert price_2025.value == pytest.approx(50 * inflation_factor)
        assert price_2025.unit == "USD/MWh"
        assert price_2025.reference_year == 2025

        # Calculate cost of energy
        energy = Quantity(10000, "MWh")
        cost = energy.value * price_2025.value

        # Create proper cost quantity
        cost_quantity = Quantity(cost, "USD", reference_year=2025)

        assert cost_quantity.value == pytest.approx(10000 * 50 * inflation_factor)

        # Convert to another currency
        cost_eur = cost_quantity.to("EUR")
        assert cost_eur.unit == "EUR"
        # Exact value depends on the exchange rate in the registry
        assert cost_eur.value > 0


class TestCrossIndustryScenarios:
    def test_industrial_energy_usage(self):
        """Test modeling industrial energy usage across sectors."""
        # Steel production energy intensity
        steel_intensity = Quantity(4.5, "MWh/t")

        # Annual steel production
        annual_production = Quantity(1000000, "t")  # 1 million tons

        # Calculate energy needs
        energy_needed = Quantity(steel_intensity.value * annual_production.value, "MWh")
        assert energy_needed.value == pytest.approx(4.5e6)  # 4.5 million MWh

        # Convert to primary energy assuming natural gas
        gas = Quantity(energy_needed.value, "MWh", "natural_gas")

        # Calculate required gas volume
        gas_volume = gas.to("m3")

        assert gas_volume.unit == "m3"
        # The value depends on the exact properties in the substance database
        assert gas_volume.value > 0

        # Calculate CO2 emissions from the gas (which has substance specified)
        emissions = gas.to(substance="CO2").to("t")

        assert emissions.substance == "CO2"
        assert emissions.unit == "t"
        # The value depends on the carbon intensity in the substance database
        assert emissions.value > 0

    def test_transportation_energy_scenario(self):
        """Test modeling transportation energy usage."""
        # Diesel fuel properties
        diesel = Quantity(1000, "L", "diesel")

        # Convert to mass
        diesel_mass = diesel.to("kg")

        # Calculate energy content
        diesel_energy = diesel_mass.to("MWh")

        assert diesel_energy.unit == "MWh"
        assert diesel_energy.value > 0

        # Calculate emissions
        emissions = diesel_energy.to(substance="CO2")

        assert emissions.substance == "CO2"
        assert emissions.unit == "kg"
        assert emissions.value > 0

        # Electric equivalent (assuming 30% efficiency for diesel engine)
        electric_equivalent = diesel_energy.value * 0.3
        ev_energy = Quantity(electric_equivalent, "MWh")

        # Calculate charging time at 150 kW
        charging_power = Quantity(150, "kW")
        charging_hours = ev_energy.value / charging_power.to("MW").value

        assert charging_hours > 0

    def test_building_energy_scenario(self):
        """Test modeling building energy usage."""
        # Building heating requirement
        annual_heating = Quantity(200, "MWh")

        # Natural gas boiler option (90% efficiency)
        gas_required = annual_heating.value / 0.9
        gas_energy = Quantity(gas_required, "MWh", "natural_gas")

        # Calculate gas volume
        gas_volume = gas_energy.to("m3")

        assert gas_volume.unit == "m3"
        assert gas_volume.value > 0

        # Heat pump option (COP = 3.5)
        electricity_required = annual_heating.value / 3.5
        electricity = Quantity(electricity_required, "MWh")

        # Compare emissions
        gas_emissions = gas_energy.to(substance="CO2")

        # Electricity emissions depend on grid mix
        # For this test, assume 200 kg CO2/MWh (mostly renewable grid)
        elec_emissions_value = electricity.value * 200 / 1000  # Convert kg to t
        elec_emissions = Quantity(elec_emissions_value, "t", "CO2")

        # Heat pump should have lower emissions with this grid mix
        assert elec_emissions.value < gas_emissions.value
