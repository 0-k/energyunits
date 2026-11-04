"""Currency conversion and inflation adjustment of compound cost units."""

import warnings

import pytest

from energyunits import EnergyUnitsWarning, MissingDataError, Quantity
from energyunits.exchange_rate import exchange_rate_registry
from energyunits.inflation import inflation_registry


def _fx(currency, year):
    return exchange_rate_registry.get_exchange_rate(currency, year)


class TestCompoundCurrencyConversion:
    def test_currency_and_energy_unit_change(self):
        """Regression: the energy part of USD/MWh -> EUR/GJ used to be ignored."""
        price = Quantity(50, "USD/MWh", reference_year=2020)
        assert price.to("EUR/GJ").value == pytest.approx(50 / _fx("EUR", 2020) / 3.6)

    def test_currency_and_power_unit_change(self):
        capex = Quantity(1000, "USD/kW", reference_year=2023)
        assert capex.to("EUR/MW").value == pytest.approx(1000 * 1000 / _fx("EUR", 2023))

    def test_prefixed_currencies(self):
        assert Quantity(1.2, "MEUR/MW").to("EUR/kW").value == pytest.approx(1200)
        assert Quantity(3, "bnUSD").to("MUSD").value == pytest.approx(3000)
        capex = Quantity(1.2, "MEUR/MW", reference_year=2020).to("USD/kW")
        assert capex.value == pytest.approx(1200 * _fx("EUR", 2020))

    def test_currency_in_denominator(self):
        # MWh per EUR -> MWh per USD: 1 USD buys fewer MWh than 1 EUR when EUR > USD
        result = Quantity(1, "MWh/EUR", reference_year=2020).to("MWh/USD")
        assert result.value == pytest.approx(1 / _fx("EUR", 2020))

    def test_latest_rate_without_reference_year(self):
        latest_year = exchange_rate_registry.get_available_years("EUR")[1]
        assert Quantity(100, "EUR").to("USD").value == pytest.approx(100 * _fx("EUR", latest_year))

    def test_future_year_uses_latest_rate_with_warning(self):
        latest_year = exchange_rate_registry.get_available_years("EUR")[1]
        with pytest.warns(EnergyUnitsWarning, match="most recent available"):
            result = Quantity(100, "EUR", reference_year=latest_year + 3).to("USD")
        assert result.value == pytest.approx(100 * _fx("EUR", latest_year))

    def test_year_before_data_raises(self):
        with pytest.raises(MissingDataError, match="No exchange rate data"):
            Quantity(100, "EUR", reference_year=1990).to("USD")

    def test_cross_currency(self):
        result = Quantity(100, "GBP/MWh", reference_year=2022).to("JPY/MWh")
        assert result.value == pytest.approx(100 * _fx("GBP", 2022) / _fx("JPY", 2022))

    def test_static_registry_rates_match_latest_data(self):
        """The registry's static currency factors equal the most recent annual averages."""
        from energyunits.registry import registry

        for code in ["EUR", "GBP", "JPY", "CNY"]:
            assert registry.get_conversion_factor(code, "USD") == pytest.approx(_fx(code, None), rel=1e-6)


