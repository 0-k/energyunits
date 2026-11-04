"""Quantity class for energy system modeling with unified .to() conversion."""

import html
import numbers
import operator
from typing import Iterator, Optional, Sequence, Tuple, Union

import numpy as np

from ._warnings import warn
from .exceptions import EnergyUnitsError, IncompatibleUnitsError
from .registry import AMOUNT_DIMENSIONS, registry

ArrayLike = Union[float, int, Sequence[float], np.ndarray]

_BASES = ("HHV", "LHV")


def _normalize_basis(basis: Optional[str]) -> Optional[str]:
    if basis is None:
        return None
    if not isinstance(basis, str) or basis.upper() not in _BASES:
        raise EnergyUnitsError(f"Basis must be 'HHV' or 'LHV', got {basis!r}")
    return basis.upper()


def _normalize_year(year) -> Optional[int]:
    if year is None:
        return None
    if isinstance(year, (bool, np.bool_)):
        raise TypeError(f"reference_year must be an integer year, got {year!r}")
    if isinstance(year, numbers.Integral):
        return int(year)
    if isinstance(year, numbers.Real) and float(year).is_integer():
        return int(year)
    raise TypeError(f"reference_year must be an integer year, got {year!r}")


def _as_array(value) -> np.ndarray:
    """Convert numeric input (scalar, sequence, ndarray, pandas object) to a float array."""
    if isinstance(value, Quantity):
        raise TypeError("Cannot use a Quantity as value; use quantity.to(...) or quantity.value instead")
    if value is None:
        raise TypeError("Quantity value must be numeric, got None")
    if hasattr(value, "to_numpy") and not isinstance(value, np.ndarray):
        try:
            return value.to_numpy(dtype=float, na_value=np.nan)
        except (TypeError, ValueError):
            pass
    array = np.asarray(value)
    kind = array.dtype.kind
    if kind == "f":
        return array
    if kind in "biu":
        return array.astype(float)
    if kind == "O":
        try:
            return np.asarray(value, dtype=float)
        except (TypeError, ValueError):
            pass
    raise TypeError(f"Quantity value must be numeric, got {type(value).__name__} with dtype '{array.dtype}'")


def _is_numeric_operand(other) -> bool:
    """True for plain numbers and numeric arrays (but not lists, strings or Quantities)."""
    if isinstance(other, Quantity):
        return False
    if isinstance(other, numbers.Number):
        return isinstance(other, numbers.Real) or isinstance(other, np.generic) and other.dtype.kind in "biuf"
    if isinstance(other, np.generic):
        return other.dtype.kind in "biuf"
    if isinstance(other, np.ndarray):
        return other.dtype.kind in "biuf"
    if isinstance(other, (str, bytes, list, tuple, dict, set)):
        return False
    dtype = getattr(other, "dtype", None)
    return hasattr(other, "__array__") and getattr(dtype, "kind", "O") in "biuf"


def _format_number(value) -> str:
    value = float(value)
    magnitude = abs(value)
    if np.isfinite(value) and magnitude != 0 and (magnitude < 0.01 or magnitude >= 1e15):
        return f"{value:.4g}"
    return f"{value:.2f}"


