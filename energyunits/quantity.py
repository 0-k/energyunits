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
            >>> coal.to("t", substance="CO2")             # Calculate CO2 emissions

            # Instead of wrapper methods, use multiplication/division:
            >>> power = Quantity(100, "MW")
            >>> time = Quantity(24, "h")
            >>> energy = power * time                     # 2400 MWh
            >>> avg_power = energy / time                 # 100 MW
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

    def __mul__(self, other: Union[int, float, "Quantity"]) -> "Quantity":
        """Multiply quantity by a scalar or another quantity."""
        if isinstance(other, (int, float)):
            # Scalar multiplication
            return Quantity(
                self.value * other, self.unit, self.substance, self.basis, self.reference_year
            )
        elif isinstance(other, Quantity):
            # Quantity multiplication
            result_value = self.value * other.value

            # Determine result unit through dimensional analysis
            result_unit = self._multiply_units(self.unit, other.unit, self.dimension, other.dimension)

            # Handle substance - clear if different, keep if same
            result_substance = self.substance if self.substance == other.substance else None

            # Handle basis - clear if different, keep if same
            result_basis = self.basis if self.basis == other.basis else None

            # Handle reference year - clear if different, keep if same
            result_ref_year = self.reference_year if self.reference_year == other.reference_year else None

            return Quantity(result_value, result_unit, result_substance, result_basis, result_ref_year)
        else:
            raise TypeError(f"Cannot multiply Quantity and {type(other)}")

    def _multiply_units(self, unit1: str, unit2: str, dim1: str, dim2: str) -> str:
        """Determine the result unit when multiplying two units."""
        # Special case: power * time = energy
        if (dim1 == "POWER" and dim2 == "TIME") or (dim1 == "TIME" and dim2 == "POWER"):
            power_unit = unit1 if dim1 == "POWER" else unit2
            try:
                # Get corresponding energy unit for the power unit
                return registry.get_corresponding_unit(power_unit, "ENERGY")
            except ValueError:
                return "MWh"  # fallback

        # Special case: mass * price_per_mass = currency
        # Handle compound units like USD/t * t = USD
        if "/" in unit1 and unit2 in unit1:
            # Extract numerator from compound unit
            numerator = unit1.split("/")[0]
            return numerator
        elif "/" in unit2 and unit1 in unit2:
            # Extract numerator from compound unit
            numerator = unit2.split("/")[0]
            return numerator

        # General case: create compound unit
        return f"{unit1}·{unit2}"

    def __rmul__(self, other: Union[int, float]) -> "Quantity":
        """Right multiplication by scalar."""
        return self.__mul__(other)

    def __truediv__(self, other: Union["Quantity", int, float]) -> "Quantity":
        """Division operator."""
        if isinstance(other, (int, float)):
            # Scalar division
            return Quantity(
                self.value / other, self.unit, self.substance, self.basis, self.reference_year
            )
        elif isinstance(other, Quantity):
            # Quantity division
            result_value = self.value / other.value

            # Determine result unit through dimensional analysis
            result_unit = self._divide_units(self.unit, other.unit, self.dimension, other.dimension)

            # Handle substance - clear if different, keep if same
            result_substance = self.substance if self.substance == other.substance else None

            # Handle basis - clear if different, keep if same
            result_basis = self.basis if self.basis == other.basis else None

            # Handle reference year - clear if different, keep if same
            result_ref_year = self.reference_year if self.reference_year == other.reference_year else None

            return Quantity(result_value, result_unit, result_substance, result_basis, result_ref_year)
        else:
            raise TypeError(f"Cannot divide Quantity by {type(other)}")

    def _divide_units(self, unit1: str, unit2: str, dim1: str, dim2: str) -> str:
        """Determine the result unit when dividing two units."""
        # Special case: energy / time = power
        if dim1 == "ENERGY" and dim2 == "TIME":
            try:
                return registry.get_corresponding_unit(unit1, "POWER")
            except ValueError:
                return "MW"  # fallback

        # Special case: same units = dimensionless (ratio)
        if unit1 == unit2:
            return ""  # dimensionless

        # General case: create compound unit
        return f"{unit1}/{unit2}"

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

        lhv_hhv_ratio = substance_registry.lhv_hhv_ratio(self.substance)

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
            return Quantity(0.0, "t", target_substance)

        from .substance import substance_registry

        # Pass self directly - calculate_combustion_product handles the mass conversion
        combustion_product = substance_registry.calculate_combustion_product(self, target_substance)

        return Quantity(
            combustion_product.value, combustion_product.unit, target_substance,
            None, self.reference_year
        )