"""Substance properties for energy system modeling."""

import difflib
import json
from pathlib import Path
from typing import Dict, List, Optional

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
)


class SubstanceRegistry:
    """Registry of substances and their properties.

    Properties per substance (all optional, ``None`` if unknown):

    * ``hhv`` / ``lhv``: higher / lower heating value in MJ/kg
    * ``density``: kg/m3
    * ``carbon_intensity``: kg CO2 per GJ (LHV basis)
    * ``carbon_content`` / ``hydrogen_content`` / ``ash_content``: mass fractions

    A module-level instance is available as
    :data:`energyunits.substance.substance_registry`.
    """

    def __init__(self) -> None:
        self._substances: Dict[str, dict] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        with open(_DATA_DIR / "substances.json", encoding="utf-8") as f:
            data = json.load(f)
        self._substances = {}
        self._ingest(data)

    def reset(self) -> None:
        """Discard custom substances and reload the bundled defaults."""
        self._load_defaults()

    def load_substances(self, file_path: str) -> None:
        """Load custom substances from a JSON file (entries are added or replaced)."""
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        self._ingest(data)

    def _ingest(self, data: dict) -> None:
        for name, props in data.items():
            if name.startswith("_"):
                continue
            if not isinstance(props, dict):
                raise ValueError(f"Properties of substance '{name}' must be a JSON object")
            for field in _NUMERIC_FIELDS:
                value = props.get(field)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
                    raise ValueError(f"Property '{field}' of substance '{name}' must be a number or null")
            self._substances[name] = dict(props)

    def __getitem__(self, substance_id: str) -> dict:
        """Dict-like access to substance data."""
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
        """Copy of all properties of a substance."""
        return dict(self[substance_id])

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
