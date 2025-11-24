# Critical Analysis: EnergyUnits Deep Dive

**Date:** 2025-11-24
**Perspective:** Top-Down, Critical Review
**Goal:** Identify opportunities for improvement beyond v0.1.0

---

## Executive Summary

EnergyUnits is a **well-designed, production-ready library** with solid fundamentals. However, there are meaningful opportunities for improvement across API ergonomics, feature completeness, performance, and user experience. This document provides a critical analysis from strategic to implementation levels.

**Overall Grade: B+ (Very Good, Room for Excellence)**

---

## 1. Strategic / Product Level

### ✅ Strengths

**Clear Value Proposition:**
- "Energy system modeling" - well-defined niche
- Not trying to be general-purpose (good!)
- Data-driven design aligns with scientific users

**Right Abstractions:**
- Dimensions, units, substances - natural mental model
- Unified `.to()` API - consistent
- NumPy integration - practical

### ⚠️ Areas for Improvement

#### 1.1 Unclear Target Audience Priority

**Issue:** The library tries to serve multiple personas:
- Energy researchers (need precision, citations)
- Energy consultants (need speed, convenience)
- Students (need simplicity, examples)
- Software engineers (need clean API, types)

**Consequence:** Some design compromises don't fully satisfy anyone.

**Example:**
```python
# Researchers want this:
coal.to("t", substance="CO2",
        oxidation_factor=0.98,  # Not complete combustion
        uncertainty_range=(0.95, 1.0))

# Engineers want this:
coal.to_co2()  # Simple, discoverable

# Library provides neither - middle ground
coal.to("t", substance="CO2")  # Okay but not great
```

**Recommendation:**
- Pick primary persona (suggest: Energy Analysts/Consultants)
- Design core API for them
- Add power-user features as optional kwargs
- Add convenience methods for common patterns

#### 1.2 Missing "Killer Feature"

**Issue:** The library is very good at what it does, but lacks a standout feature that makes it indispensable.

**What competitors offer:**
- **Pint**: Comprehensive unit system (10,000+ units)
- **CoolProp**: Thermodynamic properties (pressure-enthalpy diagrams)
- **Pyomo**: Optimization integration
- **Pandas**: DataFrame integration (we have basic, not killer)

**Potential Killer Features:**
1. **Uncertainty Quantification**
   ```python
   coal = Quantity(1000, "t", substance="coal",
                   uncertainty=UncertaintyDistribution("normal", std=50))
   co2 = coal.to_co2()
   # co2 now has propagated uncertainty
   co2.confidence_interval(0.95)  # Returns (2400, 2600) t CO2
   ```

2. **Time Series Native Support**
   ```python
   generation = TimeSeriesQuantity(
       times=pd.date_range("2024-01-01", periods=8760, freq="H"),
       values=generation_array,
       unit="MW"
   )
   generation.resample("D").mean()  # Daily average
   generation.plot()  # Auto-labeled with units
   ```

3. **Optimization-Ready**
   ```python
   # Integrate with Pyomo/scipy.optimize
   model = EnergyModel()
   coal_cost = Quantity(50, "USD/t", substance="coal")
   gas_cost = Quantity(200, "USD/t", substance="natural_gas")

   model.minimize_cost(fuels=[coal_cost, gas_cost],
                      constraint=emissions < Quantity(1000, "t", "CO2"))
   ```

**Recommendation:** Choose ONE killer feature for v0.2.0-v0.3.0.

---

## 2. API / UX Level

### ✅ Strengths

- Unified `.to()` method - consistent
- Dimensional analysis prevents errors
- Natural arithmetic operations

### ⚠️ Critical Issues

#### 2.1 Scalar Multiplication Loses Semantics

**Problem:**
```python
efficiency = 0.45
electricity = gas_energy * efficiency
# electricity.unit is still "MWh" but semantically it's different!
```

From `example_use_cases.py:231`:
```python
electricity_output = gas_energy * plant_efficiency
electricity_output.unit = "MWh"  # Manual assignment - ugly!
```

**Why it matters:** Common pattern in energy modeling (efficiencies, capacity factors).

**Solution Options:**

**Option A: Context-aware multiplication**
```python
efficiency = Efficiency(0.45)  # New class
electricity = gas_energy * efficiency
# electricity preserves unit, tracks efficiency in metadata
```

