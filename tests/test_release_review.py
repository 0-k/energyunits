"""Regression tests for the findings of the 0.3.0 release review."""

import warnings

import numpy as np
import pandas as pd
import pytest

import energyunits
from energyunits import (
    DefinitionConflictError,
    EnergyUnitsError,
    EnergyUnitsWarning,
    MissingDataError,
    Quantity,
    UnknownSubstanceError,
)
from energyunits.exchange_rate import exchange_rate_registry
from energyunits.inflation import inflation_registry
from energyunits.registry import registry
from energyunits.substance import substance_registry

GAS_LHV_PER_HHV = substance_registry.lhv_hhv_ratio("natural_gas")


class TestCancellationKeepsTheSurvivingUnit:
    """Units cancel across the operands; what did not cancel keeps its unit."""

    @pytest.mark.parametrize("swap", [False, True])
    def test_fuel_price_times_heat_rate(self, swap):
        price, heat_rate = Quantity(5, "USD/GJ"), Quantity(7, "GJ/MWh")
        cost = heat_rate * price if swap else price * heat_rate
        assert cost.unit == "USD/MWh"
        assert cost.value == pytest.approx(35)

    def test_emission_factor_times_heat_rate(self):
        result = Quantity(0.0561, "t/GJ") * Quantity(7, "GJ/MWh")
        assert result.unit == "t/MWh"
        assert result.value == pytest.approx(0.3927)

    def test_fuel_energy_divided_by_heat_rate(self):
        result = Quantity(700, "GJ") / Quantity(7, "GJ/MWh")
        assert result.unit == "MWh"
        assert result.value == pytest.approx(100)

    def test_different_units_of_one_dimension_cancel_across_operands(self):
        result = Quantity(5, "USD/GJ") * Quantity(7e6, "kJ/MWh")
        assert result.unit == "USD/MWh"
        assert result.value == pytest.approx(35)

    def test_heat_rate_times_output(self):
        result = Quantity(7, "GJ/MWh") * Quantity(100, "kWh")
        assert result.unit == "GJ"
        assert result.value == pytest.approx(0.7)

    def test_same_dimension_product_is_unchanged(self):
        result = Quantity(100, "MWh") * Quantity(3.6, "GJ")
        assert result.unit == "MWh·MWh"
        assert result.value == pytest.approx(100)


class TestProductAfterSlash:
    """Everything after the first slash is in the denominator."""

    def test_product_after_slash_is_in_the_denominator(self):
        assert registry.parse_unit("EUR/kW·a") == registry.parse_unit("EUR/kW/a")
        assert registry.parse_unit("EUR/kW*a") == registry.parse_unit("EUR/kW/a")

    def test_annual_cost(self):
        result = Quantity(40, "EUR/kW·a") * Quantity(100, "kW")
        assert result.unit == "EUR/a"
        assert result.value == pytest.approx(4000)

    def test_conversion(self):
        assert Quantity(50, "USD/MW·h").to("USD/MWh").value == pytest.approx(50)

    def test_product_before_slash_is_in_the_numerator(self):
        assert Quantity(1, "USD·h/MWh").to("USD/MW").value == pytest.approx(1)

    def test_formatted_units_parse_back(self):
        for unit in ("EUR/kW/a", "USD·h/MWh", "1/h", "t·h/a/MW"):
            terms = registry.parse_unit(unit)
            assert registry.parse_unit(registry.format_terms(terms)) == terms


class TestBasisOfHeatRates:
    def test_heat_rate_is_rescaled(self):
        lhv = Quantity(7, "GJ/MWh", "natural_gas", basis="HHV").to(basis="LHV")
        assert lhv.basis == "LHV"
        assert lhv.value == pytest.approx(7 * GAS_LHV_PER_HHV)
        assert lhv.to(basis="HHV").value == pytest.approx(7)

    def test_heat_rate_with_power_and_time(self):
        hhv = Quantity(7, "GJ/h/MW", "natural_gas").to(basis="HHV")
        assert hhv.value == pytest.approx(7 / GAS_LHV_PER_HHV)

    def test_heat_rates_on_different_bases_are_not_equal(self):
        assert Quantity(7, "GJ/MWh", "natural_gas", basis="HHV") != Quantity(7, "GJ/MWh", "natural_gas")

    def test_heat_rate_times_fuel_price_aligns_the_basis(self):
        heat_rate = Quantity(7, "GJ/MWh", "natural_gas", basis="HHV")
        price = Quantity(5, "USD/GJ", "natural_gas", basis="LHV")
        cost = heat_rate * price
        assert cost.unit == "USD/MWh"
        assert cost.value == pytest.approx(35 * GAS_LHV_PER_HHV)

    def test_dimensionless_quantity_is_ambiguous(self):
        with pytest.raises(EnergyUnitsError, match="dimensionless"):
            Quantity(0.5, "", "natural_gas", basis="HHV").to(basis="LHV")

    def test_mass_is_only_relabelled(self):
        assert Quantity(2, "t", "coal", basis="HHV").to(basis="LHV").value == pytest.approx(2)


