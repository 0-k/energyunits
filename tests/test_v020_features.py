"""Tests for v0.2.0 features: caching, discovery, constants, warnings, repr."""

import warnings

import pytest

from energyunits import Quantity, units
from energyunits.registry import registry
from energyunits.substance import substance_registry


class TestConversionCaching:
    """Test that lru_cache on registry methods works correctly."""

    def test_cached_dimension_lookup(self):
        """Repeated dimension lookups should hit cache."""
        # Call twice — second should be cached
        dim1 = registry.get_dimension("MWh")
        dim2 = registry.get_dimension("MWh")
        assert dim1 == dim2 == "ENERGY"

    def test_cached_conversion_factor(self):
        """Repeated conversion factor lookups should hit cache."""
        f1 = registry.get_conversion_factor("MWh", "GJ")
        f2 = registry.get_conversion_factor("MWh", "GJ")
        assert f1 == f2

    def test_cache_info_available(self):
        """Cache info should be accessible."""
        # Clear and call
        registry.get_dimension.cache_clear()
        registry.get_dimension("kWh")
        info = registry.get_dimension.cache_info()
        assert info.misses >= 1


class TestUnitDiscovery:
    """Test unit and substance discovery methods."""

    def test_list_all_units(self):
        units_list = Quantity.list_units()
        assert "MWh" in units_list
        assert "kg" in units_list
        assert "USD" in units_list
        assert len(units_list) > 30

    def test_list_units_by_dimension(self):
        energy_units = Quantity.list_units("ENERGY")
        assert "MWh" in energy_units
        assert "GJ" in energy_units
        assert "kg" not in energy_units

        power_units = Quantity.list_units("POWER")
        assert "MW" in power_units
        assert "MWh" not in power_units

    def test_list_dimensions(self):
        dims = Quantity.list_dimensions()
        assert "ENERGY" in dims
        assert "POWER" in dims
        assert "MASS" in dims
        assert "CURRENCY" in dims

    def test_list_all_substances(self):
        subs = Quantity.list_substances()
        assert "coal" in subs
        assert "natural_gas" in subs
        assert "hydrogen" in subs
        assert len(subs) > 15

    def test_list_substances_with_property(self):
        fuels = Quantity.list_substances(has_property="hhv")
        assert "coal" in fuels
        assert "natural_gas" in fuels
        # CO2 is a combustion product, not a fuel with heating value
        assert "CO2" not in fuels

        dense = Quantity.list_substances(has_property="density")
        assert "coal" in dense

    def test_list_currencies(self):
        currencies = Quantity.list_currencies()
        assert "USD" in currencies
        assert "EUR" in currencies
        assert len(currencies) >= 5

    def test_registry_list_units(self):
        all_units = registry.list_units()
        energy = registry.list_units("ENERGY")
        assert len(all_units) > len(energy)
        assert all(u in all_units for u in energy)

    def test_registry_list_dimensions(self):
        dims = registry.list_dimensions()
        assert isinstance(dims, list)
        assert len(dims) >= 5

    def test_substance_get_properties(self):
        props = substance_registry.get_properties("coal")
        assert "hhv" in props
        assert "lhv" in props
        assert "density" in props
        assert "carbon_content" in props


class TestUnitConstants:
    """Test the units constants module."""

    def test_energy_constants(self):
        assert units.MWh == "MWh"
        assert units.GJ == "GJ"
        assert units.kWh == "kWh"
        assert units.TWh == "TWh"

    def test_power_constants(self):
        assert units.MW == "MW"
        assert units.kW == "kW"
        assert units.GW == "GW"

    def test_mass_constants(self):
        assert units.kg == "kg"
        assert units.t == "t"

    def test_currency_constants(self):
        assert units.USD == "USD"
        assert units.EUR == "EUR"

    def test_constants_work_with_quantity(self):
        energy = Quantity(100, units.MWh)
        assert energy.unit == "MWh"
        result = energy.to(units.GJ)
        assert result.unit == "GJ"

    def test_constants_work_in_arithmetic(self):
        power = Quantity(50, units.MW)
        time = Quantity(10, units.h)
        energy = power * time
        assert energy.unit == "MWh"


