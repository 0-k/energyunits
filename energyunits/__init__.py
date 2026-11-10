"""
EnergyUnits: units, conversions and calculations for energy system modeling.

Example::

    from energyunits import Quantity

    # Basic unit conversion
    energy = Quantity(100, "MWh")
    energy.to("GJ")                                  # 360 GJ

    # Substance-based conversions
    coal = Quantity(1000, "t", "coal")
    coal.to("MWh")                                   # energy content (LHV)
    coal.to("t", substance="CO2")                    # combustion CO2

    # Power x time = energy, with automatic unit handling
    Quantity(50, "MW") * Quantity(30, "min")         # 25 MWh

    # Costs with inflation and year-dependent exchange rates
    Quantity(1000, "EUR/kW", reference_year=2015).to("USD/kW", reference_year=2024)
"""

from . import pandas_tools, units
from .exceptions import (
    DefinitionConflictError,
    EnergyUnitsError,
    EnergyUnitsWarning,
    IncompatibleUnitsError,
    MissingDataError,
    UnknownSubstanceError,
    UnknownUnitError,
)
from .quantity import Quantity

__version__ = "0.3.0"

__all__ = [
    "Quantity",
    "units",
    "pandas_tools",
    "DefinitionConflictError",
    "EnergyUnitsError",
    "EnergyUnitsWarning",
    "IncompatibleUnitsError",
    "MissingDataError",
    "UnknownSubstanceError",
    "UnknownUnitError",
    "__version__",
]
