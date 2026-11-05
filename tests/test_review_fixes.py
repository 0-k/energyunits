"""Regression tests for the findings of the 0.3.0 pre-release review."""

import numpy as np
import pytest

from energyunits import MissingDataError, Quantity
from energyunits.exchange_rate import exchange_rate_registry
from energyunits.inflation import inflation_registry
from energyunits.registry import registry
from energyunits.substance import substance_registry

GAS_HHV_PER_LHV = 53.33 / 48.0


class TestBasisInProducts:
    """Products and quotients keep the heating value basis of the energy operand."""

    def test_power_times_time(self):
        energy = Quantity(100, "MW", "natural_gas", basis="HHV") * Quantity(10, "h")
        assert energy.basis == "HHV"
        expected = Quantity(1000, "MWh", "natural_gas", basis="HHV").to("m3").value
        assert energy.to("m3").value == pytest.approx(expected)

    def test_time_times_power(self):
        energy = Quantity(10, "h") * Quantity(100, "MW", "natural_gas", basis="HHV")
        assert (energy.unit, energy.basis) == ("MWh", "HHV")
        assert energy.value == pytest.approx(1000)

    def test_energy_divided_by_time(self):
        power = Quantity(1000, "MWh", "natural_gas", basis="HHV") / Quantity(10, "h")
        assert (power.unit, power.basis) == ("MW", "HHV")


class TestBasisAlignmentInAddition:
    """+, - and comparisons convert a mass or volume operand at the left operand's basis."""

    def test_hhv_energy_plus_volume(self):
        total = Quantity(1, "MMBTU", "natural_gas", basis="HHV") + Quantity(30, "m3", "natural_gas")
        expected = 1 + Quantity(30, "m3", "natural_gas").to("MMBTU", basis="HHV").value
        assert total.basis == "HHV"
        assert total.value == pytest.approx(expected)

    def test_lhv_energy_plus_hhv_labelled_mass(self):
        total = Quantity(1, "MWh", "coal") + Quantity(1, "t", "coal", basis="HHV")
        assert total.basis in (None, "LHV")
        assert total.value == pytest.approx(1 + 25.8 / 3.6)

    def test_comparison_with_a_volume(self):
        volume = Quantity(30, "m3", "natural_gas")
        energy = volume.to("MMBTU", basis="HHV")
        assert energy == volume
        assert energy >= volume and energy <= volume


class TestAlignmentInProducts:
    """Products and quotients align heating value basis and price year where they cancel."""

    def test_hhv_price_times_lhv_energy(self):
        cost = Quantity(5, "USD/MWh", "natural_gas", basis="HHV") * Quantity(100, "MWh", "natural_gas")
        assert cost.unit == "USD"
        assert cost.value == pytest.approx(5 * 100 * GAS_HHV_PER_LHV, rel=1e-4)

    def test_lhv_energy_times_hhv_price(self):
        cost = Quantity(100, "MWh", "natural_gas") * Quantity(5, "USD/MWh", "natural_gas", basis="HHV")
        assert cost.value == pytest.approx(5 * 100 * GAS_HHV_PER_LHV, rel=1e-4)

    def test_budget_divided_by_price_of_another_year(self):
        energy = Quantity(1000, "EUR", reference_year=2015) / Quantity(100, "EUR/MWh", reference_year=2024)
        budget_2024 = Quantity(1000, "EUR", reference_year=2015).to(reference_year=2024).value
        assert energy.unit == "MWh"
        assert energy.value == pytest.approx(budget_2024 / 100)

    def test_year_of_the_cost_operand_is_kept(self):
        cost = Quantity(50, "EUR/MWh", reference_year=2015) * Quantity(10, "MWh", reference_year=2024)
        assert cost.reference_year == 2015
        assert cost.value == pytest.approx(500)

    def test_products_of_unrelated_quantities_are_unchanged(self):
        assert (Quantity(100, "MW") * Quantity(2, "h")).value == pytest.approx(200)
        cost = Quantity(1000, "EUR/kW", reference_year=2020) * Quantity(5, "MW")
        assert (cost.unit, cost.reference_year) == ("EUR", 2020)
        assert cost.value == pytest.approx(5e6)


