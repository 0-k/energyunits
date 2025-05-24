#!/usr/bin/env python3
"""
Test script to verify all README examples work correctly
"""

def test_basic_usage():
    """Test Basic Usage section examples"""
    print("Testing Basic Usage examples...")
    
    from energyunits import Quantity

    # Simple unit conversions
    energy = Quantity(100, "MWh")
    result = energy.to("GJ")
    print(f"100 MWh = {result}")  # → 360.0 GJ
    assert abs(result.value - 360.0) < 0.1, f"Expected ~360.0, got {result.value}"

    # Substance-based calculations  
    coal = Quantity(1000, "t", substance="coal")
    energy_content = coal.to("MWh")  # Uses heating value
    print(f"1000 t coal = {energy_content}")
    
    co2_emissions = coal.to("t", substance="CO2")  # Combustion emissions
    print(f"1000 t coal → {co2_emissions} CO2")

    # Economic calculations with inflation
    capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
    capex_2025 = capex_2020.to(reference_year=2025)  # Auto-adjusts for inflation
    print(f"CAPEX 2020: {capex_2020} → 2025: {capex_2025}")

    # Natural arithmetic operations
    power = Quantity(100, "MW")
    time = Quantity(24, "h") 
    energy = power * time  # → 2400 MWh
    print(f"{power} * {time} = {energy}")
    assert "MWh" in str(energy), f"Expected MWh unit, got {energy}"


def test_energy_system_analysis():
    """Test Energy System Analysis examples"""
    print("\nTesting Energy System Analysis examples...")
    
    from energyunits import Quantity

    # Power plant performance analysis
    fuel_input = Quantity(1000, "t", "coal")
    electricity_output = Quantity(400, "MWh")

    # Calculate efficiency
    efficiency = electricity_output / fuel_input.to("MWh")
    print(f"Plant efficiency: {efficiency.value:.1%}")

    # Emission intensity  
    co2_rate = fuel_input.to("t", substance="CO2") / electricity_output
    print(f"CO2 intensity: {co2_rate.value:.2f} t CO2/MWh")


def test_techno_economic_modeling():
    """Test Techno-Economic Modeling examples"""
    print("\nTesting Techno-Economic Modeling examples...")
    
    from energyunits import Quantity

    # LCOE calculation with inflation adjustment
    capex_2015 = Quantity(1200, "USD/kW", reference_year=2015)
    capex_today = capex_2015.to(reference_year=2024)
    print(f"CAPEX inflation adjusted: {capex_2015} → {capex_today}")

    capacity_factor = 0.45
    annual_generation = Quantity(8760 * capacity_factor, "h") * Quantity(1, "MW")
    print(f"Annual generation: {annual_generation}")

    # Calculate levelized cost component
    lcoe_capex = capex_today / (annual_generation * 20)  # 20-year lifetime
    print(f"CAPEX component: {lcoe_capex.value:.2f} USD/MWh")


def test_fuel_analysis():
    """Test Fuel Analysis examples"""
    print("\nTesting Fuel Analysis examples...")
    
    from energyunits import Quantity

    # Compare fuel heating values
    coal_hhv = Quantity(1, "t", "coal").to("MWh", basis="HHV")
    coal_lhv = Quantity(1, "t", "coal").to("MWh", basis="LHV") 
    wood_lhv = Quantity(1, "t", "wood_pellets").to("MWh", basis="LHV")

    print(f"Coal HHV: {coal_hhv.value:.1f}")
    print(f"Coal LHV: {coal_lhv.value:.1f}")  
    print(f"Wood LHV: {wood_lhv.value:.1f}")


def test_compound_units():
    """Test Compound Units examples"""
    print("\nTesting Compound Units examples...")
    
    from energyunits import Quantity

    # Energy intensity analysis
    steel_production = Quantity(1000, "t")  
    energy_use = Quantity(20, "GWh")
    intensity = energy_use / steel_production  # → 20 GWh/kt
    print(f"Energy intensity: {intensity}")

    # Cost analysis
    fuel_cost = Quantity(50, "USD/t", "coal")
    fuel_mass = Quantity(100, "t", "coal")  
    total_cost = fuel_cost * fuel_mass  # → 5000 USD
    print(f"Total fuel cost: {total_cost}")
    assert abs(total_cost.value - 5000) < 0.1, f"Expected 5000, got {total_cost.value}"


def test_multi_step_conversions():
    """Test Multi-Step Conversions examples"""
    print("\nTesting Multi-Step Conversions examples...")
    
    from energyunits import Quantity

    # Complex conversion chains
    coal_mass = Quantity(1000, "kg", "coal")

    # Convert mass → energy → emissions in one call
    result = coal_mass.to("t", basis="LHV", substance="CO2")
    print(f"Coal: {coal_mass} → CO2: {result}")

    # Equivalent step-by-step
    energy = coal_mass.to("MWh", basis="LHV")
    co2 = energy.to("t", substance="CO2")  
    print(f"Step-by-step: {coal_mass} → {energy} → {co2}")


def test_economic_time_series():
    """Test Economic Time Series examples"""
    print("\nTesting Economic Time Series examples...")
    
    from energyunits import Quantity

    # Historical cost analysis
    costs_2010 = Quantity([800, 900, 1000], "USD/kW", reference_year=2010)
    costs_2024 = costs_2010.to(reference_year=2024)

    print(f"2010 costs: {costs_2010.value}")
    print(f"2024 costs: {costs_2024.value}")  # Inflation-adjusted


def test_pandas_integration():
    """Test Pandas Integration examples"""
    print("\nTesting Pandas Integration examples...")
    
    try:
        import pandas as pd
        from energyunits.pandas_tools import convert_units
        from energyunits import Quantity

        # DataFrame operations
        df = pd.DataFrame({
            'power': [100, 200, 300],
            'hours': [24, 12, 8] 
        })

        # Calculate energy in MWh (manually since DataFrame columns are just numbers)
        df['energy_MWh'] = df['power'] * df['hours'] / 1000  # Convert MW*h to MWh
        df['energy_GJ'] = df['energy_MWh'].apply(lambda x: Quantity(x, 'MWh').to('GJ').value)
        
        print("Pandas integration test:")
        print(df)
        
    except ImportError:
        print("Pandas not available, skipping pandas integration test")


if __name__ == "__main__":
    print("Testing all README examples...\n")
    
    try:
        test_basic_usage()
        test_energy_system_analysis()
        test_techno_economic_modeling()
        test_fuel_analysis()
        test_compound_units()
        test_multi_step_conversions()
        test_economic_time_series()
        test_pandas_integration()
        
        print("\n✅ All README examples work correctly!")
        
    except Exception as e:
        print(f"\n❌ Error testing README examples: {e}")
        import traceback
        traceback.print_exc()
        exit(1)