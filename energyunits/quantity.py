"""
Quantity class for energy system modeling with unified conversion methods.

This module provides the core Quantity class that represents physical quantities
with units, substances, and basis specifications. It supports comprehensive
conversions including unit, substance, basis, and inflation adjustments.
"""

from typing import List, Optional, Union

import numpy as np

from .registry import registry


class Quantity:
    """
    A physical quantity with value, unit, and optional metadata.

    Represents physical quantities in energy system modeling with support for:
    - Unit conversions (e.g., MWh to GJ)
    - Substance-based conversions (e.g., coal mass to CO2 emissions)
    - Heating value basis conversions (HHV/LHV)
    - Inflation adjustments for cost quantities
    - Arithmetic operations with dimensional analysis

    Attributes:
        value: Numerical value as numpy array
        unit: Unit string (e.g., "MWh", "USD/kW")
        substance: Optional substance identifier (e.g., "coal", "natural_gas")
        basis: Optional heating value basis ("HHV" or "LHV")
        reference_year: Optional reference year for cost quantities
        dimension: Physical dimension determined from unit
    """

    def __init__(
        self,
        value: Union[float, int, List[float], np.ndarray],
        unit: str,
        substance: Optional[str] = None,
        basis: Optional[str] = None,
        reference_year: Optional[int] = None,
    ) -> None:
        """
        Initialize a physical quantity.

        Args:
            value: Numerical value (scalar, list, or numpy array)
            unit: Unit string (e.g., "MWh", "GJ", "USD/kW")
            substance: Optional substance specifier for fuel/material properties
                      (e.g., "coal", "natural_gas", "biomass")
            basis: Optional heating value basis for energy conversions
                   ("HHV" for higher heating value, "LHV" for lower heating value)
            reference_year: Optional reference year for cost quantities
                           (used for inflation adjustments)

        Raises:
            ValueError: If unit is not recognized in the registry
        """
        self.value: np.ndarray = np.asarray(value)
        self.unit: str = unit
        self.substance: Optional[str] = substance
        self.basis: Optional[str] = basis
        self.reference_year: Optional[int] = reference_year
        self.dimension: str = registry.get_dimension(unit)

    def to(
        self,
        target_unit: Optional[str] = None,
        basis: Optional[str] = None,
        substance: Optional[str] = None,
        reference_year: Optional[int] = None,
    ) -> "Quantity":
        """
        Convert to another unit, basis, substance, and/or reference year.

        This is the unified conversion method that handles all types of quantity
        transformations. Conversions are applied in sequence: substance → basis → unit → inflation.

        Args:
            target_unit: Target unit to convert to. Can be same dimension (e.g., "MWh" → "GJ")
                        or compatible dimensions (e.g., "kg" coal → "MWh" energy)
            basis: Target heating value basis for energy content calculations
                  ("HHV" for higher heating value, "LHV" for lower heating value)
            substance: Target substance for combustion product calculations
                      (supported: "CO2", "H2O", "ash" for emissions/byproducts)
            reference_year: Target reference year for inflation adjustment of cost quantities
                           (automatically detects currency from unit)

        Returns:
            New Quantity object with requested conversions applied

        Raises:
            ValueError: If conversion is not possible (incompatible units, missing data, etc.)
            TypeError: If arguments are of wrong type

        Examples:
            Basic unit conversions:
            >>> energy = Quantity(100, "MWh")
            >>> energy.to("GJ")                           # → 360 GJ

            Substance-based conversions:
            >>> coal = Quantity(1000, "kg", "coal")
            >>> coal.to("MWh")                            # Coal mass → energy content
            >>> coal.to("kg", substance="CO2")            # Coal mass → CO2 emissions

            Combined conversions:
            >>> coal.to("t", basis="LHV", substance="CO2") # Mass + basis + emissions

            Inflation adjustments:
            >>> capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
            >>> capex_2025 = capex_2020.to(reference_year=2025)  # Uses cached USD rates
            >>> capex_eur = Quantity(900, "EUR/kW", reference_year=2020)
            >>> capex_eur_2025 = capex_eur.to(reference_year=2025)  # Uses cached EUR rates

            Multi-step conversions:
            >>> capex_2020.to("EUR/MW", reference_year=2025)  # Unit + inflation (if EUR rates available)
        """
        result = self

        if substance is not None and self.substance != substance:
            result = result._convert_substance(substance)

        if basis is not None and result.basis != basis:
            result = result._convert_basis(basis)

        if target_unit is not None:
            result = result._convert_unit(target_unit)

        if reference_year is not None:
            result = result._convert_reference_year(reference_year)

        if (
            target_unit is None
            and basis is None
            and substance is None
            and reference_year is None
        ):
            return Quantity(
                self.value, self.unit, self.substance, self.basis, self.reference_year
            )

        return result

    def __str__(self) -> str:
        """String representation."""
        # Handle scalar vs array values
        if np.isscalar(self.value) or self.value.size == 1:
            # Single value - format as scalar
            scalar_val = (
                self.value.item() if hasattr(self.value, "item") else self.value
            )
            value_str = f"{scalar_val:.2f}"
        else:
            # Multiple values - show as array
            if self.value.size <= 5:
                value_str = f"[{', '.join(f'{v:.2f}' for v in self.value.flat)}]"
            else:
                value_str = f"[{self.value.flat[0]:.2f}, ..., {self.value.flat[-1]:.2f}] ({self.value.size} values)"

        if self.substance:
            return f"{value_str} {self.unit} of {self.substance}"
        return f"{value_str} {self.unit}"

    def __repr__(self) -> str:
        """Detailed representation."""
        substance_str = f", '{self.substance}'" if self.substance else ""
        basis_str = f", basis='{self.basis}'" if self.basis else ""
        ref_year_str = (
            f", reference_year={self.reference_year}" if self.reference_year else ""
        )
        return f"Quantity({self.value}, '{self.unit}'{substance_str}{basis_str}{ref_year_str})"

    def __add__(self, other: "Quantity") -> "Quantity":
        """
        Add two quantities with compatible units.

        Args:
            other: Another Quantity to add

        Returns:
            New Quantity with sum of values in the first quantity's unit

        Raises:
            TypeError: If other is not a Quantity
            ValueError: If units are incompatible for addition

        Note:
            Substance and basis are preserved only if both quantities have the same values,
            otherwise they are cleared in the result.
        """
        if not isinstance(other, Quantity):
            raise TypeError(f"Cannot add Quantity and {type(other)}")

        other_converted = other.to(self.unit)
        result_value = self.value + other_converted.value

        substance = self.substance if self.substance == other.substance else None
        basis = self.basis if self.basis == other.basis else None

        return Quantity(result_value, self.unit, substance, basis, self.reference_year)

    def __mul__(self, other: Union[int, float, "Quantity"]) -> "Quantity":
        """
        Multiply quantity by a scalar or another quantity.

        Args:
            other: Scalar (int, float) or another Quantity

        Returns:
            New Quantity with multiplied values and appropriate unit

        Raises:
            TypeError: If other is not a supported type

        Examples:
            >>> power = Quantity(100, "MW")
            >>> time = Quantity(24, "h")
            >>> energy = power * time                     # → 2400 MWh
            >>> doubled = power * 2                       # → 200 MW
            >>> cost_per_unit = Quantity(50, "USD/t")
            >>> mass = Quantity(1000, "t", "coal")
            >>> total_cost = cost_per_unit * mass         # → 50000 USD
        """
        if isinstance(other, (int, float)):
            # Scalar multiplication
            return Quantity(
                self.value * other,
                self.unit,
                self.substance,
                self.basis,
                self.reference_year,
            )
        elif isinstance(other, Quantity):
            # Quantity multiplication
            result_value = self.value * other.value

            # Determine result unit through dimensional analysis
            result_unit = self._multiply_units(
                self.unit, other.unit, self.dimension, other.dimension
            )

            # Handle substance - preserve non-None substance if one is None, clear if both differ
            if self.substance == other.substance:
                result_substance = self.substance
            elif self.substance is None:
                result_substance = other.substance
            elif other.substance is None:
                result_substance = self.substance
            else:
                result_substance = None  # Both have different non-None substances

            # Handle basis - clear if different, keep if same
            result_basis = self.basis if self.basis == other.basis else None

            # Handle reference year - clear if different, keep if same
            result_ref_year = (
                self.reference_year
                if self.reference_year == other.reference_year
                else None
            )

            return Quantity(
                result_value,
                result_unit,
                result_substance,
                result_basis,
                result_ref_year,
            )
        else:
            raise TypeError(f"Cannot multiply Quantity and {type(other)}")

    def _multiply_units(self, unit1: str, unit2: str, dim1: str, dim2: str) -> str:
        """
        Determine the result unit when multiplying two units.

        Args:
            unit1: First unit string
            unit2: Second unit string
            dim1: Physical dimension of first unit
            dim2: Physical dimension of second unit

        Returns:
            Appropriate result unit string
        """
        # Special case: power * time = energy
        if (dim1 == "POWER" and dim2 == "TIME") or (dim1 == "TIME" and dim2 == "POWER"):
            power_unit = unit1 if dim1 == "POWER" else unit2
            try:
                # Get corresponding energy unit for the power unit
                return registry.get_corresponding_unit(power_unit, "ENERGY")
            except ValueError:
                raise ValueError(
                    f"Cannot determine energy unit for power unit '{power_unit}'. "
                    f"No corresponding energy unit defined in registry."
                )

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
                self.value / other,
                self.unit,
                self.substance,
                self.basis,
                self.reference_year,
            )
        elif isinstance(other, Quantity):
            # Quantity division
            result_value = self.value / other.value

            # Determine result unit through dimensional analysis
            result_unit = self._divide_units(
                self.unit, other.unit, self.dimension, other.dimension
            )

            # Handle substance - preserve non-None substance if one is None, clear if both differ
            if self.substance == other.substance:
                result_substance = self.substance
            elif self.substance is None:
                result_substance = other.substance
            elif other.substance is None:
                result_substance = self.substance
            else:
                result_substance = None  # Both have different non-None substances

            # Handle basis - clear if different, keep if same
            result_basis = self.basis if self.basis == other.basis else None

            # Handle reference year - clear if different, keep if same
            result_ref_year = (
                self.reference_year
                if self.reference_year == other.reference_year
                else None
            )

            return Quantity(
                result_value,
                result_unit,
                result_substance,
                result_basis,
                result_ref_year,
            )
        else:
            raise TypeError(f"Cannot divide Quantity by {type(other)}")

    def _divide_units(self, unit1: str, unit2: str, dim1: str, dim2: str) -> str:
        """Determine the result unit when dividing two units."""
        # Special case: energy / time = power
        if dim1 == "ENERGY" and dim2 == "TIME":
            try:
                return registry.get_corresponding_unit(unit1, "POWER")
            except ValueError:
                raise ValueError(
                    f"Cannot determine power unit for energy unit '{unit1}'. "
                    f"No corresponding power unit defined in registry."
                )

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
                kwargs["basis"] = self.basis

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
            raise ValueError(
                f"Invalid basis conversion: {current_basis} to {target_basis}"
            )

        return Quantity(
            new_value, self.unit, self.substance, target_basis, self.reference_year
        )

    def _convert_substance(self, target_substance: str) -> "Quantity":
        """Internal method to convert to combustion products."""
        if self.substance is None:
            raise ValueError(
                "Source substance must be specified for substance conversion"
            )

        valid_products = ["CO2", "H2O", "ash"]
        if target_substance not in valid_products:
            raise ValueError(
                f"Substance conversion only supported for: {valid_products}"
            )

        # Handle renewables specially - they have zero combustion products
        if self.substance in ["wind", "solar", "hydro", "nuclear"]:
            return Quantity(0.0, "t", target_substance)

        from .substance import substance_registry

        # Pass self directly - calculate_combustion_product handles the mass conversion
        combustion_product = substance_registry.calculate_combustion_product(
            self, target_substance
        )

        return Quantity(
            combustion_product.value,
            combustion_product.unit,
            target_substance,
            None,
            self.reference_year,
        )

    def _convert_reference_year(self, target_year: int) -> "Quantity":
        """Internal method to convert reference year using inflation data."""
        if self.reference_year is None:
            raise ValueError("Reference year not specified for inflation adjustment")

        if target_year == self.reference_year:
            return Quantity(
                self.value, self.unit, self.substance, self.basis, target_year
            )

        from .inflation import inflation_registry

        # Try to detect currency from unit
        currency = inflation_registry.detect_currency_from_unit(self.unit)
        if currency is None:
            raise ValueError(
                f"Cannot detect currency from unit '{self.unit}'. "
                f"Supported currencies: {inflation_registry.get_supported_currencies()}"
            )

        # Get inflation factor
        inflation_factor = inflation_registry.get_cumulative_inflation_factor(
            currency, self.reference_year, target_year
        )

        adjusted_value = self.value * inflation_factor

        return Quantity(
            adjusted_value, self.unit, self.substance, self.basis, target_year
        )
