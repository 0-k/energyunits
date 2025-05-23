"""
Test implementations for the EnergyUnits library.

These tests correspond to the examples in the API Examples document
(see /examples/development.py) and can be used for test-driven development.
"""

import numpy as np
import pandas as pd
import pytest


class TestBasicUnitConversions:
    def test_energy_conversions(self):
        """Test basic energy unit conversions."""
        from energyunits import Quantity

        # Energy conversions
        energy = Quantity(100, "MWh")
        energy_gj = energy.to("GJ")
        energy_kwh = energy.to("kWh")

        assert energy_gj.value == pytest.approx(360)
        assert energy_gj.unit == "GJ"
        assert energy_kwh.value == pytest.approx(100000)
        assert energy_kwh.unit == "kWh"

    def test_power_conversions(self):
        """Test power unit conversions."""
        from energyunits import Quantity

        # Power conversions
        power = Quantity(50, "MW")
        power_kw = power.to("kW")
        power_gw = power.to("GW")

        assert power_kw.value == pytest.approx(50000)
        assert power_kw.unit == "kW"
        assert power_gw.value == pytest.approx(0.05)
        assert power_gw.unit == "GW"

    def test_array_conversions(self):
        """Test conversions with array values."""
        from energyunits import Quantity

        # Array conversions
        energy_values = [100, 200, 300]
        energy_array = Quantity(energy_values, "MWh")
        energy_array_gj = energy_array.to("GJ")

        assert np.allclose(energy_array_gj.value, [360, 720, 1080])
        assert energy_array_gj.unit == "GJ"


class TestPowerEnergyConversions:
    def test_power_to_energy(self):
        """Test converting power to energy."""
        from energyunits import Quantity

        # Power to energy
        power = Quantity(100, "MW")
        energy_1h = power.for_duration(hours=1)
        energy_24h = power.for_duration(hours=24)
        energy_1yr = power.for_duration(hours=8760)

        assert energy_1h.value == pytest.approx(100)
        assert energy_1h.unit == "MWh"
        assert energy_24h.value == pytest.approx(2400)
        assert energy_24h.unit == "MWh"
        assert energy_1yr.value == pytest.approx(876000)
        assert energy_1yr.unit == "MWh"

    def test_energy_to_average_power(self):
        """Test calculating average power from energy."""
        from energyunits import Quantity

        # Energy to power
        energy = Quantity(240, "MWh")
        avg_power = energy.average_power(hours=12)

        assert avg_power.value == pytest.approx(20)
        assert avg_power.unit == "MW"


class TestSubstances:
    def test_fuel_quantities(self):
        """Test creating quantities with substances."""
        from energyunits import Quantity

        # Fuel quantities
        coal = Quantity(1000, "t", "coal")
        natural_gas = Quantity(100000, "m3", "natural_gas")
        oil = Quantity(500, "barrel", "oil")

        assert coal.value == 1000
        assert coal.unit == "t"
        assert coal.substance == "coal"

        assert natural_gas.value == 100000
        assert natural_gas.unit == "m3"
        assert natural_gas.substance == "natural_gas"

        assert oil.value == 500
        assert oil.unit == "barrel"
        assert oil.substance == "oil"

    def test_substance_unit_conversions(self):
        """Test converting between units for a substance."""
        from energyunits import Quantity

        # Mass to volume conversion for a substance
        lng_mass = Quantity(1000, "t", "lng")
        lng_volume = lng_mass.to("m3")

        # Assuming a reasonable density for LNG
        assert lng_volume.value > 0  # Exact value depends on density
        assert lng_volume.unit == "m3"
        assert lng_volume.substance == "lng"

        # Carbon emissions unit conversion
        co2 = Quantity(50000, "t", "CO2")
        co2_kg = co2.to("kg")

        assert co2_kg.value == pytest.approx(50000000)
        assert co2_kg.unit == "kg"
        assert co2_kg.substance == "CO2"


class TestHeatingValues:
    def test_energy_content(self):
        """Test getting energy content of fuels."""
        from energyunits import Quantity

        # Energy content
        energy_hhv = Quantity(1000, "t", "coal", basis="HHV").to("MWh")
        energy_lhv = Quantity(1000, "t", "coal", basis="LHV").to("MWh")
        energy_to_lhv = energy_hhv.to(basis="LHV")

        # HHV should be higher than LHV
        assert energy_hhv.value > energy_lhv.value
        assert energy_hhv.unit == "MWh"
        assert energy_lhv.unit == "MWh"
        assert energy_lhv.value == energy_to_lhv.value

        # Typical value for coal is ~8.1 MWh/ton (HHV)
        assert energy_hhv.value == pytest.approx(8140, rel=0.2)

    def test_hhv_lhv_conversion(self):
        """Test converting between HHV and LHV."""
        from energyunits import Quantity

        # HHV to LHV conversion
        gas_energy_hhv = Quantity(1000, "MWh", substance="natural_gas", basis="HHV")
        gas_energy_lhv = gas_energy_hhv.to(basis="LHV")

        # LHV should be lower (typically ~10% for natural gas)
        assert gas_energy_lhv.value < gas_energy_hhv.value
        assert gas_energy_lhv.value == pytest.approx(
            0.9 * gas_energy_hhv.value, rel=0.1
        )

    def test_co2_emissions_conversion(self):
        """Test converting to CO2 emissions using unified .to() method."""
        from energyunits import Quantity

        # Test emissions calculation from fuel mass
        coal = Quantity(1000, "t", "coal")
        emissions = coal.to("t", substance="CO2")

        assert emissions.unit == "t"
        assert emissions.substance == "CO2"
        assert emissions.value > 0

        # Test emissions calculation from energy
        energy = Quantity(1000, "MWh", "natural_gas")
        emissions_from_energy = energy.to("t", substance="CO2")

        assert emissions_from_energy.unit == "t"
        assert emissions_from_energy.substance == "CO2"
        assert emissions_from_energy.value > 0

        # Test renewables have zero emissions
        wind_energy = Quantity(1000, "MWh", "wind")
        wind_emissions = wind_energy.to("t", substance="CO2")

        assert wind_emissions.value == pytest.approx(0)
        assert wind_emissions.substance == "CO2"


