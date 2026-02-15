"""
Comprehensive EnergyUnits Examples

This file demonstrates the full capabilities of the EnergyUnits library
through practical examples for energy system modeling and analysis.
"""

import numpy as np

from energyunits import Quantity
from energyunits.units import EUR, GJ, GW, MW, MWh, USD, h, kg, kW, t


def basic_conversions():
    """Basic unit conversion examples."""
    print("=== Basic Unit Conversions ===")

    # Energy conversions
    energy = Quantity(100, "MWh")
    print(f"Energy: {energy}")
    print(f"  → GJ: {energy.to('GJ')}")
    print(f"  → kWh: {energy.to('kWh')}")
    print(f"  → MMBTU: {energy.to('MMBTU')}")

    # Power conversions
    power = Quantity(50, "MW")
    print(f"\nPower: {power}")
    print(f"  → kW: {power.to('kW')}")
    print(f"  → GW: {power.to('GW')}")

    # Mass conversions
    mass = Quantity(1000, "t")
    print(f"\nMass: {mass}")
    print(f"  → kg: {mass.to('kg')}")
    print(f"  → Mt: {mass.to('Mt')}")


def substance_calculations():
    """Substance-based conversion examples."""
    print("\n=== Substance-Based Calculations ===")

    # Fuel energy content
    coal = Quantity(1000, "t", substance="coal")
    print(f"Coal mass: {coal}")
    print(f"  → Energy (HHV): {coal.to('MWh', basis='HHV')}")
    print(f"  → Energy (LHV): {coal.to('MWh', basis='LHV')}")

    # Natural gas
    gas = Quantity(10000, "m3", substance="natural_gas")
    print(f"\nNatural gas: {gas}")
    print(f"  → Energy: {gas.to('MWh')}")
    print(f"  → Mass: {gas.to('t')}")

    # Emissions calculations
    print(f"\nCO2 Emissions:")
    print(f"  Coal → CO2: {coal.to('t', substance='CO2')}")
    print(f"  Gas → CO2: {gas.to('t', substance='CO2')}")


def economic_modeling():
    """Economic calculations with inflation adjustment."""
    print("\n=== Economic Modeling ===")

    # Historical cost analysis
    capex_2015 = Quantity(1200, "USD/kW", reference_year=2015)
    capex_2020 = capex_2015.to(reference_year=2020)
    capex_2025 = capex_2015.to(reference_year=2025)

    print(f"Solar CAPEX trends:")
    print(f"  2015: {capex_2015}")
    print(f"  2020: {capex_2020}")
    print(f"  2025: {capex_2025}")

    # Multi-currency example
    eur_costs = Quantity(900, "EUR/kW", reference_year=2020)
    eur_2025 = eur_costs.to(reference_year=2025)
    print(f"\nWind CAPEX (EUR):")
    print(f"  2020: {eur_costs}")
    print(f"  2025: {eur_2025}")


def power_plant_analysis():
    """Complete power plant performance analysis."""
    print("\n=== Power Plant Analysis ===")

    # Coal power plant
    plant_capacity = Quantity(500, "MW")
    capacity_factor = 0.75
    annual_hours = Quantity(8760, "h")

    # Annual generation
    annual_generation = plant_capacity * annual_hours * capacity_factor
    print(f"Plant capacity: {plant_capacity}")
    print(f"Annual generation: {annual_generation}")

    # Fuel consumption
    fuel_consumption = Quantity(1.2e6, "t", substance="coal")  # Annual
    fuel_energy = fuel_consumption.to("MWh", basis="LHV")

    # Efficiency calculation
    efficiency_ratio = annual_generation.value / fuel_energy.value
    print(f"\nFuel consumption: {fuel_consumption}")
    print(f"Fuel energy content: {fuel_energy}")
    print(f"Plant efficiency: {efficiency_ratio:.1%}")

    # Emissions
    annual_co2 = fuel_consumption.to("t", substance="CO2")
    emission_rate_value = annual_co2.value / annual_generation.value
    print(f"\nAnnual CO2 emissions: {annual_co2}")
    print(f"Emission rate: {emission_rate_value:.3f} t CO2/MWh")


