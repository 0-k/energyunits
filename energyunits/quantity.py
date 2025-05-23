"""
Quantity class for energy system modeling with unified conversion methods.
"""

from typing import List, Optional, Union

import numpy as np

from .registry import registry


class Quantity:
    """A physical quantity with value and unit."""

    def __init__(
        self,
        value: Union[float, int, List[float], np.ndarray],
        unit: str,
        substance: Optional[str] = None,
        basis: Optional[str] = None,
        reference_year: Optional[int] = None,
    ):
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
        self.dimension = registry.get_dimension(unit)

    def to(self, target_unit: Optional[str] = None, basis: Optional[str] = None, substance: Optional[str] = None) -> "Quantity":
        """Convert to another unit, basis, and/or substance.

        Args:
            target_unit: Target unit to convert to (optional)
            basis: Target heating value basis - 'HHV' or 'LHV' (optional)
            substance: Target substance for combustion products - 'CO2', 'H2O', 'ash' (optional)

        Returns:
            A new Quantity object with converted unit, basis, and/or substance

        Examples:
            >>> energy = Quantity(100, "MWh")
            >>> energy.to("GJ")                           # Unit conversion
            >>> energy.to(basis="LHV")                    # Basis conversion
            >>> coal = Quantity(1000, "kg", "coal")
            >>> coal.to("kg", substance="CO2")            # Combustion product
            >>> coal.to("t", basis="LHV", substance="CO2") # Combined conversions
        """
        result = self

        if substance is not None and self.substance != substance:
            result = result._convert_substance(substance)

        if basis is not None and result.basis != basis:
            result = result._convert_basis(basis)

        if target_unit is not None:
            result = result._convert_unit(target_unit)

        if target_unit is None and basis is None and substance is None:
            return Quantity(
                self.value, self.unit, self.substance, self.basis, self.reference_year
            )

        return result

    def for_duration(self, hours: float) -> "Quantity":
        """Convert power to energy for a specified duration."""
        if self.dimension != "POWER":
            raise ValueError(f"for_duration only applies to power units, not {self.unit}")

        try:
            energy_unit = registry.get_corresponding_unit(self.unit, "ENERGY")
        except ValueError:
            energy_unit = "MWh"

        energy_value = registry.convert_between_dimensions(
            self.value, self.unit, energy_unit, self.substance, hours=hours
        )

        return Quantity(
            energy_value, energy_unit, self.substance, self.basis, self.reference_year
        )

    def average_power(self, hours: float) -> "Quantity":
        """Calculate average power from energy over a specified duration."""
        if self.dimension != "ENERGY":
            raise ValueError(f"average_power only applies to energy units, not {self.unit}")

        try:
            power_unit = registry.get_corresponding_unit(self.unit, "POWER")
        except ValueError:
            power_unit = "MW"

        power_value = registry.convert_between_dimensions(
            self.value, self.unit, power_unit, self.substance, hours=hours
        )

        return Quantity(
            power_value, power_unit, self.substance, self.basis, self.reference_year
        )

    def calculate_emissions(self) -> "Quantity":
        """Calculate CO2 emissions (convenience wrapper for .to(substance="CO2"))."""
        # Handle renewables specially - they have zero emissions but no heating values
        if self.substance in ["wind", "solar", "hydro", "nuclear"]:
            return Quantity(0.0, "t", "CO2")

        return self.to("t", substance="CO2")

    def adjust_inflation(self, target_year: int) -> "Quantity":
        """Adjust a cost quantity for inflation."""
        if self.reference_year is None:
            raise ValueError("Reference year not specified for inflation adjustment")

        if target_year == self.reference_year:
            return self

        years_diff = target_year - self.reference_year
        inflation_factor = (1 + 0.02) ** years_diff  # 2% annual inflation
        adjusted_value = self.value * inflation_factor

        return Quantity(
            adjusted_value, self.unit, self.substance, self.basis, target_year
        )

    def __str__(self) -> str:
        """String representation."""
        if self.substance:
            return f"{self.value:.2f} {self.unit} of {self.substance}"
        return f"{self.value:.2f} {self.unit}"

    def __repr__(self) -> str:
        """Detailed representation."""
        substance_str = f", '{self.substance}'" if self.substance else ""
        basis_str = f", basis='{self.basis}'" if self.basis else ""
        ref_year_str = f", reference_year={self.reference_year}" if self.reference_year else ""
        return f"Quantity({self.value}, '{self.unit}'{substance_str}{basis_str}{ref_year_str})"

    def __add__(self, other: "Quantity") -> "Quantity":
        """Add two quantities with compatible units."""
        if not isinstance(other, Quantity):
            raise TypeError(f"Cannot add Quantity and {type(other)}")

        other_converted = other.to(self.unit)
        result_value = self.value + other_converted.value

        substance = self.substance if self.substance == other.substance else None
        basis = self.basis if self.basis == other.basis else None

        return Quantity(result_value, self.unit, substance, basis, self.reference_year)

    def __mul__(self, other: Union[int, float]) -> "Quantity":
        """Multiply quantity by a scalar."""
        if isinstance(other, Quantity):
            raise NotImplementedError("Multiplication between quantities not implemented yet")

        return Quantity(
            self.value * other, self.unit, self.substance, self.basis, self.reference_year
        )

    def __rmul__(self, other: Union[int, float]) -> "Quantity":
        """Right multiplication by scalar."""
        return self.__mul__(other)

    def __truediv__(self, other: Union["Quantity", int, float]) -> "Quantity":
        """Division operator."""
        if isinstance(other, Quantity):
            if self.dimension == "ENERGY" and other.dimension == "TIME":
                try:
                    power_unit = registry.get_corresponding_unit(self.unit, "POWER")
                except ValueError:
                    power_unit = "MW"

                energy_mwh = self.to("MWh")
                time_h = other.to("h")
                power_value = energy_mwh.value / time_h.value

                if power_unit != "MW":
                    factor = registry.get_conversion_factor("MW", power_unit)
                    power_value = power_value * factor

                return Quantity(
                    power_value, power_unit, self.substance, self.basis, self.reference_year
                )

            return Quantity(
                self.value / other.value, f"{self.unit}/{other.unit}",
                self.substance, self.basis, self.reference_year
            )
        else:
            return Quantity(
                self.value / other, self.unit, self.substance, self.basis, self.reference_year
            )

    def __lt__(self, other: "Quantity") -> bool:
        """Less than comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value < other_converted.value)

    def __gt__(self, other: "Quantity") -> bool:
        """Greater than comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value > other_converted.value)

    def __eq__(self, other: "Quantity") -> bool:
        """Equal comparison."""
        if not isinstance(other, Quantity):
            return False
        other_converted = other.to(self.unit)
        return np.all(self.value == other_converted.value)

    def __le__(self, other: "Quantity") -> bool:
        """Less than or equal comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value <= other_converted.value)

    def __ge__(self, other: "Quantity") -> bool:
        """Greater than or equal comparison."""
        other_converted = other.to(self.unit)
        return np.all(self.value >= other_converted.value)

    def __ne__(self, other: "Quantity") -> bool:
        """Not equal comparison."""
        if not isinstance(other, Quantity):
            return True
        other_converted = other.to(self.unit)
        return np.any(self.value != other_converted.value)

    # Internal methods - not part of public API
    def _convert_unit(self, target_unit: str) -> "Quantity":
        """Internal method to convert unit only."""
        from_dim = self.dimension
        to_dim = registry.get_dimension(target_unit)

        if from_dim == to_dim:
            factor = registry.get_conversion_factor(self.unit, target_unit)
            new_value = self.value * factor
        elif registry.are_dimensions_compatible(from_dim, to_dim):
            kwargs = {}
            if self.basis is not None:
                kwargs['basis'] = self.basis

            new_value = registry.convert_between_dimensions(
                self.value, self.unit, target_unit, self.substance, **kwargs
            )
        else:
            raise ValueError(
                f"Cannot convert from {self.unit} ({from_dim}) to {target_unit} ({to_dim})"
            )

        return Quantity(
            new_value, target_unit, self.substance, self.basis, self.reference_year
        )

    def _convert_basis(self, target_basis: str) -> "Quantity":
        """Internal method to convert heating value basis only."""
        if target_basis.upper() not in ["HHV", "LHV"]:
            raise ValueError("Basis must be 'HHV' or 'LHV'")

        if self.substance is None:
            raise ValueError("Substance must be specified for basis conversion")

        current_basis = self.basis or "LHV"
        target_basis = target_basis.upper()

        if current_basis.upper() == target_basis:
            return Quantity(
                self.value, self.unit, self.substance, target_basis, self.reference_year
            )

        from .substance import substance_registry

        lhv_hhv_ratio = substance_registry.get_lhv_hhv_ratio(self.substance)

        if current_basis.upper() == "HHV" and target_basis == "LHV":
            new_value = self.value * lhv_hhv_ratio
        elif current_basis.upper() == "LHV" and target_basis == "HHV":
            new_value = self.value / lhv_hhv_ratio
        else:
            raise ValueError(f"Invalid basis conversion: {current_basis} to {target_basis}")

        return Quantity(
            new_value, self.unit, self.substance, target_basis, self.reference_year
        )

    def _convert_substance(self, target_substance: str) -> "Quantity":
        """Internal method to convert to combustion products."""
        if self.substance is None:
            raise ValueError("Source substance must be specified for substance conversion")

        valid_products = ["CO2", "H2O", "ash"]
        if target_substance not in valid_products:
            raise ValueError(f"Substance conversion only supported for: {valid_products}")

        # Handle renewables specially - they have zero combustion products
        if self.substance in ["wind", "solar", "hydro", "nuclear"]:
            return Quantity(0.0, "kg", target_substance)

        if self.dimension == "ENERGY":
            fuel_mass = self.to("kg")
        else:
            fuel_mass = self

        from .substance import substance_registry

        combustion_product = substance_registry.calculate_combustion_product(fuel_mass, target_substance)

        return Quantity(
            combustion_product.value, combustion_product.unit, target_substance,
            None, self.reference_year
        )