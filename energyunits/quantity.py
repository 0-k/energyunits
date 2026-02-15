"""Quantity class for energy system modeling with unified .to() conversion."""

import warnings
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

    @classmethod
    def list_units(cls, dimension=None):
        """List all available units, optionally filtered by dimension.

        Args:
            dimension: Filter by dimension (e.g., "ENERGY", "POWER", "MASS").

        Returns:
            Sorted list of unit strings.

        Examples:
            Quantity.list_units()            # All units
            Quantity.list_units("ENERGY")    # Energy units only
        """
        return registry.list_units(dimension)

    @classmethod
    def list_dimensions(cls):
        """List all available dimensions.

        Returns:
            Sorted list of dimension strings.
        """
        return registry.list_dimensions()

    @classmethod
    def list_substances(cls, has_property=None):
        """List all available substances.

        Args:
            has_property: Filter to substances with this property (e.g., "hhv").

        Returns:
            Sorted list of substance names.

        Examples:
            Quantity.list_substances()                # All substances
            Quantity.list_substances("density")       # Substances with density
        """
        from .substance import substance_registry

        return substance_registry.list_substances(has_property)

    @classmethod
    def list_currencies(cls):
        """List all available currencies.

        Returns:
            List of currency codes.
        """
        from .exchange_rate import exchange_rate_registry

        return exchange_rate_registry.get_supported_currencies()

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

        **Special case**: When combining currency conversion with year change:
        - Order becomes: substance → basis → inflation → unit
        - Uses "inflate first, then convert" convention
        - Issues warning about economic assumptions

        Examples:
            energy = Quantity(100, "MWh")
            energy.to("GJ")  # → 360 GJ

            coal = Quantity(1000, "kg", "coal")
            coal.to("MWh")  # Coal mass → energy content
            coal.to("kg", substance="CO2")  # Coal mass → CO2 emissions

            capex_2020 = Quantity(1000, "USD/kW", reference_year=2020)
            capex_2025 = capex_2020.to(reference_year=2025)

            cost_eur_2015 = Quantity(50, "EUR/MWh", reference_year=2015)
            cost_usd_2024 = cost_eur_2015.to("USD/MWh", reference_year=2024)
            # Inflates EUR 2015→2024, then converts using 2024 exchange rate
        """
        result = self

        # Detect currency conversion + year change combination
        from .exchange_rate import exchange_rate_registry

        is_currency_conversion = False
        if target_unit is not None:
            source_currency = exchange_rate_registry.detect_currency_from_unit(self.unit)
            target_currency = exchange_rate_registry.detect_currency_from_unit(target_unit)
            is_currency_conversion = (
                source_currency is not None
                and target_currency is not None
                and source_currency != target_currency
            )

        is_year_change = (
            reference_year is not None
            and self.reference_year is not None
            and reference_year != self.reference_year
        )

        needs_reordering = is_currency_conversion and is_year_change

        # Standard conversions
        if substance is not None and self.substance != substance:
            result = result._convert_substance(substance)

        if basis is not None and result.basis != basis:
            result = result._convert_basis(basis)

        # Special case: inflate before converting currency
        if needs_reordering:
            # Warn user about economic assumptions
            exchange_rate_registry.warn_currency_inflation_combination()

            # Do inflation first
            if reference_year is not None:
                result = result._convert_reference_year(reference_year)

            # Then do currency conversion using target year's exchange rate
            if target_unit is not None:
                result = result._convert_unit(target_unit, year_for_exchange_rate=reference_year)
        else:
            # Normal order: unit conversion, then inflation
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
            scalar_val = (
                self.value.item() if hasattr(self.value, "item") else self.value
            )
            value_str = f"{scalar_val:.2f}"
        else:
            if self.value.size <= 5:
                value_str = f"[{', '.join(f'{v:.2f}' for v in self.value.flat)}]"
            else:
                first = self.value.flat[0]
                last = self.value.flat[-1]
                size = self.value.size
                value_str = f"[{first:.2f}, ..., {last:.2f}] ({size} values)"

        if self.substance:
            return f"{value_str} {self.unit} of {self.substance}"
        return f"{value_str} {self.unit}"

    def __repr__(self) -> str:
        substance_str = f", '{self.substance}'" if self.substance else ""
        basis_str = f", basis='{self.basis}'" if self.basis else ""
        ref_year_str = (
            f", reference_year={self.reference_year}" if self.reference_year else ""
        )
        return f"Quantity({self.value}, '{self.unit}'{substance_str}{basis_str}{ref_year_str})"

    def _repr_html_(self) -> str:
        """Rich HTML representation for Jupyter notebooks."""
        if np.isscalar(self.value) or self.value.size == 1:
            scalar_val = (
                self.value.item() if hasattr(self.value, "item") else self.value
            )
            value_str = f"{scalar_val:,.4g}"
        else:
            if self.value.size <= 5:
                value_str = (
                    "[" + ", ".join(f"{v:,.4g}" for v in self.value.flat) + "]"
                )
            else:
                first = self.value.flat[0]
                last = self.value.flat[-1]
                size = self.value.size
                value_str = f"[{first:,.4g}, ..., {last:,.4g}] ({size} values)"

        parts = [
            f'<span style="font-weight:bold;font-size:1.1em">{value_str}</span>',
            f'<span style="color:#2563eb;font-weight:bold"> {self.unit}</span>',
        ]
        if self.substance:
            parts.append(
                f'<span style="background:#e0f2fe;color:#0369a1;'
                f'border-radius:4px;padding:1px 6px;margin-left:4px;'
                f'font-size:0.9em">{self.substance}</span>'
            )
        if self.basis:
            parts.append(
                f'<span style="background:#fef3c7;color:#92400e;'
                f'border-radius:4px;padding:1px 6px;margin-left:4px;'
                f'font-size:0.9em">{self.basis}</span>'
            )
        if self.reference_year:
            parts.append(
                f'<span style="background:#f3e8ff;color:#6b21a8;'
                f'border-radius:4px;padding:1px 6px;margin-left:4px;'
                f'font-size:0.9em">{self.reference_year}</span>'
            )

        return "".join(parts)

    def __add__(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            raise TypeError(f"Cannot add Quantity and {type(other)}")

        other_converted = other.to(self.unit)
        result_value = self.value + other_converted.value

        substance = self.substance if self.substance == other.substance else None
        basis = self.basis if self.basis == other.basis else None

        if (
            self.substance is not None
            and other.substance is not None
            and self.substance != other.substance
        ):
            warnings.warn(
                f"Adding quantities with different substances "
                f"('{self.substance}' and '{other.substance}'): "
                f"substance metadata will be dropped from the result.",
                UserWarning,
                stacklevel=2,
            )

        return Quantity(result_value, self.unit, substance, basis, self.reference_year)

    def __sub__(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            raise TypeError(f"Cannot subtract {type(other)} from Quantity")

        other_converted = other.to(self.unit)
        result_value = self.value - other_converted.value

        substance = self.substance if self.substance == other.substance else None
        basis = self.basis if self.basis == other.basis else None

        if (
            self.substance is not None
            and other.substance is not None
            and self.substance != other.substance
        ):
            warnings.warn(
                f"Subtracting quantities with different substances "
                f"('{self.substance}' and '{other.substance}'): "
                f"substance metadata will be dropped from the result.",
                UserWarning,
                stacklevel=2,
            )

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
                self_converted.unit,
                other_converted.unit,
                self_converted.dimension,
                other_converted.dimension,
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

    def _convert_unit(self, target_unit: str, year_for_exchange_rate: Optional[int] = None) -> "Quantity":
        from_dim = self.dimension
        to_dim = registry.get_dimension(target_unit)

        if from_dim == to_dim:
            # Check if this is a currency conversion
            from .exchange_rate import exchange_rate_registry
            source_currency = exchange_rate_registry.detect_currency_from_unit(self.unit)
            target_currency = exchange_rate_registry.detect_currency_from_unit(target_unit)

            if source_currency and target_currency and source_currency != target_currency:
                # This is a currency conversion - use year-dependent exchange rate
                year = year_for_exchange_rate or self.reference_year
                factor = exchange_rate_registry.get_conversion_factor(
                    source_currency, target_currency, year
                )
            else:
                # Standard unit conversion
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
            hint = ""
            if (from_dim in ("MASS", "VOLUME") and to_dim == "ENERGY") or (
                from_dim == "ENERGY" and to_dim in ("MASS", "VOLUME")
            ):
                hint = " Hint: specify a substance (e.g., substance='coal') to enable this conversion."
            elif from_dim in ("MASS", "VOLUME") and to_dim in ("MASS", "VOLUME"):
                hint = " Hint: specify a substance with a known density to enable this conversion."
            raise ValueError(
                f"Cannot convert from {self.unit} ({from_dim}) to {target_unit} ({to_dim}).{hint}"
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
            raise ValueError(
                f"Invalid basis conversion: {current_basis} to {target_basis}"
            )

        return Quantity(
            new_value, self.unit, self.substance, target_basis, self.reference_year
        )

    def _convert_substance(self, target_substance: str) -> "Quantity":
        if self.substance is None:
            raise ValueError(
                "Source substance must be specified for substance conversion. "
                "Example: Quantity(1000, 'kg', substance='coal').to('kg', substance='CO2')"
            )

        valid_products = ["CO2", "H2O", "ash"]
        if target_substance not in valid_products:
            raise ValueError(
                f"Substance conversion only supported for combustion products: "
                f"{', '.join(valid_products)}. Got: '{target_substance}'"
            )

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
