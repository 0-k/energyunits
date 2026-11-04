# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-11-04

First release published on PyPI. This release reworks the unit handling at the
core of the library. Several calculations of earlier versions returned **wrong
values without an error**; results computed with 0.1/0.2 that involve the cases
listed under "Fixed" should be re-checked.

### Fixed
- **Power × time and energy / time with non-hour time units**: `MW × min`,
  `kW × a`, `MWh / a`, `MWh / min` returned values as if the time were in hours
  (e.g. `100 MW × 30 min` gave 3000 MWh instead of 50 MWh, `8760 MWh / 1 a` gave
  8760 MW instead of 1 MW).
- **False unit cancellation**: `USD/MWh × h` returned `USD` and `t/MWh × t` returned
  `t`, because units were matched as substrings.
- **Currency conversion of compound units ignored the non-currency part**:
  `USD/MWh -> EUR/GJ` and `USD/kW -> EUR/MW` only applied the exchange rate.
- **Chained divisions were parsed right-to-left**: `EUR/kW/a` was treated as
  `EUR/(kW/a)`, so converting the time unit gave inverted factors.
- **HHV basis applied to fuel mass**: `Quantity(1, "t", "coal").to("MWh", basis="HHV")`
  rescaled the mass before applying the HHV (7.51 MWh instead of 7.22 MWh).
- **Combustion products of zero-carbon sources** lost the array shape (a scalar 0
  was returned for array input).
- **Reference years** were dropped when multiplying or dividing a cost by a quantity
  without one, and ignored when adding costs from different years.
- **Equality** raised an error for incompatible units and failed on floating point
  round-off (`1 MWh == 3.6 GJ`).
- **NumPy interoperability**: `quantity * np.int64(2)` raised, `np.array(...) * quantity`
  returned an object array of quantities.
- `GJ / h`, `MW × MW` and products with dimensionless quantities raised errors.
- Malformed units such as `"MW//h"` or `"MW/"` were accepted.
- `pandas_tools.convert_units` used static exchange rates and could not convert
  substance-dependent units.
- Tests mutated the global registries and depended on execution order.

### Changed
- **Unit algebra** is based on a parser (`/` and `·`/`*`, evaluated left to right)
  and dimension vectors with `POWER = ENERGY / TIME`, so equivalent units are
  compatible (`GJ/h` and `MW`, `kWh/kW` and `h`, `EUR/MW` and `EUR·h/MWh`).
- **Conversion factors** are stored relative to SI-coherent base units (J, W, kg,
  m3, s, USD); common conversions are now exact in floating point
  (`100 MWh -> 360.0 GJ`).
- **Power and energy are no longer converted implicitly**: `Quantity(100, "MW").to("MWh")`
  (which assumed one hour) now raises; multiply by a duration instead.
  `registry.convert_between_dimensions(..., hours=...)` keeps the old behaviour.
- **Conversion order** in `.to()` is basis -> substance -> unit -> reference year
  (previously substance -> basis -> ...).
- **Basis conversion** rescales energy amounts, rescales per-energy units (prices,
  emission factors) inversely and only re-labels masses and volumes.
- **Addition, subtraction and comparison** convert the right operand to the left
  operand's heating value basis and (for costs) reference year before combining.
- **Products and quotients** keep the reference year of the operand that has one.
- **Input validation**: values must be numeric (stored as float arrays), the basis
  must be HHV/LHV (case-insensitive), reference years must be integers.
- `str()` of very small values uses significant digits (`0.00034 t/kWh` instead of
  `0.00 t/kWh`); arrays show the number of values after the unit.
- Errors are raised as `EnergyUnitsError` subclasses (`UnknownUnitError`,
  `IncompatibleUnitsError`, `UnknownSubstanceError`, `MissingDataError`), all of
  which are `ValueError`s. Warnings use `EnergyUnitsWarning` and point at user code.
- `import energyunits` no longer imports pandas.
- Python 3.10 or newer is required (3.9 is end-of-life).

### Added
- Conversions between mass, volume and energy **inside compound units** with a
  substance: `USD/t -> USD/MWh`, `EUR/L -> EUR/MWh`, `MW -> t/h`.
- Combustion products for any amount unit, e.g. emission rates:
  `Quantity(500, "MW", "natural_gas").to("t/h", substance="CO2")`.
- Division rule *energy / power = time* (full-load hours) and dimensionless results
  (`GWh / MWh`, capacity factors); reciprocal units (`1/h`).
