"""Python/NumPy protocols of Quantity: operators, containers, formatting, equality."""

import copy
import pickle
import warnings

import numpy as np
import pytest

from energyunits import EnergyUnitsWarning, Quantity


class TestNumericOperands:
    @pytest.mark.parametrize("factor", [2, 2.0, np.int64(2), np.float32(2), np.array(2)])
    def test_scalar_types(self, factor):
        assert (Quantity(3, "MWh") * factor).value == pytest.approx(6)
        assert (factor * Quantity(3, "MWh")).value == pytest.approx(6)
        assert (Quantity(6, "MWh") / factor).value == pytest.approx(3)

    def test_numpy_array_operand_on_either_side(self):
        profile = np.array([0.5, 1.0, 0.25])
        left = profile * Quantity(100, "MW")
        right = Quantity(100, "MW") * profile
        assert isinstance(left, Quantity) and isinstance(right, Quantity)
        assert np.allclose(left.value, [50, 100, 25])
        assert left.unit == "MW"

    def test_pandas_series_operand(self):
        pd = pytest.importorskip("pandas")
        series = pd.Series([1.0, 2.0])
        assert isinstance(series * Quantity(1, "MWh"), Quantity)
        assert isinstance(Quantity(1, "MWh") * series, Quantity)

    def test_rejected_operands(self):
        for other in ["2", None, [1, 2], (1, 2), {"a": 1}]:
            with pytest.raises(TypeError):
                Quantity(1, "MWh") * other

    def test_values_are_not_shared_with_input(self):
        q = Quantity([1, 2, 3], "MWh")
        doubled = q * 2
        doubled.value[0] = 100
        assert q.value[0] == 1


class TestUnaryAndSum:
    def test_negation_and_abs(self):
        assert (-Quantity(5, "MWh")).value == -5
        assert abs(Quantity(-5, "MWh")).value == 5
        assert (+Quantity(5, "MWh")).value == 5

    def test_builtin_sum(self):
        total = sum([Quantity(1, "MWh"), Quantity(1000, "kWh"), Quantity(3.6, "GJ")])
        assert total.unit == "MWh"
        assert total.value == pytest.approx(3)

    def test_add_non_quantity_raises(self):
        with pytest.raises(TypeError, match="Cannot add"):
            Quantity(1, "MWh") + 5
        with pytest.raises(TypeError):
            5 + Quantity(1, "MWh")


class TestContainerProtocol:
    def test_len_getitem_iter(self):
        q = Quantity([1, 2, 3], "MWh", "coal", reference_year=2020)
        assert len(q) == 3
        assert q[1].value == 2
        assert q[1].substance == "coal"
        assert q[1:].value.tolist() == [2, 3]
        assert [item.value.item() for item in q] == [1, 2, 3]
        assert q.shape == (3,)

    def test_scalar_is_not_iterable(self):
        with pytest.raises(TypeError):
            list(Quantity(1, "MWh"))
        with pytest.raises(TypeError):
            len(Quantity(1, "MWh"))

    def test_reductions(self):
        q = Quantity([[1, 2], [3, 4]], "MWh")
        assert q.sum().value == 10
        assert q.sum(axis=0).value.tolist() == [4, 6]
        assert q.mean().value == 2.5
        assert q.min().value == 1
        assert q.max().unit == "MWh"

    def test_truthiness(self):
        assert bool(Quantity(2, "MWh"))
        assert not bool(Quantity(0, "MWh"))
        with pytest.raises(ValueError):
            bool(Quantity([1, 2], "MWh"))

    def test_float_only_for_dimensionless(self):
        assert float(Quantity(1, "GWh") / Quantity(500, "MWh")) == pytest.approx(2)
        with pytest.raises(TypeError, match="dimensionless"):
            float(Quantity(1, "MWh"))


class TestFormatting:
    def test_str(self):
        assert str(Quantity(100, "MWh")) == "100.00 MWh"
        assert str(Quantity(100, "t", "coal")) == "100.00 t of coal"
        assert str(Quantity(0.00034, "t/kWh")) == "0.00034 t/kWh"
        assert str(Quantity(0.4, "")) == "0.40"
        assert str(Quantity(list(range(10)), "MW")) == "[0.00, ..., 9.00] MW (10 values)"

    def test_format_spec(self):
        assert f"{Quantity(360, 'GJ'):.1f}" == "360.0 GJ"
        assert f"{Quantity(1234567, 'MWh'):,.0f}" == "1,234,567 MWh"
        assert f"{Quantity([1, 2], 'MW'):.1f}" == "[1.0, 2.0] MW"

    def test_repr(self):
        assert repr(Quantity(100, "MWh")) == "Quantity(100.0, 'MWh')"
        q = Quantity([1, 2], "USD/kW", "coal", "HHV", 2020)
        assert repr(q) == "Quantity([1., 2.], 'USD/kW', 'coal', basis='HHV', reference_year=2020)"

    def test_repr_html_escapes(self):
        q = Quantity(1, "MWh", substance="<script>")
        assert "<script>" not in q._repr_html_()


