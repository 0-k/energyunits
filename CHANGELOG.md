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
  rescaled the mass before applying the HHV, so the HHV/LHV ratio was applied twice.
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
  `Mtce`, `kBTU`, `kt`, `lb`, `bcm`, `gal`, `ft3`, `Mcf`, `Bcf`, `d`, `yr`, and prefixed
  currencies (`kEUR`, `MEUR`, `bnEUR`, ... for USD, EUR, GBP, JPY, CNY).
- Gas volume units `Sm3` (standard cubic metre, 15 °C; the same as `m3`) and `Nm3`
  (normal cubic metre, 0 °C; 1 Nm3 = 1.0549 Sm3).
- Substances `coking_coal`, `sub_bituminous`, `peat`, `jet_kerosene`, `lpg` and `wood`
  (IPCC categories).
- Substance fields `ipcc_category`, `lhv_range` and `carbon_intensity_range` (IPCC
  lower/upper limits for sensitivity analysis), `biogenic`, `moisture_content` and
  `density_basis`. Custom substances that give only `lhv` and `carbon_intensity` (or
  `carbon_content`) get the other value derived; ranges are validated on loading.
- `DATA_SOURCES.md`: an "Accuracy and appropriate use" section with typical deviations,
  suitable uses and how to load your own factors. The fuel tables in README and
  DATA_SOURCES are generated from `substances.json`.
- `AREA` dimension with `m2`, `km2`, `ha`, `acre`, `ft2` for irradiance (`kWh/m2/a`),
  building energy intensity (`kWh/m2/a`, `kBTU/ft2/a`), power density and yields (`t/ha`).
- Inflation data for GBP, JPY and CNY; inflation and exchange rates from 2000.
- `Quantity`: unary minus/plus, `abs()`, `sum()` support, `number / quantity`,
  indexing, iteration, `len()`, `.sum()`/`.mean()`/`.min()`/`.max()`, `.shape`,
  `.copy()`, `.is_compatible()`, `float()` for dimensionless quantities, format
  specifications (`f"{q:.1f}"`), pickling; pandas Series as operands.
- `pandas_tools`: `get_units`, `to_quantity`, `from_quantity`; substance, basis and
  reference year metadata; conversions go through `Quantity.to`.
- Registries: `reset()`, `UnitRegistry.parse_unit`, `dimension_vector`,
  `is_compatible`, `multiply_units`, `divide_units`, `conversion_factor`
  (substance-aware), `preferred_unit`, `currency_of`.
- Developer tool `scripts/update_data.py` (not installed) for the yearly data update:
  fetches exchange rates and US CPI from FRED, regenerates derived data, and checks
  consistency in CI.
- `py.typed` marker, data-integrity tests, README examples executed as tests,
  CI on Linux/Windows/macOS for Python 3.10-3.14, documentation build and wheel
  smoke test in CI; publishing checks the release tag against the version.

### Data
- **Exchange rates** replaced by Federal Reserve G.5A annual averages, extended to
  2000-2025 (2024 and 2025 are now actual values).
- **Inflation**: corrected USD values (2010, 2011, and 2014, which was 0.12 % instead
  of 1.62 %), 2024 and 2025 actuals, extended back to 2000, new GBP/JPY/CNY series;
  2026-2030 are now explicit placeholders at the 2 % target and emit a warning.
- **Fuel properties aligned with the IPCC 2006 Guidelines** (Vol. 2, Ch. 1): LHVs are
  the Table 1.2 net calorific values and `carbon_intensity` the Table 1.4 CO2 emission
  factors of the matching IPCC category; HHVs follow the IPCC rule of thumb (NCV 5 %
  below GCV for coal and oil, 10 % for natural gas). Results from fuel mass or volume
  change accordingly, for example (LHV, MJ/kg): `coal` 25.0 -> 25.8 (now "Other
  Bituminous Coal"), `bituminous` 28.5 -> 25.8, `anthracite` 31.5 -> 26.7, `lignite`
  14.0 -> 11.9, `natural_gas` 49.5 -> 48.0, `crude_oil` 42.5 -> 42.3, `diesel`
  42.8 -> 43.0, `gasoline` 44.0 -> 44.3.
- **Carbon contents** are derived from the emission factors, so CO2 from fuel energy
  reproduces the IPCC factors exactly. Previously they were set independently and
  disagreed with `carbon_intensity` (1 t of coal emitted 2.75 t CO2, now 2.44 t;
  1 GJ of coal 110 kg instead of 95).
- **Gas densities at 15 °C and 101.325 kPa** (natural gas 0.74 instead of 0.75, CO2
  1.87 instead of 1.98 kg/m3, hydrogen 0.0852 instead of 0.09). Natural gas now gives
  35.5 MJ/m3 (NCV) and 1.06 MMBtu/Mcf (GCV), within 2-3 % of typical values; the
  previous 37.1 MJ/m3 and 1.11 MMBtu/Mcf were about 7 % high.
- **Biomass** on an as-received basis (wood pellets 8 % moisture: LHV 17.0 MJ/kg
  instead of the dry-basis 18.5; wood chips 30 % moisture: LHV 12.2 MJ/kg).
  `carbon_intensity` is now the physical CO2 (pellets 99.2, chips 105.2 kg/GJ) instead
  of 0, with `biogenic: true`; CO2 from biomass was already physical.
- `methane` emits 54.9 kg CO2/GJ (stoichiometric; was listed as 56.1), `methanol` 69.1,
  `hydrogen` HHV 141.8 MJ/kg.
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
