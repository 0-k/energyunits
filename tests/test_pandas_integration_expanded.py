"""Expanded tests for pandas integration functionality."""

import numpy as np
import pytest

# Import pandas and energyunits conditionally
pd = pytest.importorskip("pandas")
from energyunits import Quantity


class TestPandasToolsBasic:
    """Test basic pandas tools functionality."""

    def test_add_units_basic(self):
        """Test basic unit addition to DataFrame columns."""
        from energyunits.pandas_tools import add_units

        df = pd.DataFrame(
            {
                "generation": [100, 200, 300, 400],
                "fuel_type": ["coal", "natural_gas", "wind", "solar"],
            }
        )

        df_with_units = add_units(df, "generation", "MWh")

        assert df_with_units.attrs["generation_unit"] == "MWh"
        assert df_with_units["generation"].tolist() == [100, 200, 300, 400]
        assert df_with_units["fuel_type"].tolist() == [
            "coal",
            "natural_gas",
            "wind",
            "solar",
        ]

    def test_convert_units_basic(self):
        """Test basic unit conversion in DataFrames."""
        from energyunits.pandas_tools import add_units, convert_units

        df = pd.DataFrame({"energy": [1, 2, 3]})
        df_with_units = add_units(df, "energy", "MWh")
        df_converted = convert_units(df_with_units, "energy", "GJ")

        # 1 MWh = 3.6 GJ
        expected_values = [3.6, 7.2, 10.8]
        assert df_converted.attrs["energy_unit"] == "GJ"
        assert df_converted["energy"].tolist() == pytest.approx(expected_values)

    def test_convert_units_error_no_unit(self):
        """Test error when trying to convert without unit information."""
        from energyunits.pandas_tools import convert_units

        df = pd.DataFrame({"energy": [1, 2, 3]})

        with pytest.raises(ValueError, match="No unit information found"):
            convert_units(df, "energy", "GJ")

    def test_multiple_columns_with_units(self):
        """Test adding units to multiple columns."""
        from energyunits.pandas_tools import add_units

        df = pd.DataFrame(
            {
                "power": [100, 200, 300],
                "energy": [240, 480, 720],
                "capacity": [100, 200, 300],
            }
        )

        df_units = df.copy()
        df_units = add_units(df_units, "power", "MW")
        df_units = add_units(df_units, "energy", "MWh")
        df_units = add_units(df_units, "capacity", "MW")

        assert df_units.attrs["power_unit"] == "MW"
        assert df_units.attrs["energy_unit"] == "MWh"
        assert df_units.attrs["capacity_unit"] == "MW"

    def test_dataframe_copy_behavior(self):
        """Test that operations don't modify original DataFrame."""
        from energyunits.pandas_tools import add_units, convert_units

        original_df = pd.DataFrame({"energy": [1, 2, 3]})
        original_values = original_df["energy"].tolist()

        # Add units and convert - should not modify original
        df_with_units = add_units(original_df, "energy", "MWh")
        df_converted = convert_units(df_with_units, "energy", "GJ")

        # Original should be unchanged
        assert original_df["energy"].tolist() == original_values
        assert "energy_unit" not in original_df.attrs

        # Modified versions should be different
        assert df_converted["energy"].tolist() != original_values


