"""Consistency checks for the bundled data files."""

import json
import math
from pathlib import Path

import pytest

import energyunits
from energyunits import units
from energyunits.registry import registry

# Use the data shipped with the *installed* package, not the source checkout.
DATA = Path(energyunits.__file__).resolve().parent / "data"


def _load(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


class TestUnitsData:
    def test_every_unit_has_positive_factor(self):
        data = _load("units.json")
        assert set(data["dimensions"]) == set(data["conversion_factors"])
        for unit, factor in data["conversion_factors"].items():
            assert factor > 0 and math.isfinite(factor), unit

    def test_base_units_have_factor_one(self):
        data = _load("units.json")
        for dimension, base in data["base_units"].items():
            assert data["dimensions"][base] == dimension
            assert data["conversion_factors"][base] == 1.0

    def test_derived_dimensions_are_coherent(self):
        data = _load("units.json")
        for name, composition in data["derived_dimensions"].items():
            base = data["base_units"][name]
            factor = 1.0
            for dimension, exp in composition.items():
                factor *= data["conversion_factors"][data["base_units"][dimension]] ** exp
            assert data["conversion_factors"][base] == pytest.approx(factor)

    def test_corresponding_units_exist(self):
        data = _load("units.json")
        for source, target in data["corresponding_units"].items():
            assert source in data["dimensions"] and target in data["dimensions"]

    def test_currency_units_consistent(self):
        data = _load("units.json")
        for unit, info in data["currency_units"].items():
            assert data["dimensions"][unit] == "CURRENCY"
            base = info["currency"]
            assert data["conversion_factors"][unit] == pytest.approx(
                info["scale"] * data["conversion_factors"][base]
            )

    def test_static_currency_factors_equal_latest_exchange_rates(self):
        factors = _load("units.json")["conversion_factors"]
        rates = _load("exchange_rates.json")
        for code, years in rates.items():
            if code.startswith("_"):
                continue
            latest = years[max(years, key=int)]
            assert factors[code] == pytest.approx(latest, rel=1e-9), code

    def test_unit_constants_match_registry(self):
        data = _load("units.json")
        constants = {name: value for name, value in vars(units).items() if not name.startswith("_")}
        assert set(constants) == set(data["dimensions"])
        for name, value in constants.items():
            assert name == value
        assert "min" not in units.__all__

    @pytest.mark.parametrize(
        "unit, expected_mwh",
        [
            ("GJ", 1 / 3.6),
            ("MMBTU", 0.29307107017222),
            ("therm", 0.029307107017222),
            ("toe", 11.63),
            ("Mtoe", 11.63e6),
            ("tce", 8.141),
            ("Gcal", 1.163),
            ("EJ", 1e9 / 3.6),
        ],
    )
    def test_energy_unit_definitions(self, unit, expected_mwh):
        assert registry.get_conversion_factor(unit, "MWh") == pytest.approx(expected_mwh, rel=1e-12)

    @pytest.mark.parametrize(
        "unit, target, expected",
        [
            ("barrel", "L", 158.987294928),
            ("gal", "L", 3.785411784),
            ("Mcf", "m3", 28.316846592),
            ("bcm", "m3", 1e9),
            ("lb", "kg", 0.45359237),
            ("kt", "t", 1000),
            ("d", "h", 24),
            ("a", "h", 8760),
        ],
    )
    def test_other_unit_definitions(self, unit, target, expected):
        assert registry.get_conversion_factor(unit, target) == pytest.approx(expected, rel=1e-12)


class TestSubstanceData:
    FIELDS = (
        "hhv",
        "lhv",
        "density",
        "carbon_intensity",
        "carbon_content",
        "hydrogen_content",
        "ash_content",
    )

    @pytest.fixture(scope="class")
    def substances(self):
        return {k: v for k, v in _load("substances.json").items() if not k.startswith("_")}

    def test_all_fields_present(self, substances):
        for name, props in substances.items():
            assert "name" in props, name
            for field in self.FIELDS:
                assert field in props, (name, field)

    def test_heating_values(self, substances):
        for name, props in substances.items():
            if props["hhv"] is None:
                assert props["lhv"] is None, name
                continue
            assert 0 < props["lhv"] <= props["hhv"], name

    def test_mass_fractions(self, substances):
        for name, props in substances.items():
            for field in ("carbon_content", "hydrogen_content", "ash_content"):
                assert 0 <= props[field] <= 1, (name, field)

    def test_carbon_content_matches_emission_factor(self, substances):
        """Stoichiometric CO2 per GJ (LHV) equals the stated emission factor for fossil fuels."""
        for name, props in substances.items():
            if props.get("biogenic"):
                assert props["carbon_intensity"] == 0, name
                continue
            if props["lhv"] is None or not props["carbon_intensity"]:
                continue
            kg_co2_per_gj = props["carbon_content"] * 44 / 12 / props["lhv"] * 1000
            assert kg_co2_per_gj == pytest.approx(props["carbon_intensity"], rel=2e-3), name


class TestEconomicData:
    @pytest.mark.parametrize("filename", ["inflation.json", "exchange_rates.json"])
    def test_years_contiguous(self, filename):
        for code, years in _load(filename).items():
            if code.startswith("_"):
                continue
            numbers = sorted(int(y) for y in years)
            assert numbers == list(range(numbers[0], numbers[-1] + 1)), code

    def test_exchange_rates_positive_and_plausible(self):
        for code, years in _load("exchange_rates.json").items():
            if code.startswith("_"):
                continue
            values = list(years.values())
            assert all(v > 0 for v in values)
            # No single-year jump of more than 30 % (catches unit/inversion mistakes)
            for previous, current in zip(values, values[1:]):
                assert 0.7 < current / previous < 1.3, code

    def test_inflation_rates_plausible(self):
        for code, years in _load("inflation.json").items():
            if code.startswith("_"):
                continue
            assert all(-5 < rate < 15 for rate in years.values()), code

    def test_projection_metadata(self):
        data = _load("inflation.json")
        projected = data["_metadata"]["projected_from"]
        assert set(projected) == {k for k in data if not k.startswith("_")}
