"""
Custom exceptions for the EnergyUnits library.

Defining specific exception types makes error handling more predictable
and helps users understand what went wrong.
"""


class EnergyUnitsError(Exception):
    """Base exception for all EnergyUnits errors."""
    pass


class UnitError(EnergyUnitsError):
    """Base class for unit-related errors."""
    pass


class UnknownUnitError(UnitError):
    """Raised when an unknown unit is encountered."""
    pass


class IncompatibleUnitsError(UnitError):
    """Raised when attempting to convert between incompatible units."""
    pass


class MissingUnitSpecificationError(UnitError):
    """Raised when unit information is required but missing."""
    pass


class SubstanceError(EnergyUnitsError):
    """Base class for substance-related errors."""
    pass


class UnknownSubstanceError(SubstanceError):
    """Raised when an unknown substance is encountered."""
    pass


class MissingSubstanceError(SubstanceError):
    """Raised when a substance is required but not provided."""
    pass


class PropertyError(EnergyUnitsError):
    """Raised for issues with property calculations."""
    pass


class ConversionError(EnergyUnitsError):
    """Raised when a conversion fails for any reason other than incompatible units."""
    pass


class OperationError(EnergyUnitsError):
    """Raised when an operation between quantities is invalid."""
    pass