**Option B: Explicit efficiency method**
```python
electricity = gas_energy.apply_efficiency(0.45)
```

**Option C: Accept the limitation, improve docs**
- Current approach is actually pragmatic
- Just needs better documentation

**Recommendation:** Option C for v0.1.0, consider Option A for v0.2.0.

#### 2.2 Value Extraction Friction

**Problem:** Common pattern requires `.value` extraction:

```python
# From example_use_cases.py
efficiency_ratio = annual_generation.value / fuel_energy.value
emission_rate_value = annual_co2.value / annual_generation.value
```

**Why it's awkward:**
- Breaks the fluent API
- Easy to forget and get a Quantity when you want a scalar
- Pollutes code with `.value` everywhere

**Better API:**
```python
# Option A: Division returns dimensionless scalar when units cancel
efficiency_ratio = (annual_generation / fuel_energy).scalar()

# Option B: Automatic scalar extraction for dimensionless
efficiency_ratio = annual_generation / fuel_energy
# Returns 0.35 (float), not Quantity(0.35, "")

# Option C: Comparison operators return booleans/floats when appropriate
ratio = annual_generation.ratio_to(fuel_energy)  # Returns float
```

**Recommendation:** Option B (auto-scalar for dimensionless) is most intuitive.

#### 2.3 No Fluent Chain for Multi-Step Conversions

**Problem:** Complex conversions require intermediate variables:

```python
# Current: verbose
gas_flow = Quantity(1000, "m3", substance="natural_gas")
gas_energy = gas_flow.to("MWh")
electricity = gas_energy * 0.45
electricity.unit = "MWh"
gas_co2 = gas_flow.to("t", substance="CO2")
emission_factor = gas_co2 / electricity
```

**Desired: fluent**
```python
emission_factor = (
    Quantity(1000, "m3", substance="natural_gas")
    .to_energy("MWh")
    .apply_efficiency(0.45)
    .emission_factor()  # Auto-calculates CO2 per MWh
)
```

**Limitation noted in code** (example_use_cases.py:241-242):
> "Complex chained conversions (gas → energy → CO2) in one step are not supported as they involve different physical transformations."

**Why this matters:** Energy analysts think in workflows, not individual conversions.

**Recommendation:** Add workflow-specific convenience methods in v0.2.0.

#### 2.4 Compound Unit String Parsing is Fragile

**Problem:**
```python
# Works:
Quantity(50, "USD/MWh")

# Unclear if these work:
Quantity(50, "USD per MWh")  # Does this work?
Quantity(50, "$/MWh")        # Does this work?
Quantity(50, "USD/MW/h")     # What about this?
```

**Testing:**
```python
# Only "/" delimiter is supported
# No "per", no "$", no double divisions
```

**Recommendation:**
- Document supported formats explicitly
- Add unit parser with better error messages
- Consider aliases: "$" → "USD", "€" → "EUR"

#### 2.5 No Unit Discovery/Introspection

**Problem:** Users can't easily discover what's available:

```python
# No way to do this:
Quantity.list_units()
Quantity.list_substances()
Quantity.find_units("energy")  # Get all energy units
```

**Recommendation:** Add discovery methods in v0.2.0.

---

## 3. Architecture Level

### ✅ Strengths

- Clean separation: Quantity, Registry, Substance, Inflation
- Data-driven design (JSON) - extensible
- Singleton registries - simple
- Pipeline-based conversions - clear

### ⚠️ Issues

#### 3.1 Tight Coupling to NumPy

**Problem:**
```python
self.value: np.ndarray = np.asarray(value)  # Always wraps
```

**Consequences:**
- Overhead for simple scalars (minimal but exists)
- NumPy dependency is hard requirement (okay for energy modeling, but limits adoption)
- Can't easily swap to other array libraries (CuPy, Dask, etc.)

**Better Design:**
```python
# Option A: Lazy wrapping
if isinstance(value, np.ndarray):
    self.value = value
else:
    self.value = value  # Keep as scalar until needed

# Option B: Abstract array interface
class ArrayBackend(ABC):
    @abstractmethod
    def asarray(self, value): ...

# Option C: Accept it - NumPy is standard
# (current approach is fine for target audience)
```

**Recommendation:** Option C is acceptable, but document NumPy as hard dependency.

#### 3.2 No Abstraction for Registry Backend

