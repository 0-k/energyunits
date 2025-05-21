"""
EnergyUnits: A Python library for handling units, conversions, and calculations in energy system modeling.

This library provides tools for working with energy units, performing conversions,
and handling energy-related calculations in a consistent way.

Example:
    ```python
    from energyunits import Quantity

    # Basic unit conversion
    energy = Quantity(100, "MWh")
    energy_gj = energy.to("GJ")  # 360 GJ

    # Power and energy conversion
    power = Quantity(50, "MW")
    energy_24h = power.for_duration(hours=24)  # 1200 MWh

    # Working with substances
    coal = Quantity(1000, "t", "coal")
    energy_content = coal.energy_content()  # MWh
    emissions = energy_content.calculate_emissions()  # tCO2
    ```
"""

from .quantity import Quantity
from .registry import registry
from .substance import substance_registry

# Import pandas integration if pandas is available
try:
    import pandas as pd
    from . import pandas_tools
except ImportError:
    # Pandas integration is optional
    pass

__version__ = "0.0.1"