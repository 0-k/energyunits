"""
EnergyUnits: A Python library for energy system modeling with units and conversions.

This library provides tools for working with energy units, performing conversions,
and handling energy-related calculations in a consistent way.

Example:
    ```python
    from energyunits import Quantity

    # Basic unit conversion
    energy = Quantity(100, "MWh")
    energy_gj = energy.to("GJ")  # 360 GJ

    # Substance-based conversions
    coal = Quantity(1000, "t", "coal")
    energy = coal.to("MWh")  # Uses heating values
    emissions = coal.to("t", substance="CO2")  # Combustion products

    # Power and energy relationships
    capacity = Quantity(50, "MW")
    time = Quantity(24, "h")
    daily_energy = capacity * time  # 1200 MWh
    ```
"""

from .quantity import Quantity

# Import pandas integration if pandas is available
try:
    import pandas as pd

    from . import pandas_tools

    _has_pandas = True
except ImportError:
    # Pandas integration is optional
    _has_pandas = False
    pandas_tools = None

__version__ = "0.0.1"

# Define public API
__all__ = ["Quantity"]
if _has_pandas:
    __all__.append("pandas_tools")
