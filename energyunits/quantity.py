"""Quantity class for energy system modeling with unified .to() conversion."""

from typing import List, Optional, Union

import numpy as np

from .registry import registry


class Quantity:
    """Physical quantity with value, unit, and optional metadata.

    Supports:
    - Unit conversions (e.g., MWh to GJ)
    - Substance-based conversions (e.g., coal mass to CO2 emissions)
    - Heating value basis conversions (HHV/LHV)
    - Inflation adjustments for cost quantities
    - Arithmetic operations with dimensional analysis
    """

    def __init__(
        self,
        value: Union[float, int, List[float], np.ndarray],
        unit: str,
        substance: Optional[str] = None,
        basis: Optional[str] = None,
        reference_year: Optional[int] = None,
    ) -> None:
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
        """Convert to another unit, basis, substance, and/or reference year.

        This is the unified conversion method. Conversions are applied in sequence:
        substance → basis → unit → inflation.

        Examples:
            energy = Quantity(100, "MWh")
            energy.to("GJ")  # → 360 GJ

            coal = Quantity(1000, "kg", "coal")
            coal.to("MWh")  # Coal mass → energy content
            coal.to("kg", substance="CO2")  # Coal mass → CO2 emissions

            capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
            capex_2025 = capex_2020.to(reference_year=2025)
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

        if all(x is None for x in [target_unit, basis, substance, reference_year]):
            return Quantity(
                self.value, self.unit, self.substance, self.basis, self.reference_year
            )

        return result

    def __str__(self) -> str:
        if np.isscalar(self.value) or self.value.size == 1:
            scalar_val = self.value.item() if hasattr(self.value, "item") else self.value
            value_str = f"{scalar_val:.2f}"
        else:
            if self.value.size <= 5:
                value_str = f"[{', '.join(f'{v:.2f}' for v in self.value.flat)}]"
            else:
                value_str = f"[{self.value.flat[0]:.2f}, ..., {self.value.flat[-1]:.2f}] ({self.value.size} values)"

        if self.substance:
            return f"{value_str} {self.unit} of {self.substance}"
        return f"{value_str} {self.unit}"

    def __repr__(self) -> str:
        substance_str = f", '{self.substance}'" if self.substance else ""
        basis_str = f", basis='{self.basis}'" if self.basis else ""
        ref_year_str = f", reference_year={self.reference_year}" if self.reference_year else ""
        return f"Quantity({self.value}, '{self.unit}'{substance_str}{basis_str}{ref_year_str})"

    def __add__(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            raise TypeError(f"Cannot add Quantity and {type(other)}")

        other_converted = other.to(self.unit)
        result_value = self.value + other_converted.value

        substance = self.substance if self.substance == other.substance else None
        basis = self.basis if self.basis == other.basis else None

        return Quantity(result_value, self.unit, substance, basis, self.reference_year)

    def __mul__(self, other: Union[int, float, "Quantity"]) -> "Quantity":
        if isinstance(other, (int, float)):
            return Quantity(
                self.value * other,
                self.unit,
                self.substance,
                self.basis,
                self.reference_year,
            )
        elif isinstance(other, Quantity):
            # Smart compound unit cancellation: convert units to match denominators
            self_converted = self
            other_converted = other

            # Check if self has compound unit (e.g., USD/kW) and other matches denominator dimension
            if "/" in self.unit:
                denominator = self.unit.split("/", 1)[1]
                denominator_dim = registry.get_dimension(denominator)
                if other.dimension == denominator_dim and other.unit != denominator:
                    other_converted = other.to(denominator)

            # Check if other has compound unit and self matches denominator dimension
            elif "/" in other.unit:
                denominator = other.unit.split("/", 1)[1]
                denominator_dim = registry.get_dimension(denominator)
                if self.dimension == denominator_dim and self.unit != denominator:
                    self_converted = self.to(denominator)

            result_value = self_converted.value * other_converted.value
            result_unit = self._multiply_units(
                self_converted.unit, other_converted.unit,
                self_converted.dimension, other_converted.dimension
            )

            if self.substance == other.substance:
                result_substance = self.substance
            elif self.substance is None:
                result_substance = other.substance
            elif other.substance is None:
                result_substance = self.substance
            else:
                result_substance = None

            result_basis = self.basis if self.basis == other.basis else None
            result_ref_year = (
                self.reference_year if self.reference_year == other.reference_year else None
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
        # Compound unit cancellation (e.g., GWh/min * min = GWh, USD/t * t = USD)
        if "/" in unit1 and unit2 in unit1:
            return unit1.split("/")[0]
        elif "/" in unit2 and unit1 in unit2:
            return unit2.split("/")[0]

        # Check dimensional multiplication rules from data
        result = registry.get_multiplication_result(dim1, dim2)
        if result:
            result_dimension, source_dimension = result
            source_unit = unit1 if dim1 == source_dimension else unit2
            return registry.get_corresponding_unit(source_unit, result_dimension)

        return f"{unit1}·{unit2}"

    def __rmul__(self, other: Union[int, float]) -> "Quantity":
        return self.__mul__(other)

    def __truediv__(self, other: Union["Quantity", int, float]) -> "Quantity":
        if isinstance(other, (int, float)):
            return Quantity(
                self.value / other,
                self.unit,
                self.substance,
                self.basis,
                self.reference_year,
            )
        elif isinstance(other, Quantity):
            result_value = self.value / other.value
            result_unit = self._divide_units(
                self.unit, other.unit, self.dimension, other.dimension
            )

            if self.substance == other.substance:
                result_substance = self.substance
            elif self.substance is None:
                result_substance = other.substance
            elif other.substance is None:
                result_substance = self.substance
            else:
                result_substance = None

            result_basis = self.basis if self.basis == other.basis else None
            result_ref_year = (
                self.reference_year if self.reference_year == other.reference_year else None
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
        # Check dimensional division rules from data
        result_dimension = registry.get_division_result(dim1, dim2)
        if result_dimension:
            return registry.get_corresponding_unit(unit1, result_dimension)

        # Same units = dimensionless
        if unit1 == unit2:
            return ""

        return f"{unit1}/{unit2}"

    def __lt__(self, other: "Quantity") -> bool:
        other_converted = other.to(self.unit)
        return np.all(self.value < other_converted.value)

    def __gt__(self, other: "Quantity") -> bool:
        other_converted = other.to(self.unit)
        return np.all(self.value > other_converted.value)

    def __eq__(self, other: "Quantity") -> bool:
        if not isinstance(other, Quantity):
            return False
        other_converted = other.to(self.unit)
        return np.all(self.value == other_converted.value)

    def __le__(self, other: "Quantity") -> bool:
        other_converted = other.to(self.unit)
        return np.all(self.value <= other_converted.value)

    def __ge__(self, other: "Quantity") -> bool:
        other_converted = other.to(self.unit)
        return np.all(self.value >= other_converted.value)

    def __ne__(self, other: "Quantity") -> bool:
        if not isinstance(other, Quantity):
            return True
        other_converted = other.to(self.unit)
        return np.any(self.value != other_converted.value)

    def _convert_unit(self, target_unit: str) -> "Quantity":
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
        if self.substance is None:
            raise ValueError("Source substance must be specified for substance conversion")

        valid_products = ["CO2", "H2O", "ash"]
        if target_substance not in valid_products:
            raise ValueError(f"Substance conversion only supported for: {valid_products}")

        # Renewables have zero combustion products
        if self.substance in ["wind", "solar", "hydro", "nuclear"]:
            return Quantity(0.0, "t", target_substance)

        from .substance import substance_registry

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
        if self.reference_year is None:
            raise ValueError("Reference year not specified for inflation adjustment")

        if target_year == self.reference_year:
            return Quantity(
                self.value, self.unit, self.substance, self.basis, target_year
            )

        from .inflation import inflation_registry

        currency = inflation_registry.detect_currency_from_unit(self.unit)
        if currency is None:
            raise ValueError(
                f"Cannot detect currency from unit '{self.unit}'. "
                f"Supported currencies: {inflation_registry.get_supported_currencies()}"
            )

        inflation_factor = inflation_registry.get_cumulative_inflation_factor(
            currency, self.reference_year, target_year
        )

        adjusted_value = self.value * inflation_factor

        return Quantity(
            adjusted_value, self.unit, self.substance, self.basis, target_year
        )
