"""Substance-aware conversions, heating value bases and combustion products."""

import numpy as np
import pytest

from energyunits import EnergyUnitsError, IncompatibleUnitsError, MissingDataError, Quantity
from energyunits.substance import substance_registry


class TestIPCCEmissionFactors:
    """CO2 from stoichiometry reproduces the IPCC 2006 default emission factors (LHV basis)."""

    @pytest.mark.parametrize(
        "fuel, kg_co2_per_gj",
        [
            ("coal", 95.0),
            ("lignite", 101.0),
            ("bituminous", 94.6),
            ("anthracite", 98.3),
            ("natural_gas", 56.1),
            ("crude_oil", 73.3),
            ("fuel_oil", 77.4),
            ("diesel", 74.1),
            ("gasoline", 69.3),
        ],
    )
    def test_emission_factor(self, fuel, kg_co2_per_gj):
        co2 = Quantity(1, "GJ", fuel).to("kg", substance="CO2")
        assert co2.value == pytest.approx(kg_co2_per_gj, rel=1e-3)

    def test_natural_gas_power_sector_factor(self):
        # The well-known ~0.202 t CO2 per MWh of gas (LHV)
        assert Quantity(1, "MWh", "natural_gas").to("t", substance="CO2").value == pytest.approx(
            0.202, rel=1e-3
        )

    def test_biomass_reports_physical_biogenic_co2(self):
        props = substance_registry["wood_pellets"]
        assert props["biogenic"] is True
        assert props["carbon_intensity"] == 0
        co2 = Quantity(1, "t", "wood_pellets").to("t", substance="CO2")
        assert co2.value == pytest.approx(0.5 * 44 / 12)


class TestHeatingValueBasis:
    def test_basis_selects_heating_value_for_mass(self):
        """Regression: HHV used to rescale the mass before converting it."""
        hhv = Quantity(1, "t", "coal").to("MWh", basis="HHV")
        lhv = Quantity(1, "t", "coal").to("MWh", basis="LHV")
        assert hhv.value == pytest.approx(26.0 / 3.6)
        assert lhv.value == pytest.approx(25.0 / 3.6)
        assert hhv.basis == "HHV"

    def test_mass_basis_is_a_label(self):
        coal = Quantity(1, "t", "coal").to(basis="HHV")
        assert coal.value == pytest.approx(1)
        assert coal.basis == "HHV"

    def test_energy_basis_conversion(self):
        gas = Quantity(100, "MWh", "natural_gas", basis="HHV")
        assert gas.to(basis="LHV").value == pytest.approx(100 * 49.5 / 55.0)
        assert gas.to(basis="LHV").to(basis="HHV").value == pytest.approx(100)

    def test_price_basis_conversion_is_inverse(self):
        """A price per MWh(HHV) is lower than the same price per MWh(LHV)."""
        price = Quantity(30, "EUR/MWh", "natural_gas", basis="HHV")
        assert price.to(basis="LHV").value == pytest.approx(30 * 55.0 / 49.5)

    def test_us_gas_price_to_european_convention(self):
        """10 USD/MMBtu (HHV, US convention) expressed in USD/MWh on LHV basis."""
        price = Quantity(10, "USD/MMBTU", "natural_gas", basis="HHV")
        converted = price.to("USD/MWh", basis="LHV")
        assert converted.value == pytest.approx(10 / 0.29307107 * 55.0 / 49.5)

    def test_mass_energy_roundtrip_independent_of_basis(self):
        energy = Quantity(100, "MWh", "coal", basis="HHV")
        assert energy.to("t").value == pytest.approx(energy.to(basis="LHV").to("t").value)

    def test_power_basis(self):
        assert Quantity(100, "MW", "natural_gas", basis="HHV").to(basis="LHV").value == pytest.approx(90)

    def test_basis_requires_substance(self):
        with pytest.raises(EnergyUnitsError, match="Substance must be specified"):
            Quantity(1, "MWh").to(basis="HHV")