**Problem:** Registries are hardcoded to load from JSON files:

```python
def _load_defaults(self):
    data_path = Path(__file__).parent / "data" / "units.json"
    with open(data_path) as f:
        data = json.load(f)
```

**Limitations:**
- Can't load from database
- Can't load from remote API
- Can't load from different format (YAML, TOML)
- Can't version/track data changes

**Better Design:**
```python
class DataBackend(ABC):
    @abstractmethod
    def load_units(self) -> dict: ...
    @abstractmethod
    def load_substances(self) -> dict: ...

class JSONBackend(DataBackend):
    def load_units(self):
        # Current implementation

class DatabaseBackend(DataBackend):
    def load_units(self):
        # Load from PostgreSQL/SQLite

class APIBackend(DataBackend):
    def load_units(self):
        # Fetch from REST API
```

**Recommendation:** Add backend abstraction in v0.3.0 (not critical for v0.1.0).

#### 3.3 String-Based Unit Representation

**Problem:** Units are strings, not typed objects:

```python
self.unit: str = unit  # Stringly-typed
```

**Consequences:**
- Typos not caught until runtime
- No IDE autocomplete
- Harder to validate
- String parsing overhead

**Alternative:**
```python
# Option A: Enum
class Unit(Enum):
    MWh = "MWh"
    GJ = "GJ"
    # ...

Quantity(100, Unit.MWh)

# Option B: Class hierarchy
class MWh(EnergyUnit):
    symbol = "MWh"
    dimension = Dimension.ENERGY

# Option C: Hybrid (string for flexibility, validate on creation)
# (current approach)
```

**Trade-offs:**
- **Strings:** Flexible, extensible, simple
- **Types:** Safe, autocomplete, but rigid

**Recommendation:** Keep strings (flexibility wins for energy modeling), but add:
```python
from energyunits.units import MWh, GJ, MW  # Constants
Quantity(100, MWh)  # Still string internally, but IDE-friendly
```

#### 3.4 No Caching of Conversions

**Problem:** Every conversion recalculates:

```python
def get_conversion_factor(self, from_unit, to_unit):
    # No caching - recalculates every time
    from_factor = self._conversion_factors.get(from_unit)
    to_factor = self._conversion_factors.get(to_unit)
    return from_factor / to_factor
```

**Impact:**
- Repeated conversions pay full cost
- Hot loops suffer (common in energy simulations)

**Solution:**
```python
@lru_cache(maxsize=128)
def get_conversion_factor(self, from_unit, to_unit):
    # ... same logic
```

**Recommendation:** Add caching in v0.1.1 (easy win).

#### 3.5 Metadata Propagation Rules are Unclear

**Problem:** When does metadata get preserved?

```python
# Addition: preserves if matching
a = Quantity(100, "MWh", substance="coal")
b = Quantity(50, "MWh", substance="coal")
c = a + b  # c.substance == "coal" ✓

# But:
d = Quantity(50, "MWh", substance="gas")
e = a + d  # e.substance == None (dropped!)
```

**Issue:** Silent data loss, not always obvious.

**Better:**
```python
# Option A: Raise error on mismatch
e = a + d  # SubstanceMismatchError

# Option B: Warn explicitly
e = a + d  # Warning: substance mismatch, dropping metadata

# Option C: Keep as tuple
e = a + d  # e.substance = ("coal", "gas")

# Option D: Current behavior (silent drop)
```

**Recommendation:** Option B (warn) for better UX.

---

## 4. Data Quality Level

### ✅ Strengths

- IPCC-verified emission factors ✓
- IEA-verified heating values ✓
- Comprehensive citations ✓
- Removed "preliminary" disclaimers ✓

### ⚠️ Gaps

#### 4.1 Missing Substance Properties

**What's missing:**
- **Sulfur content** (SO2 emissions)
- **Nitrogen content** (NOx emissions)
- **Heavy metals** (Hg, Pb for coal)
- **Moisture content** (affects LHV/HHV ratio)
- **Viscosity** (important for liquid fuels)
- **Flash point** (safety)
- **Cetane/Octane number** (fuel quality)

**Recommendation:** Prioritize by user requests. Add in v0.2.0+.

#### 4.2 Regional Variations Not Captured

**Issue:** Properties vary by region:

```json
"coal": {
  "hhv": 26.0  // Generic average
}
```

