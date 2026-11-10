"""Unit parsing, dimensional analysis and arithmetic on compound units.

Many of these are regression tests for results that used to be silently wrong.
"""

import numpy as np
import pytest

from energyunits import IncompatibleUnitsError, Quantity, UnknownUnitError
from energyunits.registry import registry


class TestParsing:
    @pytest.mark.parametrize(
        "unit, terms",
        [
            ("MWh", (("MWh", 1),)),
            ("USD/kW", (("USD", 1), ("kW", -1))),
            # Left to right: (EUR / kW) / a, i.e. both kW and a in the denominator
            ("EUR/kW/a", (("EUR", 1), ("kW", -1), ("a", -1))),
            ("MW·h", (("MW", 1), ("h", 1))),
            ("MW*h", (("MW", 1), ("h", 1))),
            ("USD / MWh", (("USD", 1), ("MWh", -1))),
            ("1/h", (("h", -1),)),
            ("MWh/MWh", ()),
            ("", ()),
        ],
    )
    def test_parse_unit(self, unit, terms):
        assert registry.parse_unit(unit) == terms

    @pytest.mark.parametrize("unit", ["MW//h", "MW/", "/h", "   ", "MW*", "MWh·"])
    def test_malformed_units_raise(self, unit):
        with pytest.raises(UnknownUnitError, match="Malformed unit"):
            registry.parse_unit(unit)

    def test_unknown_unit_in_compound(self):
        with pytest.raises(UnknownUnitError, match="Unknown unit: 'xyz' in 'USD/xyz'"):
            Quantity(1, "USD/xyz")

    def test_case_suggestion(self):
        with pytest.raises(UnknownUnitError, match="Did you mean: MWh"):
            Quantity(1, "mwh")

    def test_non_string_unit(self):
        with pytest.raises(TypeError):
            registry.parse_unit(5)


class TestDimensions:
    @pytest.mark.parametrize(
        "unit, dimension",
        [
            ("MWh", "ENERGY"),
            ("GJ/h", "POWER"),
            ("MWh/a", "POWER"),
            ("kWh/kW", "TIME"),
            ("MW*h", "ENERGY"),
            ("GWh/MWh", "DIMENSIONLESS"),
            ("USD/kW", "CURRENCY_PER_POWER"),
            ("EUR/kW/a", "CURRENCY_PER_POWER_PER_TIME"),
            ("t/MWh", "MASS_PER_ENERGY"),
        ],
    )
    def test_dimension_names(self, unit, dimension):
        assert Quantity(1, unit).dimension == dimension

    def test_dimension_vector_power(self):
        assert registry.dimension_vector("MW") == (("ENERGY", 1), ("TIME", -1))

    @pytest.mark.parametrize(
        "unit1, unit2",
        [("GJ/h", "MW"), ("kWh/kW", "h"), ("EUR/MW", "EUR·h/MWh"), ("EUR/kW/a", "EUR/kWh"), ("MW·h", "MWh")],
    )
    def test_equivalent_units_are_compatible(self, unit1, unit2):
        assert registry.is_compatible(unit1, unit2)


class TestCompoundConversions:
    def test_left_associative_division(self):
        # 100 EUR/kW/a = 100 EUR per kW per year = 100/8760 EUR per kW per hour
        assert Quantity(100, "EUR/kW/a").to("EUR/kW/h").value == pytest.approx(100 / 8760)
        assert Quantity(100, "EUR/kW/a").to("EUR/MW/a").value == pytest.approx(100_000)

    def test_equivalent_compound_units(self):
        assert Quantity(3600, "GJ/h").to("MW").value == pytest.approx(1000)
        assert Quantity(4000, "kWh/kW").to("h").value == pytest.approx(4000)
        assert Quantity(10, "EUR/MW").to("EUR·h/MWh").value == pytest.approx(10)
        assert Quantity(8760, "MWh/a").to("MW").value == pytest.approx(1)

    def test_dimensionless_roundtrip(self):
        assert Quantity(0.4, "").to("").value == pytest.approx(0.4)
        assert Quantity(2, "GWh/MWh").to("").value == pytest.approx(2000)

    def test_power_to_energy_requires_duration(self):
        with pytest.raises(IncompatibleUnitsError, match="time dimension"):
            Quantity(100, "MW").to("MWh")