class TestBasisAlignment:
    @pytest.mark.parametrize("carrier", ["wind", "solar", "hydro", "nuclear"])
    def test_fuel_plus_carrier_without_heating_value(self, carrier):
        gas = Quantity(100, "MWh", "natural_gas", basis="HHV")
        other = Quantity(50, "MWh", carrier)
        with pytest.warns(EnergyUnitsWarning, match="different substances"):
            assert (gas + other).value == pytest.approx(150)
        with pytest.warns(EnergyUnitsWarning, match="different substances"):
            assert (other + gas).value == pytest.approx(150)
        assert other < gas
        assert sum([gas, gas]).value == pytest.approx(200)

    def test_quantity_without_substance_is_not_rescaled(self):
        plain, coal = Quantity(100, "MWh"), Quantity(100, "MWh", "coal", basis="HHV")
        assert plain == coal and coal == plain
        assert (plain + coal).value == pytest.approx(200)
        assert (coal + plain).value == pytest.approx(200)
        assert (plain + coal).basis == (coal + plain).basis == "HHV"

    def test_fuels_on_different_bases_are_still_aligned(self):
        hhv = Quantity(100, "MWh", "natural_gas", basis="HHV")
        lhv = Quantity(100, "MWh", "natural_gas")
        assert (hhv + lhv).value == pytest.approx(100 + 100 / GAS_LHV_PER_HHV)
        assert (lhv + hhv).value == pytest.approx(100 + 100 * GAS_LHV_PER_HHV)
        assert hhv != lhv


class TestReferenceYearsInProducts:
    def test_exchange_rate_is_not_inflation_adjusted(self):
        result = Quantity(100, "USD", reference_year=2020) * Quantity(0.9, "EUR/USD", reference_year=2021)
        assert result.unit == "EUR"
        assert result.value == pytest.approx(90)

    def test_currency_without_inflation_data(self):
        registry.load_units({"dimensions": {"AUD": "CURRENCY"}, "conversion_factors": {"AUD": 0.65}})
        cost = Quantity(100, "AUD", reference_year=2020)
        with pytest.warns(EnergyUnitsWarning, match="without inflation adjustment"):
            ratio = cost / Quantity(50, "AUD", reference_year=2021)
        assert ratio.value == pytest.approx(2)
        assert ratio.reference_year is None
        with pytest.raises(MissingDataError):
            cost + Quantity(50, "AUD", reference_year=2021)

    def test_costs_of_different_years_are_still_aligned(self):
        factor = inflation_registry.get_cumulative_inflation_factor("EUR", 2024, 2015)
        energy = Quantity(100, "EUR", reference_year=2015) / Quantity(50, "EUR/MWh", reference_year=2024)
        assert energy.value == pytest.approx(100 / (50 * factor))

    def test_repeated_currency_is_one_currency(self):
        assert Quantity(2, "EUR·EUR/kEUR", reference_year=2015).to(
            reference_year=2020
        ).value == pytest.approx(2 * inflation_registry.get_cumulative_inflation_factor("EUR", 2015, 2020))
        cancelled = Quantity(1, "EUR·MWh/kEUR", reference_year=2015).to(reference_year=2020)
        assert cancelled.value == pytest.approx(1) and cancelled.reference_year == 2020

    def test_float_uses_the_rates_of_the_reference_year(self):
        ratio = Quantity(100, "EUR", reference_year=2010) / Quantity(100, "USD", reference_year=2010)
        assert float(ratio) == pytest.approx(exchange_rate_registry.get_exchange_rate("EUR", 2010))
        assert float(ratio) == pytest.approx(ratio.to("").value)


class TestNumpyReductions:
    def test_numpy_functions_return_quantities(self):
        q = Quantity([1.0, 2.0, 3.0], "MWh", "coal", basis="HHV")
        for function, expected in ((np.sum, 6), (np.mean, 2), (np.min, 1), (np.max, 3), (np.amax, 3)):
            result = function(q)
            assert isinstance(result, Quantity)
            assert (result.unit, result.substance, result.basis) == ("MWh", "coal", "HHV")
            assert result.value == pytest.approx(expected)

    def test_axis_and_keepdims(self):
        q = Quantity([[1.0, 2.0], [3.0, 4.0]], "MW")
        assert np.sum(q, axis=0).value.tolist() == [4, 6]
        assert q.sum(axis=1, keepdims=True).shape == (2, 1)

    def test_out_is_rejected(self):
        with pytest.raises(TypeError, match="out"):
            np.sum(Quantity([1.0, 2.0], "MW"), out=np.zeros(()))