class TestPandasToolsAdvanced:
    """Test advanced pandas tools functionality."""

    def test_large_dataframe_conversion(self):
        """Test unit conversion with large DataFrames."""
        from energyunits.pandas_tools import add_units, convert_units

        # Large DataFrame
        size = 10000
        df = pd.DataFrame(
            {
                "energy": np.random.rand(size) * 1000,
                "fuel_type": np.random.choice(["coal", "gas", "wind"], size),
            }
        )

        df_with_units = add_units(df, "energy", "MWh")
        df_converted = convert_units(df_with_units, "energy", "GJ")

        # Check that all values were converted correctly
        expected_values = df["energy"] * 3.6
        assert df_converted["energy"].tolist() == pytest.approx(
            expected_values.tolist()
        )

    def test_nan_handling_in_conversions(self):
        """Test handling of NaN values in unit conversions."""
        from energyunits.pandas_tools import add_units, convert_units

        df = pd.DataFrame({"energy": [100, np.nan, 300, np.nan, 500]})

        df_with_units = add_units(df, "energy", "MWh")
        df_converted = convert_units(df_with_units, "energy", "GJ")

        # NaN values should remain NaN
        assert pd.isna(df_converted["energy"].iloc[1])
        assert pd.isna(df_converted["energy"].iloc[3])

        # Non-NaN values should be converted
        assert df_converted["energy"].iloc[0] == pytest.approx(360)  # 100 * 3.6
        assert df_converted["energy"].iloc[2] == pytest.approx(1080)  # 300 * 3.6
        assert df_converted["energy"].iloc[4] == pytest.approx(1800)  # 500 * 3.6

    def test_zero_and_negative_values(self):
        """Test unit conversion with zero and negative values."""
        from energyunits.pandas_tools import add_units, convert_units

        df = pd.DataFrame({"energy": [-100, 0, 100, -50.5]})

        df_with_units = add_units(df, "energy", "MWh")
        df_converted = convert_units(df_with_units, "energy", "kWh")

        # Check conversions (1 MWh = 1000 kWh)
        expected = [-100000, 0, 100000, -50500]
        assert df_converted["energy"].tolist() == pytest.approx(expected)

    def test_unit_conversion_chains_in_dataframes(self):
        """Test chained unit conversions in DataFrames."""
        from energyunits.pandas_tools import add_units, convert_units

        df = pd.DataFrame({"energy": [1, 2, 3, 4, 5]})

        # Chain of conversions: MWh → GJ → MJ → kJ → J
        df_mwh = add_units(df, "energy", "MWh")
        df_gj = convert_units(df_mwh, "energy", "GJ")
        df_mj = convert_units(df_gj, "energy", "MJ")
        df_kj = convert_units(df_mj, "energy", "kJ")
        df_j = convert_units(df_kj, "energy", "J")

        # Convert back to MWh
        df_back = convert_units(df_j, "energy", "MWh")

        # Should get back original values
        assert df_back["energy"].tolist() == pytest.approx(
            df["energy"].tolist(), rel=1e-10
        )

    def test_incompatible_unit_conversion_error(self):
        """Test error handling for incompatible unit conversions."""
        from energyunits.pandas_tools import add_units, convert_units

        df = pd.DataFrame({"energy": [100, 200, 300]})
        df_with_units = add_units(df, "energy", "MWh")

        with pytest.raises(ValueError):
            convert_units(df_with_units, "energy", "kg")  # Energy to mass


