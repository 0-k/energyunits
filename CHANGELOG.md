# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

---

[0.2.0]: https://github.com/0-k/energyunits/releases/tag/v0.2.0
[0.1.0]: https://github.com/0-k/energyunits/releases/tag/v0.1.0
[0.0.1]: https://github.com/0-k/energyunits/releases/tag/v0.0.1