def lcoe_calculation():
    """Levelized Cost of Energy (LCOE) calculation."""
    print("\n=== LCOE Calculation ===")

    # Technology parameters
    capex = Quantity(1500, "USD/kW", reference_year=2020)
    opex = Quantity(25, "USD/kW")  # Annual
    capacity_factor = 0.35
    lifetime = 25  # years

    # Financial parameters
    discount_rate = 0.07

    # Calculate annual generation
    rated_capacity = Quantity(100, "MW")  # Example project
    annual_hours = Quantity(8760, "h")
    annual_generation = rated_capacity * annual_hours * capacity_factor

    print(f"Technology: Wind turbine")
    print(f"Capacity: {rated_capacity}")
    print(f"Annual generation: {annual_generation}")
    print(f"CAPEX: {capex}")

    # Present value calculations
    capex_total = capex * rated_capacity.to("kW")
    opex_annual = opex * rated_capacity.to("kW")

    # Simplified LCOE (without full financial modeling)
    capex_component = capex_total / (annual_generation * lifetime)
    opex_component = opex_annual / annual_generation

    lcoe = capex_component + opex_component
    print(f"\nLCOE breakdown:")
    print(f"  CAPEX component: {capex_component}")
    print(f"  OPEX component: {opex_component}")
    print(f"  Total LCOE: {lcoe}")


def industrial_energy_intensity():
    """Industrial energy intensity analysis."""
    print("\n=== Industrial Energy Intensity ===")

    # Steel production
    steel_production = Quantity(1000, "t")
    energy_consumption = Quantity(20, "GWh")

    # Calculate intensity
    energy_intensity = energy_consumption / steel_production
    print(f"Steel production: {steel_production}")
    print(f"Energy consumption: {energy_consumption}")
    print(f"Energy intensity: {energy_intensity}")

    # Convert to different units
    print(f"  → MWh/t: {energy_intensity.to('MWh/t')}")
    print(f"  → GJ/t: {energy_intensity.to('GJ/t')}")


def fuel_comparison():
    """Compare different fuels on various metrics."""
    print("\n=== Fuel Comparison ===")

    # Standard fuel quantities (1 tonne each)
    fuels = {
        "coal": Quantity(1, "t", substance="coal"),
        "natural_gas": Quantity(1, "t", substance="natural_gas"),
        "oil": Quantity(1, "t", substance="oil"),
    }

    print("Comparison per tonne of fuel:")
    print(f"{'Fuel':<12} {'Energy (MWh)':<12} {'CO2 (t)':<10}")
    print("-" * 35)

    for name, fuel in fuels.items():
        energy = fuel.to("MWh", basis="LHV")
        co2 = fuel.to("t", substance="CO2")
        print(f"{name:<12} {energy.value:<12.1f} {co2.value:<10.2f}")


def array_operations():
    """Working with arrays and time series data."""
    print("\n=== Array Operations ===")

    # Time series generation data
    hourly_power = np.array([400, 450, 380, 420, 390])  # MW
    hours = Quantity(hourly_power, "MW")

    print(f"Hourly power generation:")
    for i, power in enumerate(hourly_power):
        print(f"  Hour {i+1}: {power} MW")

    # Convert to energy (assuming 1-hour intervals)
    time_interval = Quantity(1, "h")
    hourly_energy = hours * time_interval

    print(f"\nHourly energy generation:")
    print(f"  Total: {hourly_energy}")
    print(f"  In GJ: {hourly_energy.to('GJ')}")

    # Cost calculation
    electricity_price = Quantity(50, "USD/MWh")
    revenue_array = hourly_energy * electricity_price
    print(f"\nHourly revenue: {revenue_array}")


