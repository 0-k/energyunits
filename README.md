# EnergyUnits

[![CI](https://github.com/0-k/energyunits/actions/workflows/workflow.yml/badge.svg)](https://github.com/0-k/energyunits/actions/workflows/workflow.yml)
[![codecov](https://codecov.io/gh/0-k/energyunits/branch/master/graph/badge.svg)](https://codecov.io/gh/0-k/energyunits)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python library for handling units, conversions, and calculations in energy system modeling. Designed for techno-economic analysis, energy planning, and quantitative energy research.

##  Key Features

- **Universal Conversions**: Energy, power, mass, volume, and cost units with intelligent dimensional analysis
- **Substance-Aware**: Built-in fuel properties database with heating values, densities, and emission factors
- **Economic Modeling**: Inflation adjustment with historical rates for USD/EUR (2010-2030)
- **Smart Arithmetic**: Natural mathematical operations with automatic unit handling
- **Pandas Ready**: Optional DataFrame integration for bulk operations
- **Energy-Focused**: Purpose-built for energy system modeling and analysis

## Quick Start

### Installation

```bash
pip install energyunits
```

### Basic Usage

```python
from energyunits import Quantity

# Simple unit conversions
energy = Quantity(100, "MWh")
print(energy.to("GJ"))  # → 360.0 GJ

# Substance-based calculations  
coal = Quantity(1000, "t", substance="coal")
energy_content = coal.to("MWh")  # Uses heating value
co2_emissions = coal.to("t", substance="CO2")  # Combustion emissions

# Economic calculations with inflation
capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
capex_2025 = capex_2020.to(reference_year=2025)  # Auto-adjusts for inflation

# Natural arithmetic operations
power = Quantity(100, "MW")
time = Quantity(24, "h") 
energy = power * time  # → 2400 MWh
```

## Use Cases

### Energy System Analysis
```python
# Power plant performance analysis
fuel_input = Quantity(1000, "t", "coal")
electricity_output = Quantity(400, "MWh")

# Calculate efficiency
efficiency = electricity_output / fuel_input.to("MWh")
print(f"Plant efficiency: {efficiency.value:.1%}")

# Emission intensity  
co2_rate = fuel_input.to("t", substance="CO2") / electricity_output
print(f"CO2 intensity: {co2_rate.value:.2f} t CO2/MWh")
```

### Techno-Economic Modeling
```python
# LCOE calculation with inflation adjustment
capex_2015 = Quantity(1200, "USD/kW", reference_year=2015)
capex_today = capex_2015.to(reference_year=2024)

capacity_factor = 0.45
annual_generation = Quantity(8760 * capacity_factor, "h") * Quantity(1, "MW")

# Calculate levelized cost component
lcoe_capex = capex_today / (annual_generation * 20)  # 20-year lifetime
print(f"CAPEX component: {lcoe_capex.value:.2f} USD/MWh")
```

### Fuel Analysis
```python
# Compare fuel heating values
coal_hhv = Quantity(1, "t", "coal").to("MWh", basis="HHV")
coal_lhv = Quantity(1, "t", "coal").to("MWh", basis="LHV") 
wood_lhv = Quantity(1, "t", "wood_pellets").to("MWh", basis="LHV")

print(f"Coal HHV: {coal_hhv.value:.1f}")
print(f"Coal LHV: {coal_lhv.value:.1f}")  
print(f"Wood LHV: {wood_lhv.value:.1f}")
```

## Advanced Features

### Compound Units
```python
# Energy intensity analysis
steel_production = Quantity(1000, "t")  
energy_use = Quantity(20, "GWh")
intensity = energy_use / steel_production  # → 20 GWh/kt

# Cost analysis
fuel_cost = Quantity(50, "USD/t", "coal")
fuel_mass = Quantity(100, "t", "coal")  
total_cost = fuel_cost * fuel_mass  # → 5000 USD
```

### Multi-Step Conversions
```python
# Complex conversion chains
coal_mass = Quantity(1000, "kg", "coal")

# Convert mass → energy → emissions in one call
result = coal_mass.to("t", basis="LHV", substance="CO2")
print(f"Coal: {coal_mass} → CO2: {result}")

# Equivalent step-by-step
energy = coal_mass.to("MWh", basis="LHV")
co2 = energy.to("t", substance="CO2")  
```

### Economic Time Series
```python
# Historical cost analysis
costs_2010 = Quantity([800, 900, 1000], "USD/kW", reference_year=2010)
costs_2024 = costs_2010.to(reference_year=2024)

print(f"2010 costs: {costs_2010.value}")
print(f"2024 costs: {costs_2024.value}")  # Inflation-adjusted
```

## Supported Units

### Energy
- `Wh`, `kWh`, `MWh`, `GWh`, `TWh`, `PWh`
- `J`, `kJ`, `MJ`, `GJ`, `TJ`, `PJ`, `EJ`
- `MMBTU` (Million British Thermal Units)

### Power  
- `W`, `kW`, `MW`, `GW`, `TW`

### Mass
- `g`, `kg`, `t` (metric tons), `Mt`, `Gt`

### Volume
- `L`, `m3`

### Currency
- `USD`, `EUR` with automatic inflation adjustment
- Compound units: `USD/kW`, `EUR/MWh`, etc.

## Built-in Substances

The library includes a comprehensive database of fuel and material properties:

- **Fossil Fuels**: coal, natural_gas, oil, diesel, gasoline
- **Renewables**: wood, biomass, biogas, ethanol
- **Zero-Carbon**: wind, solar, hydro, nuclear
- **Industrial**: steel, cement, aluminum

Each substance includes:
- Higher/Lower Heating Values (HHV/LHV)
- Density values for volume conversions
- Carbon content for emission calculations
- Chemical composition data

## Pandas Integration

```python
import pandas as pd
from energyunits.pandas_tools import convert_units

# DataFrame operations
df = pd.DataFrame({
    'power': [100, 200, 300],
    'hours': [24, 12, 8] 
})

# Calculate energy in MWh (convert MW*h to MWh)
df['energy_MWh'] = df['power'] * df['hours'] / 1000
df['energy_GJ'] = df['energy_MWh'].apply(lambda x: Quantity(x, 'MWh').to('GJ').value)
```

## Development

### Setup
```bash
git clone https://github.com/0-k/energyunits.git
cd energyunits
pip install -e .[dev]
```

### Testing
```bash
pytest                          # Run all tests
pytest --cov=energyunits       # With coverage
pytest -v                     # Verbose output
```

### Code Quality
```bash
black energyunits/             # Format code
flake8 energyunits/           # Lint
isort energyunits/            # Sort imports
```

## Documentation

- **API Reference**: [Read the Docs](https://energyunits.readthedocs.io)
- **Examples**: See `examples/` directory
- **Architecture**: See `CLAUDE.md` for design principles

## Contributing

Contributions are welcome! Please see our contributing guidelines and submit pull requests for any improvements.

##License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Martin Klein, 2025