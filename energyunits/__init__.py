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

from . import units
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
    "DefinitionConflictError",
    "EnergyUnitsError",
    "EnergyUnitsWarning",
    "IncompatibleUnitsError",
    "MissingDataError",
    "UnknownSubstanceError",
    "UnknownUnitError",
    "__version__",
]


def __getattr__(name):
    # Import the optional pandas integration lazily so that importing
    # energyunits stays fast and pandas remains optional.
    if name == "pandas_tools":
        import importlib

        return importlib.import_module(".pandas_tools", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
