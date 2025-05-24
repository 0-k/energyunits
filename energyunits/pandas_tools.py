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


def add_units(df, column, unit):
    """Add unit information to a dataframe column.

    Args:
        df: pandas DataFrame
        column: Column name to add units to
        unit: Unit string to assign

    Returns:
        DataFrame with unit information in metadata
    """
    df_copy = df.copy()
    # Store unit information in DataFrame attributes
    df_copy.attrs[f"{column}_unit"] = unit
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
    current_unit = df.attrs.get(f"{column}_unit")
    if current_unit is None:
        raise ValueError(f"No unit information found for column '{column}'")
    df_copy = df.copy()

    # Get conversion factor using registry
    from .registry import registry

    factor = registry.get_conversion_factor(current_unit, target_unit)

    # Apply conversion
    df_copy[column] = df_copy[column] * factor

    # Update unit information
    df_copy.attrs[f"{column}_unit"] = target_unit
    return df_copy
