# Data Sources and References

This document provides citations and references for all energy conversion values, fuel properties, and emission factors used in the EnergyUnits library.

## Overview

The fuel properties in `energyunits/data/substances.json` are based on authoritative sources including:
- IPCC (Intergovernmental Panel on Climate Change) Guidelines
- IEA (International Energy Agency) databases
- EPA (US Environmental Protection Agency) emission factors
- EIA (US Energy Information Administration) data
- Peer-reviewed scientific literature

## Heating Value References

### Higher Heating Value (HHV) vs Lower Heating Value (LHV)

**Definition:**
- **HHV (Higher Heating Value)**: Also called Gross Calorific Value (GCV). Assumes the water of combustion is entirely condensed and the heat contained in the water vapor is recovered.
- **LHV (Lower Heating Value)**: Also called Net Calorific Value (NCV). Assumes the products of combustion contain water vapor and the heat in the water vapor is not recovered.

**Typical HHV/LHV Relationships:**
- Coal and oil: LHV is approximately 5% lower than HHV
- Natural gas: LHV is approximately 10% lower than HHV
- Hydrogen: LHV is approximately 18% lower than HHV (142 MJ/kg vs 120 MJ/kg)

**Reference:** [H2tools - Lower and Higher Heating Values](https://h2tools.org/hyarc/calculator-tools/lower-and-higher-heating-values-fuels)

## Coal

### Classification (IEA Standards)

**Hard Coal:** Gross calorific value above 23,865 kJ/kg (23.9 MJ/kg)
- Includes anthracite, coking coal, and bituminous coal

**Sub-bituminous Coal:** Gross calorific value between 17,435 and 23,865 kJ/kg (17.4-23.9 MJ/kg)

**Brown Coal (Lignite):** Gross calorific value less than 17,435 kJ/kg (< 17.4 MJ/kg)

**Reference:** [IEA - Harmonisation of Definitions of Energy Products and Flows: Coal](https://iea.blob.core.windows.net/assets/imports/events/39/Coal.pdf)

### Heating Values

**Anthracite:**
- HHV: 24-35 MJ/kg (typical range)
- LHV: Approximately 5% lower than HHV
- **Used value:** HHV 32.5 MJ/kg, LHV 31.5 MJ/kg

**Bituminous Coal:**
- HHV: 24-30 MJ/kg (IEA classification >23.9 MJ/kg)
- LHV: Approximately 5% lower than HHV
- **Used value:** HHV 30.0 MJ/kg, LHV 28.5 MJ/kg

**Generic coal (`coal`):**
- Representative steam coal between sub-bituminous and bituminous coal
- **Used value:** HHV 26.0 MJ/kg, LHV 25.0 MJ/kg, emission factor 95.0 kg CO2/GJ

**Lignite:**
- HHV: 8-17 MJ/kg (typical range), 15-19 GJ/tonne per IEA
- LHV: Approximately 5% lower than HHV
- **Used value:** HHV 15.0 MJ/kg, LHV 14.0 MJ/kg

**References:**
- [IEA Coal Product Definitions](https://iea.blob.core.windows.net/assets/imports/events/39/Coal.pdf)
- [Engineering Toolbox - Coal Heating Values](https://www.engineeringtoolbox.com/coal-heating-values-d_1675.html)
- [World Nuclear Association - Heat Values of Various Fuels](https://world-nuclear.org/information-library/facts-and-figures/heat-values-of-various-fuels)

### CO2 Emission Factors (IPCC 2006 Guidelines)

Emission factors on a net calorific value (LHV) basis:

- **Anthracite:** 98.3 kg CO2/GJ (98,300 kg CO2/TJ)
- **Bituminous/Coking Coal:** 94.6 kg CO2/GJ (94,600 kg CO2/TJ)
- **Sub-bituminous Coal:** 96.1 kg CO2/GJ (96,100 kg CO2/TJ)
- **Lignite:** 101.0 kg CO2/GJ (101,000 kg CO2/TJ)

**Note:** IPCC 2006 assumes 100% carbon oxidation to CO2.

**Reference:** [IPCC 2006 Guidelines, Volume 2, Chapter 2: Stationary Combustion, Table 2.2](https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_2_Ch2_Stationary_Combustion.pdf)

## Natural Gas and Methane

### Heating Values

**Natural Gas:**
- HHV: 52.2-55.0 MJ/kg
- LHV: 47.1-49.5 MJ/kg (approximately 10% lower than HHV)
- **Used value:** HHV 55.0 MJ/kg, LHV 49.5 MJ/kg

**Methane (CH4):**
- HHV: 55.5 MJ/kg
- LHV: 50.0 MJ/kg
- **Used value:** HHV 55.5 MJ/kg, LHV 50.0 MJ/kg

**References:**
- [EIA - Heat Content of Natural Gas](https://www.eia.gov/dnav/ng/ng_cons_heat_a_epg0_vgth_btucf_a.htm)
- [H2tools - Lower and Higher Heating Values](https://h2tools.org/hyarc/calculator-tools/lower-and-higher-heating-values-fuels)

### Density

**Natural Gas (standard conditions):** 0.75 kg/m³

**LNG (Liquefied Natural Gas):** 450 kg/m³ (0.45 kg/L)
- Range: 410-500 kg/m³ depending on temperature, pressure, and composition

**Reference:** [IMO MEPC.281(70) - LNG Standards](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MEPCDocuments/MEPC.281(70).pdf)

### CO2 Emission Factors

**Natural Gas:** 56.1 kg CO2/GJ (56,100 kg CO2/TJ)
- Carbon content: 15.3 kgC/GJ (range 14.8-15.9 kgC/GJ)
- Conversion: 15.3 kgC/GJ × (44/12) = 56.1 kg CO2/GJ

**Reference:** [IPCC 2006 Guidelines, Volume 2, Chapter 1, Table 1.3](https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_1_Ch1_Introduction.pdf)

## Petroleum Products

### Heating Values

**Crude Oil:**
- HHV: 45.0 MJ/kg
- LHV: 42.5 MJ/kg (approximately 5% lower than HHV)
- Net calorific value: 42.3 TJ/Gg (range 40.1-44.8 TJ/Gg) per IPCC 2006

**Diesel:**
- HHV: 45.7 MJ/kg (or approximately 43 MJ/kg from other sources)
- LHV: 42.8 MJ/kg (approximately 7% lower than HHV)
- **Current values confirmed accurate**

**Gasoline (Motor Gasoline):**
- HHV: 46-47.3 MJ/kg
- LHV: 44.0 MJ/kg (approximately 7-10% lower than HHV)
- Net calorific value: 44.3 TJ/Gg per IPCC 2006
- **Current values confirmed accurate**

**Heavy Fuel Oil:**
- HHV: 43.0 MJ/kg
- LHV: 40.5 MJ/kg (approximately 5% lower than HHV)

**References:**
- [University of Waterloo - Gasoline and Diesel Fuel Properties](https://uwaterloo.ca/chem13-news-magazine/may-2018/feature/gasoline-and-diesel-fuel-carbon-pricing-and-heating-values)
- [IPCC 2006 Guidelines, Volume 2, Chapter 1, Table 1.2](https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_1_Ch1_Introduction.pdf)

### Density

**Diesel:** 840 kg/m³ (0.84 kg/L)
- Range: 820-845 kg/L at 15°C (EN 590 European standard)

**Gasoline:** 750 kg/m³ (0.75 kg/L)
- Range: 700-770 kg/L

**Crude Oil:** 870 kg/m³ (0.87 kg/L)

**Heavy Fuel Oil:** 950 kg/m³ (0.95 kg/L)

**References:**
- [Engineering Toolbox - Fuels Densities](https://www.engineeringtoolbox.com/fuels-densities-specific-volumes-d_166.html)
- [AFDC - Fuel Properties Comparison](https://afdc.energy.gov/fuels/properties)

### CO2 Emission Factors

**Motor Gasoline:** 69.3 kg CO2/GJ (69,300 kg CO2/TJ)
- Carbon content: 18.9 kgC/GJ per IPCC 2006

**Diesel (gas/diesel oil):** 74.1 kg CO2/GJ

**Heavy fuel oil (residual fuel oil):** 77.4 kg CO2/GJ

**Crude Oil:** Approximately 73.3 kg CO2/GJ
- Carbon content: 20.0 kgC/GJ (range 19.4-20.6 kgC/GJ) per IPCC 2006

**References:**
- [IPCC Annex I - Properties of CO2 and Carbon-Based Fuels](https://www.ipcc.ch/site/assets/uploads/2018/03/srccs_annex1-1.pdf)
- [IPCC 2006 Guidelines, Volume 2, Chapter 2, Table 2.2](https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_2_Ch2_Stationary_Combustion.pdf)

## Hydrogen

### Heating Values

**Hydrogen (H2):**
- HHV: 142 MJ/kg
- LHV: 120 MJ/kg
- Difference: 18.2% (significantly higher than fossil fuels due to water vapor formation)

**Note:** These values are well-established across all technical literature and regulatory documents.

**References:**
- [Wikipedia - Heat of Combustion](https://en.wikipedia.org/wiki/Heat_of_combustion)
- [European Commission (Eurostat) - Hydrogen Reporting Instructions](https://ec.europa.eu/eurostat/documents/38154/16135593/Hydrogen+-+Reporting+instructions.pdf/)
- [Hycalc.com - Hydrogen Heating Values](https://hycalc.com/hydrogen-heating-values)

### Density

**Hydrogen gas (at standard conditions):** 0.09 kg/m³

### CO2 Emissions

**Hydrogen:** 0 kg CO2/GJ (zero direct combustion emissions)
- Combustion product is water (H2O) only

## Biomass

### Wood Pellets

Values are **as received** (ENplus A1 quality, 8 % moisture), derived from dry-basis
properties (HHV 20.0 MJ/kg, 50 % carbon, 6 % hydrogen, 1 % ash):

- HHV (as received) = 20.0 × (1 - 0.08) = 18.4 MJ/kg
- LHV (as received) = HHV - 2.442 × (moisture + 8.936 × hydrogen) = 17.0 MJ/kg
  (ENplus A1 requires a net calorific value of at least 16.5 MJ/kg; typical 16.5-17.5)
- Carbon 46 %, hydrogen 5.5 %, ash 0.9 % (as received)
- Bulk density: 650 kg/m³ (range 600-750)

Earlier versions used the dry-basis LHV of 18.5 MJ/kg, which overstated the energy
content of delivered pellets by about 9 %.

**References:**
- [ENplus Handbook - Quality Requirements](https://enplus-pellets.eu/)
- [Natural Resources Canada - Solid Biofuels Bulletin](https://natural-resources.canada.ca/sites/nrcan/files/files/NRCAN_BB_no2_e13.pdf)
- [Penn State Extension - Characteristics of Biomass as Heating Fuel](https://extension.psu.edu/characteristics-of-biomass-as-a-heating-fuel)

### Wood Chips

Values are **as received** at 30 % moisture (moisture class M30), derived from
dry-basis properties (HHV 19.8 MJ/kg, 50 % carbon, 6 % hydrogen, 2 % ash):

- HHV (as received) = 13.9 MJ/kg, LHV (as received) = 12.2 MJ/kg (about 3.4 kWh/kg)
- Carbon 35 %, hydrogen 4.2 %, ash 1.4 % (as received)
- Bulk density: 350 kg/m³ (varies strongly with species and moisture)

The energy content of wood chips depends strongly on moisture: at 50 % moisture the
LHV drops to about 8 MJ/kg. Load a custom substance for other moisture contents.

## Methanol

### Heating Values

**Methanol (CH3OH):**
- HHV: 22.7-23.0 MJ/kg
- LHV: 19.9 MJ/kg
- **Current values (22.7 HHV, 19.9 LHV) confirmed accurate**

**Density:** 791-795 kg/m³
- **Used value:** 795 kg/m³

### CO2 Emissions

**Direct combustion emissions:** 1.375 kg CO2 per kg methanol
- Stoichiometric: For each gram of methanol, 44/32 grams of CO2 are emitted
- Equals 69 g CO2/MJ LHV

**Full lifecycle (natural gas-based):** 2.05-2.20 kg CO2eq/kg (includes production)

**References:**
- [Methanol Institute - Carbon Footprint of Methanol](https://www.methanol.org/wp-content/uploads/2022/01/Carbon-Footprint-of-Methanol-studio-Gear-Up-Full-Presentation.pdf)
- [IMPCA - Methanol Carbon Footprint Guidance](https://impca.eu/wp-content/uploads/2024/06/GU_IMPCA_Methanol-product-carbon-footprint-and-certification.pdf)

## Emission Calculation Methodology

### IPCC 2006 Guidelines Methodology

All CO2 emission factors follow IPCC 2006 Guidelines methodology:

1. **Carbon oxidation factor:** 100% (assumes complete oxidation of carbon to CO2)
2. **Basis:** Net calorific value (LHV)
3. **Conversion:** Carbon content (kgC/GJ) × (44/12) = CO2 emissions (kg CO2/GJ)
   - Molecular weight ratio: CO2 (44) / C (12) = 3.667

### Carbon content and emission factors in substances.json

CO2 is computed stoichiometrically from the carbon mass fraction:
`CO2 = fuel mass × carbon_content × 44/12`.

For fossil fuels, `carbon_content` is derived from the IPCC default emission factor
(`carbon_intensity`, kg CO2 per GJ on LHV basis) and the LHV used by the library:

```text
carbon_content = carbon_intensity × lhv / 1000 × 12/44
```

so that converting fuel energy to CO2 reproduces the IPCC Tier 1 factors exactly
(for example 1 GJ of natural gas -> 56.1 kg CO2, 1 MWh of coal -> 0.342 t CO2).
Methane and methanol use their stoichiometric composition. Earlier versions used
rounded carbon fractions (coal 0.75, lignite 0.65) that overstated coal emissions by
16 % and lignite emissions by 68 % relative to the IPCC factors.

For biomass (`biogenic: true`) the physical carbon content is kept, so the library
returns the biogenic CO2 that is actually emitted, while `carbon_intensity` is 0
following the IPCC convention of reporting biogenic CO2 separately.

| Substance | LHV (MJ/kg) | Carbon content | kg CO2/GJ (computed) | `carbon_intensity` |
|-----------|------------:|---------------:|---------------------:|-------------------:|
| `coal` | 25.0 | 0.6477 | 95.0 | 95.0 |
| `lignite` | 14.0 | 0.3856 | 101.0 | 101.0 |
| `bituminous` | 28.5 | 0.7353 | 94.6 | 94.6 |
| `anthracite` | 31.5 | 0.8445 | 98.3 | 98.3 |
| `natural_gas` | 49.5 | 0.7574 | 56.1 | 56.1 |
| `lng` | 49.5 | 0.7574 | 56.1 | 56.1 |
| `methane` | 50.0 | 0.7487 | 54.9 | 54.9 |
| `crude_oil` | 42.5 | 0.8496 | 73.3 | 73.3 |
| `oil` | 42.5 | 0.8496 | 73.3 | 73.3 |
| `fuel_oil` | 40.5 | 0.8549 | 77.4 | 77.4 |
| `diesel` | 42.8 | 0.8649 | 74.1 | 74.1 |
| `gasoline` | 44.0 | 0.8316 | 69.3 | 69.3 |
| `wood_pellets` | 18.5 | 0.5 | 99.1 | 0 (biogenic) |
| `wood_chips` | 16.0 | 0.48 | 110.0 | 0 (biogenic) |
| `methanol` | 19.9 | 0.3749 | 69.1 | 69.1 |

## Data Quality and Limitations

### Uncertainty Ranges

- Heating values can vary ±5-10% depending on:
  - Fuel composition and quality
  - Geographic origin (especially for coal)
  - Moisture content (especially for biomass)
  - Refining processes (for petroleum products)

- Emission factors are standardized values:
  - Actual emissions depend on combustion efficiency
  - IPCC default values assume complete combustion
  - Country-specific values may differ

### Future Updates

Data will be periodically reviewed and updated based on:
- New IPCC Guidelines releases
- Updated national inventory methodologies
- Peer-reviewed research publications
- Industry standards updates

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
| `MMBTU`, `therm`, `quad` | 10^6, 10^5 and 10^15 BTU |
| `kcal`, `Mcal`, `Gcal` | International Table calorie, 4.1868 J |
| `toe` | tonne of oil equivalent, 41.868 GJ (IEA/OECD) |
| `tce` | tonne of coal equivalent, 29.3076 GJ (7 Gcal) |
| `barrel` | US oil barrel, 42 US gallons = 0.158987294928 m3 |
| `gal` | US liquid gallon, 3.785411784 L |
| `ft3`, `Mcf`, `Bcf` | cubic foot (0.3048 m)^3, 10^3 and 10^9 ft3 |
| `bcm` | 10^9 m3 |
| `lb` | avoirdupois pound, 0.45359237 kg |
| `a`, `yr` | 8760 h (365 days), the usual convention in energy models |

Gas volumes (`m3`, `bcm`, `Mcf`) are converted to mass and energy with the density
of the substance (natural gas: 0.75 kg/m3, approximately normal conditions).

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

| Year | USD | EUR | GBP | JPY | CNY |
|------|----:|----:|----:|----:|----:|
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

\* Projections: placeholders equal to the 2 % central bank target, not forecasts.
Conversions that use them emit an `EnergyUnitsWarning`. Replace them with your own
assumptions via `inflation_registry.load_inflation()` where it matters.

Notes:

- USD rates are computed from the BLS annual average index (e.g. 2024: 313.689 vs.
  304.702 in 2023 = +2.95 %). The 2025 value (+2.6 %) is based on the published
  annual average, which excludes October 2025 (no data collection during the
  federal funding lapse).
- Values are rounded to 0.1 percentage points for EUR, GBP, JPY and CNY and to
  0.01 for USD. Earlier versions of this library contained errors for USD 2010,
  2011 and 2014 (2014 was listed as 0.12 % instead of 1.62 %) and preliminary
  estimates for 2024.

## Exchange Rates

Annual averages of daily noon buying rates in New York from the Board of Governors
of the Federal Reserve System, release G.5A ("Foreign Exchange Rates, Annual"). The
library stores all rates as US dollars per unit of currency; JPY and CNY, which the
Fed quotes as units per US dollar, are stored as the inverse of the values below.

| Year | EUR (USD per EUR) | GBP (USD per GBP) | JPY (JPY per USD) | CNY (CNY per USD) |
|------|------------------:|------------------:|------------------:|------------------:|
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

Values were taken from the most recent G.5A release that lists each year; the Fed
occasionally revises historical averages by a few units in the fourth decimal.

### How exchange rates are applied

- A quantity with a `reference_year` is converted with the rate of that year.
- Without a reference year, the most recent year (2025) is used.
- For years after the most recent available year, the most recent rate is used and
  an `EnergyUnitsWarning` is emitted. Years before 2010 raise `MissingDataError`.
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

- **2026-11 (v0.3.0):** exchange rates replaced by Federal Reserve G.5A annual
  averages (2010-2025); inflation data corrected (USD 2010/2011/2014) and extended
  with 2024/2025 actuals and GBP, JPY, CNY series; projections set to the 2 %
  target and flagged; fossil fuel carbon contents made consistent with the IPCC
  emission factors; exact unit definitions for barrel and BTU-based units; new units
  (toe, tce, Gcal, therm, quad, bcm, Mcf, lb, kt, ...).
- **2025-11:** year-dependent exchange rates; fuel properties cross-checked against
  IPCC/IEA references.

## Contact

For questions about data sources or to report discrepancies:
- Open an issue: https://github.com/0-k/energyunits/issues
- Email: hi@martinklein.co
