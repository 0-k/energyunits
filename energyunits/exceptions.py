"""Exception and warning types raised by energyunits.

All exceptions derive from :class:`EnergyUnitsError`, which itself is a
:class:`ValueError`. Code that catches ``ValueError`` therefore keeps working,
while new code can catch the more specific types.
"""


class EnergyUnitsError(ValueError):
    """Base class for all errors raised by energyunits."""


class UnknownUnitError(EnergyUnitsError):
    """A unit string contains a unit that is not registered, or is malformed."""


class IncompatibleUnitsError(EnergyUnitsError):
    """Two units cannot be converted into each other (possibly without a substance)."""


class UnknownSubstanceError(EnergyUnitsError):
    """A substance name is not registered."""


class MissingDataError(EnergyUnitsError):
    """Required data is not available (heating value, density, inflation or exchange rate)."""


class DefinitionConflictError(EnergyUnitsError):
    """Loaded data would change an existing definition (pass ``overwrite=True`` to allow it)."""


class EnergyUnitsWarning(UserWarning):
    """Warning category for assumptions made by energyunits (e.g. projected data)."""
