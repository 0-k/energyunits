# EnergyUnits Architecture

This document describes how EnergyUnits works internally: the unit model, the
conversion pipeline, the arithmetic rules, the data files and the main design
decisions.

## Principles

1. **One conversion method.** `Quantity.to()` handles units, heating value basis,
   combustion products and price base years.
2. **Correct before convenient.** Dimensions are checked for every conversion and
   every sum. Conversions that need an assumption (a substance, a duration, an
   exchange rate convention) either require it explicitly or emit a warning.
3. **Data-driven.** Units, substances, inflation and exchange rates live in JSON
   files and can be extended at runtime without code changes.
4. **Small.** The only runtime dependency is NumPy; pandas support is optional.

## Package layout

| Module | Content |
|--------|---------|
| `quantity.py` | `Quantity`: values, metadata, `.to()`, arithmetic, comparisons |
| `registry.py` | `UnitRegistry`: unit parsing, dimensions, conversion factors, unit algebra |
| `substance.py` | `SubstanceRegistry`: heating values, densities, compositions |
| `inflation.py` | `InflationRegistry`: annual inflation rates per currency |
| `exchange_rate.py` | `ExchangeRateRegistry`: annual average exchange rates |
| `pandas_tools.py` | Optional helpers that store units in `DataFrame.attrs` |
| `units.py` | String constants for every unit (IDE autocompletion) |
| `exceptions.py` | Exception and warning classes |
| `_loading.py` | Reading data sources and reporting definition conflicts (shared by the registries) |
| `data/*.json` | Bundled data |

Each registry module exposes a module-level singleton (`registry`,
`substance_registry`, `inflation_registry`, `exchange_rate_registry`) with
`load_*()` methods to add data and `reset()` to restore the defaults.

### Loading data

The registries are shared by all code in the process, so loading follows rules that
let independent packages add data without affecting each other:

1. **Validate first.** `load_*(source, overwrite=False)` accepts a JSON file path or a
   mapping (deep-copied). All entries are validated (unknown sections, unit names,
   positive factors, numeric properties, ranges, years) before anything changes.
2. **Detect conflicts.** An entry whose name exists with a different definition
   (bundled or loaded earlier) is a conflict; identical entries are accepted, so
   loading is idempotent. Multiplication rules are identified by their two
   dimensions, division rules by numerator and denominator, inflation and exchange
   rates by currency and year, `projected_from` by currency. Floats are compared
   with a relative tolerance of 1e-12.
3. **All or nothing.** Conflicts raise `DefinitionConflictError` listing them, unless
   `overwrite=True`; nothing is loaded.
4. **Copy on write.** The new state is built on copies and committed by replacing
   the containers under a lock, so loads are serialised and readers in other
   threads never see a half-loaded state or a dict that changes while they iterate.
   `UnitRegistry` then installs fresh `lru_cache`s for its cached methods; a result
   that another thread computed from the previous data can only land in the
   discarded caches.

Substance properties are stored frozen (`MappingProxyType`, lists as tuples):
`substance_registry[name]` returns the read-only view, `get_properties()` a copy.

## Quantity

A `Quantity` holds

- `value`: a float NumPy array (0-d for scalars). Integers, lists, NumPy arrays and
  pandas Series (including nullable dtypes) are accepted; non-numeric input raises
  `TypeError`.
- `unit`: the unit string as given by the user.
- `substance`: optional substance name. It is a label until a conversion needs its
  properties, so unknown names only fail at that point.
- `basis`: optional `"HHV"`/`"LHV"` (normalised to upper case). `None` means "not
  specified" and is treated as LHV by conversions.
- `reference_year`: optional integer price base year.
- `dimension`: the dimension name of the unit (derived).

All operations return new objects. NumPy defers to `Quantity` in mixed operations
(`__array_ufunc__ = None`), and so does pandas (`__pandas_priority__`), so
`array * quantity` and `series * quantity` return quantities.

## Units

### Syntax

A unit string is a sequence of registered *atomic* units joined by `/` or
`·`/`*`. Operators have equal precedence and are evaluated left to right, so
every atom after a `/` is in the denominator:

```text
"MWh"         energy
"USD/kW"      currency / power
"EUR/kW/a"    (EUR / kW) / a          -> EUR per kW and year
"USD·h/MWh"   (USD · h) / MWh
"1/h"         reciprocal time
""            dimensionless
```

