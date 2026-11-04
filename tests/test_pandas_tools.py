"""Tests for the pandas helpers that go beyond plain unit conversion."""

import warnings

import pytest

pd = pytest.importorskip("pandas")

from energyunits import Quantity  # noqa: E402
from energyunits.pandas_tools import (  # noqa: E402
    add_units,
    convert_units,
    from_quantity,
    get_units,
    to_quantity,
)


def test_add_units_validates_unit():
    with pytest.raises(ValueError, match="Unknown unit"):
        add_units(pd.DataFrame({"x": [1]}), "x", "MegaWatt")


def test_metadata_roundtrip():
    df = add_units(pd.DataFrame({"fuel": [10, 20]}), "fuel", "t", substance="coal", basis="hhv")
    assert get_units(df, "fuel") == "t"
    assert df.attrs["fuel_basis"] == "HHV"
    q = to_quantity(df, "fuel")
    assert q.substance == "coal"
    assert q.basis == "HHV"
    assert q.value.tolist() == [10.0, 20.0]


def test_substance_aware_column_conversion():
    df = add_units(pd.DataFrame({"fuel": [1.0, 2.0]}), "fuel", "t", substance="coal")
    converted = convert_units(df, "fuel", "MWh")
    assert converted["fuel"].tolist() == pytest.approx([25.8 / 3.6, 51.6 / 3.6])
    assert converted.attrs["fuel_unit"] == "MWh"
    assert converted.attrs["fuel_substance"] == "coal"


def test_currency_and_inflation_column_conversion():
    df = add_units(pd.DataFrame({"price": [50.0]}), "price", "EUR/MWh", reference_year=2015)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        converted = convert_units(df, "price", "USD/MWh", reference_year=2024)
        expected = Quantity(50, "EUR/MWh", reference_year=2015).to("USD/MWh", reference_year=2024)
    assert converted["price"].iloc[0] == pytest.approx(expected.value)
    assert converted.attrs["price_reference_year"] == 2024


def test_from_quantity_preserves_index():
    df = pd.DataFrame({"x": [1.0, 2.0]}, index=["a", "b"])
    result = from_quantity(df, "co2", Quantity([0.5, 0.7], "t", "CO2"))
    assert list(result.index) == ["a", "b"]
    assert result.attrs["co2_unit"] == "t"
    assert result.attrs["co2_substance"] == "CO2"
    assert "x_unit" not in result.attrs


def test_add_units_clears_stale_metadata():
    df = add_units(pd.DataFrame({"x": [1.0]}), "x", "t", substance="coal")
    df = add_units(df, "x", "MWh")
    assert "x_substance" not in df.attrs


def test_to_quantity_requires_units():
    with pytest.raises(ValueError, match="No unit information"):
        to_quantity(pd.DataFrame({"x": [1.0]}), "x")


def test_lazy_attribute_access():
    import energyunits

    assert energyunits.pandas_tools.add_units is add_units