class TestSubstanceMismatchWarning:
    """Test that arithmetic with different substances warns."""

    def test_add_different_substances_warns(self):
        coal = Quantity(100, "MWh", substance="coal")
        gas = Quantity(50, "MWh", substance="natural_gas")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = coal + gas
            assert len(w) == 1
            assert "different substances" in str(w[0].message)
            assert result.substance is None

    def test_add_same_substance_no_warning(self):
        a = Quantity(100, "MWh", substance="coal")
        b = Quantity(50, "MWh", substance="coal")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = a + b
            substance_warnings = [
                x for x in w if "different substances" in str(x.message)
            ]
            assert len(substance_warnings) == 0
            assert result.substance == "coal"

    def test_sub_different_substances_warns(self):
        coal = Quantity(100, "MWh", substance="coal")
        gas = Quantity(50, "MWh", substance="natural_gas")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = coal - gas
            assert len(w) == 1
            assert "different substances" in str(w[0].message)
            assert result.substance is None

    def test_sub_same_substance_no_warning(self):
        a = Quantity(100, "MWh", substance="coal")
        b = Quantity(30, "MWh", substance="coal")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = a - b
            substance_warnings = [
                x for x in w if "different substances" in str(x.message)
            ]
            assert len(substance_warnings) == 0
            assert result.substance == "coal"


class TestSubtraction:
    """Test the new __sub__ operator."""

    def test_basic_subtraction(self):
        a = Quantity(100, "MWh")
        b = Quantity(30, "MWh")
        result = a - b
        assert float(result.value) == pytest.approx(70.0)
        assert result.unit == "MWh"

    def test_subtraction_with_conversion(self):
        a = Quantity(1, "MWh")
        b = Quantity(1000, "kWh")
        result = a - b
        assert float(result.value) == pytest.approx(0.0)

    def test_subtraction_preserves_metadata(self):
        a = Quantity(100, "MWh", substance="coal", basis="LHV")
        b = Quantity(30, "MWh", substance="coal", basis="LHV")
        result = a - b
        assert result.substance == "coal"
        assert result.basis == "LHV"

    def test_subtraction_type_error(self):
        a = Quantity(100, "MWh")
        with pytest.raises(TypeError):
            a - 50


class TestJupyterRepr:
    """Test _repr_html_ for Jupyter display."""

    def test_scalar_repr_html(self):
        q = Quantity(100, "MWh")
        html = q._repr_html_()
        assert "100" in html
        assert "MWh" in html

    def test_repr_html_with_substance(self):
        q = Quantity(100, "MWh", substance="coal")
        html = q._repr_html_()
        assert "coal" in html

    def test_repr_html_with_basis(self):
        q = Quantity(100, "MWh", substance="coal", basis="LHV")
        html = q._repr_html_()
        assert "LHV" in html

    def test_repr_html_with_reference_year(self):
        q = Quantity(100, "USD/kW", reference_year=2020)
        html = q._repr_html_()
        assert "2020" in html

    def test_repr_html_array(self):
        q = Quantity([1, 2, 3], "MWh")
        html = q._repr_html_()
        assert "MWh" in html


class TestImprovedErrorMessages:
    """Test that error messages include suggestions."""

    def test_unknown_unit_suggests_close_matches(self):
        with pytest.raises(ValueError, match="Did you mean"):
            Quantity(100, "Mwh")  # lowercase w

    def test_unknown_unit_lists_all_when_no_match(self):
        with pytest.raises(ValueError, match="Available units"):
            Quantity(100, "zzz_no_match")

    def test_unknown_substance_suggests_close_matches(self):
        with pytest.raises(ValueError, match="Did you mean"):
            substance_registry["coall"]  # typo

    def test_cross_dimension_hints_substance(self):
        energy = Quantity(100, "MWh")
        with pytest.raises(ValueError, match="[Ss]ubstance"):
            energy.to("kg")

    def test_substance_conversion_usage_example(self):
        mass = Quantity(100, "t")
        with pytest.raises(ValueError, match="Example"):
            mass.to(substance="CO2")
