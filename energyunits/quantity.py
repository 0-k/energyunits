import numpy as np
from .registry import registry
from .substance import substance_registry


class Quantity:
    """A physical quantity with value and unit."""

    def __init__(self, value, unit, substance=None, basis=None, reference_year=None):
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

    def to(self, target_unit):
        """Convert to another unit with the same dimension.

        Args:
            target_unit: Target unit to convert to

        Returns:
            A new Quantity object with converted value and target unit
        """
        # Check if it's a substance-specific conversion between dimensions
        if self.substance and registry.get_dimension(self.unit) != registry.get_dimension(target_unit):
            # Handle special conversions based on substance properties
            if (registry.get_dimension(self.unit) == "MASS" and
                    registry.get_dimension(target_unit) == "VOLUME"):
                # Convert mass to volume using density
                # Get substance density (kg/m3)
                density = substance_registry.get_density(self.substance)

                # Convert to standard units (t -> kg, m3)
                mass_kg = self.to("kg").value

                # Calculate volume in m3
                volume_m3 = mass_kg / density

                # Convert to target volume unit if not m3
                if target_unit != "m3":
                    factor = registry.get_conversion_factor("m3", target_unit)
                    volume = volume_m3 * factor
                else:
                    volume = volume_m3

                return Quantity(
                    volume,
                    target_unit,
                    self.substance,
                    self.basis,
                    self.reference_year
                )

            elif (registry.get_dimension(self.unit) == "VOLUME" and
                  registry.get_dimension(target_unit) == "MASS"):
                # Convert volume to mass using density
                # Get substance density (kg/m3)
                density = substance_registry.get_density(self.substance)

                # Convert to standard unit (m3)
                volume_m3 = self.to("m3").value

                # Calculate mass in kg
                mass_kg = volume_m3 * density

                # Convert to target mass unit
                if target_unit != "kg":
                    factor = registry.get_conversion_factor("kg", target_unit)
                    mass = mass_kg * factor
                else:
                    mass = mass_kg

                return Quantity(
                    mass,
                    target_unit,
                    self.substance,
                    self.basis,
                    self.reference_year
                )

            else:
                raise ValueError(
                    f"Cannot convert from {self.unit} to {target_unit} for {self.substance}")

        # Regular conversion for compatible units
        # Get conversion factor from registry
        factor = registry.get_conversion_factor(self.unit, target_unit)

        # Apply conversion
        new_value = self.value * factor

        # Return new quantity with same metadata
        return Quantity(
            new_value,
            target_unit,
            self.substance,
            self.basis,
            self.reference_year
        )

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

        return Quantity(
            energy_value,
            energy_unit,
            self.substance,
            self.basis,
            self.reference_year
        )

    def average_power(self, hours):
        """Calculate average power from energy over a specified duration.

        Args:
            hours: Duration in hours

        Returns:
            Power quantity
        """
        if registry.get_dimension(self.unit) != "ENERGY":
            raise ValueError(
                f"average_power only applies to energy units, not {self.unit}")

        # Map energy unit to corresponding power unit
        energy_to_power = {
            "Wh": "W",
            "kWh": "kW",
            "MWh": "MW",
            "GWh": "GW",
            "TWh": "TW",
        }

        power_unit = energy_to_power.get(self.unit)
        if not power_unit:
            # Convert to MWh first, then to MW
            energy_mwh = self.to("MWh")
            power_value = energy_mwh.value / hours
            return Quantity(
                power_value,
                "MW",
                self.substance,
                self.basis,
                self.reference_year
            )

        # Energy / time = power
        power_value = self.value / hours

        return Quantity(
            power_value,
            power_unit,
            self.substance,
            self.basis,
            self.reference_year
        )

    def energy_content(self, basis="HHV"):
        """Calculate energy content based on substance properties.

        Args:
            basis: Heating value basis ("HHV" or "LHV")

        Returns:
            Energy quantity in MWh
        """
        result = substance_registry.calculate_energy_content(self, basis)
        result.basis = basis
        return result

    def to_lhv(self):
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

    def to_hhv(self):
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

    def usable_energy(self, moisture_content=None):
        """Calculate usable energy considering moisture content.

        Args:
            moisture_content: Override moisture content (0.0 to 1.0),
                             if None, uses default for substance

        Returns:
            Energy quantity adjusted for moisture
        """
        if self.substance is None:
            raise ValueError("Substance must be specified for usable energy calculation")

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

    def calculate_emissions(self):
        """Calculate CO2 emissions for this energy quantity.

        Returns:
            Quantity object with CO2 emissions in t
        """
        if registry.get_dimension(self.unit) != "ENERGY":
            # Try to convert to energy first if possible
            if self.substance:
                energy = self.energy_content()
                return energy.calculate_emissions()
            else:
                raise ValueError(
                    f"Cannot calculate emissions for {self.unit} without substance")

        return substance_registry.calculate_emissions(self)

    def adjust_inflation(self, target_year):
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

    def __str__(self):
        """String representation."""
        if self.substance:
            return f"{self.value} {self.unit} of {self.substance}"
        return f"{self.value} {self.unit}"

    def __repr__(self):
        """Detailed representation."""
        substance_str = f", '{self.substance}'" if self.substance else ""
        basis_str = f", basis='{self.basis}'" if self.basis else ""
        ref_year_str = f", reference_year={self.reference_year}" if self.reference_year else ""
        return f"Quantity({self.value}, '{self.unit}'{substance_str}{basis_str}{ref_year_str})"

    def __add__(self, other):
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

    def __mul__(self, other):
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
                    return Quantity(
                        self.value / other.value,
                        "MW",
                        self.substance,
                        self.basis,
                        self.reference_year
                    )

                # Handle other energy/time combinations
                # Convert both to standard units (MWh/h) first
                energy_mwh = self.to("MWh")
                time_h = other.to("h")
                power_mw = energy_mwh.value / time_h.value
                return Quantity(
                    power_mw,
                    "MW",
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

    def __le__(self, other):
        """Less than or equal comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value <= other_converted.value)

    def __ge__(self, other):
        """Greater than or equal comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value >= other_converted.value)

    def __ne__(self, other):
        """Not equal comparison."""
        if not isinstance(other, Quantity):
            return True
        other_converted = other.to(self.unit)
        return np.any(self.value != other_converted.value)