class TestInflation:
    def test_us_cpi_values(self):
        # BLS CPI-U annual averages: 2014 +1.62 %, 2024 +2.95 %
        assert inflation_registry.get_cumulative_inflation_factor("USD", 2013, 2014) == pytest.approx(1.0162)
        assert inflation_registry.get_cumulative_inflation_factor("USD", 2023, 2024) == pytest.approx(1.0295)

    @pytest.mark.parametrize(
        "start, end, index_start, index_end",
        [(2000, 2025, 172.2, 321.9), (2009, 2024, 214.537, 313.689), (2015, 2025, 237.017, 321.9)],
    )
    def test_us_cpi_chain_matches_bls_index(self, start, end, index_start, index_end):
        """Chained annual rates reproduce the ratio of BLS CPI-U annual average index levels."""
        factor = inflation_registry.get_cumulative_inflation_factor("USD", start, end)
        assert factor == pytest.approx(index_end / index_start, rel=2e-3)

    @pytest.mark.parametrize("currency", ["USD", "EUR", "GBP", "JPY", "CNY"])
    def test_all_currencies_supported(self, currency):
        cost = Quantity(100, f"{currency}/MWh", reference_year=2015)
        adjusted = cost.to(reference_year=2024)
        assert adjusted.reference_year == 2024
        assert adjusted.to(reference_year=2015).value == pytest.approx(100)

    def test_japan_deflation_years(self):
        # Japanese CPI fell in 2016 (-0.1 %)
        assert Quantity(100, "JPY", reference_year=2015).to(reference_year=2016).value == pytest.approx(99.9)

    def test_prefixed_currency_inflation(self):
        eur = Quantity(1, "EUR/kW", reference_year=2020).to(reference_year=2023)
        meur = Quantity(1, "MEUR/GW", reference_year=2020).to(reference_year=2023)
        assert meur.value == pytest.approx(eur.value)

    def test_currency_in_denominator_deflates(self):
        energy_per_money = Quantity(10, "MWh/USD", reference_year=2020).to(reference_year=2022)
        assert energy_per_money.value == pytest.approx(10 / (1.047 * 1.08))

    def test_projection_warning(self):
        first_projected = inflation_registry.get_projected_from("USD")
        with pytest.warns(EnergyUnitsWarning, match="projected"):
            Quantity(100, "USD", reference_year=2020).to(reference_year=first_projected)

    def test_no_warning_for_historical_years(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            Quantity(100, "USD", reference_year=2015).to(reference_year=2024)

    def test_out_of_range_message(self):
        with pytest.raises(MissingDataError, match="reference years 1999-2030"):
            Quantity(100, "USD", reference_year=2020).to(reference_year=2050)

    def test_custom_inflation_data(self, tmp_path):
        path = tmp_path / "inflation.json"
        path.write_text('{"USD": {"2031": 3.0}, "_metadata": {"projected_from": {"USD": 2031}}}')
        inflation_registry.load_inflation(str(path))
        with pytest.warns(EnergyUnitsWarning):
            result = Quantity(100, "USD", reference_year=2030).to(reference_year=2031)
        assert result.value == pytest.approx(103)


class TestCombinedCurrencyAndInflation:
    def test_inflate_then_convert(self):
        cost = Quantity(50, "EUR/MWh", reference_year=2015)
        with pytest.warns(EnergyUnitsWarning, match="INFLATE FIRST"):
            result = cost.to("USD/MWh", reference_year=2024)
        expected = (
            50 * inflation_registry.get_cumulative_inflation_factor("EUR", 2015, 2024) * _fx("EUR", 2024)
        )
        assert result.value == pytest.approx(expected)
        assert result.reference_year == 2024

    def test_combined_with_unit_change(self):
        cost = Quantity(1000, "EUR/kW", reference_year=2015)
        with pytest.warns(EnergyUnitsWarning):
            result = cost.to("USD/MW", reference_year=2024)
        expected = (
            1e6 * inflation_registry.get_cumulative_inflation_factor("EUR", 2015, 2024) * _fx("EUR", 2024)
        )
        assert result.value == pytest.approx(expected)


class TestCostArithmetic:
    def test_sum_of_costs_in_different_years_is_inflation_adjusted(self):
        """Regression: costs in different price years used to be added as-is."""
        a = Quantity(100, "USD", reference_year=2015)
        b = Quantity(100, "USD", reference_year=2024)
        total = a + b
        assert total.reference_year == 2015
        deflator = inflation_registry.get_cumulative_inflation_factor("USD", 2024, 2015)
        assert total.value == pytest.approx(100 + 100 * deflator)

    def test_sum_of_costs_in_different_currencies(self):
        total = Quantity(100, "EUR", reference_year=2020) + Quantity(100, "USD", reference_year=2020)
        assert total.unit == "EUR"
        assert total.value == pytest.approx(100 + 100 / _fx("EUR", 2020))

    def test_reference_year_propagates_through_products(self):
        capex = Quantity(1200, "EUR/kW", reference_year=2023)
        total = capex * Quantity(50, "MW")
        assert total.unit == "EUR"
        assert total.reference_year == 2023
        assert total.to(reference_year=2024).reference_year == 2024

    def test_levelized_cost_component(self):
        capex = Quantity(1200, "USD/kW", reference_year=2024)
        capacity = Quantity(1, "MW")
        generation = Quantity(3942, "MWh/a")
        lifetime = Quantity(20, "a")
        lcoe = (capex * capacity / (generation * lifetime)).to("USD/MWh")
        assert lcoe.value == pytest.approx(1200 * 1000 / (3942 * 20))
        assert lcoe.reference_year == 2024

    def test_comparison_across_years(self):
        assert Quantity(100, "USD", reference_year=2015) < Quantity(110, "USD", reference_year=2015)
        assert Quantity(100, "USD", reference_year=2015) == Quantity(100, "USD", reference_year=2015).to(
            reference_year=2024
        )
