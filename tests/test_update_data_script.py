"""Tests for the developer tool scripts/update_data.py (no network access needed)."""

import importlib.util
import io
import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "update_data.py"

pytestmark = pytest.mark.skipif(not SCRIPT.exists(), reason="scripts/ is only available in the repository")


@pytest.fixture(scope="module")
def ud():
    spec = importlib.util.spec_from_file_location("update_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def files(ud, tmp_path):
    """A copy of the repository data that the tests may modify."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for name in ("units", "inflation", "exchange_rates", "substances"):
        shutil.copy(REPO / "energyunits" / "data" / f"{name}.json", data_dir)
    shutil.copy(REPO / "DATA_SOURCES.md", tmp_path)
    shutil.copy(REPO / "README.md", tmp_path)
    return ud.DataFiles(data_dir, tmp_path / "DATA_SOURCES.md", tmp_path / "README.md")


def _monthly_csv(series, annual_index, months=12):
    rows = [f"observation_date,{series}"]
    for year, value in annual_index.items():
        for month in range(1, 13):
            rows.append(f"{year}-{month:02d}-01,{value if month <= months.get(year, 12) else '.'}")
    return "\n".join(rows) + "\n"


def test_repository_data_is_consistent(ud):
    assert ud.validate(ud.DataFiles()) == []


def test_parse_fred_csv(ud):
    text = "observation_date,AEXUSEU\n2024-01-01,1.0820\n2025-01-01,.\n2026-01-01,1.1500\n"
    assert ud.annual_series(ud.parse_fred_csv(text)) == {2024: 1.082, 2026: 1.15}
    # older FRED downloads use DATE as the first header
    assert ud.parse_fred_csv("DATE,X\n2020-01-01,3\n") == {"2020-01-01": 3.0}
    with pytest.raises(ValueError):
        ud.parse_fred_csv("")


def test_annual_average_inflation(ud):
    monthly = ud.parse_fred_csv(
        _monthly_csv("CPI", {2023: 100.0, 2024: 103.0, 2025: 105.06, 2026: 110.0}, {})
    )
    # incomplete years are skipped
    monthly = {
        date: value for date, value in monthly.items() if not (date.startswith("2026") and date > "2026-06")
    }
    assert ud.annual_average_inflation(monthly) == {2024: 3.0, 2025: 2.0}


def _months(year, value, months=range(1, 13)):
    return {f"{year}-{month:02d}-01": value for month in months}


def test_annual_average_tolerates_one_missing_month(ud):
    # October 2025 was not collected
    monthly = {**_months(2024, 100.0), **_months(2025, 102.0, [m for m in range(1, 13) if m != 10])}
    assert ud.annual_average_inflation(monthly) == {2025: 2.0}


def test_unfinished_year_is_skipped(ud):
    # January to November of the current year are published, December is not
    monthly = {**_months(2025, 100.0), **{f"2026-{m:02d}-01": 100.0 + m for m in range(1, 12)}}
    assert ud.annual_average_inflation(monthly) == {}


def test_missing_december_is_accepted_once_later_data_exists(ud):
    monthly = {**_months(2024, 100.0), **_months(2025, 102.0, range(1, 12)), "2026-01-01": 103.0}
    assert ud.annual_average_inflation(monthly) == {2025: 2.0}


def test_exchange_rate_conventions(ud):
    assert ud.usd_per_unit(1.13064, quoted_per_usd=False) == 1.1306
    assert ud.usd_per_unit(149.5686, quoted_per_usd=True) == pytest.approx(1 / 149.5686, rel=1e-8)
    with pytest.raises(ValueError):
        ud.usd_per_unit(0, quoted_per_usd=True)


def _next_year(files):
    """The first year without exchange rate data (works whatever year the data ends)."""
    return max(int(y) for y in files.load("exchange_rates")["EUR"]) + 1


def test_fetch_with_fake_downloads(ud, files):
    year = _next_year(files)

    def fake_get(url, timeout):
        series = url.rsplit("=", 1)[1]
        if series == "CPIAUCNS":
            return _monthly_csv(series, {year - 2: 313.689, year - 1: 321.9, year: 330.0}, {})
        values = {"AEXUSEU": 1.17, "AEXUSUK": 1.35, "AEXJPUS": 150.0, "AEXCHUS": 7.1}
        return f"observation_date,{series}\n{year}-01-01,{values[series]}\n"

    out = io.StringIO()
    changes = ud.fetch(files, get=fake_get, since=year, out=out)
    assert changes["exchange rate EUR (USD per EUR)"] == [(year, None, 1.17)]
    assert "Nothing written" in out.getvalue()
    assert str(year) not in files.load("exchange_rates")["EUR"]

    ud.fetch(files, get=fake_get, since=year, write=True, out=out)
    fx = files.load("exchange_rates")
    inflation = files.load("inflation")
    assert fx["EUR"][str(year)] == 1.17
    assert fx["JPY"][str(year)] == pytest.approx(1 / 150.0)
    assert list(fx["EUR"])[-1] == str(year)
    assert inflation["USD"][str(year)] == round((330.0 / 321.9 - 1) * 100, 2)
    assert inflation["_metadata"]["projected_from"]["USD"] == year + 1

    # derived data is stale until sync
    assert any("out of date" in problem for problem in ud.validate(files))
    changed = ud.sync(files)
    assert len(changed) == 2
    assert ud.validate(files) == []
    units = files.load("units")["conversion_factors"]
    assert units["EUR"] == 1.17
    assert units["MEUR"] == 1.17e6
    assert f"| {year} | 1.1700 | 1.3500 | 150.0 | 7.1 |" in files.docs.read_text(encoding="utf-8")


def test_set_values_by_hand(ud, files):
    projected = files.load("inflation")["_metadata"]["projected_from"]
    first_projected = projected["GBP"]
    ud.set_inflation(files, "GBP", first_projected, 3.1)
    ud.set_exchange_rate(files, "CNY", first_projected, 7.05, per_usd=True)
    inflation = files.load("inflation")
    assert inflation["GBP"][str(first_projected)] == 3.1
    # the year is now historical for GBP only
    assert inflation["_metadata"]["projected_from"]["GBP"] == first_projected + 1
    assert inflation["_metadata"]["projected_from"]["EUR"] == projected["EUR"]
    assert files.load("exchange_rates")["CNY"][str(first_projected)] == pytest.approx(1 / 7.05)
    with pytest.raises(ValueError):
        ud.set_inflation(files, "GBP", first_projected, 250)


def test_setting_a_later_projection_keeps_earlier_years_projected(ud, files):
    first_projected = files.load("inflation")["_metadata"]["projected_from"]["EUR"]
    ud.set_inflation(files, "EUR", first_projected + 2, 2.3)
    inflation = files.load("inflation")
    assert inflation["EUR"][str(first_projected + 2)] == 2.3
    assert inflation["_metadata"]["projected_from"]["EUR"] == first_projected
    # setting the years in order moves the boundary
    ud.set_inflation(files, "EUR", first_projected, 2.4)
    ud.set_inflation(files, "EUR", first_projected + 1, 2.2)
    assert files.load("inflation")["_metadata"]["projected_from"]["EUR"] == first_projected + 2


def test_validate_detects_problems(ud, files):
    fx = files.load("exchange_rates")
    del fx["EUR"]["2010"]
    fx["GBP"]["2011"] = fx["GBP"]["2010"] * 3
    files.save("exchange_rates", fx)
    problems = ud.validate(files)
    assert any("EUR has gaps" in p for p in problems)
    assert any("GBP jumps" in p for p in problems)


def test_command_line(ud, files, capsys):
    args = ["--data-dir", str(files.data_dir), "--docs", str(files.docs), "--readme", str(files.readme)]
    assert ud.main(args + ["check"]) == 0
    assert ud.main(args + ["set", "fx", "eur", str(_next_year(files)), "1.2"]) == 0
    assert ud.main(args + ["check"]) == 1
    assert ud.main(args + ["sync"]) == 0
    assert ud.main(args + ["check"]) == 0
    assert json.loads(files.path("units").read_text(encoding="utf-8"))["conversion_factors"]["kEUR"] == 1200.0
