"""
Pandas integration for the EnergyUnits library.

This module provides functions for working with units in pandas DataFrames.

Example:
    ```python
    import pandas as pd
    from energyunits.pandas_tools import add_units, convert_units

    # Create a dataframe with energy data
    df = pd.DataFrame({
        'generation': [100, 200, 300, 400],
        'fuel_type': ['coal', 'natural_gas', 'wind', 'solar'],
    })

    # Add units to dataframe
    df_with_units = add_units(df, 'generation', 'MWh')

    # Convert units in dataframe
    df_gj = convert_units(df_with_units, 'generation', 'GJ')
    ```
"""

import numpy as np
import pandas as pd

from .quantity import Quantity
from .substance import substance_registry


def add_units(df, column, unit):
    """Add unit information to a dataframe column.

    Args:
        df: pandas DataFrame
        column: Column name to add units to
        unit: Unit string to assign

    Returns:
        DataFrame with unit information in metadata
    """
    # Make a copy to avoid modifying the original
    df_copy = df.copy()

    # Store unit information in DataFrame attributes
    if hasattr(df_copy, "attrs"):
        df_copy.attrs[f"{column}_unit"] = unit
    else:
        # For older pandas versions without attrs
        df_copy._metadata = getattr(df_copy, "_metadata", []) + [f"{column}_unit"]
        setattr(df_copy, f"{column}_unit", unit)

    return df_copy


def convert_units(df, column, target_unit):
    """Convert values in a dataframe column to a new unit.

    Args:
        df: pandas DataFrame with unit information
        column: Column name to convert
        target_unit: Target unit to convert to

    Returns:
        DataFrame with converted values and updated unit information
    """
    # Get current unit from metadata
    current_unit = None
    if hasattr(df, "attrs"):
        current_unit = df.attrs.get(f"{column}_unit")
    else:
        current_unit = getattr(df, f"{column}_unit", None)

    if current_unit is None:
        raise ValueError(f"No unit information found for column '{column}'")

    # Make a copy to avoid modifying the original
    df_copy = df.copy()

    # Get conversion factor using registry
    from .registry import registry

    factor = registry.get_conversion_factor(current_unit, target_unit)

    # Apply conversion
    df_copy[column] = df_copy[column] * factor

    # Update unit information
    if hasattr(df_copy, "attrs"):
        df_copy.attrs[f"{column}_unit"] = target_unit
    else:
        setattr(df_copy, f"{column}_unit", target_unit)

    return df_copy


def calculate_emissions(df, energy_col, fuel_col, output_col="emissions"):
    """Calculate CO2 emissions based on energy values and fuel types.

    Args:
        df: pandas DataFrame
        energy_col: Column name with energy values
        fuel_col: Column name with fuel types
        output_col: Name for emissions column to create

    Returns:
        DataFrame with emissions column added
    """
    # Make a copy to avoid modifying the original
    df_copy = df.copy()

    # Get energy unit from metadata
    energy_unit = None
    if hasattr(df, "attrs"):
        energy_unit = df.attrs.get(f"{energy_col}_unit")
    else:
        energy_unit = getattr(df, f"{energy_col}_unit", None)

    if energy_unit is None:
        raise ValueError(f"No unit information found for column '{energy_col}'")

    # Initialize emissions column
    df_copy[output_col] = 0.0

    # Calculate emissions for each row
    for idx, row in df_copy.iterrows():
        energy_value = row[energy_col]
        fuel_type = row[fuel_col]

        try:
            # Create Quantity object
            energy = Quantity(energy_value, energy_unit, fuel_type)

            # Calculate emissions
            emissions = substance_registry.calculate_emissions(energy)

            # Store emissions value
            df_copy.loc[idx, output_col] = emissions.value

        except (ValueError, KeyError):
            # Set zero emissions for unknown fuels or renewables
            if fuel_type in ["wind", "solar", "hydro", "nuclear"]:
                df_copy.loc[idx, output_col] = 0.0
            else:
                # Keep NaN for truly unknown substances
                df_copy.loc[idx, output_col] = np.nan

    # Add unit information for emissions column
    if hasattr(df_copy, "attrs"):
        df_copy.attrs[f"{output_col}_unit"] = "t"
    else:
        setattr(df_copy, f"{output_col}_unit", "t")

    return df_copy


def energy_balance(df, columns, name="balance"):
    """Calculate an energy balance from multiple columns.

    Args:
        df: pandas DataFrame with unit information
        columns: Dictionary mapping column names to sign (+1 or -1)
        name: Name for the balance column to create

    Returns:
        DataFrame with balance column added
    """
    # Make a copy to avoid modifying the original
    df_copy = df.copy()

    # Get unit from first column (all columns must have same unit)
    first_col = list(columns.keys())[0]
    unit = None
    if hasattr(df, "attrs"):
        unit = df.attrs.get(f"{first_col}_unit")
    else:
        unit = getattr(df, f"{first_col}_unit", None)

    if unit is None:
        raise ValueError(f"No unit information found for column '{first_col}'")

    # Initialize balance column
    df_copy[name] = 0.0

    # Calculate balance
    for col, sign in columns.items():
        # Check unit compatibility
        col_unit = None
        if hasattr(df, "attrs"):
            col_unit = df.attrs.get(f"{col}_unit")
        else:
            col_unit = getattr(df, f"{col}_unit", None)

        if col_unit != unit:
            raise ValueError(f"Incompatible units: {unit} and {col_unit}")

        # Add to balance
        df_copy[name] += sign * df_copy[col]

    # Add unit information for balance column
    if hasattr(df_copy, "attrs"):
        df_copy.attrs[f"{name}_unit"] = unit
    else:
        setattr(df_copy, f"{name}_unit", unit)

    return df_copy