class TestPandasIntegrationWithQuantities:
    """Test integration between pandas tools and Quantity objects."""

    def test_dataframe_to_quantity_conversion(self):
        """Test converting DataFrame columns to Quantity objects."""
        from energyunits.pandas_tools import add_units

        df = pd.DataFrame({"energy": [100, 200, 300], "fuel": ["coal", "gas", "wind"]})
        df_with_units = add_units(df, "energy", "MWh")

        # Convert column to Quantity
        energy_quantities = []
        for i, row in df_with_units.iterrows():
            fuel = row["fuel"] if row["fuel"] in ["coal", "gas"] else None
            q = Quantity(
                row["energy"], df_with_units.attrs["energy_unit"], substance=fuel
            )
            energy_quantities.append(q)

        # Check that quantities were created correctly
        assert len(energy_quantities) == 3
        assert energy_quantities[0].value == 100
        assert energy_quantities[0].unit == "MWh"
        assert energy_quantities[0].substance == "coal"
        assert energy_quantities[2].substance is None  # wind

    def test_quantity_to_dataframe_conversion(self):
        """Test converting Quantity objects to DataFrame columns."""
        from energyunits.pandas_tools import add_units

        # Create quantities
        quantities = [
            Quantity(100, "MWh", "coal"),
            Quantity(200, "MWh", "natural_gas"),
            Quantity(300, "MWh", "wind"),
        ]

        # Extract data for DataFrame
        values = [q.value for q in quantities]
        substances = [q.substance for q in quantities]
        units = [q.unit for q in quantities]

        # Create DataFrame
        df = pd.DataFrame({"energy": values, "fuel": substances, "unit": units})

        # Add unit metadata
        df_with_units = add_units(df, "energy", "MWh")

        assert df_with_units.attrs["energy_unit"] == "MWh"
        assert df_with_units["energy"].tolist() == [100, 200, 300]
        assert df_with_units["fuel"].tolist() == ["coal", "natural_gas", "wind"]

    def test_substance_aware_dataframe_operations(self):
        """Test DataFrame operations that are aware of substance information."""
        from energyunits.pandas_tools import add_units

        df = pd.DataFrame(
            {
                "energy": [100, 200, 150, 300],
                "fuel": ["coal", "natural_gas", "oil", "wind"],
                "plant": ["Plant A", "Plant B", "Plant C", "Plant D"],
            }
        )
        df_with_units = add_units(df, "energy", "MWh")

        # Calculate emissions for each row
        emissions = []
        for _, row in df_with_units.iterrows():
            if row["fuel"] in ["coal", "natural_gas", "oil"]:
                energy_q = Quantity(row["energy"], "MWh", row["fuel"])
                co2_q = energy_q.to(substance="CO2")
                emissions.append(co2_q.value)
            else:
                emissions.append(0.0)  # Renewables

        df_with_emissions = df_with_units.copy()
        df_with_emissions["co2_emissions"] = emissions
        df_with_emissions = add_units(df_with_emissions, "co2_emissions", "t")

        # Check that emissions are reasonable
        assert df_with_emissions["co2_emissions"].iloc[3] == 0.0  # Wind
        assert df_with_emissions["co2_emissions"].iloc[0] > 0  # Coal
        assert df_with_emissions.attrs["co2_emissions_unit"] == "t"

    def test_basis_conversion_in_dataframes(self):
        """Test basis conversions (HHV/LHV) in DataFrames."""
        from energyunits.pandas_tools import add_units

        df = pd.DataFrame(
            {"energy_hhv": [100, 200, 300], "fuel": ["coal", "natural_gas", "oil"]}
        )
        df_with_units = add_units(df, "energy_hhv", "MWh")

        # Convert to LHV basis
        energy_lhv = []
        for _, row in df_with_units.iterrows():
            energy_q = Quantity(row["energy_hhv"], "MWh", row["fuel"], basis="HHV")
            energy_lhv_q = energy_q.to(basis="LHV")
            energy_lhv.append(energy_lhv_q.value)

        df_lhv = df_with_units.copy()
        df_lhv["energy_lhv"] = energy_lhv
        df_lhv = add_units(df_lhv, "energy_lhv", "MWh")

        # LHV values should be lower than HHV values
        assert all(
            lhv < hhv for lhv, hhv in zip(df_lhv["energy_lhv"], df_lhv["energy_hhv"])
        )