class TestPandasValues:
    @pytest.mark.parametrize(
        "values",
        [pd.to_timedelta(["1h", "2h"]), pd.to_datetime(["2020-01-01"]), pd.period_range("2020", periods=2)],
    )
    def test_dates_and_durations_are_rejected(self, values):
        with pytest.raises(TypeError, match="numeric"):
            Quantity(pd.Series(values), "h")

    def test_date_column_in_dataframe_is_rejected(self):
        frame = pd.DataFrame({"a": [1.0], "when": pd.to_datetime(["2020-01-01"])})
        with pytest.raises(TypeError, match="numeric"):
            Quantity(frame, "MWh")

    def test_numeric_frames_and_nullable_series(self):
        assert Quantity(pd.DataFrame({"a": [1, 2], "b": [1.5, 2.5]}), "MWh").shape == (2, 2)
        nullable = Quantity(pd.Series([1, None], dtype="Int64"), "MWh")
        assert nullable.value[0] == 1 and np.isnan(nullable.value[1])
        with pytest.raises(TypeError, match="strings"):
            Quantity(pd.DataFrame({"a": [1, 2], "b": ["1", "2"]}), "MWh")


class TestEquality:
    def test_incompatible_units_are_not_equal(self):
        assert Quantity(1, "t") != Quantity(1, "MWh")
        assert not Quantity(1, "MW") == Quantity(1, "MWh")

    def test_missing_exchange_rate_raises(self):
        with pytest.raises(MissingDataError):
            Quantity(100, "EUR", reference_year=1995) == Quantity(113, "USD", reference_year=1995)

    def test_unknown_substance_raises(self):
        with pytest.raises(UnknownSubstanceError):
            Quantity(1, "t", "coall") == Quantity(7.17, "MWh", "coall")


class TestLoading:
    def test_factor_relative_to_a_unit(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            registry.load_units(
                {
                    "dimensions": {"boe": "ENERGY"},
                    "conversion_factors": {"boe": {"value": 1.7, "unit": "MWh"}},
                }
            )
        assert Quantity(1, "boe").to("MWh").value == pytest.approx(1.7)

    def test_factor_relative_to_a_unit_of_the_same_file(self):
        registry.load_units(
            {
                "dimensions": {"plot": "AREA", "kplot": "AREA"},
                "conversion_factors": {"plot": 500.0, "kplot": {"value": 1000, "unit": "plot"}},
            }
        )
        assert Quantity(1, "kplot").to("m2").value == pytest.approx(500_000)

    @pytest.mark.parametrize(
        "factor",
        [
            {"value": 1.7, "unit": "nope"},
            {"value": 1.7},
            {"value": -1, "unit": "MWh"},
            {"value": 1, "unit": 3},
        ],
    )
    def test_malformed_relative_factor(self, factor):
        with pytest.raises(ValueError):
            registry.load_units({"dimensions": {"boe": "ENERGY"}, "conversion_factors": {"boe": factor}})
        assert not registry.has_unit("boe")

    def test_plain_factor_of_a_changed_base_unit_warns(self):
        with pytest.warns(EnergyUnitsWarning, match=r"'boe' \(in J, 0.2: MWh\)"):
            registry.load_units({"dimensions": {"boe": "ENERGY"}, "conversion_factors": {"boe": 1.7}})

    def test_plain_factor_of_an_unchanged_base_unit_does_not_warn(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            registry.load_units({"dimensions": {"MMscf": "VOLUME"}, "conversion_factors": {"MMscf": 28316.8}})
            registry.load_units({"dimensions": {"MWh": "ENERGY"}, "conversion_factors": {"MWh": 3.6e9}})

    def test_comment_keys_inside_sections_are_ignored(self):
        registry.load_units(
            {
                "dimensions": {"_comment": "my units", "plot": "AREA"},
                "conversion_factors": {"_comment": "in m2", "plot": 500.0},
            }
        )
        assert "_comment" not in registry.list_units()
        assert "my units" not in registry.list_dimensions()
        assert registry.has_unit("plot")

    def test_rule_with_dimensions_in_other_order_is_identical(self):
        rule = {"dimensions": ["TIME", "POWER"], "result_dimension": "ENERGY", "source_dimension": "POWER"}
        registry.load_units({"dimensional_multiplication_rules": [rule]})
        with pytest.raises(DefinitionConflictError):
            registry.load_units({"dimensional_multiplication_rules": [{**rule, "result_dimension": "MASS"}]})

    def test_numpy_scalars_are_numbers(self):
        inflation_registry.load_inflation({"USD": {2033: np.int64(3)}})
        registry.load_units({"dimensions": {"plot": "AREA"}, "conversion_factors": {"plot": np.float32(500)}})
        substance_registry.load_substances({"my_fuel": {"lhv": np.float32(20), "hhv": np.int64(22)}})
        assert Quantity(1, "plot").to("m2").value == pytest.approx(500)
        for boolean in (True, np.bool_(True)):
            with pytest.raises(ValueError):
                registry.load_units({"dimensions": {"x": "AREA"}, "conversion_factors": {"x": boolean}})

    def test_derived_carbon_content_is_validated(self):
        with pytest.raises(ValueError, match="carbon_content.*derived"):
            substance_registry.load_substances({"f2": {"lhv": 120.0, "carbon_intensity": 95.0}})
        assert "f2" not in substance_registry


def test_pandas_tools_is_a_regular_submodule():
    assert "pandas_tools" in energyunits.__all__
    assert energyunits.pandas_tools.convert_units is not None