**Reality:**
- US Appalachian coal: 30-32 MJ/kg
- Chinese coal: 20-24 MJ/kg
- Indonesian coal: 18-22 MJ/kg
- German lignite: 8-12 MJ/kg

**Better:**
```json
"coal_us_bituminous": { "hhv": 31.0, "region": "US" },
"coal_china_bituminous": { "hhv": 22.0, "region": "CN" },
"coal": { "hhv": 26.0, "region": null }  // Generic fallback
```

**Recommendation:** Add regional variants in v0.2.0.

#### 4.3 No Temperature/Pressure Dependence

**Issue:** Many properties vary with conditions:

```python
# Natural gas density depends on pressure/temperature!
gas = Quantity(1000, "m3", substance="natural_gas")
# Assumes standard conditions (0°C, 1 atm)
# What if it's at 50°C, 10 bar?
```

**Proper handling:**
```python
gas = Quantity(1000, "m3", substance="natural_gas",
               temperature=Quantity(50, "C"),
               pressure=Quantity(10, "bar"))
gas.to("kg")  # Uses real gas law
```

**Recommendation:** v1.0.0 feature (major architectural change).

#### 4.4 Inflation Data Will Age

**Problem:** Inflation JSON will be outdated soon:

```json
"2025": 2.50,  // Estimate
"2026": 2.30,  // Estimate
```

**Needs:**
- Auto-update mechanism
- Fetch from FRED API
- Version/timestamp data files

**Recommendation:**
```python
inflation_registry.update_from_fred()  # Fetch latest
inflation_registry.data_version  # "2024-11-24"
```

---

## 5. Feature Completeness

### Missing Common Operations

#### 5.1 No Comparison Across Substances

**Use case:** "Which fuel is cheaper per MWh?"

```python
# Current: manual
coal_cost = Quantity(50, "USD/t", substance="coal")
gas_cost = Quantity(200, "USD/t", substance="natural_gas")

coal_energy = Quantity(1, "t", substance="coal").to("MWh")
gas_energy = Quantity(1, "t", substance="natural_gas").to("MWh")

coal_per_mwh = coal_cost.value / coal_energy.value
gas_per_mwh = gas_cost.value / gas_energy.value

# Desired: automatic
coal_cost.compare_to(gas_cost, basis="MWh")
# Returns: {"coal": 2.0 USD/MWh, "gas": 4.0 USD/MWh}
```

#### 5.2 No "What-If" Analysis

**Use case:** "How does plant efficiency affect emissions?"

```python
# Desired:
plant = EnergyPlant(
    fuel=Quantity(1000, "t", substance="coal"),
    efficiency=Quantity(0.35, "")
)

plant.vary("efficiency", range(0.30, 0.45, 0.05))
# Returns DataFrame with efficiency vs emissions
```

#### 5.3 No Unit Algebra DSL

**Use case:** "Define custom compound units easily"

```python
# Desired:
from energyunits import Q
EUR_per_MWh = Q.EUR / Q.MWh
tonnes_per_year = Q.t / Q.a

price = Quantity(50, EUR_per_MWh)
```

#### 5.4 No Batch Operations

**Use case:** "Convert many quantities at once"

```python
# Desired:
batch = QuantityBatch([
    Quantity(100, "MWh"),
    Quantity(50, "GJ"),
    Quantity(200, "kWh")
])
batch.to("MWh")  # Vectorized conversion
# Returns: [100, 13.9, 0.2] MWh
```

---

## 6. Performance

### Current: "Good Enough"

Benchmarks (from ARCHITECTURE.md):
- Simple conversion: ~5 μs ✓
- Cross-dimensional: ~50 μs ✓
- Array (1000 elements): ~100 μs ✓

### Optimization Opportunities

#### 6.1 Critical Path Optimization

**Hot path:** `get_conversion_factor` called millions of times.

**Current:**
```python
def get_conversion_factor(self, from_unit, to_unit):
    from_factor = self._conversion_factors.get(from_unit)
    to_factor = self._conversion_factors.get(to_unit)
    return from_factor / to_factor
```

**Optimized:**
```python
@lru_cache(maxsize=256)  # +10x speedup
def get_conversion_factor(self, from_unit, to_unit):
    # ... same
```

#### 6.2 Numba JIT for Array Operations

