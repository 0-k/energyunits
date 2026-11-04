# Data Sources and References

This document provides citations and references for all energy conversion values, fuel properties, and emission factors used in the EnergyUnits library.

## Overview

Fuel properties in `energyunits/data/substances.json` follow the **2006 IPCC Guidelines
for National Greenhouse Gas Inventories, Volume 2 (Energy), Chapter 1** wherever the
IPCC defines a fuel category:

- net calorific values (NCV, the same as LHV): default values and 95 % confidence limits
  of **Table 1.2**;
- CO2 emission factors: default values and lower/upper limits of **Table 1.4**, assuming
  complete oxidation.

These are the IPCC **Tier 1** defaults: global averages for use when no country- or
plant-specific data are available. Read [Accuracy and appropriate use](#accuracy-and-appropriate-use)
before using them for anything other than energy-system modelling and screening.

## Fuel Properties

### Method

- **LHV (NCV)**: IPCC default (Table 1.2). Conversions use the LHV unless `basis="HHV"`.
- **HHV (GCV)**: the IPCC publishes NCVs only. For IPCC fuels the HHV follows the IPCC rule
  of thumb that the NCV is about 5 % below the GCV for coal and oil and about 10 % below
  for natural gas, i.e. HHV = NCV / 0.95 or NCV / 0.90. Pure compounds (methane, hydrogen,
  methanol) use their thermochemical values; biomass uses moisture-based estimates.
- **CO2 emission factor** (`carbon_intensity`, kg CO2 per GJ on NCV basis): IPCC default
  (Table 1.4).
- **Carbon content**: derived as `carbon_intensity × lhv / 1000 × 12/44`. CO2 computed from
  fuel *energy* therefore reproduces the IPCC factor exactly, and CO2 from fuel *mass* equals
  NCV × emission factor.
- **Ranges** (`lhv_range`, `carbon_intensity_range`): IPCC lower and upper limits, available
  through `substance_registry.get_properties(name)`.
- **Densities** are not IPCC data: liquids at 15 °C, solids as indicative bulk densities,
  gases at 15 °C and 101.325 kPa (see [Gas reference conditions](#gas-reference-conditions)).
- **Hydrogen and ash contents** are indicative typical values. They are only used for
  `substance="H2O"` and `substance="ash"`; H2O from fuel moisture is not included.

### Fuels

<!-- BEGIN GENERATED fuel-table: edit `energyunits/data/substances.json` and run `python scripts/update_data.py sync` -->
| Substance | IPCC category | LHV (MJ/kg) [IPCC range] | HHV (MJ/kg) | kg CO2/GJ [IPCC range] | Density (kg/m3) |
|-----------|---------------|------:|------:|------:|------:|
| `coal` | Other Bituminous Coal | 25.8 [19.9–30.5] | 27.16 | 94.6 [89.5–99.7] | 833 |
| `bituminous` | Other Bituminous Coal | 25.8 [19.9–30.5] | 27.16 | 94.6 [89.5–99.7] | 833 |
| `coking_coal` | Coking Coal | 28.2 [24.0–31.0] | 29.68 | 94.6 [87.3–101.0] | 800 |
| `sub_bituminous` | Sub-Bituminous Coal | 18.9 [11.5–26.0] | 19.89 | 96.1 [92.8–100.0] | 800 |
| `anthracite` | Anthracite | 26.7 [21.6–32.2] | 28.11 | 98.3 [94.6–101.0] | 1000 |
| `lignite` | Lignite | 11.9 [5.5–21.6] | 12.53 | 101.0 [90.9–115.0] | 700 |
| `peat` | Peat | 9.76 [7.8–12.5] | 10.27 | 106.0 [100.0–108.0] | 350 |
| `natural_gas` | Natural Gas | 48.0 [46.5–50.4] | 53.33 | 56.1 [54.3–58.3] | 0.74 |
| `lng` | Natural Gas | 48.0 [46.5–50.4] | 53.33 | 56.1 [54.3–58.3] | 450 |
| `crude_oil` | Crude Oil | 42.3 [40.1–44.8] | 44.53 | 73.3 [71.1–75.5] | 870 |
| `oil` | Crude Oil | 42.3 [40.1–44.8] | 44.53 | 73.3 [71.1–75.5] | 870 |
| `fuel_oil` | Residual Fuel Oil | 40.4 [39.8–41.7] | 42.53 | 77.4 [75.5–78.8] | 950 |
| `diesel` | Gas/Diesel Oil | 43.0 [41.4–43.3] | 45.26 | 74.1 [72.6–74.8] | 840 |
| `gasoline` | Motor Gasoline | 44.3 [42.5–44.8] | 46.63 | 69.3 [67.5–73.0] | 750 |
| `jet_kerosene` | Jet Kerosene | 44.1 [42.0–45.0] | 46.42 | 71.5 [69.7–74.4] | 800 |
| `lpg` | Liquefied Petroleum Gases | 47.3 [44.8–52.2] | 49.79 | 63.1 [61.6–65.6] | 540 |
| `wood` | Wood/Wood Waste | 15.6 [7.9–31.0] | 17.1 | 112.0 [95.0–132.0] (biogenic) | – |
| `wood_pellets` | Wood/Wood Waste | 17.0 [7.9–31.0] | 18.4 | 99.2 [95.0–132.0] (biogenic) | 650 |
| `wood_chips` | Wood/Wood Waste | 12.2 [7.9–31.0] | 13.9 | 105.2 [95.0–132.0] (biogenic) | 350 |
| `methane` | – | 50.0 | 55.5 | 54.9 | 0.68 |
| `hydrogen` | – | 120.0 | 141.8 | 0.0 | 0.0852 |
| `methanol` | – | 19.9 | 22.7 | 69.1 | 795 |
<!-- END GENERATED fuel-table -->

Notes:

- `coal` and `bituminous` both use the IPCC category "Other Bituminous Coal" (steam coal,
  the most common coal in power generation); `oil` is crude oil; `lng` is natural gas in
  liquid form.
- `methane`, `hydrogen` and `methanol` are pure compounds with thermochemical heating values
  and stoichiometric composition.
- `wood` is the IPCC default pair for Wood/Wood Waste. Its NCV and emission factor are
  independent averages, so results from wood *mass* are only indicative; the HHV assumes
  20 % moisture.
- `wood_pellets` and `wood_chips` are product definitions (see [Biomass](#biomass)) whose
  values lie within the IPCC range for wood.
- `wind`, `solar`, `hydro` and `nuclear` have no combustion products; `CO2`, `H2O` and
  `ash` are combustion products.

### Gas reference conditions

Densities of gases refer to **15 °C and 101.325 kPa** (ISO 13443 standard reference
conditions), the convention of IEA and Energy Institute statistics. A gas volume in `m3`,
`bcm`, `ft3`, `Mcf` or `Bcf` is therefore a standard volume (`Sm3`). US standard cubic feet
(60 °F, 14.73 psia) differ by less than 0.1 %, which is ignored. For normal cubic metres
(0 °C, 101.325 kPa) use the unit `Nm3`: the same amount of gas occupies 288.15/273.15 times
the volume at 15 °C, so 1 Nm3 = 1.0549 Sm3.

With a density of 0.74 kg/m3 at 15 °C and the IPCC NCV of 48.0 MJ/kg, natural gas gives:

| Quantity | Value | Comparison |
|----------|-------|------------|
| NCV per volume | 35.5 MJ/Sm3, 37.5 MJ/Nm3 | typical H-gas: 34-37 MJ/Sm3 |
| GCV per Mcf | 1.06 MMBtu | US average heat content about 1.037 MMBtu/Mcf (EIA), +2 % |
| 1 bcm | 35.5 PJ = 9.87 TWh (NCV) | Energy Institute: 1 bcm ≈ 0.86 Mtoe = 36 PJ |

Gas composition varies: low-calorific L-gas has about 15 % less energy per cubic metre.
Load a custom substance for a specific gas quality.

### Biomass

**Wood pellets** (`wood_pellets`) are **as received** (ENplus A1 quality, 8 % moisture),
derived from dry-basis properties (HHV 20.0 MJ/kg, 50 % carbon, 6 % hydrogen, 1 % ash):

- HHV = 20.0 × (1 - 0.08) = 18.4 MJ/kg; LHV = HHV - 2.442 × (moisture + 8.936 × hydrogen)
  = 17.0 MJ/kg (ENplus A1 requires at least 16.5 MJ/kg)
- Carbon 46 %, hydrogen 5.5 %, ash 0.9 % (as received); bulk density 650 kg/m3

**Wood chips** (`wood_chips`) are **as received** at 30 % moisture (class M30), derived from
HHV 19.8 MJ/kg (dry), 50 % carbon, 6 % hydrogen, 2 % ash: HHV 13.9 MJ/kg, LHV 12.2 MJ/kg
(about 3.4 kWh/kg). At 50 % moisture the LHV drops to about 8 MJ/kg; load a custom substance
for other moisture contents.

**Biogenic CO2**: `carbon_intensity` is the physical CO2 released by combustion (the IPCC
lists 112 kg/GJ for wood in Table 1.4). Inventories report biogenic CO2 as a memo item and
not in national totals; the fuels are marked `biogenic: true`. The library always returns
the physical CO2, so apply the accounting convention in your model.

**References:**
- [ENplus Handbook - Quality Requirements](https://enplus-pellets.eu/)
- [Natural Resources Canada - Solid Biofuels Bulletin](https://natural-resources.canada.ca/sites/nrcan/files/files/NRCAN_BB_no2_e13.pdf)

### Verification of the IPCC values

The defaults and NCV limits were checked against reproductions of Tables 1.2 and 1.4 and
against Chapter 2 (Stationary Combustion), which repeats the emission factors with their
limits. The lower/upper limits of the emission factors for natural gas, lignite,
sub-bituminous coal, gas/diesel oil, residual fuel oil, LPG and jet kerosene could not be
cross-checked against a second source and should be confirmed against the official PDF
when the data are next reviewed.

## Accuracy and appropriate use

The defaults are IPCC Tier 1 values. How reliable a result is depends mainly on what the
calculation starts from:

| Calculation | Basis | Typical deviation from country- or plant-specific values |
|-------------|-------|----------------------------------------------------------|
| CO2 from fuel **energy**: oil products, natural gas | IPCC Tier 1 default | 1-3 % |
| CO2 from fuel energy: hard coal | IPCC Tier 1 default | 3-5 % |
| CO2 from fuel energy: lignite, peat | IPCC Tier 1 default (lignite: 90.9-115 kg/GJ) | up to about 10 % |
| Energy or CO2 from fuel **mass**: oil products | NCV range of a few % | a few % |
| Energy or CO2 from fuel mass: hard coal | NCV range 19.9-30.5 MJ/kg (other bituminous coal) | 10-20 % |
| Energy or CO2 from fuel mass: lignite, peat | NCV range 5.5-21.6 MJ/kg (lignite) | up to 50 % |
| Energy or CO2 from fuel mass: biomass | depends on moisture | 30 % or more |
| Energy from gas **volume** | composition and reference conditions | 2-5 % (H-gas), about 15 % (L-gas) |
| Results on HHV basis | IPCC rule of thumb for HHV | 1-3 %; more for LPG and wet lignite |
| H2O and ash | indicative composition | large |

**Suitable for:** energy-system modelling, techno-economic analysis, scenario and screening
studies, sanity checks. Prefer energy-based inputs (MWh or GJ of fuel) where you can.

**Not suitable for:** compliance reporting (the EU ETS Monitoring and Reporting Regulation
requires Tier 2/3 or measured values; national inventories use country-specific factors),
plant-level accounting and product carbon footprints.

**Not included:**

- CH4 and N2O from combustion. For power plants they add less than 1 % CO2-equivalent for
  fossil fuels; for small-scale combustion and biomass they matter more.
- Upstream and lifecycle emissions (mining, methane leakage, transport, processing).
- Incomplete oxidation (the IPCC defaults assume all carbon is oxidised).

**Sensitivity analysis with the IPCC ranges:**

```python
from energyunits import Quantity
from energyunits.substance import substance_registry

props = substance_registry.get_properties("lignite")
low, high = props["lhv_range"]                       # 5.5, 21.6 MJ/kg
energy = Quantity(1000, "t", "lignite").to("GJ")     # 11900.00 GJ (default 11.9 MJ/kg)
print(energy * (low / props["lhv"]), energy * (high / props["lhv"]))   # 5500.00 GJ of lignite 21600.00 GJ of lignite
```

**Using your own factors:** load a custom substance. Emission factors are usually published
per unit of energy; if only `lhv` and `carbon_intensity` are given, the carbon content is
derived automatically (illustrative values for a German lignite, `my_fuels.json`):

```json
{"rhenish_lignite": {"name": "Rhenish lignite", "lhv": 8.9, "carbon_intensity": 113.5}}
```

```python
from energyunits import Quantity
from energyunits.substance import substance_registry

substance_registry.load_substances("my_fuels.json")
print(Quantity(1, "t", "rhenish_lignite").to("t", substance="CO2"))   # 1.01 t of CO2
```

Add `hhv`, `density` and the other fields of the table above as needed; a conversion that
needs a missing field raises `MissingDataError`.

## Additional References

### Primary Sources

1. **IPCC Guidelines:**
   - [2006 IPCC Guidelines for National Greenhouse Gas Inventories](https://www.ipcc-nggip.iges.or.jp/public/2006gl/)
   - [IPCC Emissions Factor Database](https://ghgprotocol.org/Third-Party-Databases/IPCC-Emissions-Factor-Database)

2. **US EPA:**
   - [Emission Factors for Greenhouse Gas Inventories (2024)](https://www.epa.gov/system/files/documents/2024-02/ghg-emission-factors-hub-2024.pdf)
   - [Greenhouse Gas Equivalencies Calculator](https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references)

3. **IEA:**
   - [Emissions Factors 2024 Database](https://www.iea.org/data-and-statistics/data-product/emissions-factors-2024)
   - [IEA Methodology - Emission Factors](https://iea.blob.core.windows.net/assets/884cd44a-3a59-4359-9bc4-d5c5fb3cc66c/IEA_Methodology_Emission_Factors.pdf)

4. **The Climate Registry:**
   - [2024 Default Emission Factors](https://theclimateregistry.org/wp-content/uploads/2024/03/2024-Emission-Factor-Document_FINAL.pdf)

### Secondary Sources

- [Engineering Toolbox](https://www.engineeringtoolbox.com/) - Technical reference data
- [World Nuclear Association - Heat Values](https://world-nuclear.org/information-library/facts-and-figures/heat-values-of-various-fuels)
- [H2tools - Hydrogen Properties](https://h2tools.org/)
- [AFDC - Alternative Fuels Data Center](https://afdc.energy.gov/)

## Unit Definitions

Conversion factors are exact by definition unless noted.

| Unit | Definition |
|------|------------|
| `Wh` | 3600 J |
| `BTU` | International Table BTU, 1055.05585262 J |
| `kBTU`, `MMBTU`, `therm`, `quad` | 10^3, 10^6, 10^5 and 10^15 BTU |
| `kcal`, `Mcal`, `Gcal` | International Table calorie, 4.1868 J |
| `toe` | tonne of oil equivalent, 41.868 GJ (IEA/OECD) |
| `tce` | tonne of coal equivalent, 29.3076 GJ (7 Gcal) |
| `barrel` | US oil barrel, 42 US gallons = 0.158987294928 m3 |
| `gal` | US liquid gallon, 3.785411784 L |
| `ft3`, `Mcf`, `Bcf` | cubic foot (0.3048 m)^3, 10^3 and 10^9 ft3 |
| `bcm` | 10^9 m3 |
| `Sm3` | standard cubic metre of gas (15 °C, 101.325 kPa), equal to `m3` |
| `Nm3` | normal cubic metre of gas (0 °C, 101.325 kPa) = 288.15/273.15 Sm3 |
| `lb` | avoirdupois pound, 0.45359237 kg |
| `ha`, `km2` | 10^4 m2, 10^6 m2 |
| `acre` | international acre, 4046.8564224 m2 |
| `ft2` | square foot, 0.09290304 m2 |
| `a`, `yr` | 8760 h (365 days), the usual convention in energy models |

Gas volumes are standard volumes at 15 °C, see [Gas reference conditions](#gas-reference-conditions).

## Inflation Data

Annual consumer price inflation in percent, defined as the change of the annual
average price index from the previous year. Converting from reference year A to B
multiplies by the product of `(1 + rate/100)` for all years after A up to B.

| Currency | Source |
|----------|--------|
| USD | US Bureau of Labor Statistics, CPI-U, U.S. city average, all items |
| EUR | Eurostat, HICP all items, euro area, annual average rate of change |
| GBP | UK Office for National Statistics, CPI annual average rate (D7G7) |
| JPY | Statistics Bureau of Japan, CPI all items, yearly average |
| CNY | National Bureau of Statistics of China, CPI, annual change |

<!-- BEGIN GENERATED inflation-table: edit the JSON data and run `python scripts/update_data.py sync` -->
| Year | USD | EUR | GBP | JPY | CNY |
|------|----:|----:|----:|----:|----:|
| 2000 | 3.36 | 2.20 | 0.80 | -0.70 | 0.40 |
| 2001 | 2.85 | 2.40 | 1.20 | -0.70 | 0.70 |
| 2002 | 1.58 | 2.30 | 1.30 | -0.90 | -0.80 |
| 2003 | 2.28 | 2.10 | 1.40 | -0.30 | 1.20 |
| 2004 | 2.66 | 2.20 | 1.30 | 0.00 | 3.90 |
| 2005 | 3.39 | 2.20 | 2.10 | -0.30 | 1.80 |
| 2006 | 3.23 | 2.20 | 2.30 | 0.30 | 1.50 |
| 2007 | 2.85 | 2.10 | 2.30 | 0.00 | 4.80 |
| 2008 | 3.84 | 3.30 | 3.60 | 1.40 | 5.90 |
| 2009 | -0.36 | 0.30 | 2.20 | -1.40 | -0.70 |
| 2010 | 1.64 | 1.60 | 3.30 | -0.70 | 3.30 |
| 2011 | 3.16 | 2.70 | 4.50 | -0.30 | 5.40 |
| 2012 | 2.07 | 2.50 | 2.80 | 0.00 | 2.60 |
| 2013 | 1.46 | 1.40 | 2.60 | 0.40 | 2.60 |
| 2014 | 1.62 | 0.40 | 1.50 | 2.70 | 2.00 |
| 2015 | 0.12 | 0.00 | 0.00 | 0.80 | 1.40 |
| 2016 | 1.26 | 0.20 | 0.70 | -0.10 | 2.00 |
| 2017 | 2.13 | 1.50 | 2.70 | 0.50 | 1.60 |
| 2018 | 2.44 | 1.80 | 2.50 | 1.00 | 2.10 |
| 2019 | 1.81 | 1.20 | 1.80 | 0.50 | 2.90 |
| 2020 | 1.23 | 0.30 | 0.90 | 0.00 | 2.50 |
| 2021 | 4.70 | 2.60 | 2.60 | -0.20 | 0.90 |
| 2022 | 8.00 | 8.40 | 9.10 | 2.50 | 2.00 |
| 2023 | 4.12 | 5.40 | 7.30 | 3.20 | 0.20 |
| 2024 | 2.95 | 2.40 | 2.50 | 2.70 | 0.20 |
| 2025 | 2.60 | 2.10 | 3.40 | 3.20 | 0.00 |
| 2026* | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 |
| 2027* | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 |
| 2028* | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 |
| 2029* | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 |
| 2030* | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 |
<!-- END GENERATED inflation-table -->

\* Projections: placeholders equal to the 2 % central bank target, not forecasts.
Conversions that use them emit an `EnergyUnitsWarning`. Replace them with your own
assumptions via `inflation_registry.load_inflation()` where it matters.

Notes:

- USD rates are computed from the BLS annual average index (e.g. 2024: 313.689 vs.
  304.702 in 2023 = +2.95 %). The 2025 value (+2.6 %) is based on the published
  annual average, which excludes October 2025 (no data collection during the
  federal funding lapse).
- Values are rounded to 0.1 percentage points for EUR, GBP, JPY and CNY and to
  0.01 for USD. Values for 2000-2009 were cross-checked against secondary
  compilations (World Bank, OBR) and agree within 0.1 percentage points; the euro area
  aggregate refers to the changing composition of the euro area in each year. Earlier versions of this library contained errors for USD 2010,
  2011 and 2014 (2014 was listed as 0.12 % instead of 1.62 %) and preliminary
  estimates for 2024.

## Exchange Rates

Annual averages of daily noon buying rates in New York from the Board of Governors
of the Federal Reserve System, release G.5A ("Foreign Exchange Rates, Annual"). The
library stores all rates as US dollars per unit of currency; JPY and CNY, which the
Fed quotes as units per US dollar, are stored as the inverse of the values below.

<!-- BEGIN GENERATED exchange-rate-table: edit the JSON data and run `python scripts/update_data.py sync` -->
| Year | EUR (USD per EUR) | GBP (USD per GBP) | JPY (JPY per USD) | CNY (CNY per USD) |
|------|------------------:|------------------:|------------------:|------------------:|
| 2000 | 0.9232 | 1.5156 | 107.8 | 8.2784 |
| 2001 | 0.8952 | 1.4396 | 121.57 | 8.277 |
| 2002 | 0.9454 | 1.5025 | 125.22 | 8.2771 |
| 2003 | 1.1321 | 1.6347 | 115.94 | 8.2772 |
| 2004 | 1.2438 | 1.8330 | 108.15 | 8.2768 |
| 2005 | 1.2449 | 1.8204 | 110.11 | 8.1936 |
| 2006 | 1.2563 | 1.8434 | 116.31 | 7.9723 |
| 2007 | 1.3711 | 2.0020 | 117.76 | 7.6058 |
| 2008 | 1.4726 | 1.8545 | 103.39 | 6.9477 |
| 2009 | 1.3935 | 1.5661 | 93.68 | 6.8307 |
| 2010 | 1.3261 | 1.5465 | 87.78 | 6.7696 |
| 2011 | 1.3931 | 1.6039 | 79.7 | 6.463 |
| 2012 | 1.2859 | 1.5852 | 79.82 | 6.3093 |
| 2013 | 1.3281 | 1.5642 | 97.6 | 6.1478 |
| 2014 | 1.3297 | 1.6484 | 105.74 | 6.162 |
| 2015 | 1.1096 | 1.5284 | 121.05 | 6.2827 |
| 2016 | 1.1072 | 1.3555 | 108.66 | 6.64 |
| 2017 | 1.1301 | 1.2890 | 112.1 | 6.7569 |
| 2018 | 1.1817 | 1.3363 | 110.3974 | 6.609 |
| 2019 | 1.1194 | 1.2768 | 109.0188 | 6.9081 |
| 2020 | 1.1410 | 1.2829 | 106.7754 | 6.9042 |
| 2021 | 1.1830 | 1.3764 | 109.8429 | 6.4508 |
| 2022 | 1.0534 | 1.2371 | 131.4589 | 6.729 |
| 2023 | 1.0817 | 1.2440 | 140.5001 | 7.0809 |
| 2024 | 1.0820 | 1.2781 | 151.4551 | 7.1957 |
| 2025 | 1.1306 | 1.3192 | 149.5686 | 7.1875 |
<!-- END GENERATED exchange-rate-table -->

Values were taken from the most recent G.5A release that lists each year; the Fed
occasionally revises historical averages by a few units in the fourth decimal.

### How exchange rates are applied

- A quantity with a `reference_year` is converted with the rate of that year.
- Without a reference year, the most recent year (2025) is used.
- For years after the most recent available year, the most recent rate is used and
  an `EnergyUnitsWarning` is emitted. Years before 2000 raise `MissingDataError`.
- The static currency factors in `units.json` equal the most recent annual averages;
  they are used by `registry.get_conversion_factor()` and for currencies without
  year-dependent data.

### Currency + inflation convention: "inflate first, then convert"

When a conversion changes both the currency and the reference year, the value is
first inflated in its original currency and then converted with the exchange rate
of the target year:

```python
cost_eur_2015 = Quantity(50, "EUR/MWh", reference_year=2015)
cost_usd_2024 = cost_eur_2015.to("USD/MWh", reference_year=2024)
# 1. inflate EUR 2015 -> 2024 with euro area HICP (x 1.2615)
# 2. convert with the 2024 annual average rate (1.0820 USD/EUR) -> 68.25 USD/MWh
```

Converting first and inflating afterwards (with US inflation) gives a different
result, because inflation differentials and exchange rate changes do not cancel
exactly. Neither path is "right"; the library uses one deterministic convention and
emits an `EnergyUnitsWarning` whenever it applies. For financial analysis use
dedicated tools.

**Limitations:** annual averages smooth over intra-year volatility, rates exclude
spreads and fees, and the CNY is a managed currency.

## Version History

- **2026-11 (v0.3.0):** fuel properties aligned with the IPCC 2006 Tier 1 defaults (Tables 1.2 and
  1.4) including their ranges, new IPCC fuel categories, gas densities at 15 °C; exchange rates replaced by Federal Reserve G.5A annual
  averages (2000-2025); inflation data corrected (USD 2010/2011/2014) and extended
  with 2000-2009, 2024/2025 actuals and GBP, JPY, CNY series; projections set to the 2 %
  target and flagged; fossil fuel carbon contents made consistent with the IPCC
  emission factors (superseded by the IPCC alignment); exact unit definitions for barrel and BTU-based units; new units
  (toe, tce, Gcal, therm, quad, bcm, Mcf, lb, kt, ...).
- **2025-11:** year-dependent exchange rates; fuel properties cross-checked against
  IPCC/IEA references.

## Contact

For questions about data sources or to report discrepancies:
- Open an issue: https://github.com/0-k/energyunits/issues
- Email: hi@martinklein.co
