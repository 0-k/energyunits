"""Substance properties for energy system modeling."""

import difflib
import json
import threading
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Dict, List, Optional

from ._loading import DataSource, is_number, raise_conflicts, read_source, same_value
from .exceptions import EnergyUnitsError, MissingDataError, UnknownSubstanceError

_DATA_DIR = Path(__file__).parent / "data"

#: Combustion products that can be derived from fuel composition:
#: product -> (composition field, kg product per kg of the element/fraction)
COMBUSTION_PRODUCTS: Dict[str, tuple] = {
    "CO2": ("carbon_content", 44.0 / 12.0),
    "H2O": ("hydrogen_content", 18.0 / 2.0),
    "ash": ("ash_content", 1.0),
}

_NUMERIC_FIELDS = (
    "hhv",
    "lhv",
    "density",
    "carbon_intensity",
    "carbon_content",
    "hydrogen_content",
    "ash_content",
    "moisture_content",
)
_RANGE_FIELDS = ("lhv_range", "carbon_intensity_range")


def _freeze(value):
    """Read-only copy: mappings become mapping proxies, lists become tuples."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value):
    """Mutable copy of a frozen value (mapping proxies become dicts; tuples stay tuples)."""
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_thaw(item) for item in value)
    return value


def _validate(name, props) -> None:
    if not isinstance(name, str) or not name or name != name.strip():
        raise ValueError(f"Invalid substance name {name!r}")
    if not isinstance(props, Mapping):
        raise ValueError(f"Properties of substance '{name}' must be a JSON object")
    for field in _NUMERIC_FIELDS:
        value = props.get(field)
        if value is not None and not is_number(value):
            raise ValueError(f"Property '{field}' of substance '{name}' must be a number or null")
    for field in _RANGE_FIELDS:
        value = props.get(field)
        if value is None:
            continue
        where = f"Property '{field}' of substance '{name}'"
        if not (isinstance(value, (list, tuple)) and len(value) == 2 and all(is_number(v) for v in value)):
            raise ValueError(f"{where} must be [lower, upper] or null")
        if value[0] > value[1]:
            raise ValueError(f"{where}: lower limit exceeds upper limit")


def _differences(old: Mapping, new: Mapping) -> str:
    """Short description of how ``new`` differs from ``old`` (for conflict messages)."""
    changed = [
        f"{key} {old.get(key)!r} -> {value!r}"
        for key, value in new.items()
        if not same_value(old.get(key), value)
    ]
    dropped = [key for key, value in old.items() if key not in new and value is not None]
    text = ", ".join(changed[:4]) + (f" and {len(changed) - 4} more" if len(changed) > 4 else "")
    if dropped:
        text += ("; " if text else "") + f"would drop {len(dropped)} other properties"
    return text


def _complete_carbon(props: dict) -> dict:
    """Derive carbon_content from carbon_intensity and lhv (or vice versa) if only one is given.

    Emission factors are usually published per unit of energy (kg CO2/GJ), so a
    custom fuel with ``lhv`` and ``carbon_intensity`` is enough for all CO2
    conversions: ``carbon_content = carbon_intensity * lhv / 1000 * 12/44``.
    """
    lhv = props.get("lhv")
    if not lhv:
        return props
    if props.get("carbon_content") is None and props.get("carbon_intensity") is not None:
        props["carbon_content"] = props["carbon_intensity"] * lhv / 1000 * 12 / 44
    elif props.get("carbon_intensity") is None and props.get("carbon_content") is not None:
        props["carbon_intensity"] = props["carbon_content"] * 44 / 12 / lhv * 1000
    return props


class SubstanceRegistry:
    """Registry of substances and their properties.

    Properties per substance (all optional, ``None`` if unknown):

    * ``hhv`` / ``lhv``: higher / lower heating value in MJ/kg
    * ``lhv_range`` / ``carbon_intensity_range``: IPCC lower and upper limits
    * ``density``: kg/m3 (gases at 15 °C and 101.325 kPa, see ``density_basis``)
    * ``carbon_intensity``: kg CO2 per GJ (LHV basis)
    * ``carbon_content`` / ``hydrogen_content`` / ``ash_content``: mass fractions
    * ``ipcc_category`` / ``source``: provenance of the values

    A module-level instance is available as
    :data:`energyunits.substance.substance_registry`.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._substances: Dict[str, Mapping] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        with open(_DATA_DIR / "substances.json", encoding="utf-8") as f:
            self._ingest(json.load(f), overwrite=False, replace_all=True)

    def reset(self) -> None:
        """Discard custom substances and reload the bundled defaults.

        This affects every user of the registry in the process; it is meant for
        scripts and tests, not for libraries.
        """
        self._load_defaults()

    def load_substances(self, source: DataSource, overwrite: bool = False) -> None:
        """Load custom substances from a JSON file or a mapping.

        Format: ``{"my_fuel": {"lhv": 24.0, "hhv": 25.3, "carbon_intensity": 95.0, ...}}``
        with the properties listed in the class documentation. Keys starting with
        ``_`` are ignored. If only one of ``carbon_intensity`` and ``carbon_content``
        is given (together with ``lhv``), the other is derived.

        Loading is all or nothing. Substances identical to existing ones are
        accepted, so loading the same data twice is harmless.

        Args:
            source: Path of a JSON file, or a mapping with the same structure.
            overwrite: Replace existing substances whose properties differ. Without
                it such conflicts raise :class:`DefinitionConflictError`.
                Overwriting changes results for every user of the registry in the process.

        Raises:
            DefinitionConflictError: if a substance of the same name exists with other properties.
            ValueError: if the data is malformed (nothing is loaded).
        """
        self._ingest(read_source(source), overwrite=overwrite)

    def _ingest(self, data: dict, overwrite: bool, replace_all: bool = False) -> None:
        entries = {}
        for name, props in data.items():
            if isinstance(name, str) and name.startswith("_"):
                continue
            _validate(name, props)
            entries[name] = _freeze(_complete_carbon(_thaw(props)))
        with self._lock:
            substances = {} if replace_all else dict(self._substances)
            conflicts = [
                f"{name}: {_differences(substances[name], props)}"
                for name, props in entries.items()
                if name in substances and not same_value(substances[name], props)
            ]
            if not overwrite:
                raise_conflicts("substances", conflicts)
            substances.update(entries)
            self._substances = substances

    def __getitem__(self, substance_id: str) -> Mapping:
        """Read-only view of the properties of a substance (use :meth:`get_properties` for a copy)."""
        if substance_id not in self._substances:
            close = difflib.get_close_matches(str(substance_id), self._substances.keys(), n=3)
            msg = f"Unknown substance: '{substance_id}'."
            if close:
                msg += f" Did you mean: {', '.join(close)}?"
            else:
                msg += f" Available substances: {', '.join(sorted(self._substances))}"
            raise UnknownSubstanceError(msg)
        return self._substances[substance_id]

    def __contains__(self, substance_id: str) -> bool:
        """Check if substance exists."""
        return substance_id in self._substances

    def _property(self, substance_id: str, field: str, description: str) -> float:
        value = self[substance_id].get(field)
        if value is None:
            raise MissingDataError(f"Substance '{substance_id}' has no {description}")
        return value

    def hhv(self, substance_id: str) -> float:
        """Higher heating value in MJ/kg."""
        return self._property(substance_id, "hhv", "heating value (hhv)")

    def lhv(self, substance_id: str) -> float:
        """Lower heating value in MJ/kg."""
        return self._property(substance_id, "lhv", "heating value (lhv)")

    def density(self, substance_id: str) -> float:
        """Density in kg/m3."""
        return self._property(substance_id, "density", "defined density")

    def lhv_hhv_ratio(self, substance_id: str) -> float:
        """Ratio of lower to higher heating value."""
        return self.lhv(substance_id) / self.hhv(substance_id)

    def list_substances(self, has_property: Optional[str] = None) -> List[str]:
        """List all available substances, optionally filtered by property.

        Args:
            has_property: Only return substances where this property is defined
                (e.g. ``"hhv"``, ``"density"``, ``"carbon_content"``).

        Returns:
            Sorted list of substance names.
        """
        if has_property is None:
            return sorted(self._substances)
        return sorted(name for name, props in self._substances.items() if props.get(has_property) is not None)

    def get_properties(self, substance_id: str) -> dict:
        """Copy of all properties of a substance (ranges as ``(lower, upper)`` tuples)."""
        return _thaw(self[substance_id])

    def combustion_product_factor(self, substance_id: str, product: str) -> float:
        """Mass of combustion ``product`` per unit mass of fuel (e.g. t CO2 per t coal)."""
        if product not in COMBUSTION_PRODUCTS:
            raise EnergyUnitsError(
                f"Substance conversion only supported for combustion products: "
                f"{', '.join(COMBUSTION_PRODUCTS)}. Got: '{product}'"
            )
        field, molar_ratio = COMBUSTION_PRODUCTS[product]
        content = self._property(substance_id, field, field.replace("_", " "))
        return content * molar_ratio

    def calculate_combustion_product(self, fuel_quantity, target_substance: str):
        """Combustion product of a fuel quantity, in tonnes where possible.

        Equivalent to ``fuel_quantity.to(substance=target_substance)`` converted to ``t``.
        """
        if fuel_quantity.substance is None:
            raise EnergyUnitsError("Fuel substance must be specified")
        product = fuel_quantity.to(substance=target_substance)
        from .registry import registry

        if registry.is_compatible(product.unit, "t"):
            return product.to("t")
        return product


substance_registry = SubstanceRegistry()