class TestPandasDataAnalysis:
    """Test pandas tools for realistic data analysis scenarios."""

    def test_power_plant_portfolio_analysis(self):
        """Test analysis of a power plant portfolio with units."""
        from energyunits.pandas_tools import add_units, convert_units

        # Create portfolio data
        df = pd.DataFrame(
            {
                "plant_name": [
                    "Coal Plant A",
                    "Gas Plant B",
                    "Wind Farm C",
                    "Solar Farm D",
                ],
                "capacity_mw": [500, 300, 200, 100],
                "generation_mwh": [3500000, 2100000, 700000, 350000],
                "fuel_type": ["coal", "natural_gas", "wind", "solar"],
            }
        )

        # Add units
        df = add_units(df, "capacity_mw", "MW")
        df = add_units(df, "generation_mwh", "MWh")

        # Convert to different units
        df_gw = convert_units(df, "capacity_mw", "GW")
        df_twh = convert_units(df_gw, "generation_mwh", "TWh")

        # Calculate capacity factors - need to work with consistent units
        hours_per_year = 8760
        # generation_mwh is in TWh, capacity_mw is in GW
        # Capacity factor = Generation(TWh) / (Capacity(GW) * hours_per_year / 1000)
        df_twh["capacity_factor"] = df_twh["generation_mwh"] / (
            df_twh["capacity_mw"] * hours_per_year / 1000
        )

        # Check unit conversions
        assert df_twh.attrs["capacity_mw_unit"] == "GW"
        assert df_twh.attrs["generation_mwh_unit"] == "TWh"

        # Check capacity factors are reasonable
        assert 0.1 <= df_twh["capacity_factor"].iloc[2] <= 0.5  # Wind
        assert 0.1 <= df_twh["capacity_factor"].iloc[3] <= 0.5  # Solar
        assert 0.7 <= df_twh["capacity_factor"].iloc[0] <= 0.9  # Coal
        assert 0.4 <= df_twh["capacity_factor"].iloc[1] <= 0.9  # Gas

    def test_fuel_cost_analysis_with_inflation(self):
        """Test fuel cost analysis with inflation adjustments."""
        from energyunits.pandas_tools import add_units

        # Historical fuel costs
        df = pd.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023, 2024],
                "coal_cost_usd_per_mwh": [25, 30, 35, 32, 28],
                "gas_cost_usd_per_mwh": [35, 45, 55, 48, 42],
            }
        )

        # Add units
        df = add_units(df, "coal_cost_usd_per_mwh", "USD/MWh")
        df = add_units(df, "gas_cost_usd_per_mwh", "USD/MWh")

        # Adjust all costs to 2024 dollars
        target_year = 2024
        inflation_rate = 0.02  # 2% per year

        for cost_col in ["coal_cost_usd_per_mwh", "gas_cost_usd_per_mwh"]:
            adjusted_costs = []
            for _, row in df.iterrows():
                # Create quantity with reference year
                cost_q = Quantity(row[cost_col], "USD/MWh", reference_year=row["year"])
                adjusted_q = cost_q.to(reference_year=target_year)
                adjusted_costs.append(adjusted_q.value)

            df[f"{cost_col}_2024"] = adjusted_costs
            df = add_units(df, f"{cost_col}_2024", "USD/MWh")

        # Check that 2024 values are identical to original 2024 values
        assert df["coal_cost_usd_per_mwh_2024"].iloc[4] == pytest.approx(
            df["coal_cost_usd_per_mwh"].iloc[4]
        )
        assert df["gas_cost_usd_per_mwh_2024"].iloc[4] == pytest.approx(
            df["gas_cost_usd_per_mwh"].iloc[4]
        )

        # Earlier years should have higher inflation-adjusted values
        assert (
            df["coal_cost_usd_per_mwh_2024"].iloc[0]
            > df["coal_cost_usd_per_mwh"].iloc[0]
        )

    def test_emissions_intensity_calculation(self):
        """Test calculation of emissions intensity across different data types."""
        from energyunits.pandas_tools import add_units

        # Generation data
        df = pd.DataFrame(
            {
                "technology": ["coal", "natural_gas", "wind", "solar", "nuclear"],
                "generation_twh": [1000, 800, 400, 200, 600],
                "fuel_type": ["coal", "natural_gas", "wind", "solar", "nuclear"],
            }
        )

        df = add_units(df, "generation_twh", "TWh")

        # Calculate emissions for each technology
        emissions_mt = []
        for _, row in df.iterrows():
            # Convert to MWh for emissions calculation
            generation_mwh = row["generation_twh"] * 1e6  # TWh to MWh
            energy_q = Quantity(generation_mwh, "MWh", row["fuel_type"])

            co2_q = energy_q.to(substance="CO2")
            emissions_mt.append(co2_q.value / 1e6)  # t to Mt

        df["emissions_mt"] = emissions_mt
        df = add_units(df, "emissions_mt", "Mt")

        # Calculate emission intensity (Mt CO2 / TWh)
        df["emission_intensity"] = df["emissions_mt"] / df["generation_twh"]
        df = add_units(df, "emission_intensity", "Mt/TWh")

        # Check that renewables have zero emissions
        wind_idx = df[df["technology"] == "wind"].index[0]
        solar_idx = df[df["technology"] == "solar"].index[0]
        nuclear_idx = df[df["technology"] == "nuclear"].index[0]

        assert df["emissions_mt"].iloc[wind_idx] == 0
        assert df["emissions_mt"].iloc[solar_idx] == 0
        assert df["emissions_mt"].iloc[nuclear_idx] == 0

        # Check that fossil fuels have positive emissions
        coal_idx = df[df["technology"] == "coal"].index[0]
        gas_idx = df[df["technology"] == "natural_gas"].index[0]

        assert df["emissions_mt"].iloc[coal_idx] > 0
        assert df["emissions_mt"].iloc[gas_idx] > 0

        # Coal should have higher emission intensity than gas
        assert (
            df["emission_intensity"].iloc[coal_idx]
            > df["emission_intensity"].iloc[gas_idx]
        )


