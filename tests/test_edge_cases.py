"""
Edge case tests for the EnergyUnits library.

These tests focus on extreme values, boundary conditions, and unusual scenarios.
"""

import numpy as np
import pytest

from energyunits import Quantity


class TestExtremeValues:
    def test_very_large_values(self):
        """Test conversions with very large values."""
        # Large energy
        huge_energy = Quantity(1e20, "J")
        huge_mwh = huge_energy.to("MWh")
        assert huge_mwh.value == pytest.approx(2.77778e10, rel=1e-5)

        # Large power
        huge_power = Quantity(1e6, "GW")
        huge_tw = huge_power.to("TW")
        assert huge_tw.value == pytest.approx(1e3, rel=1e-5)

        # Large mass
        huge_mass = Quantity(1e12, "kg")
        huge_mt = huge_mass.to("Mt")
        assert huge_mt.value == pytest.approx(1e3, rel=1e-5)

    def test_very_small_values(self):
        """Test conversions with very small values."""
        # Small energy
        tiny_energy = Quantity(1e-9, "MWh")
        tiny_j = tiny_energy.to("J")
        assert tiny_j.value == pytest.approx(3.6)

        # Small power
        tiny_power = Quantity(1e-9, "GW")  # 1 nanowatt
        tiny_w = tiny_power.to("W")
        assert tiny_w.value == pytest.approx(1.0)

        # Small mass
        tiny_mass = Quantity(1e-6, "t")  # 1 milligram
        tiny_g = tiny_mass.to("g")
        assert tiny_g.value == pytest.approx(1.0)

    def test_zero_values(self):
        """Test conversions with zero values."""
        # Zero energy
        zero_energy = Quantity(0, "MWh")
        zero_gj = zero_energy.to("GJ")
        assert zero_gj.value == 0
        assert zero_gj.unit == "GJ"

        # Zero power
        zero_power = Quantity(0, "MW")
        zero_kw = zero_power.to("kW")
        assert zero_kw.value == 0
        assert zero_kw.unit == "kW"

        # Zero time
        zero_time = Quantity(0, "h")
        zero_min = zero_time.to("min")
        assert zero_min.value == 0
        assert zero_min.unit == "min"

    def test_mixed_array_types(self):
        """Test with mixed array types."""
        # Integer and float mix
        mixed_array = [100, 200.5, 300, 400.25]
        energy = Quantity(mixed_array, "MWh")
        energy_gj = energy.to("GJ")
        assert np.allclose(energy_gj.value, np.array([360, 721.8, 1080, 1440.9]))

        # With nan and inf
        special_array = [100, np.nan, 300, np.inf]
        energy = Quantity(special_array, "MWh")
        energy_gj = energy.to("GJ")
        assert np.isnan(energy_gj.value[1])
        assert np.isinf(energy_gj.value[3])
        assert energy_gj.value[0] == pytest.approx(360)
        assert energy_gj.value[2] == pytest.approx(1080)

    def test_array_broadcasting(self):
        """Test array broadcasting in operations."""
        # Adding scalar to array
        array_energy = Quantity([100, 200, 300], "MWh")
        scalar_energy = Quantity(50, "MWh")
        result = array_energy + scalar_energy
        assert np.all(result.value == np.array([150, 250, 350]))

        # Adding arrays of different sizes (numpy broadcasting)
        array1 = Quantity([100, 200, 300], "MWh")
        array2 = Quantity([10], "MWh")
        result = array1 + array2
        assert np.all(result.value == np.array([110, 210, 310]))

        # Adding arrays of different sizes (numpy broadcasting)
        array1 = Quantity([100, 200, 300], "MWh")
        array2 = Quantity([1], "GWh")
        result = array1 + array2
        assert np.all(result.value == np.array([1100, 1200, 1300]))


class TestUnusualScenarios:
    def test_compound_unit_operations(self):
        """Test operations with compound units."""
        # Conversion between related compound units
        price1 = Quantity(50, "USD/MWh")
        price2 = price1.to("USD/GJ")
        assert price2.value == pytest.approx(50 / 3.6)  # 1 MWh = 3.6 GJ

        # Compound unit multiplication - now works!
        energy_density = Quantity(10, "MWh/t")
        mass = Quantity(5, "t")

        # This should now work and return 50 MWh
        result = energy_density * mass
        assert result.value == pytest.approx(50)
        assert result.unit == "MWh"  # USD/t * t = USD

    def test_multistep_conversions(self):
        """Test conversions that require multiple steps."""
        # Energy → Power → Energy again using new multiplication/division
        energy1 = Quantity(240, "MWh")
        time = Quantity(12, "h")
        power = energy1 / time  # 20 MW
        energy2 = power * time  # 240 MWh again

        assert power.unit == "MW"
        assert energy2.unit == "MWh"
        assert power.value == pytest.approx(20)
        assert energy2.value == pytest.approx(240)

    def test_alternative_units(self):
        """Test less common units and conversions."""
        # British thermal units
        energy_mmbtu = Quantity(1, "MMBTU")
        energy_mwh = energy_mmbtu.to("MWh")
        assert energy_mwh.value == pytest.approx(0.293071)

        # Oil barrels
        oil = Quantity(1000, "barrel", "oil")
        oil_m3 = oil.to("m3")
        assert oil_m3.value == pytest.approx(159)  # 1 barrel = 159 liters = 0.159 m3

    def test_substance_mixtures(self):
        """Test handling substance mixtures and edge cases."""
        # Adding different substances clears the substance attribute
        coal = Quantity(100, "t", "coal")
        gas = Quantity(100, "t", "natural_gas")
        mixture = coal + gas

        assert mixture.value == pytest.approx(200)
        assert mixture.unit == "t"
        assert mixture.substance is None  # Substance should be cleared

        # Energy content calculations require substance
        with pytest.raises(ValueError):
            energy = mixture.to("MWh")