`UnitRegistry.parse_unit()` returns a tuple of `(atom, exponent)` pairs with
identical atoms merged (`"MWh/MWh"` parses to `()`). Malformed strings (`"MW//h"`,
`"MW/"`, whitespace only) and unknown atoms raise `UnknownUnitError` with
suggestions for close matches. Exponent syntax (`m^2`) is not supported; `m3` is
an atom of its own.

### Dimensions

Every atom belongs to a named dimension. Base dimensions are `ENERGY`, `MASS`,
`VOLUME`, `AREA`, `TIME` and `CURRENCY`; `POWER` is a *derived* dimension defined as
`ENERGY / TIME` in `units.json`. Each unit therefore has a **dimension vector**
over base dimensions:

```text
MW       -> ENERGY^1 TIME^-1
GJ/h     -> ENERGY^1 TIME^-1      (same as MW)
kWh/kW   -> TIME^1                (same as h)
EUR/kW/a -> CURRENCY^1 ENERGY^-1  (same as EUR/kWh)
```

Two units are convertible without further information if their vectors are equal.
`get_dimension()` returns a readable name: the registered dimension for atoms, the
name of a matching dimension for compound units (`"GJ/h"` -> `POWER`,
`"kWh/kW"` -> `TIME`) and otherwise a descriptive name built from the atoms
(`"USD/kW"` -> `CURRENCY_PER_POWER`).

### Conversion factors

Each atom has a factor relative to the **SI-coherent base unit** of its dimension:
J, W, kg, m3, m2, s and USD. Factors of derived dimensions must be coherent with their
definition (`factor(W) == factor(J) / factor(s)`); a data-integrity test enforces
this. Keeping factors relative to SI units means metric prefixes are exact powers
of ten and conversions like `MWh -> GJ` are exact in floating point. For the same
reason, numerators and denominators of factors are kept separate until the final
step (`unit_factor_parts()`, `combine_units()`).

When a calculation has to *choose* a unit (for example `GJ / h`), the
`preferred_units` table is used (MWh, MW, t, m3, h, USD), not the SI base.

Currency factors in `units.json` are static rates (the most recent annual average
in `exchange_rates.json`). Year-specific rates are applied by `Quantity` on top of
them (see below).

## The conversion pipeline

`Quantity.to(target_unit, basis, substance, reference_year)` applies the requested
steps in this order:

1. **Basis** (`_convert_basis`). Requires a substance. The value is multiplied by
   `(LHV/HHV) ** e` when going from HHV to LHV, where `e` is the exponent of
   `ENERGY` in the unit: energy amounts shrink (`e = 1`), per-energy quantities such
   as prices and emission factors grow (`e = -1`), and masses/volumes are only
   re-labelled (`e = 0`).
2. **Substance** (`_convert_substance`). Converts a fuel quantity into a combustion
   product (`CO2`, `H2O`, `ash`). The amount part of the unit (energy, volume or
   mass) is first expressed as mass of fuel (`MWh -> t`, `MW -> t/h`,
   `USD/MWh -> USD/t`), then multiplied by the product factor
   (`carbon_content * 44/12`, `hydrogen_content * 9`, `ash_content`). Sources
   without combustion products return zeros with the same shape. The basis is reset
   (products have none); the reference year is kept.
3. **Unit** (`_convert_unit`). Two cases:
   - *Same dimension vector*: scale by the ratio of factors.
   - *Amount swap*: if the vectors differ only by exchanging one of MASS, VOLUME,
     ENERGY for another (with the same exponent), the substance's heating value
     (per basis) and density bridge the gap. This covers `t -> MWh`, `m3 -> t`,
     `USD/t -> USD/MWh` and `MW -> t/h` with the same code.
   - Anything else raises `IncompatibleUnitsError`. In particular, power and energy
     differ by `TIME` and are never converted implicitly.

   If the source and target units contain one currency each and these differ, the
   static currency factor is replaced by the exchange rate of the quantity's
   reference year (or the most recent year without one).
4. **Reference year** (`_convert_reference_year`). Multiplies by the cumulative
   inflation factor of the unit's currency, raised to the currency's exponent (a
   currency in the denominator deflates).

