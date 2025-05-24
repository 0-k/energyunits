# EnergyUnits API Examples

"""
This document demonstrates the intended public API for the EnergyUnits library through common use cases. These examples can guide implementation and serve as a reference for expected behavior.
"""


## Basic Unit Conversions

from energyunits import Quantity
print(Quantity(100, "GWh/min").to("MW"))

# Energy conversions
energy = Quantity(100, "MWh")  # returns a Quantity object, prints as "100 MWh"
energy_gj = energy.to("GJ")  # 360 GJ
energy_kwh = energy.to("kWh")  # 100,000 kWh

# Power conversions
power = Quantity(50, "MW")
power_kw = power.to("kW")  # 50,000 kW
power_gw = power.to("GW")  # 0.05 GW

# Array conversions
energy_values = [100, 200, 300]
energy_array = Quantity(energy_values, "MWh")
energy_array_gj = energy_array.to("GJ")  # [360, 720, 1080] GJ


## Power and Energy Conversions

from energyunits import Quantity

# Convert power to energy (time integration)
power = Quantity(100, "MW")
energy_1h = power.for_duration(hours=1)  # 100 MWh
energy_24h = power.for_duration(hours=24)  # 2400 MWh
energy_1yr = power.for_duration(hours=8760)  # 876,000 MWh

# Calculate average power from energy (time differentiation)
energy = Quantity(240, "MWh")
avg_power_12h = energy.average_power(hours=12)  # 20 MW


## Working with Substances

from energyunits import Quantity

# Fuel quantities
coal = Quantity(1000, "t", "coal")
natural_gas = Quantity(100000, "m3", "natural_gas")
oil = Quantity(500, "barrel", "oil")

# Convert between mass and volume where applicable
lng_mass = Quantity(1000, "t", "lng")
lng_volume = lng_mass.to("m3")  # Converts using density

# Carbon emissions
co2 = Quantity(50000, "t", "CO2")
co2_kg = co2.to("kg")  # 50,000,000 kg


## Heating Values

from energyunits import Quantity

# Get energy content with specific heating value basis
coal = Quantity(1000, "t", "coal")
energy_hhv = coal.to(basis="HHV")  # ~8140 MWh
energy_lhv = coal.to(basis="LHV")  # ~7730 MWh

# Convert energy between HHV and LHV bases
gas_energy_hhv = Quantity(1000, "MWh", substance="natural_gas", basis="HHV")
gas_energy_lhv = gas_energy_hhv.to(basis="LHV")  # ~900 MWh (depends on fuel)



## Compound Units


from energyunits import Quantity

# Energy prices
electricity_price = Quantity(50, "USD/MWh")
gas_price = Quantity(10, "USD/MMBTU")

# Convert between price units
gas_price_mwh = gas_price.to("USD/MWh")  # ~34.1 USD/MWh

# Energy intensity
steel_intensity = Quantity(4.5, "MWh/t")
aluminum_intensity = Quantity(15, "MWh/t")


## Mathematical Operations

from energyunits import Quantity

# Addition of compatible quantities
energy1 = Quantity(100, "MWh")
energy2 = Quantity(500, "GJ")
total_energy = energy1 + energy2  # Converts to common unit, returns 238.9 MWh

# Multiplication by scalar
capacity = Quantity(50, "MW")
doubled = capacity * 2  # 100 MW

# Division between quantities
energy = Quantity(1000, "MWh")
time = Quantity(10, "h")
power = energy / time  # 100 MW

# Comparison operations
energy_small = Quantity(1, "GJ")
energy_large = Quantity(1, "MWh")
is_larger = energy_large > energy_small  # True (3.6 GJ > 1 GJ)


## Pandas Integration

import numpy as np
import pandas as pd

from energyunits.pandas_tools import add_units, calculate_emissions, convert_units

# Create dataframe with energy data
df = pd.DataFrame(
    {
        "generation": [100, 200, 300, 400],
        "fuel_type": ["coal", "natural_gas", "wind", "solar"],
    }
)

# Add units to dataframe
df_with_units = add_units(df, "generation", "MWh")

# Convert units in dataframe
df_gj = convert_units(df_with_units, "generation", "GJ")

# Calculate emissions
df_with_emissions = calculate_emissions(
    df_with_units, energy_col="generation", fuel_col="fuel_type"
)

# Access unit information
print(df_with_units.attrs["generation_unit"])  # 'MWh'


## Cost Calculations

from energyunits import Quantity

# Adjust for inflation
capex_2015 = Quantity(1000, "USD/kW", reference_year=2015)
capex_current = capex_2015.adjust_inflation(target_year=2025)


gas = Quantity(10, "MWh", "natural_gas")

 # Calculate required gas volume
gas_volume = gas.to("m3")
print(gas_volume)
emissions = gas.to(substance="CO2")
print(emissions.to("t"))


