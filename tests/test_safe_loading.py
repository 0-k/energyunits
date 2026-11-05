"""Loading custom data never silently changes existing definitions (registries are reset after each test)."""

import json
import threading
from pathlib import Path

import pytest

import energyunits
from energyunits import DefinitionConflictError, Quantity
from energyunits.exchange_rate import exchange_rate_registry
from energyunits.inflation import inflation_registry
from energyunits.registry import registry
from energyunits.substance import substance_registry

DATA = Path(energyunits.__file__).resolve().parent / "data"
MMSCF = {"dimensions": {"MMscf": "VOLUME"}, "conversion_factors": {"MMscf": 28316.846592}}


class TestUnits:
    def test_new_units_from_a_mapping(self):
        registry.load_units(MMSCF)
        assert Quantity(1, "MMscf").to("m3").value == pytest.approx(28316.846592)

    def test_loading_the_same_data_twice_is_harmless(self, tmp_path):
        path = tmp_path / "units.json"
        path.write_text(json.dumps(MMSCF))
        registry.load_units(path)
        registry.load_units(str(path))
        registry.load_units(MMSCF)
        assert Quantity(1, "MMscf").to("m3").value == pytest.approx(28316.846592)

    def test_bundled_data_can_be_loaded_again(self):
        registry.load_units(DATA / "units.json")
        substance_registry.load_substances(DATA / "substances.json")
        inflation_registry.load_inflation(DATA / "inflation.json")
        exchange_rate_registry.load_exchange_rates(DATA / "exchange_rates.json")

    def test_redefining_a_unit_raises_and_loads_nothing(self):
        registry.load_units(MMSCF)
        other = {
            "dimensions": {"MMscf": "VOLUME", "Mscf": "VOLUME"},
            "conversion_factors": {"MMscf": 26800.0, "Mscf": 28.316846592},
        }
        with pytest.raises(
            DefinitionConflictError, match=r"conversion_factors\['MMscf'\]: 28316.846592 -> 26800.0"
        ):
            registry.load_units(other)
        assert Quantity(1, "MMscf").to("m3").value == pytest.approx(28316.846592)
        assert not registry.has_unit("Mscf")

    def test_bundled_units_are_protected(self):
        with pytest.raises(DefinitionConflictError, match="overwrite=True"):
            registry.load_units({"conversion_factors": {"MWh": 3.7e9}})
        with pytest.raises(DefinitionConflictError):
            registry.load_units({"dimensions": {"t": "VOLUME"}})
        assert Quantity(1, "MWh").to("GJ").value == 3.6

    def test_conflict_error_is_a_value_error(self):
        with pytest.raises(ValueError):
            registry.load_units({"conversion_factors": {"MWh": 3.7e9}})

    def test_overwrite(self):
        registry.load_units(MMSCF)
        assert Quantity(1, "MMscf").to("m3").value == pytest.approx(28316.846592)  # fills the caches
        registry.load_units({"conversion_factors": {"MMscf": 26800.0}}, overwrite=True)
        assert Quantity(1, "MMscf").to("m3").value == pytest.approx(26800.0)

    def test_conflicting_rule(self):
        rule = {
            "numerator_dimension": "ENERGY",
            "denominator_dimension": "TIME",
            "result_dimension": "ENERGY",
        }
        with pytest.raises(DefinitionConflictError, match="dimensional_division_rules"):
            registry.load_units({"dimensional_division_rules": [rule]})
        same = {"numerator_dimension": "ENERGY", "denominator_dimension": "TIME", "result_dimension": "POWER"}
        registry.load_units({"dimensional_division_rules": [same]})
        assert (Quantity(10, "MWh") / Quantity(2, "h")).unit == "MW"

    def test_invalid_data_leaves_the_registry_unchanged(self):
        data = {
            "dimensions": {"widget": "A"},
            "conversion_factors": {"widget": 1.0},
            "derived_dimensions": {"A": {"B": 1}, "B": {"A": 1}},
        }
        with pytest.raises(ValueError, match="Circular"):
            registry.load_units(data)
        assert not registry.has_unit("widget")
        assert Quantity(1, "MW").to("kW").value == 1000

    @pytest.mark.parametrize(
        "data, message",
        [
            ({"conversion_factor": {"x": 1.0}}, "Unknown section"),
            ({"dimensions": {"x": "ENERGY"}, "conversion_factors": {"x": 0}}, "positive number"),
            ({"dimensions": {"x": "ENERGY"}, "conversion_factors": {"x": "1"}}, "positive number"),
            ({"dimensions": ["x"]}, "must be an object"),
            ({"dimensions": {"x y": "ENERGY"}}, "Invalid unit name"),
            ({"dimensional_division_rules": [{"numerator_dimension": "ENERGY"}]}, "missing"),
            ({"currency_units": {"kAUD": {"scale": 1000}}}, "currency"),
        ],
    )
    def test_malformed_data(self, data, message):
        with pytest.raises(ValueError, match=message):
            registry.load_units(data)

    def test_comment_keys_are_ignored(self):
        registry.load_units({"_note": "custom gas units", **MMSCF})
        assert registry.has_unit("MMscf")

    def test_source_types(self):
        with pytest.raises(TypeError, match="file path or a mapping"):
            registry.load_units(42)
        with pytest.raises(FileNotFoundError):
            registry.load_units("does-not-exist.json")

    def test_later_changes_to_the_mapping_have_no_effect(self):
        data = json.loads(json.dumps(MMSCF))
        registry.load_units(data)
        data["conversion_factors"]["MMscf"] = 1.0
        assert Quantity(1, "MMscf").to("m3").value == pytest.approx(28316.846592)

    def test_caches_remain_inspectable(self):
        registry.get_dimension("kWh")
        assert registry.get_dimension.cache_info().currsize >= 1


