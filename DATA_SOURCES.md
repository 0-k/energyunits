# Data Sources and References

This document provides citations and references for all energy conversion values, fuel properties, and emission factors used in the EnergyUnits library.

## Overview

All data in `energyunits/data/substances.json` has been verified against authoritative sources including:
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

**Hard Coal:** Gross calorific value above 23.865 kJ/kg (23.9 MJ/kg)
- Includes anthracite, coking coal, and bituminous coal

**Sub-bituminous Coal:** Gross calorific value between 17.435 and 23.865 kJ/kg (17.4-23.9 MJ/kg)

**Brown Coal (Lignite):** Gross calorific value less than 17.435 kJ/kg (< 17.4 MJ/kg)

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

**Sub-bituminous Coal:**
- HHV: 17.4-23.9 MJ/kg (IEA classification)
- **Used value:** HHV 23.0 MJ/kg, LHV 22.0 MJ/kg

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

**Diesel and Fuel Oil:** Approximately 74.1 kg CO2/GJ (typical value for distillate fuel oil)

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

**Heating Values:**
- HHV: 18.4-20.5 MJ/kg (softwoods 19.66-20.36 MJ/kg, hardwoods 17.63-20.81 MJ/kg)
- LHV: 15.6-17.0 MJ/kg (softwoods 15.63-16.94 MJ/kg, hardwoods 14.41-17.91 MJ/kg)
- **Used values:** HHV 20.0 MJ/kg, LHV 18.5 MJ/kg

**Density:** 650-700 kg/m³ (bulk density)
- **Used value:** 650 kg/m³