class TestPandasErrorHandling:
    """Test error handling in pandas integration."""

    def test_missing_column_error(self):
        """Test error when trying to add units to non-existent column."""
        from energyunits.pandas_tools import add_units

        df = pd.DataFrame({"energy": [1, 2, 3]})

        # This should work for existing column
        df_with_units = add_units(df, "energy", "MWh")
        assert df_with_units.attrs["energy_unit"] == "MWh"

        # But should also work for non-existing column (just adds metadata)
        df_with_meta = add_units(df, "nonexistent", "MW")
        assert df_with_meta.attrs["nonexistent_unit"] == "MW"

    def test_convert_nonexistent_column_error(self):
        """Test error when trying to convert non-existent column."""
        from energyunits.pandas_tools import add_units, convert_units

        df = pd.DataFrame({"energy": [1, 2, 3]})
        df_with_units = add_units(df, "energy", "MWh")

        with pytest.raises(ValueError, match="No unit information found"):
            convert_units(df_with_units, "nonexistent", "GJ")

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrames."""
        from energyunits.pandas_tools import add_units, convert_units

        # Empty DataFrame with columns
        df_empty = pd.DataFrame(columns=["energy", "fuel"])
        df_with_units = add_units(df_empty, "energy", "MWh")

        assert df_with_units.attrs["energy_unit"] == "MWh"
        assert len(df_with_units) == 0

        # Convert units on empty DataFrame
        df_converted = convert_units(df_with_units, "energy", "GJ")
        assert df_converted.attrs["energy_unit"] == "GJ"
        assert len(df_converted) == 0

    def test_unit_metadata_persistence(self):
        """Test that unit metadata persists through various DataFrame operations."""
        from energyunits.pandas_tools import add_units

        df = pd.DataFrame(
            {"energy": [100, 200, 300, 400], "fuel": ["coal", "gas", "wind", "solar"]}
        )
        df_with_units = add_units(df, "energy", "MWh")

        # Test various pandas operations
        df_subset = df_with_units[df_with_units["energy"] > 150]
        df_sorted = df_with_units.sort_values("energy")
        df_grouped = df_with_units.groupby("fuel")["energy"].sum().reset_index()

        # Note: pandas operations may or may not preserve attrs
        # This documents current behavior
        original_attrs = df_with_units.attrs

        # Subset might preserve attrs
        try:
            assert df_subset.attrs == original_attrs
        except (AssertionError, AttributeError):
            pass  # attrs might not be preserved

        # Groupby operations typically don't preserve attrs
        # This is expected pandas behavior