class TestSubstances:
    def test_redefining_a_bundled_substance_raises(self):
        with pytest.raises(DefinitionConflictError, match=r"coal: .*lhv 25.8 -> 20.0"):
            substance_registry.load_substances({"coal": {"lhv": 20.0, "carbon_intensity": 94.6}})
        assert Quantity(1, "t", "coal").to("GJ").value == pytest.approx(25.8)

    def test_overwrite(self):
        substance_registry.load_substances({"coal": {"lhv": 20.0, "carbon_intensity": 94.6}}, overwrite=True)
        assert Quantity(1, "t", "coal").to("GJ").value == pytest.approx(20.0)

    def test_round_trip_of_properties_is_harmless(self):
        props = substance_registry.get_properties("lignite")
        substance_registry.load_substances({"lignite": props})
        substance_registry.load_substances({"my_lignite": {**props, "lhv": 8.9}})
        assert Quantity(1, "t", "my_lignite").to("GJ").value == pytest.approx(8.9)

    def test_all_or_nothing(self):
        with pytest.raises(DefinitionConflictError):
            substance_registry.load_substances({"biogas": {"lhv": 20.0}, "natural_gas": {"lhv": 50.0}})
        assert "biogas" not in substance_registry
        with pytest.raises(ValueError):
            substance_registry.load_substances({"biogas": {"lhv": 20.0}, "bad": {"lhv": "x"}})
        assert "biogas" not in substance_registry

    def test_item_access_is_read_only(self):
        with pytest.raises(TypeError):
            substance_registry["coal"]["lhv"] = 1.0
        assert substance_registry["coal"]["lhv_range"] == (19.9, 30.5)

    def test_get_properties_returns_an_independent_copy(self):
        props = substance_registry.get_properties("coal")
        props["lhv"] = 1.0
        assert substance_registry["coal"]["lhv"] == 25.8

    def test_nested_custom_fields_are_frozen(self):
        substance_registry.load_substances({"fuel": {"lhv": 20.0, "notes": {"tags": ["a"]}}})
        notes = substance_registry["fuel"]["notes"]
        assert notes["tags"] == ("a",)
        with pytest.raises(TypeError):
            notes["tags"] = ()


class TestEconomicData:
    def test_new_years_and_currencies_are_added(self):
        inflation_registry.load_inflation({"USD": {"2031": 2.0}, "AUD": {"2020": 0.9, "2021": 2.9}})
        assert inflation_registry.get_available_years("USD")[1] == 2031
        exchange_rate_registry.load_exchange_rates({"AUD": {"2020": 0.69}})
        assert exchange_rate_registry.get_exchange_rate("AUD", 2020) == 0.69

    def test_changing_a_bundled_rate_raises(self):
        with pytest.raises(DefinitionConflictError, match="inflation rate USD 2026"):
            inflation_registry.load_inflation({"USD": {"2026": 2.9}})
        with pytest.raises(DefinitionConflictError, match="exchange rate EUR 2020"):
            exchange_rate_registry.load_exchange_rates({"EUR": {"2020": 1.5}})

    def test_projected_from_change_raises(self):
        with pytest.raises(DefinitionConflictError, match="projected_from USD"):
            inflation_registry.load_inflation({"_metadata": {"projected_from": {"USD": 2031}}})

    def test_replacing_a_projection_with_an_actual_value(self):
        inflation_registry.load_inflation(
            {"USD": {"2026": 2.9}, "_metadata": {"projected_from": {"USD": 2027}}}, overwrite=True
        )
        assert inflation_registry.get_projected_from("USD") == 2027
        assert inflation_registry.get_cumulative_inflation_factor("USD", 2025, 2026) == pytest.approx(1.029)

    @pytest.mark.parametrize("rates", [{"USD": {"2031": "2.0"}}, {"USD": {"20x1": 2.0}}, {"USD": [2.0]}])
    def test_malformed_inflation_data(self, rates):
        with pytest.raises(ValueError):
            inflation_registry.load_inflation(rates)


def test_conversions_in_other_threads_are_unaffected_by_loading():
    """Readers see existing definitions unchanged while another thread loads new ones."""
    expected = (
        Quantity(1, "MWh").to("GJ").value,
        Quantity(100, "USD/t", "coal").to("USD/MWh").value,
        (Quantity(10, "MW") * Quantity(30, "min")).value,
    )
    errors = []
    stop = threading.Event()

    def convert():
        try:
            while not stop.is_set():
                result = (
                    Quantity(1, "MWh").to("GJ").value,
                    Quantity(100, "USD/t", "coal").to("USD/MWh").value,
                    (Quantity(10, "MW") * Quantity(30, "min")).value,
                )
                if result != expected:
                    errors.append(result)
        except Exception as exc:  # noqa: BLE001 - any error is a failure
            errors.append(exc)

    readers = [threading.Thread(target=convert) for _ in range(4)]
    for thread in readers:
        thread.start()
    try:
        for i in range(200):
            registry.load_units(
                {"dimensions": {f"u{i}": "ENERGY"}, "conversion_factors": {f"u{i}": float(i + 1)}}
            )
            substance_registry.load_substances({f"fuel{i}": {"lhv": 20.0 + i}})
    finally:
        stop.set()
        for thread in readers:
            thread.join()
    assert errors == []
    assert Quantity(1, "u199").to("J").value == 200.0
