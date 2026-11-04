"""Unit registry: unit parsing, dimensional analysis and conversion factors.

Unit strings
------------
A unit string is a sequence of registered *atomic* units joined by ``/``
(division) or ``·`` / ``*`` (multiplication). Operators have equal precedence
and are evaluated left to right, so every atom after a ``/`` is in the
denominator::

    "MWh"          energy
    "USD/kW"       currency per power
    "EUR/kW/a"     (EUR / kW) / a, e.g. fixed O&M cost
    "t/MWh"        emission factor
    "MW·h"         power times time (same dimension as "MWh")
    "1/h"          a rate
    ""             dimensionless

Dimensions
----------
Every atomic unit belongs to a named dimension (``ENERGY``, ``POWER``,
``MASS``, ...). Derived dimensions are defined in terms of base dimensions
(``POWER = ENERGY / TIME``), so units are compared by their *dimension vector*:
``"GJ/h"`` and ``"MW"`` have the same dimension, as do ``"kWh/kW"`` and ``"h"``.

Conversion factors are stored relative to the base unit of each dimension.
Internally the factors are relative to SI-coherent base units (J, W, kg, m3,
s, USD), which keeps metric conversions exact in floating point. For derived
dimensions the factors must be coherent with the definition, i.e.
``factor(W) == factor(J) / factor(s)``.
"""

import difflib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .exceptions import IncompatibleUnitsError, MissingDataError, UnknownUnitError

#: Parsed unit: tuple of ``(atomic_unit, exponent)`` pairs.
Terms = Tuple[Tuple[str, int], ...]
#: Dimension vector: sorted tuple of ``(base_dimension, exponent)`` pairs.
DimensionVector = Tuple[Tuple[str, int], ...]

DIMENSIONLESS = "DIMENSIONLESS"
#: Dimensions that describe an *amount of substance* and can be converted into
#: each other when a substance (heating value, density) is known.
AMOUNT_DIMENSIONS = ("MASS", "VOLUME", "ENERGY")

_DATA_DIR = Path(__file__).parent / "data"
_SPLIT_RE = re.compile(r"\s*([/·*])\s*")
_INVALID_ATOM_RE = re.compile(r"[/·*\s]")