def complex_conversions():
    """Complex multi-step conversion examples."""
    print("\n=== Complex Conversions ===")

    # Natural gas pipeline to electricity
    gas_flow = Quantity(1000, "m3", substance="natural_gas")
    print(f"Natural gas input: {gas_flow}")

    # Step 1: Gas to energy
    gas_energy = gas_flow.to("MWh")
    print(f"  → Energy content: {gas_energy}")

    # Step 2: Apply power plant efficiency
    plant_efficiency = 0.45
    electricity_output = gas_energy * plant_efficiency
    print(f"  → Electricity output (45% eff): {electricity_output}")

    # Step 3: Calculate emissions per electricity unit
    gas_co2 = gas_flow.to("t", substance="CO2")
    emission_factor = gas_co2 / electricity_output
    print(f"  → CO2 emissions: {gas_co2}")
    print(f"  → Emission factor: {emission_factor}")

    # Note: Complex chained conversions (gas → energy → CO2) in one step
    # are not supported as they involve different physical transformations.
    # The step-by-step approach above is the recommended method.


def discovery_api():
    """Demonstrate the discovery API (v0.2.0)."""
    print("\n=== Discovery API ===")

    # List all energy units
    energy_units = Quantity.list_units("ENERGY")
    print(f"Energy units: {energy_units}")

    # List all dimensions
    dims = Quantity.list_dimensions()
    print(f"Dimensions: {dims}")

    # List fuels with heating values
    fuels = Quantity.list_substances("hhv")
    print(f"Fuels with HHV: {fuels}")

    # List all currencies
    currencies = Quantity.list_currencies()
    print(f"Currencies: {currencies}")

    # Get all properties of a substance
    from energyunits.substance import substance_registry

    props = substance_registry.get_properties("natural_gas")
    print(f"\nNatural gas properties:")
    for key, val in props.items():
        print(f"  {key}: {val}")


def unit_constants_example():
    """Demonstrate IDE-friendly unit constants (v0.2.0)."""
    print("\n=== Unit Constants ===")

    # Using constants instead of strings
    energy = Quantity(500, MWh)
    power = Quantity(100, MW)
    time_period = Quantity(8760, h)
    mass = Quantity(1000, t)

    print(f"Energy: {energy}")
    print(f"  → GJ: {energy.to(GJ)}")
    print(f"Power: {power}")
    print(f"Time: {time_period}")

    # Arithmetic with constants
    annual_gen = power * time_period
    print(f"Annual generation: {annual_gen}")


def subtraction_example():
    """Demonstrate subtraction (v0.2.0)."""
    print("\n=== Subtraction ===")

    budget = Quantity(1000, MWh)
    consumed = Quantity(600, MWh)
    remaining = budget - consumed
    print(f"Budget: {budget}")
    print(f"Consumed: {consumed}")
    print(f"Remaining: {remaining}")

    # Works across units
    total = Quantity(1, GJ)
    used = Quantity(100, MWh)
    # Note: converts to the left operand's unit
    diff = total - used
    print(f"\n{total} - {used} = {diff}")


def currency_conversion_example():
    """Demonstrate year-dependent currency conversions."""
    print("\n=== Currency Conversions ===")

    # EUR to USD with year-dependent rates
    cost_eur_2015 = Quantity(50, "EUR/MWh", reference_year=2015)
    cost_usd_2024 = cost_eur_2015.to("USD/MWh", reference_year=2024)

    print(f"Original: {cost_eur_2015} (2015)")
    print(f"Converted: {cost_usd_2024} (2024)")
    print("  (inflated EUR 2015→2024, then converted at 2024 exchange rate)")


if __name__ == "__main__":
    """Run all examples."""
    basic_conversions()
    substance_calculations()
    economic_modeling()
    power_plant_analysis()
    lcoe_calculation()
    industrial_energy_intensity()
    fuel_comparison()
    array_operations()
    complex_conversions()
    discovery_api()
    unit_constants_example()
    subtraction_example()
    currency_conversion_example()

    print("\n=== Examples Complete ===")
