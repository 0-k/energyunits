"""Substance properties for energy system modeling."""

import json
from pathlib import Path


class SubstanceRegistry:
    """Registry of substances and their properties."""

    def __init__(self):
        self._substances = {}
        self._load_defaults()

    def _load_defaults(self):
        """Load default substance data from JSON."""
        data_path = Path(__file__).parent / "data" / "substances.json"
        with open(data_path) as f:
            data = json.load(f)
        # Filter out metadata fields
        self._substances = {k: v for k, v in data.items() if not k.startswith("_")}

    def load_substances(self, file_path: str):
        """Load custom substances from JSON file."""
        with open(file_path) as f:
            data = json.load(f)
        # Filter out metadata fields
        self._substances.update({k: v for k, v in data.items() if not k.startswith("_")})

    def __getitem__(self, substance_id):
        """Dict-like access to substance data."""
        if substance_id not in self._substances:
            import difflib

            close = difflib.get_close_matches(
                substance_id, self._substances.keys(), n=3
            )
            msg = f"Unknown substance: '{substance_id}'."
            if close:
                msg += f" Did you mean: {', '.join(close)}?"
            else:
                msg += (
                    f" Available substances: {', '.join(sorted(self._substances.keys()))}"
                )
            raise ValueError(msg)
        return self._substances[substance_id]

    def __contains__(self, substance_id):
        """Check if substance exists."""
        return substance_id in self._substances

    def hhv(self, substance_id):
        """Get higher heating value in MJ/kg."""
        substance = self[substance_id]
        hhv = substance["hhv"]
        if hhv is None:
            raise ValueError(f"Substance '{substance_id}' has no heating value")
        return hhv

    def lhv(self, substance_id):
        """Get lower heating value in MJ/kg."""
        substance = self[substance_id]
        lhv = substance["lhv"]
        if lhv is None:
            raise ValueError(f"Substance '{substance_id}' has no heating value")
        return lhv

    def density(self, substance_id):
        """Get density in kg/m3."""
        substance = self[substance_id]
        density = substance["density"]
        if density is None:
            raise ValueError(f"Substance '{substance_id}' has no defined density")
        return density

    def list_substances(self, has_property=None):
        """List all available substances, optionally filtered by property.

        Args:
            has_property: Filter to substances that have this property defined
                          (e.g., "hhv", "density", "carbon_content").

        Returns:
            Sorted list of substance names.
        """
        if has_property is None:
            return sorted(self._substances.keys())
        return sorted(
            name
            for name, props in self._substances.items()
            if props.get(has_property) is not None
        )

    def get_properties(self, substance_id):
        """Get all properties for a substance as a dict.

        Args:
            substance_id: Substance identifier.

        Returns:
            Dict of property name to value.
        """
        return dict(self[substance_id])

    def lhv_hhv_ratio(self, substance_id):
        """Get the ratio of LHV to HHV."""
        return self.lhv(substance_id) / self.hhv(substance_id)

    def calculate_combustion_product(self, fuel_quantity, target_substance):
        """Calculate combustion products from fuel based on stoichiometry."""
        from .quantity import Quantity

        if fuel_quantity.substance is None:
            raise ValueError("Fuel substance must be specified")

        fuel_t = fuel_quantity.to("t")
        fuel_mass = fuel_t.value
        substance = self[fuel_quantity.substance]

        if target_substance == "CO2":
            carbon_mass = fuel_mass * substance["carbon_content"]
            co2_mass = carbon_mass * (44 / 12)
            return Quantity(co2_mass, "t", "CO2")

        elif target_substance == "H2O":
            hydrogen_mass = fuel_mass * substance["hydrogen_content"]
            water_mass = hydrogen_mass * (18 / 2)
            return Quantity(water_mass, "t", "H2O")

        elif target_substance == "ash":
            ash_mass = fuel_mass * substance["ash_content"]
            return Quantity(ash_mass, "t", "ash")

        else:
            raise ValueError(f"Unknown combustion product: {target_substance}")


substance_registry = SubstanceRegistry()