class TestMultiplication:
    @pytest.mark.parametrize(
        "a, b, expected_value, expected_unit",
        [
            ((100, "MW"), (30, "min"), 50, "MWh"),
            ((1, "kW"), (1, "a"), 8760, "kWh"),
            ((2, "GW"), (1, "d"), 48, "GWh"),
            ((30, "min"), (100, "MW"), 50, "MWh"),
            ((1500, "USD/kW"), (500, "MW"), 750e6, "USD"),
            ((500, "MW"), (1500, "USD/kW"), 750e6, "USD"),
            ((50, "EUR/MWh"), (2, "GWh"), 100_000, "EUR"),
            ((0.35, "t/MWh"), (3, "TWh"), 1.05e6, "t"),
            ((40, "EUR/kW/a"), (100, "MW"), 4e6, "EUR/a"),
            ((4e6, "EUR/a"), (25, "a"), 1e8, "EUR"),
            ((0.4, ""), (100, "MWh"), 40, "MWh"),
            ((100, "MWh"), (0.4, ""), 40, "MWh"),
        ],
    )
    def test_products(self, a, b, expected_value, expected_unit):
        result = Quantity(*a) * Quantity(*b)
        assert result.unit == expected_unit
        assert result.value == pytest.approx(expected_value)

    def test_no_false_cancellation(self):
        # "h" is a substring of "USD/MWh" but must not cancel it
        result = Quantity(50, "USD/MWh") * Quantity(10, "h")
        assert result.unit == "USD·h/MWh"
        assert result.to("USD/MW").value == pytest.approx(500)

        # t/MWh * t is t²/MWh, not t
        result = Quantity(0.5, "t/MWh") * Quantity(2, "t")
        assert result.unit == "t·t/MWh"
        assert result.value == pytest.approx(1)

    def test_product_of_same_dimension(self):
        result = Quantity(2, "MW") * Quantity(3000, "kW")
        assert result.unit == "MW·MW"
        assert result.value == pytest.approx(6)

    def test_annual_energy_from_capacity_and_full_load_hours(self):
        capacity = Quantity(2, "GW")
        flh = Quantity(4000, "h")
        assert (capacity * flh).to("TWh").value == pytest.approx(8)


class TestDivision:
    @pytest.mark.parametrize(
        "a, b, expected_value, expected_unit",
        [
            ((8760, "MWh"), (1, "a"), 1, "MW"),
            ((60, "MWh"), (30, "min"), 120, "MW"),
            ((3600, "GJ"), (1, "h"), 1000, "MW"),
            ((100, "MWh"), (50, "MW"), 2, "h"),
            ((8, "TWh"), (2, "GW"), 4000, "h"),
            ((1, "GWh"), (500, "MWh"), 2, ""),
            ((1000, "USD"), (2, "MWh"), 500, "USD/MWh"),
            ((100, "t"), (50, "m3"), 2, "t/m3"),
            ((1000, "EUR/kW"), (20, "a"), 50, "EUR/kW/a"),
            ((100, "MWh"), (0.5, ""), 200, "MWh"),
        ],
    )
    def test_quotients(self, a, b, expected_value, expected_unit):
        result = Quantity(*a) / Quantity(*b)
        assert result.unit == expected_unit
        assert result.value == pytest.approx(expected_value)

    def test_capacity_factor(self):
        generation = Quantity(3504, "GWh/a")
        capacity = Quantity(1000, "MW")
        capacity_factor = generation / capacity
        assert capacity_factor.dimension == "DIMENSIONLESS"
        assert float(capacity_factor) == pytest.approx(0.4)

    def test_reciprocal(self):
        rate = 1 / Quantity(4, "h")
        assert rate.unit == "1/h"
        assert rate.value == pytest.approx(0.25)
        assert (rate * Quantity(2, "d")).to("").value == pytest.approx(12)

    def test_division_and_multiplication_roundtrip(self):
        energy = Quantity([10, 20, 30], "GWh")
        duration = Quantity(90, "min")
        assert np.allclose(((energy / duration) * duration).to("GWh").value, energy.value)


class TestExhaustiveUnitRoundtrips:
    @pytest.mark.parametrize("dimension", ["ENERGY", "POWER", "MASS", "VOLUME", "TIME", "CURRENCY"])
    def test_all_pairs_roundtrip(self, dimension):
        units = registry.list_units(dimension)
        for a in units:
            for b in units:
                forward = registry.get_conversion_factor(a, b)
                backward = registry.get_conversion_factor(b, a)
                assert forward * backward == pytest.approx(1.0, rel=1e-12), (a, b)

    def test_power_units_coherent_with_energy_per_hour(self):
        for power in registry.list_units("POWER"):
            energy = registry.get_corresponding_unit(power, "ENERGY")
            assert registry.get_conversion_factor(f"{energy}/h", power) == pytest.approx(1.0, rel=1e-12)
