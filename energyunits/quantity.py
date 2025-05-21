"""
Improved Quantity class with simplified unit conversion methods.
"""

import numpy as np
from typing import Union, Optional, List, Any
from .registry import registry


class Quantity:
    """A physical quantity with value and unit."""

    def __init__(self, value: Union[float, int, List[float], np.ndarray],
                 unit: str,
                 substance: Optional[str] = None,
                 basis: Optional[str] = None,
                 reference_year: Optional[int] = None):
        """Initialize a physical quantity.

        Args:
            value: Numerical value (scalar or array)
            unit: Unit string (e.g., "MWh", "GJ")
            substance: Optional substance specifier (e.g., "coal", "natural_gas")
            basis: Optional heating value basis ("HHV" or "LHV")
            reference_year: Optional reference year for costs
        """
        self.value = np.asarray(value)
        self.unit = unit
        self.substance = substance
        self.basis = basis
        self.reference_year = reference_year

        # Get dimension from registry
        self.dimension = registry.get_dimension(unit)

    def to(self, target_unit: str) -> 'Quantity':
        """Convert to another unit (same or compatible dimension).

        Args:
            target_unit: Target unit to convert to

        Returns:
            A new Quantity object with converted value and target unit
        """
        # Get the dimensions
        from_dim = self.dimension
        to_dim = registry.get_dimension(target_unit)

        # Case 1: Same dimension - standard conversion
        if from_dim == to_dim:
            # Get conversion factor from registry
            factor = registry.get_conversion_factor(self.unit, target_unit)
            # Apply conversion
            new_value = self.value * factor

        # Case 2: Different but compatible dimensions
        elif registry.are_dimensions_compatible(from_dim, to_dim):
            # Use the dimension relationship to convert
            new_value = registry.convert_between_dimensions(
                self.value, self.unit, target_unit, self.substance)
        else:
            raise ValueError(f"Cannot convert from {self.unit} ({from_dim}) to "
                             f"{target_unit} ({to_dim})")

        # Return new quantity with same metadata
        return Quantity(
            new_value,
            target_unit,
            self.substance,
            self.basis,
            self.reference_year
        )

    def for_duration(self, hours: float) -> 'Quantity':
        """Convert power to energy for a specified duration.

        Args:
            hours: Duration in hours

        Returns:
            Energy quantity
        """
        if self.dimension != "POWER":
            raise ValueError(
                f"for_duration only applies to power units, not {self.unit}")

        # Get the corresponding energy unit
        try:
            energy_unit = registry.get_corresponding_unit(self.unit, "ENERGY")
        except ValueError:
            energy_unit = "MWh"  # Default if no direct correspondence

        # Convert power to energy
        energy_value = registry.convert_between_dimensions(
            self.value, self.unit, energy_unit, self.substance, hours=hours)

        return Quantity(
            energy_value,
            energy_unit,
            self.substance,
            self.basis,
            self.reference_year
        )

    def average_power(self, hours: float) -> 'Quantity':
        """Calculate average power from energy over a specified duration.

        Args:
            hours: Duration in hours

        Returns:
            Power quantity
        """
        if self.dimension != "ENERGY":
            raise ValueError(
                f"average_power only applies to energy units, not {self.unit}")

        # Get the corresponding power unit
        try:
            power_unit = registry.get_corresponding_unit(self.unit, "POWER")
        except ValueError:
            power_unit = "MW"  # Default if no direct correspondence

        # Convert energy to power
        power_value = registry.convert_between_dimensions(
            self.value, self.unit, power_unit, self.substance, hours=hours)

        return Quantity(
            power_value,
            power_unit,
            self.substance,
            self.basis,
            self.reference_year
        )

    def energy_content(self, basis: str = "HHV") -> 'Quantity':
        """Calculate energy content based on substance properties.

        Args:
            basis: Heating value basis ("HHV" or "LHV")

        Returns:
            Energy quantity in MWh
        """
        from .substance import substance_registry

        result = substance_registry.calculate_energy_content(self, basis)
        result.basis = basis
        return result

    def to_lhv(self) -> 'Quantity':
        """Convert energy from HHV to LHV basis.

        Returns:
            Energy quantity with LHV basis
        """
        if self.basis is None:
            self.basis = "HHV"  # Assume HHV if not specified

        if self.basis == "LHV":
            return self  # Already LHV

        if self.substance is None:
            raise ValueError("Substance must be specified for HHV/LHV conversion")

        from .substance import substance_registry

        # Get ratio of LHV to HHV
        ratio = substance_registry.get_lhv_hhv_ratio(self.substance)

        # Apply ratio
        new_value = self.value * ratio

        # Return new quantity
        return Quantity(
            new_value,
            self.unit,
            self.substance,
            "LHV",
            self.reference_year
        )

    def to_hhv(self) -> 'Quantity':
        """Convert energy from LHV to HHV basis.

        Returns:
            Energy quantity with HHV basis
        """
        if self.basis is None:
            self.basis = "LHV"  # Assume LHV if not specified

        if self.basis == "HHV":
            return self  # Already HHV

        if self.substance is None:
            raise ValueError("Substance must be specified for LHV/HHV conversion")

        from .substance import substance_registry

        # Get ratio of LHV to HHV
        ratio = substance_registry.get_lhv_hhv_ratio(self.substance)

        # Apply inverse ratio
        new_value = self.value / ratio

        # Return new quantity
        return Quantity(
            new_value,
            self.unit,
            self.substance,
            "HHV",
            self.reference_year
        )

    def usable_energy(self, moisture_content: Optional[float] = None) -> 'Quantity':
        """Calculate usable energy considering moisture content.

        Args:
            moisture_content: Override moisture content (0.0 to 1.0),
                             if None, uses default for substance

        Returns:
            Energy quantity adjusted for moisture
        """
        if self.substance is None:
            raise ValueError("Substance must be specified for usable energy calculation")

        from .substance import substance_registry

        # Calculate energy content (LHV basis)
        energy = self.energy_content(basis="LHV")

        # Get moisture adjustment factor
        if moisture_content is None:
            moisture_content = substance_registry.get_moisture_content(self.substance)
        else:
            # Validate moisture content
            if not 0 <= moisture_content <= 1:
                raise ValueError("Moisture content must be between 0 and 1")

        # Typical substance moisture content
        typical_moisture = substance_registry.get_moisture_content(self.substance)

        # Adjust energy for moisture difference
        # More moisture = less usable energy
        moisture_factor = (1 - moisture_content) / (1 - typical_moisture)
        adjusted_value = energy.value * moisture_factor

        # Return adjusted energy
        return Quantity(
            adjusted_value,
            energy.unit,
            self.substance,
            "LHV",  # Usable energy is typically LHV
            self.reference_year
        )

    def calculate_emissions(self) -> 'Quantity':
        """Calculate CO2 emissions for this energy quantity.

        Returns:
            Quantity object with CO2 emissions in t
        """
        from .substance import substance_registry

        if self.dimension != "ENERGY":
            # Try to convert to energy first if possible
            if self.substance:
                energy = self.energy_content()
                return energy.calculate_emissions()
            else:
                raise ValueError(
                    f"Cannot calculate emissions for {self.unit} without substance")

        return substance_registry.calculate_emissions(self)

    def adjust_inflation(self, target_year: int) -> 'Quantity':
        """Adjust a cost quantity for inflation.

        Args:
            target_year: Year to adjust cost to

        Returns:
            Adjusted cost quantity
        """
        if self.reference_year is None:
            raise ValueError("Reference year not specified for inflation adjustment")

        if target_year == self.reference_year:
            return self

        # Simple inflation model (~2% per year)
        # In a real implementation, this would use actual inflation data
        years_diff = target_year - self.reference_year
        inflation_factor = (1 + 0.02) ** years_diff

        adjusted_value = self.value * inflation_factor

        # Return adjusted quantity
        return Quantity(
            adjusted_value,
            self.unit,
            self.substance,
            self.basis,
            target_year
        )

    def __str__(self) -> str:
        """String representation."""
        if self.substance:
            return f"{self.value} {self.unit} of {self.substance}"
        return f"{self.value} {self.unit}"

    def __repr__(self) -> str:
        """Detailed representation."""
        substance_str = f", '{self.substance}'" if self.substance else ""
        basis_str = f", basis='{self.basis}'" if self.basis else ""
        ref_year_str = f", reference_year={self.reference_year}" if self.reference_year else ""
        return f"Quantity({self.value}, '{self.unit}'{substance_str}{basis_str}{ref_year_str})"

    def __add__(self, other: 'Quantity') -> 'Quantity':
        """Add two quantities with compatible units."""
        if not isinstance(other, Quantity):
            raise TypeError(f"Cannot add Quantity and {type(other)}")

        # Convert other to this unit
        other_converted = other.to(self.unit)

        # Add values
        result_value = self.value + other_converted.value

        # Check for substance compatibility
        substance = self.substance
        if substance != other.substance:
            substance = None  # Clear substance if mixing different substances

        # Check for basis compatibility
        basis = self.basis
        if basis != other.basis:
            basis = None  # Clear basis if mixing different bases

        # Return new quantity
        return Quantity(
            result_value,
            self.unit,
            substance,
            basis,
            self.reference_year
        )

    def __mul__(self, other: Union[int, float]) -> 'Quantity':
        """Multiply quantity by a scalar."""
        if isinstance(other, Quantity):
            raise NotImplementedError(
                "Multiplication between quantities not implemented yet")

        # Scalar multiplication
        return Quantity(
            self.value * other,
            self.unit,
            self.substance,
            self.basis,
            self.reference_year
        )

    def __rmul__(self, other: Union[int, float]) -> 'Quantity':
        """Right multiplication by scalar."""
        return self.__mul__(other)

    def __truediv__(self, other: Union['Quantity', int, float]) -> 'Quantity':
        """Division operator."""
        if isinstance(other, Quantity):
            # Special case: Energy / Time = Power
            if (self.dimension == "ENERGY" and other.dimension == "TIME"):
                # Try to get the corresponding power unit
                try:
                    power_unit = registry.get_corresponding_unit(self.unit, "POWER")
                except ValueError:
                    power_unit = "MW"  # Default to MW if no correspondence

                # Convert both to standard units
                energy_mwh = self.to("MWh")
                time_h = other.to("h")

                # Calculate power
                power_value = energy_mwh.value / time_h.value

                # Convert to target power unit if needed
                if power_unit != "MW":
                    factor = registry.get_conversion_factor("MW", power_unit)
                    power_value = power_value * factor

                return Quantity(
                    power_value,
                    power_unit,
                    self.substance,
                    self.basis,
                    self.reference_year
                )

            # General case - create compound unit
            return Quantity(
                self.value / other.value,
                f"{self.unit}/{other.unit}",
                self.substance,
                self.basis,
                self.reference_year
            )
        else:
            # Division by scalar
            return Quantity(
                self.value / other,
                self.unit,
                self.substance,
                self.basis,
                self.reference_year
            )

    def __lt__(self, other: 'Quantity') -> bool:
        """Less than comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value < other_converted.value)

    def __gt__(self, other: 'Quantity') -> bool:
        """Greater than comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value > other_converted.value)

    def __eq__(self, other: 'Quantity') -> bool:
        """Equal comparison."""
        if not isinstance(other, Quantity):
            return False
        other_converted = other.to(self.unit)
        return np.all(self.value == other_converted.value)

    def __le__(self, other: 'Quantity') -> bool:
        """Less than or equal comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value <= other_converted.value)

    def __ge__(self, other: 'Quantity') -> bool:
        """Greater than or equal comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value >= other_converted.value)

    def __ne__(self, other: 'Quantity') -> bool:
        """Not equal comparison."""
        if not isinstance(other, Quantity):
            return True
        other_converted = other.to(self.unit)
        return np.any(self.value != other_converted.value)