**Currency and year together.** When both the currency and the reference year
change, steps 3 and 4 are swapped: the value is inflated in its original currency
first and then converted with the exchange rate of the *target* year. An
`EnergyUnitsWarning` documents the convention.

## Arithmetic

### Addition, subtraction and comparison

The right operand is *aligned* to the left one (`Quantity._align`): converted to
the left unit, to the left heating value basis (if it has a substance; a mass or
volume is then converted to energy at that basis, so `MMBTU (HHV) + m3` adds HHV
energy) and, for monetary units, to the left reference year. Then the values are
combined; an operand that already matches is used as is. Mixing substances drops the substance and warns.
`==` uses a relative tolerance of 1e-9 so that conversions that differ only by
floating point round-off compare equal; incompatible quantities are unequal.
`sum()` works because `0 + quantity` is supported.

### Multiplication and division

`UnitRegistry.combine_units()` computes the unit and the scaling of the result:

1. **Merge atoms of the same kind.** Atoms with the same dimension (and, for
   currencies, the same currency code) are merged; later atoms are converted into
   the first one. This turns `USD/kW × MW` into `USD` (×1000) and
   `GWh / MWh` into a dimensionless 1000.
2. **Apply dimension rules.** The rules in `units.json` combine one atom from each
   operand:
   - `POWER × TIME -> ENERGY` (`MW × min -> MWh`, using the corresponding unit of
     the power atom),
   - `ENERGY / TIME -> POWER` (`MWh / a -> MW`),
   - `ENERGY / POWER -> TIME` (`MWh / MW -> h`).

   The result unit is the *corresponding* unit (`MW` <-> `MWh`, ...) or the
   preferred unit of the result dimension. A rule is only applied when it is
   dimensionally coherent, and never to atoms of the same operand, so units such as
   `MWh/a` or `EUR/kW/a` are not rewritten by themselves.
3. **Format** the remaining atoms canonically: numerator atoms joined with `·`,
   then `/atom` for every denominator atom.

Before multiplying or dividing, what can cancel is aligned: if both operands are
fuel energy of the same substance on different bases, the right one is converted
to the left basis (`USD/MWh (HHV) × MWh (LHV)`), and if both are monetary with
different reference years, the right one is inflated to the left year
(`EUR (2015) / EUR/MWh (2024)`).

Metadata of products and quotients: the substance is kept if equal or if only one
operand has one. The basis is that of the operand with fuel energy
(`MW (HHV) × h` is HHV energy), or dropped if two such operands disagree. The
reference year is that of the monetary operand, or of whichever operand has one.

Scalars and numeric arrays scale the value and keep unit and metadata.
`number / quantity` returns the reciprocal unit (`1 / Quantity(4, "h")` is
`0.25 1/h`).

## Data files

All files live in `energyunits/data/`. Keys starting with `_` are metadata and are
ignored by the loaders.

### `units.json`

| Section | Content |
|---------|---------|
| `dimensions` | atom -> dimension name |
| `conversion_factors` | atom -> factor relative to the base unit of its dimension |
| `base_units` | dimension -> unit with factor 1 (SI-coherent) |
| `preferred_units` | dimension -> unit chosen by calculations |
| `derived_dimensions` | e.g. `{"POWER": {"ENERGY": 1, "TIME": -1}}` |
| `currency_units` | atom -> `{"currency": code, "scale": factor}` (e.g. `MEUR`) |
| `corresponding_units` | e.g. `MW` <-> `MWh` |
| `dimensional_multiplication_rules` / `dimensional_division_rules` | see above |

Example custom file:

```json
{
  "dimensions": {"MMscf": "VOLUME", "AUD": "CURRENCY"},
  "conversion_factors": {"MMscf": 28316.846592, "AUD": 0.65}
}
```

Unit names must not contain whitespace, `/`, `*` or `·`.

### `substances.json`

One object per substance with `name`, `hhv`, `lhv` (MJ/kg), `density` (kg/m3),
`carbon_intensity` (kg CO2/GJ, LHV), `carbon_content`, `hydrogen_content`,
`ash_content` (mass fractions) and optionally `ipcc_category`, `lhv_range` and
`carbon_intensity_range` (IPCC lower/upper limits as `[low, high]`), `density_basis`,
`moisture_content`, `biogenic` and `source`. Missing properties may be `null` or
omitted; conversions that need them raise `MissingDataError`. Conversions only use
the heating values, density and composition; the other fields are documentation and
inputs for sensitivity analysis.