**References:**
- [Natural Resources Canada - Solid Biofuels Bulletin](https://natural-resources.canada.ca/sites/nrcan/files/files/NRCAN_BB_no2_e13.pdf)
- [EUBIA - Biomass Characteristics](https://www.eubia.org/cms/wiki-biomass/biomass-characteristics-2/)
- [Penn State Extension - Characteristics of Biomass as Heating Fuel](https://extension.psu.edu/characteristics-of-biomass-as-a-heating-fuel)

### Wood Chips

**Heating Values:**
- HHV: 19.0 MJ/kg (dry basis)
- LHV: 16.0 MJ/kg (accounting for moisture)

**Density:** 350 kg/m³ (bulk density, varies with moisture content)

**Note:** Values vary significantly based on wood species and moisture content.

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

### Carbon Intensity Values in substances.json

The `carbon_intensity` field in `substances.json` represents **kg CO2 emissions per GJ of fuel energy (LHV basis)**.

These values are used to calculate CO2 emissions when converting from fuel energy to CO2 mass:
```python
coal_energy = Quantity(1, "GJ", substance="coal", basis="LHV")
co2_emissions = coal_energy.to("t", substance="CO2")
```

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

## Inflation Data

### USD Inflation Rates (2010-2024)

Historical inflation rates sourced from U.S. Bureau of Labor Statistics (BLS) Consumer Price Index (CPI) data, available through FRED (Federal Reserve Economic Data).

**Historical Values (2010-2024):**
The library uses annual CPI percentage changes published by BLS. Key verified values:
- 2020: 1.23%
- 2021: 4.70%
- 2022: 8.00%
- 2023: 4.12%
- 2024: ~2.9-3.15% (preliminary/estimated)

**Future Projections (2025-2030):**
Values for 2025-2030 are estimates based on Federal Reserve targets and economic projections. These should be treated as approximate and updated as actual data becomes available.

**References:**
- [FRED - Inflation, Consumer Prices for United States](https://fred.stlouisfed.org/series/FPCPITOTLZGUSA)
- [BLS - Consumer Price Index](https://www.bls.gov/cpi/)
- [US Inflation Calculator - Current Rates](https://www.usinflationcalculator.com/inflation/current-inflation-rates/)

### EUR Inflation Rates (2010-2024)

Historical inflation rates sourced from Eurostat's Harmonised Index of Consumer Prices (HICP) for the Euro area.

**Historical Values (2010-2024):**
- 2020: 0.3%
- 2021: 2.6%
- 2022: 8.4%
- 2023: ~5.4%
- 2024: ~2.8% (preliminary/estimated)

**Future Projections (2025-2030):**
Values for 2025-2030 are estimates based on ECB inflation targets. These should be treated as approximate.

**References:**
- [Eurostat - HICP Inflation Rate](https://ec.europa.eu/eurostat/databrowser/view/tec00118/default/table?lang=en)
- [Eurostat - Inflation in the Euro Area](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Inflation_in_the_euro_area)
- [Trading Economics - Euro Area Inflation](https://tradingeconomics.com/euro-area/inflation-cpi)

### Methodology

The library uses these inflation rates to adjust currency values between reference years using cumulative inflation:

```python
adjusted_value = original_value × Π(1 + inflation_rate_i)
```

where the product is taken over all years between the original and target reference year.

**Important Notes:**
1. Inflation adjustments are approximate and suitable for planning purposes
2. Future year projections are estimates and should be updated regularly
3. Different price indices exist (CPI, PPI, GDP deflator) - this library uses consumer price indices
4. Real-world inflation varies by sector and geography

## Currency Conversion Values

### Year-Dependent Exchange Rates

**New in v0.2.0**: The library now includes year-dependent exchange rates for historical economic analysis.

Exchange rate data is stored in `exchange_rates.json` with annual average rates from 2010-2025 for:
- **EUR** (Euro)
- **GBP** (British Pound)
- **JPY** (Japanese Yen)
- **CNY** (Chinese Yuan)
- **USD** (US Dollar - base currency, always 1.0)

**Data Sources:**
- European Central Bank (ECB) - EUR/USD reference rates
- Bank of England - GBP/USD official rates
- Bank of Japan - JPY/USD rates
- People's Bank of China - CNY/USD reference rates
- Cross-validated with IMF, US Treasury, and FRED data

**Methodology:**
Annual averages computed from daily reference rates published by central banks. This provides representative rates for year-over-year economic analysis while avoiding daily volatility.

### Currency + Inflation Convention: "Inflate First, Then Convert"

When combining currency conversion with inflation adjustment, the library uses a **deterministic convention**:

```python
cost_eur_2015 = Quantity(50, "EUR/MWh", reference_year=2015)
cost_usd_2024 = cost_eur_2015.to("USD/MWh", reference_year=2024)

# Execution order:
# 1. Inflate EUR from 2015 to 2024 using EUR inflation rates
# 2. Convert EUR to USD using 2024 exchange rate
```

**Why This Matters:**

The order matters because exchange rates and inflation rates are not perfectly synchronized:
- **Path 1** (Inflate then Convert): 50 EUR × 1.20 EUR-inflation × 1.085 EUR/USD = ~65 USD
- **Path 2** (Convert then Inflate): 50 EUR × 1.11 EUR/USD(2015) × 1.30 USD-inflation = ~72 USD

These give **different results** (~10% difference) because EUR and USD had different inflation rates over this period.

**Convention Used:** Path 1 (Inflate First, Then Convert)
- More closely approximates purchasing power parity
- Answers: "What would this cost in today's dollars?"
- Library issues a warning when this combination is detected

**Important Limitations:**

1. **Economic Assumptions**: This convention makes economic assumptions that may not suit all analyses
2. **Not Financial Returns**: Does not model actual financial returns from currency holdings
3. **Approximate**: Annual averages smooth over intra-year volatility
4. **No Transaction Costs**: Rates don't include spreads, fees, or transaction costs
5. **For Financial Precision**: Use dedicated forex/economic analysis tools

**Supported Use Cases:**
- Historical energy cost comparisons across countries
- Long-term infrastructure project cost analysis
- Academic/research economic modeling
- Rough currency conversions for context

**Example: Brexit Impact Visible in Data**

```python
# GBP exchange rate before/after Brexit referendum (June 2016)
gbp_2015 = Quantity(100, "GBP", reference_year=2015).to("USD")
# → ~153 USD (strong pound)

gbp_2017 = Quantity(100, "GBP", reference_year=2017).to("USD")
# → ~129 USD (post-Brexit depreciation)
```

### Static Fallback Rates (units.json)

For backwards compatibility, `units.json` retains static exchange rate factors:
- USD: 1.00
- EUR: 1.08 (approximate 2024-2025 average)
- GBP: 1.27
- JPY: 0.0067
- CNY: 0.14

These are used only when `reference_year` is not specified. **Recommendation**: Always specify `reference_year` for currency conversions to use accurate historical rates.

## Version History

- **2025-11-24:** Year-dependent currency conversions
  - Added historical exchange rate data (2010-2025) for EUR, GBP, JPY, CNY
  - Implemented "inflate first, then convert" convention for currency + inflation
  - Exchange rates sourced from ECB, Bank of England, Bank of Japan, PBOC
  - Added comprehensive documentation of path dependency and economic assumptions

- **2025-11-23:** Initial comprehensive data verification and documentation
  - Fuel properties updated from preliminary estimates to IPCC/IEA standards
  - CO2 emission factors verified against IPCC 2006 Guidelines
  - Heating values cross-referenced with multiple authoritative sources
  - Added inflation data sources and methodology documentation
  - Documented currency conversion limitations

## Contact

For questions about data sources or to report discrepancies:
- Open an issue: https://github.com/0-k/energyunits/issues
- Email: hi@martinklein.co
