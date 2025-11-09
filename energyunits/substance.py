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
            self._substances = json.load(f)

    def load_substances(self, file_path: str):
        """Load custom substances from JSON file."""
        with open(file_path) as f:
            data = json.load(f)
        self._substances.update(data)

    def __getitem__(self, substance_id):
        """Dict-like access to substance data."""
        if substance_id not in self._substances:
            raise ValueError(f"Unknown substance: {substance_id}")
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