def test_units_with_several_currencies_use_rates_of_the_reference_year():
    result = Quantity(1, "EUR/kUSD", reference_year=2015).to("GBP/kUSD")
    assert result.value == pytest.approx(Quantity(1, "EUR", reference_year=2015).to("GBP").value)
    result = Quantity(1, "USD/EUR", reference_year=2015).to("USD/GBP")
    assert result.value == pytest.approx(Quantity(1, "GBP", reference_year=2015).to("EUR").value)


def test_registry_views_can_be_loaded_again():
    substance_registry.load_substances({"mylib_coal": substance_registry["coal"]})
    assert Quantity(1, "t", "mylib_coal").to("GJ").value == pytest.approx(25.8)
    substance_registry.load_substances({"fuel": {"lhv": 20.0, "notes": {"tags": ["a"]}}})
    substance_registry.load_substances({"fuel_copy": dict(substance_registry["fuel"])})
    assert substance_registry["fuel_copy"]["notes"]["tags"] == ("a",)


class TestExactCurrencyPrefixes:
    @pytest.mark.parametrize("unit", sorted(registry._currency_units))
    def test_prefix_conversions_are_exact(self, unit):
        code, scale = registry.currency_of(unit)
        assert Quantity(1, unit).to(code).value == scale
        assert Quantity(scale, code).to(unit).value == 1.0

    def test_merging_prefixed_currencies_is_exact(self):
        assert (Quantity(1, "kEUR") / Quantity(1, "EUR")).value == 1000.0
        assert (Quantity(1, "kEUR/MWh") * Quantity(1, "MWh")).to("EUR").value == 1000.0
        assert Quantity(1, "MGBP/MW").to("GBP/kW").value == 1000.0


@pytest.mark.parametrize(
    "props",
    [
        {"lhv": 50.0, "density": 0},
        {"lhv": 50.0, "density": -0.7},
        {"lhv": -1.0},
        {"hhv": 0.0},
        {"lhv": 30.0, "hhv": 20.0},
        {"carbon_content": 1.5},
        {"ash_content": -0.1},
        {"carbon_intensity": -5.0},
    ],
)
def test_implausible_substance_values_are_rejected(props):
    with pytest.raises(ValueError):
        substance_registry.load_substances({"x": props})
    assert "x" not in substance_registry


class TestEmptySeries:
    def test_currency_without_years_is_rejected(self):
        with pytest.raises(ValueError, match="at least one year"):
            inflation_registry.load_inflation({"AUD": {}})
        with pytest.raises(ValueError, match="at least one year"):
            exchange_rate_registry.load_exchange_rates({"AUD": {}})

    def test_available_years_of_unknown_currency(self):
        with pytest.raises(MissingDataError):
            inflation_registry.get_available_years("XYZ")


class TestNumericInput:
    @pytest.mark.parametrize(
        "make",
        [
            lambda pd: pd.Series(["1.5", "2"]),
            lambda pd: pd.Series(["1.5"], dtype="string"),
            lambda pd: np.array(["1.5"], dtype=object),
            lambda pd: np.array([1.0, "2"], dtype=object),
        ],
    )
    def test_numeric_strings_are_rejected(self, make):
        pd = pytest.importorskip("pandas")
        with pytest.raises(TypeError):
            Quantity(make(pd), "MWh")

    def test_object_arrays_of_numbers_are_accepted(self):
        pd = pytest.importorskip("pandas")
        assert Quantity(np.array([1, 2.5], dtype=object), "MWh").value.tolist() == [1.0, 2.5]
        values = Quantity(pd.Series([1.0, None], dtype=object), "MWh").value
        assert values[0] == 1.0 and np.isnan(values[1])


class TestNoNeedlessConversion:
    def test_same_unit_operands_are_not_converted(self, monkeypatch):
        calls = []
        original = Quantity._convert_unit

        def spy(self, *args, **kwargs):
            calls.append(args)
            return original(self, *args, **kwargs)

        monkeypatch.setattr(Quantity, "_convert_unit", spy)
        a, b = Quantity([1.0, 2.0], "MWh"), Quantity([3.0, 4.0], "MWh")
        assert (a + b).value.tolist() == [4.0, 6.0]
        assert (b - a).value.tolist() == [2.0, 2.0]
        assert a < b and a != b
        assert calls == []

    def test_identity_conversion_returns_an_independent_copy(self):
        q = Quantity([1.0, 2.0], "MWh")
        converted = q.to("MWh")
        assert converted.value.tolist() == [1.0, 2.0]
        assert converted.value is not q.value