class TestCompoundSubstanceConversions:
    def test_fuel_price_per_mass_to_per_energy(self):
        price = Quantity(100, "USD/t", "coal")
        assert price.to("USD/MWh").value == pytest.approx(100 / (25.0 / 3.6))
        assert price.to("USD/GJ").value == pytest.approx(100 / 25.0)

    def test_fuel_price_per_volume(self):
        price = Quantity(1.5, "EUR/L", "diesel")
        # 1 L = 0.84 kg = 0.84 * 42.8 MJ; 3600 MJ per MWh
        assert price.to("EUR/MWh").value == pytest.approx(1.5 / (0.84 * 42.8 / 3600))

    def test_thermal_power_to_fuel_flow(self):
        assert Quantity(100, "MW", "natural_gas").to("t/h").value == pytest.approx(100 * 3.6 / 49.5)
        assert Quantity(1, "t/h", "coal").to("MW").value == pytest.approx(25.0 / 3.6)

    def test_heating_value_unit(self):
        assert Quantity(1, "t", "coal").to("GJ").value == pytest.approx(25.0)

    def test_requires_substance(self):
        with pytest.raises(IncompatibleUnitsError, match="Substance required"):
            Quantity(100, "USD/t").to("USD/MWh")

    def test_missing_density(self):
        with pytest.raises(MissingDataError, match="density"):
            Quantity(1, "t", "hydro").to("m3")


class TestCombustionProducts:
    def test_array_shape_preserved_for_zero_emission_sources(self):
        """Regression: wind/solar used to return a scalar 0."""
        result = Quantity([100, 200, 300], "MWh", "wind").to("t", substance="CO2")
        assert result.value.shape == (3,)
        assert np.all(result.value == 0)

    def test_mass_unit_preserved(self):
        co2 = Quantity(1000, "kg", "coal").to(substance="CO2")
        assert co2.unit == "kg"
        assert co2.value == pytest.approx(1000 * 0.6477 * 44 / 12)

    def test_energy_source_gives_tonnes(self):
        co2 = Quantity(1, "MWh", "coal").to(substance="CO2")
        assert co2.unit == "t"
        assert co2.value == pytest.approx(95.0 * 3.6 / 1000, rel=1e-3)

    def test_emission_rate_from_thermal_power(self):
        rate = Quantity(100, "MW", "natural_gas").to("t/h", substance="CO2")
        assert rate.unit == "t/h"
        assert rate.substance == "CO2"
        assert rate.value == pytest.approx(100 * 0.0561 * 3.6, rel=1e-3)

    def test_annual_fuel_use_to_annual_emissions(self):
        assert Quantity(2, "Mt/a", "lignite").to("Mt/a", substance="CO2").value == pytest.approx(
            2 * 0.3856 * 44 / 12
        )

    def test_hhv_fuel_energy(self):
        hhv = Quantity(100, "MWh", "natural_gas", basis="HHV").to("t", substance="CO2")
        lhv = Quantity(90, "MWh", "natural_gas").to("t", substance="CO2")
        assert hhv.value == pytest.approx(lhv.value)
        assert hhv.basis is None

    def test_reference_year_preserved(self):
        result = Quantity(100, "MWh", "coal", reference_year=2020).to(substance="CO2")
        assert result.reference_year == 2020

    def test_unsupported_product(self):
        with pytest.raises(EnergyUnitsError, match="combustion products"):
            Quantity(1, "t", "coal").to(substance="NOx")

    def test_product_of_unit_without_amount(self):
        with pytest.raises(IncompatibleUnitsError, match="amount of fuel"):
            Quantity(1, "USD", "coal").to(substance="CO2")

    def test_calculate_combustion_product_helper(self):
        co2 = substance_registry.calculate_combustion_product(Quantity(1000, "kg", "coal"), "CO2")
        assert co2.unit == "t"
        assert co2.value == pytest.approx(0.6477 * 44 / 12)


class TestSubstanceRegistry:
    def test_custom_substance_with_partial_properties(self, tmp_path):
        path = tmp_path / "fuels.json"
        path.write_text('{"biogas": {"name": "Biogas", "lhv": 20.0, "hhv": 22.0}}')
        substance_registry.load_substances(str(path))
        assert Quantity(1, "t", "biogas").to("GJ").value == pytest.approx(20.0)
        with pytest.raises(MissingDataError, match="carbon content"):
            Quantity(1, "t", "biogas").to(substance="CO2")

    def test_invalid_property_type(self, tmp_path):
        path = tmp_path / "fuels.json"
        path.write_text('{"bad": {"lhv": "twenty"}}')
        with pytest.raises(ValueError, match="must be a number"):
            substance_registry.load_substances(str(path))

    def test_reset(self, tmp_path):
        path = tmp_path / "fuels.json"
        path.write_text('{"biogas": {"lhv": 20.0}}')
        substance_registry.load_substances(str(path))
        substance_registry.reset()
        assert "biogas" not in substance_registry