- Units: `BTU`, `therm`, `quad`, `kcal`, `Mcal`, `Gcal`, `toe`, `ktoe`, `Mtoe`, `tce`,
  `Mtce`, `kt`, `lb`, `bcm`, `gal`, `ft3`, `Mcf`, `Bcf`, `d`, `yr`, and prefixed
  currencies (`kEUR`, `MEUR`, `bnEUR`, ... for USD, EUR, GBP, JPY, CNY).
- Inflation data for GBP, JPY and CNY.
- `Quantity`: unary minus/plus, `abs()`, `sum()` support, `number / quantity`,
  indexing, iteration, `len()`, `.sum()`/`.mean()`/`.min()`/`.max()`, `.shape`,
  `.copy()`, `.is_compatible()`, `float()` for dimensionless quantities, format
  specifications (`f"{q:.1f}"`), pickling; pandas Series as operands.
- `pandas_tools`: `get_units`, `to_quantity`, `from_quantity`; substance, basis and
  reference year metadata; conversions go through `Quantity.to`.
- Registries: `reset()`, `UnitRegistry.parse_unit`, `dimension_vector`,
  `is_compatible`, `multiply_units`, `divide_units`, `conversion_factor`
  (substance-aware), `preferred_unit`, `currency_of`.
- `py.typed` marker, data-integrity tests, README examples executed as tests,
  CI on Linux/Windows/macOS for Python 3.10-3.14, documentation build and wheel
  smoke test in CI; publishing checks the release tag against the version.

### Data
- **Exchange rates** replaced by Federal Reserve G.5A annual averages 2010-2025
  (2024 and 2025 are now actual values).
- **Inflation**: corrected USD values (2010, 2011, and 2014, which was 0.12 % instead
  of 1.62 %), 2024 and 2025 actuals for USD and EUR, new GBP/JPY/CNY series;
  2026-2030 are now explicit placeholders at the 2 % target and emit a warning.
- **Carbon contents** of fossil fuels are now consistent with the IPCC 2006
  emission factors stored in `carbon_intensity` (coal emitted 110 instead of
  95 kg CO2/GJ, lignite 170 instead of 101).
- **Biomass** on an as-received basis (wood pellets 8 % moisture: LHV 17.0 MJ/kg
  instead of the dry-basis 18.5; wood chips 30 % moisture: LHV 12.2 MJ/kg).
- Exact definitions for `barrel` (42 US gal) and the BTU-based units.

## [0.2.0] - 2026-02-15

### Added
- **Performance: Conversion factor caching**
  - `@lru_cache` on `get_dimension()` and `get_conversion_factor()` in `UnitRegistry`
  - Cache automatically invalidated when custom units are loaded
  - Up to 10x speedup for repeated conversions in hot loops

- **Unit & substance discovery methods**
  - `Quantity.list_units(dimension=None)` — list available units, optionally filtered by dimension
  - `Quantity.list_dimensions()` — list all dimensions (ENERGY, POWER, MASS, etc.)
  - `Quantity.list_substances(has_property=None)` — list substances with optional property filter
  - `Quantity.list_currencies()` — list supported currencies
  - `SubstanceRegistry.get_properties(substance_id)` — get all properties for a substance
  - `UnitRegistry.list_units(dimension=None)` and `UnitRegistry.list_dimensions()`

- **Unit constants module (`energyunits.units`)**
  - IDE-friendly string constants: `from energyunits.units import MWh, GJ, USD`
  - Enables autocompletion and typo prevention while remaining simple strings

- **Subtraction operator (`__sub__`)**
  - `Quantity(100, "MWh") - Quantity(30, "MWh")` now works
  - Includes automatic unit conversion like `__add__`

- **Jupyter/IPython rich HTML repr**
  - `_repr_html_()` method on `Quantity` for rich display in notebooks
  - Color-coded badges for substance, basis, and reference year

### Improved
- **Better error messages with suggestions**
  - Unknown unit names now suggest close matches via `difflib.get_close_matches`
  - Unknown substance names suggest close matches
  - Cross-dimensional conversion errors hint about specifying a substance
  - Substance conversion errors include usage examples

- **Substance metadata warnings on arithmetic**
  - Adding or subtracting quantities with different substances now emits a `UserWarning`
  - Prevents silent metadata loss

- **Substance metadata consistency in add/sub**
  - `__add__`/`__sub__` now preserve substance when one operand has `None`, matching `__mul__`/`__truediv__` behavior