class TestCompoundUnits:
    def test_energy_prices(self):
        """Test working with energy prices."""
        from energyunits import Quantity

        # Energy prices
        electricity_price = Quantity(50, "USD/MWh")
        gas_price = Quantity(10, "USD/MMBTU")

        # Check units and values
        assert electricity_price.unit == "USD/MWh"
        assert electricity_price.value == 50
        assert gas_price.unit == "USD/MMBTU"
        assert gas_price.value == 10

        # Convert between price units
        gas_price_mwh = gas_price.to("USD/MWh")

        assert gas_price_mwh.unit == "USD/MWh"
        # 1 MMBTU ≈ 0.293 MWh
        assert gas_price_mwh.value == pytest.approx(10 / 0.293, rel=0.1)

    def test_energy_intensity(self):
        """Test energy intensity units."""
        from energyunits import Quantity

        # Energy intensity
        steel_intensity = Quantity(4.5, "MWh/t")
        aluminum_intensity = Quantity(15, "MWh/t")

        assert steel_intensity.unit == "MWh/t"
        assert steel_intensity.value == 4.5
        assert aluminum_intensity.unit == "MWh/t"
        assert aluminum_intensity.value == 15


class TestMathOperations:
    def test_addition(self):
        """Test addition of compatible quantities."""
        from energyunits import Quantity

        # Addition
        energy1 = Quantity(100, "MWh")
        energy2 = Quantity(500, "GJ")
        total = energy1 + energy2

        # 500 GJ = 138.9 MWh
        assert total.value == pytest.approx(100 + 138.9, rel=0.01)
        assert total.unit == "MWh"  # Should keep the unit of the first quantity

    def test_scalar_multiplication(self):
        """Test multiplication by scalars."""
        from energyunits import Quantity

        # Multiplication
        capacity = Quantity(50, "MW")
        doubled = capacity * 2

        assert doubled.value == pytest.approx(100)
        assert doubled.unit == "MW"

    def test_quantity_division(self):
        """Test division between quantities."""
        from energyunits import Quantity

        # Division
        energy = Quantity(1000, "MWh")
        time = Quantity(10, "h")
        power = energy / time

        assert power.value == pytest.approx(100)
        assert power.unit == "MW"

    def test_comparisons(self):
        """Test comparison operations between quantities."""
        from energyunits import Quantity

        # Comparisons
        energy_small = Quantity(1, "GJ")
        energy_large = Quantity(1, "MWh")

        assert energy_large > energy_small
        assert energy_large >= energy_small
        assert energy_small < energy_large
        assert energy_small <= energy_large
        assert energy_large != energy_small


class TestPandasIntegration:
    def test_pandas_unit_operations(self):
        """Test integration with pandas DataFrames."""
        import pandas as pd

        from energyunits.pandas_tools import (
            add_units,
            calculate_emissions,
            convert_units,
        )

        # Create dataframe
        df = pd.DataFrame(
            {
                "generation": [100, 200, 300, 400],
                "fuel_type": ["coal", "natural_gas", "wind", "solar"],
            }
        )

        # Add units
        df_with_units = add_units(df, "generation", "MWh")

        # Check units are stored in metadata
        assert df_with_units.attrs["generation_unit"] == "MWh"

        # Convert units
        df_gj = convert_units(df_with_units, "generation", "GJ")

        # Check conversion
        assert df_gj.attrs["generation_unit"] == "GJ"
        assert df_gj["generation"][0] == pytest.approx(360)

        # Calculate emissions using the updated pandas function (which uses unified .to() method)
        df_emissions = calculate_emissions(
            df_with_units, energy_col="generation", fuel_col="fuel_type"
        )

        # Check emissions column exists
        assert "emissions" in df_emissions.columns
        # Fossil fuels should have positive emissions
        assert df_emissions["emissions"][0] > 0  # Coal
        assert df_emissions["emissions"][1] > 0  # Natural gas
        # Renewables should have zero emissions
        assert df_emissions["emissions"][2] == 0  # Wind
        assert df_emissions["emissions"][3] == 0  # Solar


class TestCostCalculations:
    def test_inflation_adjustment(self):
        """Test adjusting costs for inflation."""
        from energyunits import Quantity

        # Define cost with reference year
        capex_2015 = Quantity(1000, "USD/kW", reference_year=2015)

        # Adjust for inflation
        capex_2025 = capex_2015.adjust_inflation(target_year=2025)

        assert capex_2025.unit == "USD/kW"
        assert (
            capex_2025.value > capex_2015.value
        )  # Inflation should increase the value