`carbon_content` equals `carbon_intensity × lhv / 1000 × 12/44`, so CO2 from fuel
energy reproduces the emission factor and CO2 from fuel mass equals NCV × factor
(checked by tests against the IPCC defaults). A loaded substance that gives only one
of the two gets the other derived (`substance._complete_carbon`). The fuel tables in
README.md and DATA_SOURCES.md are generated from this file by
`scripts/update_data.py sync`.

### `inflation.json`

```json
{"_metadata": {"projected_from": {"USD": 2026}}, "USD": {"2010": 1.64, "2011": 3.16}}
```

The value for year Y is the change of the annual average price index from Y-1 to Y
in percent. Years from `projected_from` onwards are projections; conversions that
use them warn.

### `exchange_rates.json`

```json
{"EUR": {"2024": 1.0820, "2025": 1.1306}}
```

USD per unit of currency, annual averages. Years after the last available year use
the last rate (with a warning); earlier years raise `MissingDataError`.

## Errors and warnings

All exceptions derive from `EnergyUnitsError`, which subclasses `ValueError`:
`UnknownUnitError`, `IncompatibleUnitsError`, `UnknownSubstanceError` and
`MissingDataError`. Invalid argument *types* raise `TypeError`.

Assumptions are reported as `EnergyUnitsWarning` (a `UserWarning`). Warnings are
attributed to the first stack frame outside the package, so they point at the
user's line.

## Design decisions

**Why string units instead of unit objects?** Energy models read units from
spreadsheets, CSV headers and configuration files. Plain strings (`"EUR/kW/a"`)
round-trip through all of them; `energyunits.units` offers constants for IDE
support.

**Why not pint?** pint is a general-purpose library. EnergyUnits is narrower but
adds the domain knowledge that energy work needs and pint lacks: substances
(heating values, densities, emissions), heating value bases, price base years and
year-dependent exchange rates.

**Why no implicit power <-> energy conversion?** `Quantity(100, "MW").to("MWh")`
would require an assumed duration. Multiplying by an explicit `Quantity(1, "h")` is
just as short and cannot be misread.

**Why LHV as default basis?** LHV (net calorific value) is the convention of IPCC
emission factors, IEA balances and most European statistics. Use `basis="HHV"`
for US conventions.

**Why inflate first, then convert?** It answers "what does this cost in target
year money in the target currency" with the target year's market exchange rate and
the source country's price development. The alternative path gives different
numbers; the warning makes the choice visible.

**Why shared registries?** Units in energy models are strings read from data
files, and a `Quantity` is plain data that can be pickled and combined with any other.
Separate registry objects (as in pint) isolate packages completely, but every quantity
then carries its registry and mixing quantities from two registries has to fail. The
loading rules above give most of the isolation for packages that add data; a scoped
override (`contextvars`) or separate registries can be added later without changing
the existing API.

**Why physical CO2 for biomass?** The library reports what is emitted. Accounting
conventions (biogenic CO2 counted as zero) are a reporting decision left to the
model; `carbon_intensity` is the physical factor (IPCC Table 1.4 lists 112 kg/GJ for
wood) and `biogenic` marks the fuels.

## Testing

The test suite covers every conversion path, the unit algebra (including
regression tests for previously wrong results), metadata propagation, Python and
NumPy protocols, the pandas helpers, the consistency of all bundled data and every
example in the README (the documented outputs are compared with the actual
output). Tests reset the global registries after each test (`tests/conftest.py`).
CI runs on Linux, Windows and macOS for all supported Python versions, without
pandas, builds the documentation and smoke-tests the built wheel.

## Limitations and possible extensions

- No temperature, pressure or length dimensions (length can be loaded as a custom
  dimension, see the tests). Affine units such as degree Celsius
  would need special handling.
- No uncertainty propagation.
- One set of registries per process: there is no scoped override (for example for a
  sensitivity run in one thread) yet.
- One currency per unit for year-specific exchange rates and inflation
  (units such as `USD/EUR` use static rates).
- Inflation and exchange rate data cover 2000-2025 (inflation projections to 2030).
- pandas does not propagate `DataFrame.attrs` through every operation.
