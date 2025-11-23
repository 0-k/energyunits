# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/0-k/energyunits/releases/tag/v0.1.0
[0.0.1]: https://github.com/0-k/energyunits/releases/tag/v0.0.1
