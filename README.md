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
print(Quantity(1000, "t", "coal").to("t", substance="CO2"))  # 2374.90 t of CO2
print(Quantity(1200, "EUR/kW", reference_year=2015).to(reference_year=2024))  # 1513.78 EUR/kW
```

## Features

- **Units for energy work**: SI and IEC-style energy units plus energy-statistics units
  (`toe`, `Mtoe`, `tce`, `Gcal`, `MMBTU`, `therm`, `quad`), gas volumes (`bcm`, `Mcf`),
  `barrel`, `lb`, and currencies with prefixes (`kEUR`, `MUSD`, `bnEUR`, ...).
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

## Fuels and substances

Specify a `substance` to convert between mass, volume and energy. Energy content uses
the lower heating value (LHV) unless the basis is set to `"HHV"`.

```python
from energyunits import Quantity

coal = Quantity(1, "t", "coal")
print(coal.to("MWh"))                     # 6.94 MWh of coal
print(coal.to("MWh", basis="HHV"))        # 7.22 MWh of coal
print(Quantity(1000, "L", "diesel").to("kg"))          # 840.00 kg of diesel
print(Quantity(1, "bcm", "natural_gas").to("TWh"))     # 10.31 TWh of natural_gas

# Also inside compound units
print(Quantity(100, "USD/t", "coal").to("USD/MWh"))    # 14.40 USD/MWh of coal
print(Quantity(500, "MW", "natural_gas").to("t/h"))    # 36.36 t/h of natural_gas
```

### Heating value basis

Changing the basis rescales energy amounts with the LHV/HHV ratio, rescales
per-energy units (prices, emission factors) inversely, and only re-labels masses and
volumes.

```python
from energyunits import Quantity

print(Quantity(100, "MWh", "natural_gas", basis="HHV").to(basis="LHV"))     # 90.00 MWh of natural_gas
print(Quantity(30, "EUR/MWh", "natural_gas", basis="HHV").to(basis="LHV"))  # 33.33 EUR/MWh of natural_gas

# A US Henry Hub price (HHV) in the European LHV convention
henry_hub = Quantity(3.5, "USD/MMBTU", "natural_gas", basis="HHV")
print(henry_hub.to("USD/MWh", basis="LHV"))   # 13.27 USD/MWh of natural_gas
```

### Emissions

`.to(substance=...)` converts a fuel quantity into its combustion products `"CO2"`,
`"H2O"` or `"ash"`, based on the fuel composition. The carbon contents are set so that
CO2 reproduces the IPCC 2006 default emission factors (kg CO2 per GJ, LHV basis).

```python
from energyunits import Quantity

print(Quantity(1, "GJ", "natural_gas").to("kg", substance="CO2"))   # 56.10 kg of CO2
print(Quantity(1, "MWh", "coal").to("t", substance="CO2"))          # 0.34 t of CO2
print(Quantity(1000, "t", "lignite").to("t", substance="CO2"))      # 1413.87 t of CO2

# Emission rate of a 500 MW (fuel input) gas plant
print(Quantity(500, "MW", "natural_gas").to("t/h", substance="CO2"))   # 100.99 t/h of CO2

# Zero-carbon sources keep the array shape
print(Quantity([100, 200], "MWh", "wind").to("t", substance="CO2"))    # [0.00, 0.00] t of CO2
```

Energy amounts refer to *fuel* energy. For biomass the physical (biogenic) CO2 is
returned; its `carbon_intensity` is 0 following IPCC accounting conventions.

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
  (national CPI), historical 2010-2025. Rates for 2026-2030 are placeholders at the
  2 % central bank target and trigger a warning when used.
- **Exchange rates**: annual averages 2010-2025 from the Federal Reserve G.5A release.
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
print(df["fuel"].round(1).tolist())   # [6944.4, 17361.1]
print(df.attrs["fuel_unit"])          # MWh
print(to_quantity(df, "fuel").sum().to("GWh"))   # 24.31 GWh of coal
```

pandas does not keep `attrs` through every operation (for example `groupby`); re-attach
units with `add_units` where needed.

## Discovering units and data

```python
from energyunits import Quantity
from energyunits.substance import substance_registry

print(Quantity.list_dimensions())        # ['CURRENCY', 'ENERGY', 'MASS', 'POWER', 'TIME', 'VOLUME']
print(Quantity.list_currencies())        # ['CNY', 'EUR', 'GBP', 'JPY', 'USD']
print("hydrogen" in Quantity.list_substances("hhv"))   # True
print(substance_registry.get_properties("natural_gas")["lhv"])   # 49.5
```

Unit names are also available as constants for autocompletion:

```python
from energyunits import Quantity
from energyunits.units import GJ, MWh

print(Quantity(1, MWh).to(GJ))   # 3.60 GJ
```

## Extending

All data lives in JSON files under `energyunits/data/`. Additional units, substances,
inflation rates and exchange rates can be loaded at runtime:

```python
import json

from energyunits import Quantity
from energyunits.registry import registry
from energyunits.substance import substance_registry

with open("custom_units.json", "w") as f:
    json.dump({"dimensions": {"MMscf": "VOLUME"}, "conversion_factors": {"MMscf": 28316.846592}}, f)
registry.load_units("custom_units.json")
print(Quantity(1, "MMscf").to("m3"))   # 28316.85 m3

with open("custom_fuels.json", "w") as f:
    json.dump({"biomethane": {"name": "Biomethane", "hhv": 55.5, "lhv": 50.0, "density": 0.72}}, f)
substance_registry.load_substances("custom_fuels.json")
print(Quantity(1, "t", "biomethane").to("MWh"))   # 13.89 MWh of biomethane
```

Conversion factors are relative to the SI base unit of each dimension (J, W, kg, m3,
s, USD). Use `inflation_registry.load_inflation()` and
`exchange_rate_registry.load_exchange_rates()` for economic data, and `.reset()` on any
registry to restore the bundled defaults. The file formats are described in
[ARCHITECTURE.md](https://github.com/0-k/energyunits/blob/master/ARCHITECTURE.md).

## Errors and warnings

All errors derive from `energyunits.EnergyUnitsError`, which is a `ValueError`:

| Exception                | Raised when                                                    |
|--------------------------|----------------------------------------------------------------|
| `UnknownUnitError`       | a unit is unknown or malformed (with suggestions)              |
| `IncompatibleUnitsError` | units cannot be converted, or a substance is required          |
| `UnknownSubstanceError`  | a substance is unknown                                         |
| `MissingDataError`       | a heating value, density, inflation or exchange rate is missing |

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
| Energy    | `J` `kJ` `MJ` `GJ` `TJ` `PJ` `EJ`, `Wh` `kWh` `MWh` `GWh` `TWh` `PWh`, `BTU` `MMBTU` `therm` `quad`, `kcal` `Mcal` `Gcal`, `toe` `ktoe` `Mtoe`, `tce` `Mtce` |
| Power     | `W` `kW` `MW` `GW` `TW` |
| Mass      | `g` `kg` `t` `kt` `Mt` `Gt` `lb` |
| Volume    | `L` `m3` `bcm`, `barrel` (US oil barrel), `gal` (US gallon), `ft3` `Mcf` `Bcf` |
| Time      | `s` `min` `h` `d` `a`/`yr` (8760 h) |
| Currency  | `USD` `EUR` `GBP` `JPY` `CNY`, each with `k`, `M` and `bn` prefixes (e.g. `kEUR`, `MUSD`, `bnEUR`) |

### Substances

| Substance      | LHV MJ/kg | HHV MJ/kg | Density kg/m3 | kg CO2/GJ (LHV) |
|----------------|----------:|----------:|--------------:|----------------:|
| `coal`         | 25.0 | 26.0 | 833  | 95.0  |
| `lignite`      | 14.0 | 15.0 | 700  | 101.0 |
| `bituminous`   | 28.5 | 30.0 | 833  | 94.6  |
| `anthracite`   | 31.5 | 32.5 | 1000 | 98.3  |
| `natural_gas`  | 49.5 | 55.0 | 0.75 | 56.1  |
| `lng`          | 49.5 | 55.0 | 450  | 56.1  |
| `methane`      | 50.0 | 55.5 | 0.68 | 54.9  |
| `crude_oil`, `oil` | 42.5 | 45.0 | 870 | 73.3 |
| `fuel_oil`     | 40.5 | 43.0 | 950  | 77.4  |
| `diesel`       | 42.8 | 45.7 | 840  | 74.1  |
| `gasoline`     | 44.0 | 47.3 | 750  | 69.3  |
| `methanol`     | 19.9 | 22.7 | 795  | 69.1  |
| `hydrogen`     | 120.0 | 142.0 | 0.09 | 0 |
| `wood_pellets` | 17.0 | 18.4 | 650  | 0 (biogenic) |
| `wood_chips`   | 12.2 | 13.9 | 350  | 0 (biogenic) |

Further entries: `wind`, `solar`, `hydro`, `nuclear` (no combustion products) and the
products `CO2`, `H2O`, `ash`. Biomass values are as received (pellets 8 %, chips 30 %
moisture). Gas densities refer to approximately normal conditions. Sources and
caveats are documented in
[DATA_SOURCES.md](https://github.com/0-k/energyunits/blob/master/DATA_SOURCES.md).

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