class UnitRegistry:
    """Registry of units, dimensions and conversion factors.

    A module-level instance is available as :data:`energyunits.registry.registry`.
    """

    def __init__(self) -> None:
        self._load_defaults()

    # ------------------------------------------------------------------ loading

    def _load_defaults(self) -> None:
        self._dimensions: Dict[str, str] = {}
        self._conversion_factors: Dict[str, float] = {}
        self._base_units: Dict[str, str] = {}
        self._preferred_units: Dict[str, str] = {}
        self._derived_dimensions: Dict[str, Dict[str, int]] = {}
        self._currency_units: Dict[str, dict] = {}
        self._corresponding_units: Dict[str, str] = {}
        self._dimensional_multiplication_rules: List[dict] = []
        self._dimensional_division_rules: List[dict] = []
        with open(_DATA_DIR / "units.json", encoding="utf-8") as f:
            self._ingest(json.load(f))

    def reset(self) -> None:
        """Discard all custom units and reload the bundled defaults."""
        self._load_defaults()

    def load_units(self, file_path: str) -> None:
        """Load additional units from a JSON file.

        The file may contain any of the sections of the bundled ``units.json``:
        ``dimensions``, ``conversion_factors``, ``base_units``, ``preferred_units``,
        ``derived_dimensions``, ``currency_units``, ``corresponding_units``,
        ``dimensional_multiplication_rules`` and ``dimensional_division_rules``.
        Existing entries with the same name are overwritten.
        """
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        self._ingest(data)

    def _ingest(self, data: dict) -> None:
        dimensions = data.get("dimensions", {})
        for unit in dimensions:
            if not isinstance(unit, str) or not unit or unit == "1" or _INVALID_ATOM_RE.search(unit):
                raise ValueError(
                    f"Invalid unit name {unit!r}: unit names must be non-empty and must not "
                    "contain whitespace, '/', '*' or '·'."
                )
        self._dimensions.update(dimensions)
        self._conversion_factors.update(
            {unit: float(factor) for unit, factor in data.get("conversion_factors", {}).items()}
        )
        self._base_units.update(data.get("base_units", {}))
        self._preferred_units.update(data.get("preferred_units", {}))
        for name, composition in data.get("derived_dimensions", {}).items():
            self._derived_dimensions[name] = {dim: int(exp) for dim, exp in composition.items()}
        self._currency_units.update(data.get("currency_units", {}))
        self._corresponding_units.update(data.get("corresponding_units", {}))
        for rule in data.get("dimensional_multiplication_rules", []):
            if rule not in self._dimensional_multiplication_rules:
                self._dimensional_multiplication_rules.append(rule)
        for rule in data.get("dimensional_division_rules", []):
            if rule not in self._dimensional_division_rules:
                self._dimensional_division_rules.append(rule)
        self._rebuild()

    def _rebuild(self) -> None:
        self._clear_caches()
        names = list(self._dimensions.values()) + list(self._derived_dimensions) + list(self._base_units)
        self._vector_names: Dict[DimensionVector, str] = {(): DIMENSIONLESS}
        for name in dict.fromkeys(names):
            self._vector_names.setdefault(self._dimension_name_vector(name), name)

    def _clear_caches(self) -> None:
        for method in (
            UnitRegistry.parse_unit,
            UnitRegistry.unit_factor_parts,
            UnitRegistry.dimension_vector,
            UnitRegistry.get_dimension,
            UnitRegistry.unit_factor,
            UnitRegistry.get_conversion_factor,
            UnitRegistry.combine_units,
        ):
            method.cache_clear()

    # ------------------------------------------------------------------ parsing

    @lru_cache(maxsize=4096)
    def parse_unit(self, unit: str) -> Terms:
        """Parse a unit string into ``((atom, exponent), ...)``.

        Identical atoms are merged (``"MWh/MWh"`` parses to ``()``).

        Raises:
            TypeError: if ``unit`` is not a string.
            UnknownUnitError: if the string is malformed or contains unknown units.
        """
        if not isinstance(unit, str):
            raise TypeError(f"Unit must be a string, got {type(unit).__name__}")
        if unit == "":
            return ()
        parts = _SPLIT_RE.split(unit)
        exponents: Dict[str, int] = {}
        sign = 1
        for index, part in enumerate(parts):
            if index % 2:
                sign = -1 if part == "/" else 1
                continue
            atom = part.strip()
            if not atom:
                raise UnknownUnitError(f"Malformed unit: '{unit}' (empty component).")
            if atom == "1" and index == 0:
                continue
            if atom not in self._dimensions:
                raise UnknownUnitError(self._unknown_unit_message(atom, unit))
            exponents[atom] = exponents.get(atom, 0) + sign
        return tuple((atom, exp) for atom, exp in exponents.items() if exp != 0)

    def validate_unit(self, unit: str) -> None:
        """Raise an error if ``unit`` is not a valid unit string."""
        self.parse_unit(unit)

    def _unknown_unit_message(self, atom: str, unit: str) -> str:
        msg = f"Unknown unit: '{atom}'"
        if atom != unit:
            msg += f" in '{unit}'"
        msg += "."
        known = list(self._dimensions)
        same_case = [u for u in known if u.lower() == atom.lower()]
        close = same_case + [u for u in difflib.get_close_matches(atom, known, n=3) if u not in same_case]
        if close:
            msg += f" Did you mean: {', '.join(close[:3])}?"
        else:
            msg += f" Available units: {', '.join(sorted(known))}"
        return msg

    def format_terms(self, terms: Sequence[Tuple[str, int]]) -> str:
        """Format parsed terms as a canonical unit string (inverse of :meth:`parse_unit`)."""
        numerator: List[str] = []
        denominator: List[str] = []
        for atom, exp in terms:
            if exp > 0:
                numerator.extend([atom] * exp)
            elif exp < 0:
                denominator.extend([atom] * -exp)
        if not numerator and not denominator:
            return ""
        result = "·".join(numerator) if numerator else "1"
        for atom in denominator:
            result += "/" + atom
        return result

    # --------------------------------------------------------------- dimensions

    def _dimension_name_vector(self, name: str, _seen: Tuple[str, ...] = ()) -> DimensionVector:
        if name == DIMENSIONLESS:
            return ()
        composition = self._derived_dimensions.get(name)
        if composition is None:
            return ((name, 1),)
        if name in _seen:
            raise ValueError(f"Circular definition of derived dimension '{name}'")
        vector: Dict[str, int] = {}
        for sub_name, exp in composition.items():
            for dim, sub_exp in self._dimension_name_vector(sub_name, _seen + (name,)):
                vector[dim] = vector.get(dim, 0) + sub_exp * exp
        return tuple(sorted((d, e) for d, e in vector.items() if e))

    @lru_cache(maxsize=4096)
    def dimension_vector(self, unit: str) -> DimensionVector:
        """Return the dimension of ``unit`` expressed in base dimensions.

        Example: ``dimension_vector("MW") == (("ENERGY", 1), ("TIME", -1))``.
        """
        vector: Dict[str, int] = {}
        for atom, exp in self.parse_unit(unit):
            for dim, dim_exp in self._dimension_name_vector(self._dimensions[atom]):
                vector[dim] = vector.get(dim, 0) + dim_exp * exp
        return tuple(sorted((d, e) for d, e in vector.items() if e))

    def dimension_exponent(self, unit: str, dimension: str) -> int:
        """Exponent of a base dimension in ``unit`` (e.g. ENERGY in ``"USD/MWh"`` is -1)."""
        return dict(self.dimension_vector(unit)).get(dimension, 0)

    @lru_cache(maxsize=4096)
    def get_dimension(self, unit: str) -> str:
        """Return the dimension name of a unit.

        Atomic units return their registered dimension (``"MWh"`` -> ``"ENERGY"``).
        Compound units whose dimension equals a named dimension return that name
        (``"GJ/h"`` -> ``"POWER"``, ``"kWh/kW"`` -> ``"TIME"``); other compound units
        return a descriptive name such as ``"CURRENCY_PER_POWER"``.
        """
        terms = self.parse_unit(unit)
        if not terms:
            return DIMENSIONLESS
        if len(terms) == 1 and terms[0][1] == 1:
            return self._dimensions[terms[0][0]]
        name = self._vector_names.get(self.dimension_vector(unit))
        if name is not None:
            return name
        numerator = [self._dimensions[a] for a, e in terms if e > 0 for _ in range(e)]
        denominator = [self._dimensions[a] for a, e in terms if e < 0 for _ in range(-e)]
        return "_PER_".join(["·".join(numerator) if numerator else DIMENSIONLESS] + denominator)

    def has_unit(self, unit: str) -> bool:
        """True if ``unit`` is a valid unit string."""
        try:
            self.parse_unit(unit)
        except (TypeError, ValueError):
            return False
        return True

    def base_unit(self, dimension: str) -> str:
        """Base unit (conversion factor 1) of a dimension, e.g. ``"ENERGY"`` -> ``"J"``."""
        try:
            return self._base_units[dimension]
        except KeyError:
            raise UnknownUnitError(f"No base unit defined for dimension '{dimension}'") from None

    def preferred_unit(self, dimension: str) -> str:
        """Unit used when a calculation has to choose one, e.g. ``"ENERGY"`` -> ``"MWh"``."""
        preferred = self._preferred_units.get(dimension)
        return preferred if preferred is not None else self.base_unit(dimension)

    def is_compatible(self, unit1: str, unit2: str) -> bool:
        """True if both units have the same dimension (directly convertible)."""
        return self.dimension_vector(unit1) == self.dimension_vector(unit2)

    def list_units(self, dimension: Optional[str] = None) -> list:
        """List all registered atomic units, optionally filtered by dimension.

        Args:
            dimension: Filter by dimension (e.g. ``"ENERGY"``, ``"POWER"``, ``"MASS"``).

        Returns:
            Sorted list of unit strings.
        """
        if dimension is None:
            return sorted(self._dimensions)
        dimension = dimension.upper()
        return sorted(u for u, d in self._dimensions.items() if d == dimension)

    def list_dimensions(self) -> list:
        """List all dimension names that registered units belong to."""
        return sorted(set(self._dimensions.values()))

    # -------------------------------------------------------- conversion factors

    @lru_cache(maxsize=4096)
    def unit_factor_parts(self, unit: str) -> Tuple[float, float]:
        """Size of ``unit`` relative to the base units as ``(numerator, denominator)``."""
        numerator = denominator = 1.0
        for atom, exp in self.parse_unit(unit):
            atom_factor = self._conversion_factors.get(atom)
            if atom_factor is None:
                raise MissingDataError(f"No conversion factor defined for unit '{atom}'.")
            if exp > 0:
                numerator *= atom_factor**exp
            else:
                denominator *= atom_factor**-exp
        return numerator, denominator

    @lru_cache(maxsize=4096)
    def unit_factor(self, unit: str) -> float:
        """Size of ``unit`` relative to the coherent base units (J, W, kg, m3, s, USD)."""
        numerator, denominator = self.unit_factor_parts(unit)
        return numerator / denominator

    @lru_cache(maxsize=4096)
    def get_conversion_factor(self, from_unit: str, to_unit: str) -> float:
        """Factor ``f`` such that ``value_in_to_unit = value_in_from_unit * f``.

        Both units must have the same dimension. Currency units use the static
        (most recent) exchange rates; :class:`~energyunits.Quantity` applies
        year-specific rates on top.

        Raises:
            IncompatibleUnitsError: if the dimensions differ.
        """
        if self.dimension_vector(from_unit) != self.dimension_vector(to_unit):
            raise IncompatibleUnitsError(f"Incompatible units: {from_unit} and {to_unit}")
        if self.parse_unit(from_unit) == self.parse_unit(to_unit):
            return 1.0
        numerator, denominator = self.scaling_parts(from_unit, to_unit)
        return numerator / denominator

    def scaling_parts(self, from_unit: str, to_unit: str) -> Tuple[float, float]:
        """``(numerator, denominator)`` of the factor between two units of the same dimension."""
        from_num, from_den = self.unit_factor_parts(from_unit)
        to_num, to_den = self.unit_factor_parts(to_unit)
        return from_num * to_den, from_den * to_num

    def conversion_factor(
        self,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        basis: Optional[str] = None,
    ) -> float:
        """Conversion factor that may use substance properties.

        Units of the same dimension convert directly. Units whose dimensions
        differ only by swapping one amount dimension (MASS, VOLUME, ENERGY) for
        another are converted through the substance's heating value (``basis``,
        default LHV) and density. This covers simple cases (``t`` -> ``MWh``) as
        well as compound ones (``USD/t`` -> ``USD/MWh``, ``MW`` -> ``t/h``).

        Raises:
            IncompatibleUnitsError: if no conversion exists or a substance is required.
        """
        from_vector = dict(self.dimension_vector(from_unit))
        to_vector = dict(self.dimension_vector(to_unit))
        difference = {
            dim: from_vector.get(dim, 0) - to_vector.get(dim, 0) for dim in set(from_vector) | set(to_vector)
        }
        difference = {dim: exp for dim, exp in difference.items() if exp}
        if not difference:
            return self.get_conversion_factor(from_unit, to_unit)

        pair = self._amount_dimension_swap(difference)
        if pair is None:
            raise IncompatibleUnitsError(self._incompatible_message(from_unit, to_unit, difference))
        source_dim, target_dim, exponent = pair
        if substance is None:
            raise IncompatibleUnitsError(
                f"Substance required for {source_dim.lower()} to {target_dim.lower()} conversion "
                f"({from_unit} -> {to_unit}). Specify one, e.g. Quantity(..., substance='coal')."
            )
        ratio = self._amount_ratio(source_dim, target_dim, substance, basis)
        return self.unit_factor(from_unit) * ratio**exponent / self.unit_factor(to_unit)

    @staticmethod
    def _amount_dimension_swap(difference: Dict[str, int]) -> Optional[Tuple[str, str, int]]:
        if len(difference) != 2:
            return None
        (dim1, exp1), (dim2, exp2) = difference.items()
        if exp1 != -exp2 or dim1 not in AMOUNT_DIMENSIONS or dim2 not in AMOUNT_DIMENSIONS:
            return None
        return (dim1, dim2, exp1) if exp1 > 0 else (dim2, dim1, exp2)

    def _amount_ratio(self, source_dim: str, target_dim: str, substance: str, basis: Optional[str]) -> float:
        """Amount of ``target_dim`` (base units) per base unit of ``source_dim``."""
        from .substance import substance_registry

        def tonnes_per_base_unit(dim: str) -> float:
            if dim == "MASS":
                return 1.0 / self.unit_factor("t")
            if dim == "ENERGY":
                if basis is not None and basis.upper() == "HHV":
                    heating_value = substance_registry.hhv(substance)
                else:
                    heating_value = substance_registry.lhv(substance)
                if heating_value <= 0:
                    raise MissingDataError(f"Substance '{substance}' has no positive heating value")
                # heating value in MJ/kg -> base energy units per base mass unit
                return 1.0 / (heating_value * self.unit_factor("MJ/kg")) / self.unit_factor("t")
            # VOLUME: density in kg/m3 -> base mass units per base volume unit
            density = substance_registry.density(substance)
            return density * self.unit_factor("kg/m3") / self.unit_factor("t")

        return tonnes_per_base_unit(source_dim) / tonnes_per_base_unit(target_dim)

    def _incompatible_message(self, from_unit: str, to_unit: str, difference: Dict[str, int]) -> str:
        msg = (
            f"Cannot convert from {from_unit} ({self.get_dimension(from_unit)}) "
            f"to {to_unit} ({self.get_dimension(to_unit)})."
        )
        if set(difference) == {"TIME"}:
            msg += (
                " The units differ by a time dimension: multiply or divide by a duration "
                "instead, e.g. Quantity(100, 'MW') * Quantity(2, 'h')."
            )
        return msg

    # ------------------------------------------------------------- unit algebra

    def multiply_units(self, unit1: str, unit2: str) -> Tuple[str, float]:
        """Unit of a product and the factor to apply to the product of the values.

        Example: ``multiply_units("USD/kW", "MW") == ("USD", 1000.0)``.
        """
        unit, numerator, denominator = self.combine_units(unit1, unit2, 1)
        return unit, numerator / denominator

    def divide_units(self, unit1: str, unit2: str) -> Tuple[str, float]:
        """Unit of a quotient and the factor to apply to the quotient of the values.

        Example: ``divide_units("MWh", "a") == ("MW", 1 / 8760)``.
        """
        unit, numerator, denominator = self.combine_units(unit1, unit2, -1)
        return unit, numerator / denominator

    @lru_cache(maxsize=4096)
    def combine_units(self, unit1: str, unit2: str, sign: int) -> Tuple[str, float, float]:
        """Unit of ``unit1 * unit2`` (``sign=1``) or ``unit1 / unit2`` (``sign=-1``).

        Returns ``(unit, numerator, denominator)``; the combined value is
        ``value1 * value2 * numerator / denominator`` (or ``value1 / value2 * ...``).
        Keeping numerator and denominator separate preserves floating point exactness.
        """
        items = [[atom, exp, {0}] for atom, exp in self.parse_unit(unit1)]
        items += [[atom, exp * sign, {1}] for atom, exp in self.parse_unit(unit2)]
        scale = [1.0, 1.0]
        items = self._merge_same_kind(items, scale)
        while self._apply_dimension_rule(items, scale):
            items = self._merge_same_kind(items, scale)
        return self.format_terms([(atom, exp) for atom, exp, _ in items]), scale[0], scale[1]

    def _scale_by(self, scale: List[float], atom: str, exp: int) -> None:
        """Multiply ``scale`` (numerator, denominator) by ``factor(atom) ** exp``."""
        if exp > 0:
            scale[0] *= self._conversion_factors[atom] ** exp
        elif exp < 0:
            scale[1] *= self._conversion_factors[atom] ** -exp

    def _same_kind(self, atom1: str, atom2: str) -> bool:
        dim = self._dimensions[atom1]
        if dim != self._dimensions[atom2]:
            return False
        if atom1 not in self._conversion_factors or atom2 not in self._conversion_factors:
            return False
        currency1 = self.currency_of(atom1)
        if currency1 is not None:
            currency2 = self.currency_of(atom2)
            return currency2 is not None and currency1[0] == currency2[0]
        return True

    def _merge_same_kind(self, items: list, scale: List[float]) -> list:
        """Merge atoms of the same kind, converting later atoms into earlier ones."""
        merged: list = []
        for atom, exp, origin in items:
            for existing in merged:
                if existing[0] == atom:
                    existing[1] += exp
                    existing[2] = existing[2] | origin
                    break
                if self._same_kind(existing[0], atom):
                    # atom**exp == (factor(atom) / factor(existing))**exp * existing**exp
                    self._scale_by(scale, atom, exp)
                    self._scale_by(scale, existing[0], -exp)
                    existing[1] += exp
                    existing[2] = existing[2] | origin
                    break
            else:
                merged.append([atom, exp, set(origin)])
        return [item for item in merged if item[1] != 0]

    def _result_unit(self, atom: str, result_dimension: str) -> Optional[str]:
        corresponding = self._corresponding_units.get(atom)
        if corresponding is not None and self._dimensions.get(corresponding) == result_dimension:
            return corresponding
        return self._preferred_units.get(result_dimension, self._base_units.get(result_dimension))

    def _atom_vector(self, atom: str) -> Dict[str, int]:
        return dict(self._dimension_name_vector(self._dimensions[atom]))

    def _apply_dimension_rule(self, items: list, scale: List[float]) -> bool:
        """Apply the first matching multiplication/division rule in place (e.g. MW·h -> MWh).

        Rules only combine atoms that stem from different operands, so a unit
        like ``"MWh/a"`` is never rewritten on its own. Returns True if a rule was applied.
        """
        candidates = []
        for rule in self._dimensional_multiplication_rules:
            dims = list(rule["dimensions"])
            source_dim = rule["source_dimension"]
            other_dim = dims[1] if dims[0] == source_dim else dims[0]
            candidates.append((source_dim, 1, other_dim, 1, rule["result_dimension"]))
        for rule in self._dimensional_division_rules:
            candidates.append(
                (rule["numerator_dimension"], 1, rule["denominator_dimension"], -1, rule["result_dimension"])
            )

        for source_dim, source_exp, other_dim, other_exp, result_dim in candidates:
            for i, source in enumerate(items):
                if source[1] != source_exp or self._dimensions[source[0]] != source_dim:
                    continue
                for j, other in enumerate(items):
                    if j == i or other[1] != other_exp or self._dimensions[other[0]] != other_dim:
                        continue
                    if source[2] | other[2] != {0, 1}:
                        continue
                    target = self._result_unit(source[0], result_dim)
                    if target is None or target not in self._dimensions:
                        continue
                    # Only apply rules that are dimensionally coherent.
                    expected: Dict[str, int] = {}
                    for atom, exp in ((source[0], source_exp), (other[0], other_exp)):
                        for dim, dim_exp in self._atom_vector(atom).items():
                            expected[dim] = expected.get(dim, 0) + dim_exp * exp
                    if {d: e for d, e in expected.items() if e} != self._atom_vector(target):
                        continue
                    if any(a not in self._conversion_factors for a in (source[0], other[0], target)):
                        continue
                    # source * other**other_exp == factor * target
                    self._scale_by(scale, source[0], 1)
                    self._scale_by(scale, other[0], other_exp)
                    self._scale_by(scale, target, -1)
                    items[i] = [target, 1, source[2] | other[2]]
                    del items[j]
                    return True
        return False

    # ---------------------------------------------------------------- currencies

    def currency_of(self, atom: str) -> Optional[Tuple[str, float]]:
        """Return ``(currency_code, scale)`` for a currency unit, else ``None``.

        Example: ``currency_of("MEUR") == ("EUR", 1e6)``.
        """
        if self._dimensions.get(atom) != "CURRENCY":
            return None
        info = self._currency_units.get(atom)
        if info is None:
            return atom, 1.0
        return info["currency"], float(info.get("scale", 1.0))

    def currency_terms(self, unit: str) -> List[Tuple[str, str, int]]:
        """Currency atoms of a unit as ``(atom, currency_code, exponent)`` tuples."""
        result = []
        for atom, exp in self.parse_unit(unit):
            info = self.currency_of(atom)
            if info is not None:
                result.append((atom, info[0], exp))
        return result

    # ------------------------------------------------------ legacy/compat helpers

    def are_dimensions_compatible(self, from_dim: str, to_dim: str) -> bool:
        """Check whether two *named* dimensions can be converted into each other.

        ``ENERGY``/``POWER`` pairs are reported as compatible for backwards
        compatibility with :meth:`convert_between_dimensions`; :class:`Quantity`
        itself requires an explicit duration for that conversion.
        """
        if from_dim == to_dim:
            return True
        conversions = {
            ("ENERGY", "POWER"),
            ("POWER", "ENERGY"),
            ("MASS", "VOLUME"),
            ("VOLUME", "MASS"),
            ("MASS", "ENERGY"),
            ("ENERGY", "MASS"),
            ("ENERGY", "VOLUME"),
            ("VOLUME", "ENERGY"),
        }
        return (from_dim, to_dim) in conversions

    def convert_between_dimensions(
        self,
        value,
        from_unit: str,
        to_unit: str,
        substance: Optional[str] = None,
        **kwargs,
    ):
        """Convert a value between related dimensions.

        Mass, volume and energy conversions use the substance properties
        (``basis`` keyword, default LHV). Power/energy conversions use the
        ``hours`` keyword (default 1 h).
        """
        from_dim = self.get_dimension(from_unit)
        to_dim = self.get_dimension(to_unit)
        if {from_dim, to_dim} == {"POWER", "ENERGY"}:
            hours = kwargs.get("hours", 1.0)
            if from_dim == "POWER":
                return (
                    value
                    * self.get_conversion_factor(from_unit, "MW")
                    * hours
                    * self.get_conversion_factor("MWh", to_unit)
                )
            return (
                value
                * self.get_conversion_factor(from_unit, "MWh")
                / hours
                * self.get_conversion_factor("MW", to_unit)
            )
        try:
            factor = self.conversion_factor(from_unit, to_unit, substance, kwargs.get("basis"))
        except IncompatibleUnitsError as exc:
            if "Substance required" in str(exc):
                raise
            raise IncompatibleUnitsError(f"No conversion defined between {from_dim} and {to_dim}") from exc
        return value * factor

    def get_corresponding_unit(self, unit: str, target_dimension: str) -> str:
        """Get the corresponding unit in another dimension (e.g. ``MW`` -> ``MWh``)."""
        corresponding = self._corresponding_units.get(unit)
        if corresponding is not None and self._dimensions.get(corresponding) == target_dimension:
            return corresponding
        raise UnknownUnitError(f"No corresponding {target_dimension} unit for {unit}")

    def get_multiplication_result(self, dim1: str, dim2: str) -> Optional[tuple]:
        """Result and source dimension of multiplying two dimensions, if a rule exists.

        Example: ``("POWER", "TIME")`` -> ``("ENERGY", "POWER")``.
        """
        for rule in self._dimensional_multiplication_rules:
            if sorted(rule["dimensions"]) == sorted([dim1, dim2]):
                return rule["result_dimension"], rule["source_dimension"]
        return None

    def get_division_result(self, numerator_dim: str, denominator_dim: str) -> Optional[str]:
        """Result dimension of dividing two dimensions, if a rule exists.

        Example: ``("ENERGY", "TIME")`` -> ``"POWER"``.
        """
        for rule in self._dimensional_division_rules:
            if (
                rule["numerator_dimension"] == numerator_dim
                and rule["denominator_dimension"] == denominator_dim
            ):
                return rule["result_dimension"]
        return None


registry = UnitRegistry()