class Quantity:
    """Physical quantity with value, unit and optional metadata.

    Args:
        value: Number or array-like of numbers (lists, NumPy arrays, pandas Series).
            Values are stored as a float :class:`numpy.ndarray` (0-d for scalars).
        unit: Unit string, e.g. ``"MWh"``, ``"USD/kW"``, ``"t/MWh"``, ``"EUR/kW/a"``.
            See :mod:`energyunits.registry` for the syntax.
        substance: Optional substance (fuel) name, e.g. ``"coal"``, used for
            mass/volume/energy and combustion product conversions.
        basis: Optional heating value basis, ``"HHV"`` or ``"LHV"``. When not
            given, conversions assume LHV.
        reference_year: Optional price base year for monetary quantities.

    Examples:
        >>> Quantity(100, "MWh").to("GJ")
        Quantity(360.0, 'GJ')
        >>> Quantity(50, "MW") * Quantity(30, "min")
        Quantity(25.0, 'MWh')
    """

    __slots__ = ("value", "unit", "substance", "basis", "reference_year", "dimension")

    # Make NumPy defer to Quantity in mixed operations (``array * quantity``).
    __array_ufunc__ = None
    # Make pandas defer to Quantity in mixed operations (``series * quantity``).
    __pandas_priority__ = 5000
    __hash__ = None  # mutable value array, defines __eq__

    def __init__(
        self,
        value: ArrayLike,
        unit: str,
        substance: Optional[str] = None,
        basis: Optional[str] = None,
        reference_year: Optional[int] = None,
    ) -> None:
        if not isinstance(unit, str):
            raise TypeError(f"Unit must be a string, got {type(unit).__name__}")
        if substance is not None and not isinstance(substance, str):
            raise TypeError(f"Substance must be a string, got {type(substance).__name__}")
        self.dimension: str = registry.get_dimension(unit)
        self.value: np.ndarray = _as_array(value)
        self.unit: str = unit
        self.substance: Optional[str] = substance
        self.basis: Optional[str] = _normalize_basis(basis)
        self.reference_year: Optional[int] = _normalize_year(reference_year)

    @classmethod
    def _make(cls, value, unit, substance, basis, reference_year) -> "Quantity":
        """Fast internal constructor for already validated metadata."""
        quantity = object.__new__(cls)
        quantity.value = np.asarray(value)
        quantity.unit = unit
        quantity.dimension = registry.get_dimension(unit)
        quantity.substance = substance
        quantity.basis = basis
        quantity.reference_year = reference_year
        return quantity

    def _with_value(self, value) -> "Quantity":
        return self._make(value, self.unit, self.substance, self.basis, self.reference_year)

    def copy(self) -> "Quantity":
        """Return a copy of this quantity."""
        return self._with_value(self.value.copy())

    # ---------------------------------------------------------------- discovery

    @classmethod
    def list_units(cls, dimension: Optional[str] = None) -> list:
        """List all available units, optionally filtered by dimension.

        Examples:
            Quantity.list_units()            # All units
            Quantity.list_units("ENERGY")    # Energy units only
        """
        return registry.list_units(dimension)

    @classmethod
    def list_dimensions(cls) -> list:
        """List all available dimensions."""
        return registry.list_dimensions()

    @classmethod
    def list_substances(cls, has_property: Optional[str] = None) -> list:
        """List all available substances, optionally only those with a property (e.g. ``"hhv"``)."""
        from .substance import substance_registry

        return substance_registry.list_substances(has_property)

    @classmethod
    def list_currencies(cls) -> list:
        """List all currencies with year-dependent exchange rates."""
        from .exchange_rate import exchange_rate_registry

        return exchange_rate_registry.get_supported_currencies()

    def is_compatible(self, unit: str) -> bool:
        """True if this quantity can be converted to ``unit`` without a substance."""
        return registry.is_compatible(self.unit, unit)

    # --------------------------------------------------------------- conversion

    def to(
        self,
        target_unit: Optional[str] = None,
        basis: Optional[str] = None,
        substance: Optional[str] = None,
        reference_year: Optional[int] = None,
    ) -> "Quantity":
        """Convert to another unit, heating value basis, substance and/or reference year.

        Conversions are applied in this order: basis -> substance -> unit -> reference year.

        * **unit**: any unit of the same dimension (``MWh`` -> ``GJ``, ``USD/kW`` ->
          ``EUR/MW``). Mass, volume and energy are converted into each other using
          the substance's heating value and density, also inside compound units
          (``USD/t`` -> ``USD/MWh``, ``MW`` -> ``t/h``).
        * **basis**: ``"HHV"`` or ``"LHV"``. Energy amounts are rescaled with the
          substance's LHV/HHV ratio, per-energy units (e.g. ``USD/MWh``) inversely;
          mass and volume amounts are only re-labelled.
        * **substance**: combustion products ``"CO2"``, ``"H2O"`` or ``"ash"`` from
          the fuel composition (``t coal`` -> ``t CO2``, ``MW gas`` -> ``t/h CO2``).
        * **reference_year**: inflation adjustment of monetary quantities.

        When a currency conversion is combined with a change of reference year,
        the value is first inflated in the original currency and then converted
        with the exchange rate of the target year (a warning is emitted).

        Examples:
            Quantity(100, "MWh").to("GJ")                        # 360 GJ
            Quantity(1000, "kg", "coal").to("MWh")               # 7.17 MWh (LHV)
            Quantity(1000, "kg", "coal").to("kg", substance="CO2")
            Quantity(1000, "USD/kW", reference_year=2020).to(reference_year=2025)
            Quantity(50, "EUR/MWh", reference_year=2015).to("USD/MWh", reference_year=2024)
        """
        if target_unit is None and basis is None and substance is None and reference_year is None:
            return self.copy()
        if target_unit is not None and not isinstance(target_unit, str):
            raise TypeError(f"Target unit must be a string, got {type(target_unit).__name__}")
        basis = _normalize_basis(basis)
        reference_year = _normalize_year(reference_year)

        result = self
        if basis is not None and result.basis != basis:
            result = result._convert_basis(basis)
        if substance is not None and substance != result.substance:
            result = result._convert_substance(substance)

        currency_change = target_unit is not None and _changes_currency(result.unit, target_unit)
        year_change = (
            reference_year is not None
            and result.reference_year is not None
            and reference_year != result.reference_year
        )
        if currency_change and year_change:
            from .exchange_rate import exchange_rate_registry

            exchange_rate_registry.warn_currency_inflation_combination()
            result = result._convert_reference_year(reference_year)
            result = result._convert_unit(target_unit, exchange_rate_year=reference_year)
        else:
            if target_unit is not None:
                result = result._convert_unit(target_unit)
            if reference_year is not None:
                result = result._convert_reference_year(reference_year)
        if result is self:
            result = self.copy()
        return result

    def _convert_unit(self, target_unit: str, exchange_rate_year: Optional[int] = None) -> "Quantity":
        from .exchange_rate import exchange_rate_registry

        year = exchange_rate_year if exchange_rate_year is not None else self.reference_year
        correction = exchange_rate_registry.unit_correction_factor(self.unit, target_unit, year)
        if correction == 1.0 and registry.is_compatible(self.unit, target_unit):
            # Two-step scaling keeps common conversions exact (100 MWh -> 360.0 GJ).
            numerator, denominator = registry.scaling_parts(self.unit, target_unit)
            value = self.value * numerator / denominator
        else:
            factor = registry.conversion_factor(self.unit, target_unit, self.substance, self.basis)
            value = self.value * (factor * correction)
        return self._make(value, target_unit, self.substance, self.basis, self.reference_year)

    def _convert_basis(self, target_basis: str) -> "Quantity":
        target_basis = _normalize_basis(target_basis)
        if self.substance is None:
            raise EnergyUnitsError("Substance must be specified for basis conversion")
        current_basis = self.basis or "LHV"
        exponent = registry.dimension_exponent(self.unit, "ENERGY")
        if current_basis == target_basis or exponent == 0:
            return self._make(self.value.copy(), self.unit, self.substance, target_basis, self.reference_year)

        from .substance import substance_registry

        ratio = substance_registry.lhv_hhv_ratio(self.substance)
        factor = ratio**exponent if target_basis == "LHV" else ratio**-exponent
        return self._make(self.value * factor, self.unit, self.substance, target_basis, self.reference_year)

    def _convert_substance(self, target_substance: str) -> "Quantity":
        if self.substance is None:
            raise EnergyUnitsError(
                "Source substance must be specified for substance conversion. "
                "Example: Quantity(1000, 'kg', substance='coal').to('kg', substance='CO2')"
            )
        from .substance import substance_registry

        product_factor = substance_registry.combustion_product_factor(self.substance, target_substance)
        mass_unit, exponent = self._fuel_mass_unit()
        if product_factor == 0:
            if exponent < 0:
                raise EnergyUnitsError(
                    f"'{self.substance}' produces no {target_substance}; cannot express "
                    f"'{self.unit}' per unit of {target_substance}."
                )
            value = np.zeros_like(self.value)
        else:
            value = self._convert_unit(mass_unit).value * product_factor**exponent
        return self._make(value, mass_unit, target_substance, None, self.reference_year)

    def _fuel_mass_unit(self) -> Tuple[str, int]:
        """Unit of this quantity with its amount of fuel expressed as mass."""
        vector = dict(registry.dimension_vector(self.unit))
        amounts = [dim for dim in AMOUNT_DIMENSIONS if vector.get(dim)]
        if len(amounts) != 1:
            raise IncompatibleUnitsError(
                f"Cannot determine the amount of fuel in unit '{self.unit}' "
                "for a combustion product conversion."
            )
        amount_dim = amounts[0]
        if amount_dim == "MASS":
            return self.unit, vector["MASS"]
        exponents: dict = {}
        for atom, exp in registry.parse_unit(self.unit):
            atom_vector = dict(registry.dimension_vector(atom))
            if amount_dim in atom_vector:
                replacement = [(registry.preferred_unit("MASS"), atom_vector[amount_dim])]
                replacement += [
                    (registry.preferred_unit(d), e) for d, e in atom_vector.items() if d != amount_dim
                ]
                for new_atom, new_exp in replacement:
                    exponents[new_atom] = exponents.get(new_atom, 0) + new_exp * exp
            else:
                exponents[atom] = exponents.get(atom, 0) + exp
        return registry.format_terms(list(exponents.items())), vector[amount_dim]

    def _convert_reference_year(self, target_year: int) -> "Quantity":
        if self.reference_year is None:
            raise EnergyUnitsError("Reference year not specified for inflation adjustment")
        if target_year == self.reference_year:
            return self._make(self.value.copy(), self.unit, self.substance, self.basis, target_year)

        from .inflation import inflation_registry

        terms = registry.currency_terms(self.unit)
        if not terms:
            raise EnergyUnitsError(
                f"Cannot detect currency from unit '{self.unit}'. "
                f"Supported currencies: {inflation_registry.get_supported_currencies()}"
            )
        if len(terms) > 1:
            raise EnergyUnitsError(
                f"Cannot adjust inflation for a unit with several currencies: '{self.unit}'"
            )
        _, currency, exponent = terms[0]
        factor = inflation_registry.get_cumulative_inflation_factor(
            currency, self.reference_year, target_year
        )
        if inflation_registry.uses_projection(currency, self.reference_year, target_year):
            warn(
                f"Inflation adjustment of {currency} between {self.reference_year} and {target_year} uses "
                f"projected rates from {inflation_registry.get_projected_from(currency)} onwards "
                f"(placeholder values, not historical data)."
            )
        return self._make(self.value * factor**exponent, self.unit, self.substance, self.basis, target_year)

    # ---------------------------------------------------------- representation

    def _label(self, value_str: str) -> str:
        text = f"{value_str} {self.unit}" if self.unit else value_str
        if self.substance:
            text += f" of {self.substance}"
        if self.value.size > 5:
            text += f" ({self.value.size} values)"
        return text

    def _value_string(self, formatter) -> str:
        if self.value.size == 1:
            return formatter(self.value.item())
        if self.value.size <= 5:
            return "[" + ", ".join(formatter(v) for v in self.value.flat) + "]"
        return f"[{formatter(self.value.flat[0])}, ..., {formatter(self.value.flat[-1])}]"

    def __str__(self) -> str:
        return self._label(self._value_string(_format_number))

    def __format__(self, format_spec: str) -> str:
        if not format_spec:
            return str(self)
        return self._label(self._value_string(lambda v: format(v, format_spec)))

    def __repr__(self) -> str:
        if self.value.ndim == 0:
            value_repr = repr(self.value.item())
        else:
            value_repr = np.array2string(self.value, separator=", ", threshold=20)
        substance_str = f", '{self.substance}'" if self.substance else ""
        basis_str = f", basis='{self.basis}'" if self.basis else ""
        year_str = f", reference_year={self.reference_year}" if self.reference_year is not None else ""
        return f"Quantity({value_repr}, '{self.unit}'{substance_str}{basis_str}{year_str})"

    def _repr_html_(self) -> str:
        """Rich HTML representation for Jupyter notebooks."""
        value_str = html.escape(self._value_string(lambda v: f"{v:,.4g}"))
        if self.value.size > 5:
            value_str += f" ({self.value.size} values)"
        parts = [
            f'<span style="font-weight:bold;font-size:1.1em">{value_str}</span>',
            f'<span style="color:#2563eb;font-weight:bold"> {html.escape(self.unit)}</span>',
        ]
        badge = "border-radius:4px;padding:1px 6px;margin-left:4px;font-size:0.9em"
        if self.substance:
            parts.append(
                f'<span style="background:#e0f2fe;color:#0369a1;{badge}">{html.escape(self.substance)}</span>'
            )
        if self.basis:
            parts.append(
                f'<span style="background:#fef3c7;color:#92400e;{badge}">{html.escape(self.basis)}</span>'
            )
        if self.reference_year is not None:
            parts.append(
                f'<span style="background:#f3e8ff;color:#6b21a8;{badge}">{self.reference_year}</span>'
            )
        return "".join(parts)

    # ------------------------------------------------------- array behaviour

    @property
    def shape(self) -> tuple:
        """Shape of the value array (``()`` for scalars)."""
        return self.value.shape

    def __len__(self) -> int:
        return len(self.value)

    def __bool__(self) -> bool:
        # NumPy semantics: scalars by value, multi-element arrays are ambiguous.
        return bool(self.value)

    def __float__(self) -> float:
        if registry.dimension_vector(self.unit) != ():
            raise TypeError(
                f"Only dimensionless quantities can be converted to float, not '{self.unit}'. "
                f"Use quantity.value or quantity.to(unit).value instead."
            )
        return float(self.value * registry.unit_factor(self.unit))

    def __getitem__(self, key) -> "Quantity":
        return self._with_value(self.value[key])

    def __iter__(self) -> Iterator["Quantity"]:
        if self.value.ndim == 0:
            raise TypeError("Iteration over a scalar Quantity")
        for item in self.value:
            yield self._with_value(item)

    def sum(self, axis=None) -> "Quantity":
        """Sum of the values (same unit and metadata)."""
        return self._with_value(np.sum(self.value, axis=axis))

    def mean(self, axis=None) -> "Quantity":
        """Mean of the values (same unit and metadata)."""
        return self._with_value(np.mean(self.value, axis=axis))

    def min(self, axis=None) -> "Quantity":
        """Minimum of the values (same unit and metadata)."""
        return self._with_value(np.min(self.value, axis=axis))

    def max(self, axis=None) -> "Quantity":
        """Maximum of the values (same unit and metadata)."""
        return self._with_value(np.max(self.value, axis=axis))

    # --------------------------------------------------------------- arithmetic

    def _align(self, other: "Quantity") -> "Quantity":
        """``other`` converted to this quantity's unit, heating value basis and reference year."""
        target_basis = None
        if (
            other.substance is not None
            and (other.basis or "LHV") != (self.basis or "LHV")
            and registry.dimension_exponent(other.unit, "ENERGY") != 0
        ):
            target_basis = self.basis or "LHV"
        target_year = None
        if (
            self.reference_year is not None
            and other.reference_year is not None
            and self.reference_year != other.reference_year
            and registry.currency_terms(other.unit)
        ):
            target_year = self.reference_year
        return other.to(self.unit, basis=target_basis, reference_year=target_year)

    def _merged_substance(self, other: "Quantity", verb: Optional[str] = None) -> Optional[str]:
        if self.substance == other.substance:
            return self.substance
        if self.substance is None:
            return other.substance
        if other.substance is None:
            return self.substance
        if verb is not None:
            warn(
                f"{verb} quantities with different substances ('{self.substance}' and '{other.substance}'): "
                f"substance metadata will be dropped from the result."
            )
        return None

    def _add_or_subtract(self, other: "Quantity", sign: int, verb: str) -> "Quantity":
        aligned = self._align(other)
        value = self.value + aligned.value if sign > 0 else self.value - aligned.value
        substance = self._merged_substance(other, verb)
        if self.basis == aligned.basis or aligned.basis is None:
            basis = self.basis
        elif self.basis is None:
            basis = aligned.basis
        else:
            basis = None
        if self.reference_year is None:
            year = aligned.reference_year
        elif aligned.reference_year is None or aligned.reference_year == self.reference_year:
            year = self.reference_year
        else:
            year = None
        return self._make(value, self.unit, substance, basis, year)

    def __add__(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            raise TypeError(f"Cannot add Quantity and {type(other).__name__}")
        return self._add_or_subtract(other, 1, "Adding")

    def __radd__(self, other) -> "Quantity":
        if isinstance(other, numbers.Number) and other == 0:  # supports sum([...])
            return self.copy()
        raise TypeError(f"Cannot add {type(other).__name__} and Quantity")

    def __sub__(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            raise TypeError(f"Cannot subtract {type(other).__name__} from Quantity")
        return self._add_or_subtract(other, -1, "Subtracting")

    def __rsub__(self, other) -> "Quantity":
        if isinstance(other, numbers.Number) and other == 0:
            return -self
        raise TypeError(f"Cannot subtract Quantity from {type(other).__name__}")

    def __neg__(self) -> "Quantity":
        return self._with_value(-self.value)

    def __pos__(self) -> "Quantity":
        return self.copy()

    def __abs__(self) -> "Quantity":
        return self._with_value(np.abs(self.value))

    def __round__(self, ndigits: Optional[int] = None) -> "Quantity":
        return self._with_value(np.round(self.value, ndigits or 0))

    def _multiply_or_divide(self, other: "Quantity", multiply: bool) -> "Quantity":
        unit, numerator, denominator = registry.combine_units(self.unit, other.unit, 1 if multiply else -1)
        value = self.value * other.value if multiply else self.value / other.value
        if numerator != denominator:
            value = value * numerator / denominator
        basis = self.basis if self.basis == other.basis else None
        if self.reference_year is None:
            year = other.reference_year
        elif other.reference_year is None or other.reference_year == self.reference_year:
            year = self.reference_year
        else:
            year = None
        return self._make(value, unit, self._merged_substance(other), basis, year)

    def __mul__(self, other: Union["Quantity", ArrayLike]) -> "Quantity":
        if isinstance(other, Quantity):
            return self._multiply_or_divide(other, multiply=True)
        if _is_numeric_operand(other):
            return self._with_value(self.value * _as_array(other))
        raise TypeError(f"Cannot multiply Quantity and {type(other).__name__}")

    def __rmul__(self, other: ArrayLike) -> "Quantity":
        if _is_numeric_operand(other):
            return self._with_value(_as_array(other) * self.value)
        raise TypeError(f"Cannot multiply {type(other).__name__} and Quantity")

    def __truediv__(self, other: Union["Quantity", ArrayLike]) -> "Quantity":
        if isinstance(other, Quantity):
            return self._multiply_or_divide(other, multiply=False)
        if _is_numeric_operand(other):
            return self._with_value(self.value / _as_array(other))
        raise TypeError(f"Cannot divide Quantity by {type(other).__name__}")

    def __rtruediv__(self, other: ArrayLike) -> "Quantity":
        if not _is_numeric_operand(other):
            raise TypeError(f"Cannot divide {type(other).__name__} by Quantity")
        unit, numerator, denominator = registry.combine_units("", self.unit, -1)
        value = _as_array(other) / self.value
        if numerator != denominator:
            value = value * numerator / denominator
        return self._make(value, unit, self.substance, self.basis, self.reference_year)

    # -------------------------------------------------------------- comparisons

    def _compare(self, other, op) -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        aligned = self._align(other)
        return bool(np.all(op(self.value, aligned.value)))

    def __lt__(self, other: "Quantity") -> bool:
        return self._compare(other, operator.lt)

    def __gt__(self, other: "Quantity") -> bool:
        return self._compare(other, operator.gt)

    def __le__(self, other: "Quantity") -> bool:
        return self._compare(other, lambda a, b: (a < b) | np.isclose(a, b, rtol=1e-9, atol=0.0))

    def __ge__(self, other: "Quantity") -> bool:
        return self._compare(other, lambda a, b: (a > b) | np.isclose(a, b, rtol=1e-9, atol=0.0))

    def __eq__(self, other: object) -> bool:
        """Equality after unit conversion, with a relative tolerance of 1e-9.

        Quantities of incompatible dimensions are not equal.
        """
        if not isinstance(other, Quantity):
            return NotImplemented
        try:
            aligned = self._align(other)
            return bool(np.all(np.isclose(self.value, aligned.value, rtol=1e-9, atol=0.0)))
        except (ValueError, TypeError):
            return False

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result


def _changes_currency(from_unit: str, to_unit: str) -> bool:
    source = {code for _, code, _ in registry.currency_terms(from_unit)}
    target = {code for _, code, _ in registry.currency_terms(to_unit)}
    return bool(source) and bool(target) and source != target