**Target:** Array conversions (current: 100 μs for 1000 elements)

```python
@numba.jit(nopython=True)
def _vectorized_convert(values, factor):
    return values * factor

# Potential: 10-100x speedup for large arrays
```

#### 6.3 Lazy Evaluation

**Concept:** Don't convert until needed:

```python
result = quantity.to("GJ")  # Returns LazyQuantity
result.value  # Triggers conversion
```

**Benefit:** Avoid conversions that are never used.

---

## 7. User Experience

### Documentation Gaps

#### 7.1 No "Getting Started" Tutorial

**Issue:** README has examples, but no narrative tutorial.

**Need:**
- "Your First Energy Calculation" tutorial
- "Common Pitfalls and How to Avoid Them"
- "Migrating from Pint/Excel"

#### 7.2 No Error Message Guide

**Issue:** Error messages are correct but terse:

```python
ValueError: Cannot convert from MWh to kg
```

**Better:**
```python
ConversionError: Cannot convert 100 MWh to kg

  This conversion requires specifying a substance (fuel type).

  Did you mean:
    Quantity(100, "MWh", substance="coal").to("kg")

  Available substances: coal, natural_gas, oil, ...

  Learn more: https://docs.energyunits.org/conversions#mass-energy
```

#### 7.3 No Jupyter Integration

**Missing:**
- Rich HTML repr in Jupyter
- Interactive plots
- Unit-aware widgets

**Example:**
```python
# In Jupyter:
quantity
# Shows: pretty formatted with unit, substance badge, uncertainty bar
```

#### 7.4 No Examples Repository

**Need:** Separate repo with real-world examples:
- Solar farm economics
- Coal plant decommissioning analysis
- Grid balancing calculations
- Carbon accounting for company

---

## 8. Testing

### ✅ Strengths
- 230 tests, 100% pass rate ✓
- Good coverage across modules ✓
- README examples tested ✓

### ⚠️ Gaps

#### 8.1 No Property-Based Testing

**Missing:** Use Hypothesis to generate test cases:

```python
@given(value=floats(min_value=0),
       unit=sampled_from(["MWh", "GJ", "kWh"]))
def test_conversion_roundtrip(value, unit):
    q = Quantity(value, unit)
    assert q.to("MWh").to(unit).value == pytest.approx(value)
```

#### 8.2 No Performance Regression Tests

**Missing:** Benchmark suite that tracks performance over time:

```python
def test_conversion_speed(benchmark):
    q = Quantity(100, "MWh")
    benchmark(lambda: q.to("GJ"))
    # Fails if > 10 μs (regression)
```

#### 8.3 No Integration Tests with Real Data

**Missing:** Tests with actual project data:

```python
def test_real_powerplant_data():
    # Load actual CSV from power plant
    # Run through library
    # Compare to known-good results
```

---

## 9. Ecosystem Integration

### Missing Integrations

#### 9.1 Pandas Extension Array

**Current:** Basic pandas support via functions.

**Better:** Native pandas dtype:

```python
df["power"] = pd.array([100, 200, 300], dtype=Quantity("MW"))
df["power"].mean()  # Quantity(200, "MW")
df["power"].to("kW")  # Column-wise conversion
```

#### 9.2 Pydantic Models

**Use case:** API validation

```python
from pydantic import BaseModel

class PowerPlant(BaseModel):
    capacity: Quantity  # Validates units
    fuel_type: str

plant = PowerPlant(
    capacity=Quantity(500, "MW"),
    fuel_type="coal"
)
```

#### 9.3 Polars Support

**Polars is faster than pandas** - growing adoption:

```python
import polars as pl

df = pl.DataFrame({
    "power": [100, 200, 300],
    "unit": ["MW", "MW", "MW"]
})
df = df.with_columns(
    pl.col("power").energy.to("GJ")  # Custom namespace
)
```

#### 9.4 Xarray for Multi-Dimensional Data

**Use case:** Hourly data × locations × scenarios:

```python
import xarray as xr

generation = xr.DataArray(
    data=np.random.rand(8760, 50, 3),
    dims=["time", "location", "scenario"],
    attrs={"units": Quantity("MW")}
)
generation.energy.to("GWh")  # Xarray accessor
```

---

## 10. Deployment & Maintenance

