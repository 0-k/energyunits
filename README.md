# EnergyUnits

[![CI](https://github.com/0-k/energyunits/actions/workflows/workflow.yml/badge.svg)](https://github.com/0-k/energyunits/actions/workflows/workflow.yml)
[![codecov](https://codecov.io/gh/0-k/energyunits/branch/master/graph/badge.svg)](https://codecov.io/gh/0-k/energyunits)
[![PyPI](https://img.shields.io/pypi/v/energyunits.svg)](https://pypi.org/project/energyunits/)
[![Python](https://img.shields.io/pypi/pyversions/energyunits.svg)](https://pypi.org/project/energyunits/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/0-k/energyunits/blob/master/LICENSE)

**Units, conversions and calculations for energy system modeling.**

EnergyUnits handles the quantities energy modelers work with every day: energy, power,
fuels, emissions, costs, inflation and exchange rates. It is a small, dependency-light
library on top of NumPy with one conversion method, `.to()`, and arithmetic that keeps
track of units.

```python
from energyunits import Quantity

print(Quantity(100, "MWh").to("GJ"))                         # 360.00 GJ
print((Quantity(2, "GW") * Quantity(4000, "h")).to("TWh"))   # 8.00 TWh
print(Quantity(1000, "t", "coal").to("t", substance="CO2"))  # 2440.68 t of CO2
print(Quantity(1200, "EUR/kW", reference_year=2015).to(reference_year=2024))  # 1513.78 EUR/kW
```

## Features

- **Units for energy work**: SI and IEC-style energy units plus energy-statistics units
  (`toe`, `Mtoe`, `tce`, `Gcal`, `MMBTU`, `therm`, `quad`), gas volumes (`bcm`, `Mcf`),
  `barrel`, `lb`, areas (`m2`, `ha`, `km2`, `acre`, `ft2`) and currencies with prefixes
  (`kEUR`, `MUSD`, `bnEUR`, ...).
- **Compound units with dimensional analysis**: `EUR/kW/a`, `t/MWh`, `USD/MMBTU`, `GJ/h`,
  `kWh/kW` are parsed, checked and converted (`GJ/h` and `MW` are the same dimension).
- **Arithmetic that gets units right**: `MW × h → MWh`, `USD/kW × MW → USD`,
  `MWh / MW → h`, `MWh / a → MW`, `GWh/a / MW → capacity factor`.
- **Fuel database** (heating values, densities, compositions) for mass ↔ volume ↔ energy
  conversions, also inside compound units (`USD/t → USD/MWh`, `MW → t/h`).
- **Heating value basis** (HHV/LHV) applied correctly to amounts, prices and fuel masses.
- **Emissions**: CO2, H2O and ash from fuel composition, reproducing the IPCC 2006 default
  emission factors.
- **Costs**: inflation adjustment for USD, EUR, GBP, JPY and CNY and year-dependent
  exchange rates (US Federal Reserve annual averages).
- **NumPy and pandas**: values are NumPy arrays; helpers attach units to DataFrame columns.
- **Extensible** through JSON files; typed exceptions; only NumPy as a dependency.

## Installation

```bash
pip install energyunits
pip install "energyunits[pandas]"   # with the optional pandas helpers
```

Requires Python 3.10 or newer.

## Quick start

A `Quantity` has a value (number or array), a unit and optional metadata: a
`substance` (fuel), a heating value `basis` (`"HHV"`/`"LHV"`) and a price
`reference_year`.

```python
from energyunits import Quantity

energy = Quantity(100, "MWh")
print(energy.to("GJ"))      # 360.00 GJ
print(energy.to("MMBTU"))   # 341.21 MMBTU
print(energy.value)         # 100.0

# Power x time = energy, with automatic unit handling
print(Quantity(50, "MW") * Quantity(30, "min"))   # 25.00 MWh
print(Quantity(8, "TWh") / Quantity(2, "GW"))     # 4000.00 h  (full-load hours)
print(Quantity(8760, "MWh") / Quantity(1, "a"))   # 1.00 MW    (average power)

# Costs scale with capacity, unit prefixes are aligned automatically
print(Quantity(1500, "USD/kW") * Quantity(500, "MW"))   # 750000000.00 USD
```

## Units

Unit strings combine registered units with `/` and `·` (or `*`). Operators are
evaluated left to right, so every unit after a `/` is in the denominator:
`"EUR/kW/a"` is euros per kilowatt per year. `""` is dimensionless and `"1/h"` a rate.

```python
from energyunits import Quantity

print(Quantity(100, "EUR/kW/a").to("EUR/MW/a"))   # 100000.00 EUR/MW/a
print(Quantity(3600, "GJ/h").to("MW"))            # 1000.00 MW
print(Quantity(1, "Mtoe").to("TWh"))              # 11.63 TWh
print(Quantity(4000, "kWh/kW").to("h"))           # 4000.00 h
print(Quantity(1, "GJ/h").dimension)              # POWER

print(Quantity.list_units("POWER"))   # ['GW', 'MW', 'TW', 'W', 'kW']
```

Units that only differ by a time dimension are not silently converted:
`Quantity(100, "MW").to("MWh")` raises an error; multiply by a duration instead.

### Arithmetic

Addition, subtraction and comparisons convert the right operand to the unit of the
left one. Multiplication and division combine units, cancel matching dimensions and
apply the rules *power × time = energy*, *energy / time = power* and
*energy / power = time*.

```python
from energyunits import Quantity

capacity = Quantity(100, "MW")
fixed_om = Quantity(40, "EUR/kW/a")
print(fixed_om * capacity)                           # 4000000.00 EUR/a

generation = Quantity(3504, "GWh/a")
capacity_factor = generation / Quantity(1000, "MW")
print(capacity_factor)                               # 0.40
print(float(capacity_factor))                        # 0.4

emission_factor = Quantity(0.35, "t/MWh")
print(emission_factor * Quantity(3, "TWh"))          # 1050000.00 t

print(Quantity(1, "MWh") + Quantity(500, "kWh"))     # 1.50 MWh
print(Quantity(1, "MWh") == Quantity(3.6, "GJ"))     # True
print(sum([Quantity(1, "MWh"), Quantity(3.6, "GJ")]))  # 2.00 MWh
```

Results that do not simplify keep a compound unit that can be converted later:

```python
from energyunits import Quantity

price_times_hours = Quantity(50, "USD/MWh") * Quantity(10, "h")
print(price_times_hours)                  # 500.00 USD·h/MWh
print(price_times_hours.to("USD/MW"))     # 500.00 USD/MW
```

### Area-based quantities

Areas combine with energy and power like any other unit, which covers irradiance,
building energy intensity, land use and biomass yields:

```python
from energyunits import Quantity

# PV: annual irradiation x module area x efficiency
print(Quantity(1700, "kWh/m2/a") * Quantity(20, "m2") * 0.2)   # 6800.00 kWh/a

# Building energy intensity, EU and US conventions
print(Quantity(120, "kWh/m2/a") * Quantity(500, "m2"))         # 60000.00 kWh/a
print(Quantity(40, "kBTU/ft2/a").to("kWh/m2/a"))               # 126.18 kWh/m2/a

# Biomass yield and power density
print((Quantity(10, "t/ha", "wood_chips") * Quantity(200, "ha")).to("GWh"))  # 6.78 GWh of wood_chips
print(Quantity(1, "W/m2").to("MW/km2"))                        # 1.00 MW/km2
```

## Fuels and substances

Specify a `substance` to convert between mass, volume and energy. Energy content uses
the lower heating value (LHV) unless the basis is set to `"HHV"`.

```python
from energyunits import Quantity

coal = Quantity(1, "t", "coal")
print(coal.to("MWh"))                     # 7.17 MWh of coal
print(coal.to("MWh", basis="HHV"))        # 7.54 MWh of coal
print(Quantity(1000, "L", "diesel").to("kg"))          # 840.00 kg of diesel
print(Quantity(1, "bcm", "natural_gas").to("TWh"))     # 9.87 TWh of natural_gas
print(Quantity(1, "Nm3", "natural_gas").to("kWh"))     # 10.41 kWh of natural_gas

# Also inside compound units
print(Quantity(100, "USD/t", "coal").to("USD/MWh"))    # 13.95 USD/MWh of coal
print(Quantity(500, "MW", "natural_gas").to("t/h"))    # 37.50 t/h of natural_gas
```

### Heating value basis

Changing the basis rescales energy amounts with the LHV/HHV ratio, rescales
per-energy units (prices, emission factors) inversely, and only re-labels masses and
volumes.

```python
from energyunits import Quantity

print(Quantity(100, "MWh", "natural_gas", basis="HHV").to(basis="LHV"))     # 90.01 MWh of natural_gas
print(Quantity(30, "EUR/MWh", "natural_gas", basis="HHV").to(basis="LHV"))  # 33.33 EUR/MWh of natural_gas

# A US Henry Hub price (HHV) in the European LHV convention
henry_hub = Quantity(3.5, "USD/MMBTU", "natural_gas", basis="HHV")
print(henry_hub.to("USD/MWh", basis="LHV"))   # 13.27 USD/MWh of natural_gas

# Mixed bases are aligned in arithmetic: an HHV price times fuel energy on LHV
print(henry_hub * Quantity(1000, "MWh", "natural_gas"))   # 13268.61 USD of natural_gas
```

### Emissions

`.to(substance=...)` converts a fuel quantity into its combustion products `"CO2"`,
`"H2O"` or `"ash"`, based on the fuel composition. The carbon contents are set so that
CO2 reproduces the IPCC 2006 Tier 1 emission factors (kg CO2 per GJ, LHV basis).

```python
from energyunits import Quantity

print(Quantity(1, "GJ", "natural_gas").to("kg", substance="CO2"))   # 56.10 kg of CO2
print(Quantity(1, "MWh", "coal").to("t", substance="CO2"))          # 0.34 t of CO2
print(Quantity(1000, "t", "lignite").to("t", substance="CO2"))      # 1201.90 t of CO2

# Emission rate of a 500 MW (fuel input) gas plant
print(Quantity(500, "MW", "natural_gas").to("t/h", substance="CO2"))   # 100.98 t/h of CO2

# Zero-carbon sources keep the array shape
print(Quantity([100, 200], "MWh", "wind").to("t", substance="CO2"))    # [0.00, 0.00] t of CO2
```

Energy amounts refer to *fuel* energy. For biomass the physical (biogenic) CO2 is
returned; biomass is marked `biogenic` because inventories report this CO2 separately.

## Costs, inflation and exchange rates

Monetary quantities carry a `reference_year` (price base year). Changing it applies
the cumulative consumer price inflation of the currency; changing the currency uses
the annual average exchange rate of the reference year.

```python
from energyunits import Quantity

capex = Quantity(1000, "USD/kW", reference_year=2015)
print(capex.to(reference_year=2024))   # 1323.40 USD/kW

price = Quantity(50, "EUR/MWh", reference_year=2020)
print(price.to("USD/MWh"))             # 57.05 USD/MWh  (2020 exchange rate)
print(price.to("USD/GJ"))              # 15.85 USD/GJ

print(Quantity(1.2, "MEUR/MW", reference_year=2023).to("USD/kW"))   # 1298.04 USD/kW
```

When the currency and the reference year change together, the value is first inflated
in its original currency and then converted with the exchange rate of the target year.
Because this involves an economic assumption, an `EnergyUnitsWarning` is emitted.

```python
import warnings

from energyunits import EnergyUnitsWarning, Quantity

with warnings.catch_warnings():
    warnings.simplefilter("ignore", EnergyUnitsWarning)
    cost = Quantity(50, "EUR/MWh", reference_year=2015).to("USD/MWh", reference_year=2024)
print(cost)                  # 68.25 USD/MWh
print(cost.reference_year)   # 2024
```

Reference years propagate through arithmetic, and sums of costs from different years
are inflation-adjusted to the year of the left operand:

```python
from energyunits import Quantity

capex = Quantity(1200, "USD/kW", reference_year=2024)
total = capex * Quantity(1, "MW")
print(total, total.reference_year)   # 1200000.00 USD 2024

annual_generation = Quantity(3942, "MWh/a")
lifetime = Quantity(20, "a")
print((total / (annual_generation * lifetime)).to("USD/MWh"))   # 15.22 USD/MWh

print(Quantity(100, "USD", reference_year=2015) + Quantity(100, "USD", reference_year=2024))  # 175.56 USD
```

Data coverage:

- **Inflation**: USD (BLS CPI-U), EUR (Eurostat HICP), GBP (ONS CPI), JPY and CNY
  (national CPI), historical 2000-2025. Rates for 2026-2030 are placeholders at the
  2 % central bank target and trigger a warning when used.
- **Exchange rates**: annual averages 2000-2025 from the Federal Reserve G.5A release.
  Later years use the most recent rate, with a warning. Without a reference year the
  most recent rate is used.

See [DATA_SOURCES.md](https://github.com/0-k/energyunits/blob/master/DATA_SOURCES.md) for
sources and the exact values.

## Arrays and pandas

Values are NumPy arrays, so time series work directly. NumPy arrays and pandas Series
can be combined with quantities on either side.

```python
import numpy as np

from energyunits import Quantity

hourly_power = Quantity([400, 450, 380], "MW")
print(hourly_power * Quantity(1, "h"))      # [400.00, 450.00, 380.00] MWh
print(hourly_power.mean())                  # 410.00 MW
print((hourly_power * Quantity(1, "h")).sum().to("GWh"))   # 1.23 GWh
print(np.array([0.5, 1.0]) * Quantity(100, "MW"))          # [50.00, 100.00] MW
print(hourly_power[0])                      # 400.00 MW
```

The optional `energyunits.pandas_tools` module stores units in `DataFrame.attrs`:

```python
import pandas as pd

from energyunits.pandas_tools import add_units, convert_units, to_quantity

df = pd.DataFrame({"fuel": [1000.0, 2500.0]})
df = add_units(df, "fuel", "t", substance="coal")
df = convert_units(df, "fuel", "MWh")
print(df["fuel"].round(1).tolist())   # [7166.7, 17916.7]
print(df.attrs["fuel_unit"])          # MWh
print(to_quantity(df, "fuel").sum().to("GWh"))   # 25.08 GWh of coal
```

pandas does not keep `attrs` through every operation (for example `groupby`); re-attach
units with `add_units` where needed.

## Discovering units and data

```python
from energyunits import Quantity
from energyunits.substance import substance_registry

print(Quantity.list_dimensions())        # ['AREA', 'CURRENCY', 'ENERGY', 'MASS', 'POWER', 'TIME', 'VOLUME']
print(Quantity.list_currencies())        # ['CNY', 'EUR', 'GBP', 'JPY', 'USD']
print("hydrogen" in Quantity.list_substances("hhv"))   # True
print(substance_registry.get_properties("natural_gas")["lhv"])   # 48.0
```

Unit names are also available as constants for autocompletion:

```python
from energyunits import Quantity
from energyunits.units import GJ, MWh

print(Quantity(1, MWh).to(GJ))   # 3.60 GJ
```

## Extending

All data lives in JSON files under `energyunits/data/`. Additional units, substances,
inflation rates and exchange rates can be loaded at runtime, from a JSON file or a dict
with the same structure:

```python
import json

from energyunits import Quantity
from energyunits.registry import registry
from energyunits.substance import substance_registry

registry.load_units({"dimensions": {"MMscf": "VOLUME"}, "conversion_factors": {"MMscf": 28316.846592}})
print(Quantity(1, "MMscf").to("m3"))   # 28316.85 m3

with open("custom_fuels.json", "w") as f:
    json.dump({"biomethane": {"name": "Biomethane", "hhv": 55.5, "lhv": 50.0, "density": 0.72}}, f)
substance_registry.load_substances("custom_fuels.json")
print(Quantity(1, "t", "biomethane").to("MWh"))   # 13.89 MWh of biomethane
```

Conversion factors are relative to the SI base unit of each dimension (J, W, kg, m3,
m2, s, USD). Use `inflation_registry.load_inflation()` and
`exchange_rate_registry.load_exchange_rates()` for economic data. The formats are
described in [ARCHITECTURE.md](https://github.com/0-k/energyunits/blob/master/ARCHITECTURE.md).

### Loaded data is shared, existing definitions are protected

The registries are shared by all code in the Python process, including other packages
that use energyunits. Loading is therefore additive:

- New names are added. Data identical to an existing definition is accepted, so loading
  the same file twice is harmless.
- Data that would change an existing definition, bundled or loaded by other code, raises
  `DefinitionConflictError` and nothing is loaded:

```python
from energyunits import DefinitionConflictError
from energyunits.substance import substance_registry

try:
    substance_registry.load_substances({"coal": {"lhv": 20.0, "carbon_intensity": 94.6}})
except DefinitionConflictError as error:
    print(str(error).splitlines()[1].strip())   # coal: lhv 25.8 -> 20.0, carbon_content 0.66564 -> 0.516; would drop 10 other properties
```

- Use a new name instead (`"my_coal"`), or pass `overwrite=True` to replace the
  definition deliberately, for every user in the process.
- `substance_registry["coal"]` is read-only; `substance_registry.get_properties("coal")`
  returns a copy that you can modify and load under a new name.
- Loading is thread-safe, and conversions running in other threads keep seeing the
  existing definitions.

**In a library** that depends on energyunits, load your data at import time under names
with your own prefix (`mylib_coal`, `mylib_MMscf`), never pass `overwrite=True` for names
you did not define, and never call `reset()`, which removes every custom definition in
the process. `reset()` is meant for scripts and tests.

## Errors and warnings

All errors derive from `energyunits.EnergyUnitsError`, which is a `ValueError`:

| Exception                | Raised when                                                    |
|--------------------------|----------------------------------------------------------------|
| `UnknownUnitError`       | a unit is unknown or malformed (with suggestions)              |
| `IncompatibleUnitsError` | units cannot be converted, or a substance is required          |
| `UnknownSubstanceError`  | a substance is unknown                                         |
| `MissingDataError`       | a heating value, density, inflation or exchange rate is missing |
| `DefinitionConflictError` | loaded data would change an existing definition              |

```python
from energyunits import IncompatibleUnitsError, Quantity

try:
    Quantity(100, "MWh").to("t")
except IncompatibleUnitsError as error:
    print(error)   # Substance required for energy to mass conversion (MWh -> t). Specify one, e.g. Quantity(..., substance='coal').
```

Assumptions (projected inflation, exchange rates beyond the available years, mixing
substances in a sum, combined currency and inflation conversions) are reported as
`EnergyUnitsWarning`, which can be filtered with the `warnings` module.

## Reference

### Units

| Dimension | Units |
|-----------|-------|
| Energy    | `J` `kJ` `MJ` `GJ` `TJ` `PJ` `EJ`, `Wh` `kWh` `MWh` `GWh` `TWh` `PWh`, `BTU` `kBTU` `MMBTU` `therm` `quad`, `kcal` `Mcal` `Gcal`, `toe` `ktoe` `Mtoe`, `tce` `Mtce` |
| Power     | `W` `kW` `MW` `GW` `TW` |
| Mass      | `g` `kg` `t` `kt` `Mt` `Gt` `lb` |
| Volume    | `L` `m3` `bcm`, `barrel` (US oil barrel), `gal` (US gallon), `ft3` `Mcf` `Bcf`, `Sm3` (standard, 15 °C), `Nm3` (normal, 0 °C) |
| Area      | `m2` `km2` `ha` `acre` `ft2` |
| Time      | `s` `min` `h` `d` `a`/`yr` (8760 h) |
| Currency  | `USD` `EUR` `GBP` `JPY` `CNY`, each with `k`, `M` and `bn` prefixes (e.g. `kEUR`, `MUSD`, `bnEUR`) |

### Substances

Fuel properties are the IPCC 2006 Tier 1 defaults (net calorific values from Table 1.2,
CO2 emission factors from Table 1.4) wherever the IPCC defines the fuel; the IPCC
lower/upper limits are stored with each value.

<!-- BEGIN GENERATED substance-table: edit `energyunits/data/substances.json` and run `python scripts/update_data.py sync` -->
| Substance | IPCC category | LHV (MJ/kg) | HHV (MJ/kg) | kg CO2/GJ (LHV) | Density (kg/m3) |
|-----------|---------------|------:|------:|------:|------:|
| `coal` | Other Bituminous Coal | 25.8 | 27.16 | 94.6 | 833 |
| `bituminous` | Other Bituminous Coal | 25.8 | 27.16 | 94.6 | 833 |
| `coking_coal` | Coking Coal | 28.2 | 29.68 | 94.6 | 800 |
| `sub_bituminous` | Sub-Bituminous Coal | 18.9 | 19.89 | 96.1 | 800 |
| `anthracite` | Anthracite | 26.7 | 28.11 | 98.3 | 1000 |
| `lignite` | Lignite | 11.9 | 12.53 | 101.0 | 700 |
| `peat` | Peat | 9.76 | 10.27 | 106.0 | 350 |
| `natural_gas` | Natural Gas | 48.0 | 53.33 | 56.1 | 0.74 |
| `lng` | Natural Gas | 48.0 | 53.33 | 56.1 | 450 |
| `crude_oil` | Crude Oil | 42.3 | 44.53 | 73.3 | 870 |
| `oil` | Crude Oil | 42.3 | 44.53 | 73.3 | 870 |
| `fuel_oil` | Residual Fuel Oil | 40.4 | 42.53 | 77.4 | 950 |
| `diesel` | Gas/Diesel Oil | 43.0 | 45.26 | 74.1 | 840 |
| `gasoline` | Motor Gasoline | 44.3 | 46.63 | 69.3 | 750 |
| `jet_kerosene` | Jet Kerosene | 44.1 | 46.42 | 71.5 | 800 |
| `lpg` | Liquefied Petroleum Gases | 47.3 | 49.79 | 63.1 | 540 |
| `wood` | Wood/Wood Waste | 15.6 | 17.1 | 112.0 (biogenic) | – |
| `wood_pellets` | Wood/Wood Waste | 17.0 | 18.4 | 99.2 (biogenic) | 650 |
| `wood_chips` | Wood/Wood Waste | 12.2 | 13.9 | 105.2 (biogenic) | 350 |
| `methane` | – | 50.0 | 55.5 | 54.9 | 0.68 |
| `hydrogen` | – | 120.0 | 141.8 | 0.0 | 0.0852 |
| `methanol` | – | 19.9 | 22.7 | 69.1 | 795 |
<!-- END GENERATED substance-table -->

Further entries: `wind`, `solar`, `hydro`, `nuclear` (no combustion products) and the
products `CO2`, `H2O`, `ash`. HHVs of IPCC fuels follow the IPCC rule of thumb (NCV 5 %
below GCV for coal and oil, 10 % for natural gas). Biomass values are as received (pellets
8 %, chips 30 % moisture). Gas densities refer to 15 °C and 101.325 kPa; use `Nm3` for
normal cubic metres (0 °C).

**How accurate are the defaults?** CO2 from fuel *energy* reproduces the IPCC Tier 1
factors exactly, typically within 1-5 % of country-specific values (up to about 10 % for
lignite). Results that start from fuel *mass* or *volume* also depend on the heating value,
which varies much more (lignite 5.5-21.6 MJ/kg). The defaults suit energy-system modelling
and screening, not compliance reporting; CH4, N2O and upstream emissions are not included.
See [Accuracy and appropriate use](https://github.com/0-k/energyunits/blob/master/DATA_SOURCES.md#accuracy-and-appropriate-use)
for details and how to load your own factors.

## Documentation

- [ARCHITECTURE.md](https://github.com/0-k/energyunits/blob/master/ARCHITECTURE.md): design, unit algebra and data formats
- [DATA_SOURCES.md](https://github.com/0-k/energyunits/blob/master/DATA_SOURCES.md): sources for all bundled data
- [CHANGELOG.md](https://github.com/0-k/energyunits/blob/master/CHANGELOG.md): release notes
- [examples/](https://github.com/0-k/energyunits/tree/master/examples): runnable examples

## Development

```bash
git clone https://github.com/0-k/energyunits.git
cd energyunits
pip install -e ".[dev]"

pytest                                   # tests (including the examples in this README)
black energyunits tests && isort energyunits tests && flake8 energyunits
```

Releases are published from GitHub releases; see
[RELEASE.md](https://github.com/0-k/energyunits/blob/master/RELEASE.md).

## License

MIT, see [LICENSE](https://github.com/0-k/energyunits/blob/master/LICENSE). Martin Klein, 2024-2026.
