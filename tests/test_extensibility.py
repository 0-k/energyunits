"""Loading custom data into the registries (all registries are reset after each test)."""

import json

import pytest

import energyunits
from energyunits import EnergyUnitsWarning, MissingDataError, Quantity, UnknownUnitError
from energyunits.exchange_rate import exchange_rate_registry
from energyunits.registry import registry


def _write(tmp_path, name, data):
    path = tmp_path / name
    path.write_text(json.dumps(data))
    return str(path)


class TestCustomUnits:
    def test_custom_unit_in_existing_dimension(self, tmp_path):
        registry.load_units(
            _write(
                tmp_path,
                "u.json",
                {"dimensions": {"MMscf": "VOLUME"}, "conversion_factors": {"MMscf": 28316.846592}},
            )
        )
        assert Quantity(1, "MMscf").to("m3").value == pytest.approx(28316.846592)
        assert "MMscf" in Quantity.list_units("VOLUME")

    def test_custom_derived_dimension(self, tmp_path):
        data = {
            "dimensions": {"m": "LENGTH", "km": "LENGTH", "kWh/km_unit": "ENERGY_PER_LENGTH"},
            "conversion_factors": {"m": 1.0, "km": 1000.0, "kWh/km_unit": 3.6e3},
            "base_units": {"LENGTH": "m", "ENERGY_PER_LENGTH": "kWh/km_unit"},
            "derived_dimensions": {"ENERGY_PER_LENGTH": {"ENERGY": 1, "LENGTH": -1}},
        }
        with pytest.raises(ValueError, match="Invalid unit name"):
            registry.load_units(_write(tmp_path, "bad.json", data))

        data["dimensions"] = {"m": "LENGTH", "km": "LENGTH", "Wh_per_m": "ENERGY_PER_LENGTH"}
        data["conversion_factors"] = {"m": 1.0, "km": 1000.0, "Wh_per_m": 3600.0}
        data["base_units"] = {"LENGTH": "m"}
        registry.load_units(_write(tmp_path, "u.json", data))
        consumption = Quantity(0.2, "kWh/km")
        assert consumption.dimension == "ENERGY_PER_LENGTH"
        assert consumption.to("Wh_per_m").value == pytest.approx(0.2)
        assert (consumption * Quantity(100, "km")).to("kWh").value == pytest.approx(20)

    def test_circular_derived_dimension(self, tmp_path):
        data = {"derived_dimensions": {"A": {"B": 1}, "B": {"A": 1}}, "dimensions": {"xa": "A"}}
        with pytest.raises(ValueError, match="Circular"):
            registry.load_units(_write(tmp_path, "u.json", data))

    def test_unit_without_factor(self, tmp_path):
        registry.load_units(_write(tmp_path, "u.json", {"dimensions": {"widget": "ENERGY"}}))
        with pytest.raises(MissingDataError, match="No conversion factor"):
            Quantity(1, "widget").to("MWh")

    def test_custom_multiplication_rule_needs_coherent_dimensions(self, tmp_path):
        # A rule between undeclared dimensions is ignored instead of producing wrong values
        data = {
            "dimensions": {"N": "FORCE", "m": "LENGTH"},
            "conversion_factors": {"N": 1.0, "m": 1.0},
            "dimensional_multiplication_rules": [
                {"dimensions": ["FORCE", "LENGTH"], "result_dimension": "ENERGY", "source_dimension": "FORCE"}
            ],
        }
        registry.load_units(_write(tmp_path, "u.json", data))
        assert registry.get_multiplication_result("FORCE", "LENGTH") == ("ENERGY", "FORCE")
        assert (Quantity(2, "N") * Quantity(3, "m")).unit == "N·m"

    def test_reset_discards_custom_units(self, tmp_path):
        registry.load_units(
            _write(
                tmp_path,
                "u.json",
                {"dimensions": {"MMscf": "VOLUME"}, "conversion_factors": {"MMscf": 28316.846592}},
            )
        )
        registry.reset()
        with pytest.raises(UnknownUnitError):
            Quantity(1, "MMscf")

    def test_registry_helpers(self):
        assert registry.base_unit("ENERGY") == "J"
        assert registry.preferred_unit("ENERGY") == "MWh"
        assert registry.has_unit("EUR/kW/a")
        assert not registry.has_unit("EUR/xyz")
        assert registry.get_division_result("ENERGY", "POWER") == "TIME"
        assert registry.get_division_result("MASS", "TIME") is None
        assert registry.currency_of("MEUR") == ("EUR", 1e6)
        assert registry.currency_of("MWh") is None
        with pytest.raises(UnknownUnitError):
            registry.base_unit("LENGTH")


class TestCustomExchangeRates:
    def test_new_currency(self, tmp_path):
        registry.load_units(
            _write(
                tmp_path, "u.json", {"dimensions": {"AUD": "CURRENCY"}, "conversion_factors": {"AUD": 0.65}}
            )
        )
        exchange_rate_registry.load_exchange_rates(
            _write(tmp_path, "fx.json", {"AUD": {"2020": 0.69, "2021": 0.75}})
        )
        assert "AUD" in Quantity.list_currencies()
        assert Quantity(100, "AUD", reference_year=2020).to("USD").value == pytest.approx(69)
        assert Quantity(100, "AUD", reference_year=2021).to("EUR").value == pytest.approx(75 / 1.1830)

    def test_currency_without_rates_uses_static_factor(self, tmp_path):
        registry.load_units(
            _write(
                tmp_path, "u.json", {"dimensions": {"CHF": "CURRENCY"}, "conversion_factors": {"CHF": 1.1}}
            )
        )
        assert Quantity(100, "CHF", reference_year=2020).to("USD").value == pytest.approx(110)

    def test_invalid_rate(self, tmp_path):
        with pytest.raises(ValueError, match="must be positive"):
            exchange_rate_registry.load_exchange_rates(_write(tmp_path, "fx.json", {"EUR": {"2020": 0}}))

    def test_detect_currency(self):
        assert exchange_rate_registry.detect_currency_from_unit("MEUR/GW") == "EUR"
        assert exchange_rate_registry.detect_currency_from_unit("€ per MWh") is None
        assert exchange_rate_registry.get_available_years("USD") is None
        assert exchange_rate_registry.convert_currency(5, "EUR", "EUR", 2020) == 5

    def test_future_year_warning_points_to_caller(self):
        with pytest.warns(EnergyUnitsWarning) as record:
            Quantity(1, "EUR", reference_year=2099).to("USD")
        assert record[0].filename == __file__


def test_unknown_package_attribute():
    with pytest.raises(AttributeError):
        energyunits.does_not_exist
