import numpy as np
from .registry import registry


class Quantity:
    """A physical quantity with value and unit."""

    def __init__(self, value, unit, substance=None):
        """Initialize a physical quantity.

        Args:
            value: Numerical value (scalar or array)
            unit: Unit string (e.g., "MWh", "GJ")
            substance: Optional substance specifier (e.g., "coal", "natural_gas")
        """
        self.value = np.asarray(value)
        self.unit = unit
        self.substance = substance

        # Get dimension from registry
        self.dimension = registry.get_dimension(unit)

    def to(self, target_unit):
        """Convert to another unit with the same dimension.

        Args:
            target_unit: Target unit to convert to

        Returns:
            A new Quantity object with converted value and target unit
        """
        # Get conversion factor from registry
        factor = registry.get_conversion_factor(self.unit, target_unit)

        # Apply conversion
        new_value = self.value * factor

        # Return new quantity with same metadata
        return Quantity(new_value, target_unit, self.substance)

    def for_duration(self, hours):
        """Convert power to energy for a specified duration.

        Args:
            hours: Duration in hours

        Returns:
            Energy quantity
        """
        if registry.get_dimension(self.unit) != "POWER":
            raise ValueError(
                f"for_duration only applies to power units, not {self.unit}")

        # Map power unit to corresponding energy unit
        power_to_energy = {
            "W": "Wh",
            "kW": "kWh",
            "MW": "MWh",
            "GW": "GWh",
            "TW": "TWh",
        }

        energy_unit = power_to_energy.get(self.unit)
        if not energy_unit:
            raise ValueError(f"No corresponding energy unit for {self.unit}")

        # Power * time = energy
        energy_value = self.value * hours

        return Quantity(energy_value, energy_unit, self.substance)

    def __str__(self):
        """String representation."""
        if self.substance:
            return f"{self.value} {self.unit} of {self.substance}"
        return f"{self.value} {self.unit}"

    def __repr__(self):
        """Detailed representation."""
        substance_str = f", '{self.substance}'" if self.substance else ""
        return f"Quantity({self.value}, '{self.unit}'{substance_str})"

    def __add__(self, other):
        """Add two quantities with compatible units."""
        if not isinstance(other, Quantity):
            raise TypeError(f"Cannot add Quantity and {type(other)}")

        # Convert other to this unit
        other_converted = other.to(self.unit)

        # Add values
        result_value = self.value + other_converted.value

        # Return new quantity with this unit
        return Quantity(result_value, self.unit, self.substance)

    def __mul__(self, other):
        """Multiply quantity by a scalar."""
        if isinstance(other, Quantity):
            raise NotImplementedError(
                "Multiplication between quantities not implemented yet")

        # Scalar multiplication
        return Quantity(self.value * other, self.unit, self.substance)

    def __rmul__(self, other):
        """Right multiplication by scalar."""
        return self.__mul__(other)

    def __truediv__(self, other):
        """Division operator."""
        if isinstance(other, Quantity):
            # Energy / time special case
            if (self.dimension == "ENERGY" and
                    other.dimension == "TIME"):
                if self.unit == "MWh" and other.unit == "h":
                    return Quantity(self.value / other.value, "MW", self.substance)
                # Handle other energy/time combinations

            # General case - create compound unit
            return Quantity(
                self.value / other.value,
                f"{self.unit}/{other.unit}",
                self.substance
            )
        else:
            # Division by scalar
            return Quantity(self.value / other, self.unit, self.substance)

    def __lt__(self, other):
        """Less than comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value < other_converted.value)

    def __gt__(self, other):
        """Greater than comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value > other_converted.value)

    def __eq__(self, other):
        """Equal comparison."""
        if not isinstance(other, Quantity):
            return False
        other_converted = other.to(self.unit)
        return np.all(self.value == other_converted.value)