### ✅ Strengths
- PyPI-ready ✓
- GitHub Actions CI ✓
- Semantic versioning ✓

### ⚠️ Gaps

#### 10.1 No Conda Package

**Issue:** Scientific Python users often use Conda:

```bash
# Desired:
conda install -c conda-forge energyunits

# Current:
pip install energyunits  # Only option
```

#### 10.2 No Docker Image

**Use case:** Reproducible environments:

```dockerfile
FROM python:3.11
RUN pip install energyunits==0.1.0
# ... rest of setup
```

**Better:** Official Docker image on Docker Hub.

#### 10.3 No Deprecation Policy

**Issue:** How will breaking changes be handled?

**Need:**
- Clear deprecation timeline
- Warnings for deprecated features
- Migration guides

#### 10.4 No Security Policy

**Missing:** SECURITY.md with vulnerability reporting process.

---

## 11. Comparison to Competitors

### Pint (General-Purpose)

**Pint Advantages:**
- 10,000+ units vs our 50
- Mature (10+ years)
- Better Pandas integration
- Context managers for unit systems

**Our Advantages:**
- Energy-specific (substances, emissions)
- Inflation adjustment
- Cleaner API for energy modeling
- Better documentation

**Strategic Position:** We're "Pint for Energy Analysts"

### CoolProp (Thermodynamics)

**CoolProp Advantages:**
- Real fluid properties (pressure-enthalpy)
- Phase changes
- C++ speed

**Our Advantages:**
- Simpler API
- Economic modeling
- Better unit handling

**Strategic Position:** We're "Simple Energy Units" (CoolProp is "Complete Thermodynamics")

---

## 12. Risk Assessment

### Technical Risks

**1. NumPy Dependency Becomes Problematic**
- Likelihood: Low
- Impact: Medium
- Mitigation: Already accepted

**2. Data Goes Stale**
- Likelihood: High (inflation data)
- Impact: Medium
- Mitigation: Auto-update mechanism

**3. Breaking Changes Needed**
- Likelihood: Medium (API improvements)
- Impact: High
- Mitigation: Good deprecation policy

### Adoption Risks

**1. "Not Invented Here" Syndrome**
- Users already have Excel/Python scripts
- Migration cost high
- Mitigation: Excel import/export tools

**2. Competition from Existing Tools**
- Pint is "good enough"
- Mitigation: Killer feature (uncertainty?)

**3. Learning Curve**
- Dimensional analysis is new to some
- Mitigation: Better tutorials

---

## Priority Recommendations

### Critical (Fix Before v1.0)

1. **Dimensionless quantities return scalars** (API improvement)
2. **Add conversion factor caching** (easy performance win)
3. **Better error messages with suggestions** (UX)
4. **Deprecation policy** (governance)

### High Priority (v0.2.0)

1. **Uncertainty quantification** (killer feature)
2. **Regional fuel variants** (data quality)
3. **Fluent API for workflows** (UX)
4. **Pandas extension dtype** (ecosystem)
5. **Unit discovery methods** (UX)

### Medium Priority (v0.3.0)

1. **Time series support** (feature)
2. **Backend abstraction** (architecture)
3. **Numba optimization** (performance)
4. **Property-based tests** (quality)
5. **Conda package** (distribution)

### Low Priority (v1.0+)

1. **Temperature/pressure dependence** (feature)
2. **Optimization integration** (feature)
3. **Jupyter rich repr** (UX)
4. **Docker images** (deployment)

---

## Conclusion

**EnergyUnits v0.1.0 is production-ready** with solid fundamentals. The architecture is sound, the data is verified, and the core features work well.

**However, there's a clear path to excellence:**

1. **Pick a killer feature** (recommend: uncertainty quantification)
2. **Fix API friction** (dimensionless scalars, better errors)
3. **Deepen data** (regional variants, more properties)
4. **Broaden ecosystem** (pandas dtype, polars, xarray)
5. **Performance optimization** (caching, Numba for hot paths)

**Grade Evolution:**
- v0.1.0: B+ (Very Good)
- v0.2.0 w/ above changes: A- (Excellent)
- v1.0.0 w/ killer feature: A (Outstanding)

The foundation is excellent. Now it's about polish, depth, and that one feature that makes it indispensable.

---

**Prepared by:** Claude
**Date:** 2025-11-24
**Purpose:** Critical analysis for improvement planning