class TestEquality:
    def test_equality_tolerates_conversion_roundoff(self):
        assert Quantity(1, "MWh") == Quantity(3.6, "GJ")
        assert Quantity(100, "kWh") == Quantity(0.1, "MWh")
        assert Quantity(1, "MWh") != Quantity(1.001, "MWh")

    def test_incompatible_units_are_not_equal(self):
        assert Quantity(1, "MWh") != Quantity(1, "t")
        assert not (Quantity(1, "MWh") == Quantity(1, "t"))

    def test_comparison_with_non_quantity(self):
        assert Quantity(1, "MWh") != 1
        with pytest.raises(TypeError):
            Quantity(1, "MWh") < 1

    def test_ordering_with_conversion(self):
        assert Quantity(1, "MWh") >= Quantity(3.6, "GJ")
        assert Quantity(1, "MWh") <= Quantity(3.6, "GJ")
        assert Quantity(1, "MWh") > Quantity(3.5, "GJ")

    def test_unhashable(self):
        with pytest.raises(TypeError):
            hash(Quantity(1, "MWh"))


class TestMetadataPropagation:
    def test_add_aligns_heating_value_basis(self):
        hhv = Quantity(100, "MWh", "natural_gas", basis="HHV")
        lhv = Quantity(90, "MWh", "natural_gas", basis="LHV")
        total = hhv + lhv
        assert total.basis == "HHV"
        assert total.value == pytest.approx(200)

    def test_add_unspecified_basis_treated_as_lhv(self):
        total = Quantity(90, "MWh", "natural_gas") + Quantity(100, "MWh", "natural_gas", basis="HHV")
        assert total.value == pytest.approx(180)

    def test_add_mass_quantities_with_different_basis_labels(self):
        total = Quantity(1, "t", "coal", basis="HHV") + Quantity(1, "t", "coal")
        assert total.value == pytest.approx(2)

    def test_substance_mismatch_warns(self):
        with pytest.warns(EnergyUnitsWarning, match="different substances"):
            total = Quantity(1, "MWh", "coal") + Quantity(1, "MWh", "natural_gas")
        assert total.substance is None

    def test_warning_points_to_caller(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Quantity(1, "MWh", "coal") + Quantity(1, "MWh", "natural_gas")
        assert caught[0].filename == __file__

    def test_reference_year_from_either_operand(self):
        assert (Quantity(2, "MW") * Quantity(5, "USD/kW", reference_year=2020)).reference_year == 2020
        assert (Quantity(5, "USD", reference_year=2020) / Quantity(2, "MWh")).reference_year == 2020
        mixed = Quantity(5, "USD", reference_year=2020) / Quantity(2, "USD/MWh", reference_year=2021)
        assert mixed.reference_year is None


class TestSerialization:
    def test_pickle_and_copy(self):
        q = Quantity([1, 2], "MWh", "coal", "HHV", 2020)
        for clone in (pickle.loads(pickle.dumps(q)), copy.deepcopy(q), q.copy(), q.to()):
            assert clone == q
            assert (clone.unit, clone.substance, clone.basis, clone.reference_year) == (
                "MWh",
                "coal",
                "HHV",
                2020,
            )
            assert clone.value is not q.value

    def test_slots_prevent_typos(self):
        with pytest.raises(AttributeError):
            Quantity(1, "MWh").units = "GJ"


class TestInputValidation:
    def test_pandas_nullable_values(self):
        pd = pytest.importorskip("pandas")
        q = Quantity(pd.array([1, None], dtype="Int64"), "MWh")
        assert q.value[0] == 1 and np.isnan(q.value[1])

    def test_quantity_as_value_rejected(self):
        with pytest.raises(TypeError, match="Cannot use a Quantity"):
            Quantity(Quantity(1, "MWh"), "MWh")

    def test_substance_must_be_string(self):
        with pytest.raises(TypeError):
            Quantity(1, "t", substance=5)