### Fixed
- **Heating value precision**: replaced hardcoded `0.2778` with `1/3.6` in all MJ/kg to MWh/t conversions, eliminating ~0.008% systematic error
- **Wood pellets LHV data**: corrected from 17.0 to 18.5 MJ/kg to match DATA_SOURCES.md and physical expectations (HHV/LHV ratio 0.925)
- **HTML injection in `_repr_html_()`**: user-provided strings (substance, basis, unit) now escaped via `html.escape()`
- **Renewable CO2 conversion unit**: no longer hardcodes `"t"` — preserves source mass unit (e.g., `"kg"` stays `"kg"`)
- **Currency detection false positives**: switched from substring matching to component-based matching (e.g., `"EUR"` no longer matches inside `"NEURON"`)
- **Duplicate USD in `list_currencies()`**: `ExchangeRateRegistry.get_supported_currencies()` now returns deduplicated sorted list

## [0.1.0] - 2025-11-14

### Added
- **Core Unit Conversion System**
  - Support for energy units (Wh, kWh, MWh, GWh, TWh, PWh, J, kJ, MJ, GJ, TJ, PJ, EJ, MMBTU)
  - Support for power units (W, kW, MW, GW, TW)
  - Support for mass units (g, kg, t, Mt, Gt)
  - Support for volume units (L, m3, barrel)
  - Support for time units (s, min, h, a)
  - Support for currency units (USD, EUR, GBP, JPY, CNY)
  - Unified `.to()` conversion method for all conversion types

- **Substance-Aware Conversions**
  - Comprehensive fuel properties database with 20+ substances
  - Fossil fuels: coal (bituminous, sub-bituminous, lignite), natural gas, LNG, methane, crude oil, diesel, gasoline
  - Renewable fuels: wood pellets, wood chips, hydrogen
  - Zero-carbon sources: wind, solar, hydro, nuclear
  - Combustion products: CO2, H2O, ash
  - Heating value conversions (HHV/LHV basis)
  - Automatic basis conversion between HHV and LHV

- **Inflation Adjustment**
  - Historical inflation rates for USD and EUR (2010-2030)
  - Automatic currency detection from units
  - Cumulative inflation calculation
  - Reference year tracking in conversions

- **Smart Arithmetic Operations**
  - Natural multiplication: power × time = energy
  - Natural division: energy ÷ time = power
  - Compound unit cancellation (e.g., USD/kW × MW = USD)
  - Dimensional analysis for operation validation
  - Comparison operations (<, >, ==, <=, >=, !=)
  - Addition/subtraction with automatic unit conversion

- **Data-Driven Architecture**
  - All unit definitions stored in JSON (units.json)
  - All substance properties in JSON (substances.json)
  - All inflation rates in JSON (inflation.json)
  - Dimensional multiplication rules in data layer
  - Dimensional division rules in data layer
  - Extensible via custom JSON files

- **Array and Data Frame Support**
  - Full NumPy array support for batch calculations
  - Time series operations
  - Optional pandas integration with unit metadata preservation
  - Bulk conversion operations

- **Advanced Features**
  - Multi-step conversion chains (mass → energy → emissions)
  - Complex compound units (USD/MWh, MWh/t, etc.)
  - Metadata preservation (substance, basis, reference_year)
  - Custom unit/substance loading from external files

### Development & Quality
- Comprehensive test suite with 199+ tests across 15 test files
- CI/CD pipeline with GitHub Actions (Python 3.9-3.13)
- Code coverage tracking with Codecov (80% target)
- Black code formatting enforcement
- Isort import sorting
- Flake8 linting
- Type hints throughout codebase
- Sphinx documentation setup
- README examples validated as executable tests

### Documentation
- Comprehensive README with quick start guide
- Multiple use case examples (energy system analysis, techno-economic modeling, fuel analysis)
- Advanced features documentation
- Extensibility guide with JSON examples
- Complete unit and substance reference tables
- Inline code documentation with docstrings
- Example scripts in `/examples` directory

## [0.0.1] - 2024 (Initial Development)

### Added
- Initial project structure
- Basic quantity and registry implementation
- Core conversion functionality

[0.3.0]: https://github.com/0-k/energyunits/releases/tag/v0.3.0
[0.2.0]: https://github.com/0-k/energyunits/releases/tag/v0.2.0
[0.1.0]: https://github.com/0-k/energyunits/releases/tag/v0.1.0
[0.0.1]: https://github.com/0-k/energyunits/releases/tag/v0.0.1
