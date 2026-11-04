"""Area units and area-specific quantities (irradiance, energy intensity, yields)."""

import pytest

from energyunits import IncompatibleUnitsError, Quantity
from energyunits.registry import registry


class TestAreaUnits:
    @pytest.mark.parametrize(
        "unit, m2",
        [("m2", 1.0), ("km2", 1e6), ("ha", 1e4), ("acre", 4046.8564224), ("ft2", 0.09290304)],
    )
    def test_definitions(self, unit, m2):
        assert registry.get_conversion_factor(unit, "m2") == pytest.approx(m2, rel=1e-12)

    def test_dimension(self):
        assert Quantity(1, "ha").dimension == "AREA"
        assert "AREA" in Quantity.list_dimensions()
        assert Quantity.list_units("AREA") == ["acre", "ft2", "ha", "km2", "m2"]
        assert Quantity(1, "kWh/m2").dimension == "ENERGY_PER_AREA"

    def test_common_conversions(self):
        assert Quantity(1, "km2").to("ha").value == pytest.approx(100)
        assert Quantity(1, "acre").to("ha").value == pytest.approx(0.40468564224)
        assert Quantity(1000, "ft2").to("m2").value == pytest.approx(92.90304)

    def test_area_is_not_volume(self):
        with pytest.raises(IncompatibleUnitsError, match="Cannot convert"):
            Quantity(1, "m2").to("m3")


class TestAreaSpecificQuantities:
    def test_pv_irradiance(self):
        power = Quantity(1000, "W/m2") * Quantity(2, "m2")
        assert power.unit == "W"
        assert power.value == pytest.approx(2000)

    def test_pv_annual_yield(self):
        irradiation = Quantity(1700, "kWh/m2/a")
        module_area = Quantity(20, "m2")
        generation = irradiation * module_area * 0.2
        assert generation.unit == "kWh/a"
        assert generation.value == pytest.approx(6800)

    def test_building_energy_intensity(self):
        demand = Quantity(120, "kWh/m2/a") * Quantity(500, "m2")
        assert demand.to("MWh/a").value == pytest.approx(60)

    def test_us_energy_use_intensity(self):
        # 1 kBtu/ft2 = 1055055.85262 J / 0.09290304 m2 = 3.1546 kWh/m2
        assert Quantity(1, "kBTU/ft2").to("kWh/m2").value == pytest.approx(3.154590745, rel=1e-9)
        assert Quantity(1, "kBTU").to("BTU").value == pytest.approx(1000)

    def test_power_density(self):
        # 1 W/m2 = 1 MW/km2
        assert Quantity(1, "W/m2").to("MW/km2").value == pytest.approx(1)
        assert (Quantity(5, "MW/km2") * Quantity(10, "km2")).to("MW").value == pytest.approx(50)

    def test_biomass_yield(self):
        harvest = Quantity(10, "t/ha", "wood_chips") * Quantity(200, "ha")
        assert harvest.unit == "t"
        assert harvest.substance == "wood_chips"
        assert harvest.to("MWh").value == pytest.approx(2000 * 12.2 / 3.6)

    def test_land_use_per_energy(self):
        # 2 ha per GWh/a = 20 m2 per MWh/a
        land_use = Quantity(2, "ha") / Quantity(1, "GWh/a")
        assert land_use.unit == "ha·a/GWh"
        assert land_use.to("m2·a/MWh").value == pytest.approx(20)
