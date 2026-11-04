#!/usr/bin/env python3
"""Maintain the data bundled with energyunits and the tables generated from it.

This is a developer tool. It lives in the repository only, is not part of the
installed package and needs nothing beyond the Python standard library.

Commands
--------
fetch   Download annual exchange rates (EUR, GBP, JPY, CNY; Federal Reserve G.5A)
        and the US CPI-U (BLS) from FRED and show how they differ from the bundled
        data. Nothing is written unless ``--write`` is given.
set     Set a single value by hand, e.g. inflation rates that are not on FRED.
sync    Regenerate derived data: the static currency factors in ``units.json``
        and the generated tables in ``DATA_SOURCES.md`` and ``README.md``
        (inflation, exchange rates, fuel properties).
check   Validate the data and fail if derived data is out of date (runs in CI).

Yearly update, once the annual averages of the previous year are published
(usually by mid-February)::

    python scripts/update_data.py fetch            # review the differences
    python scripts/update_data.py fetch --write
    python scripts/update_data.py set inflation EUR 2026 2.4   # Eurostat HICP, annual average rate of change
    python scripts/update_data.py set inflation GBP 2026 3.1   # ONS series D7G7
    python scripts/update_data.py set inflation JPY 2026 2.0   # Statistics Bureau of Japan
    python scripts/update_data.py set inflation CNY 2026 0.5   # National Bureau of Statistics of China
    python scripts/update_data.py sync
    pytest

Setting a historical value for a year that was a projection moves the
``projected_from`` boundary of that currency forward.
"""

import argparse
import csv
import datetime
import io
import json
import math
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPO / "energyunits" / "data"
DEFAULT_DOCS = REPO / "DATA_SOURCES.md"
DEFAULT_README = REPO / "README.md"

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
#: currency -> (FRED series of the G.5A annual average, quoted as units per USD?)
FRED_EXCHANGE_RATES = {
    "EUR": ("AEXUSEU", False),
    "GBP": ("AEXUSUK", False),
    "JPY": ("AEXJPUS", True),
    "CNY": ("AEXCHUS", True),
}
#: CPI-U, U.S. city average, all items, not seasonally adjusted (BLS), monthly
FRED_US_CPI = "CPIAUCNS"
MANUAL_INFLATION_SOURCES = {
    "EUR": "Eurostat prc_hicp_aind, euro area, all-items HICP, annual average rate of change",
    "GBP": "ONS series D7G7 (CPI annual rate), annual value",
    "JPY": "Statistics Bureau of Japan, CPI all items, yearly average, change over the previous year",
    "CNY": "National Bureau of Statistics of China, CPI, change over the previous year",
}
CURRENCY_ORDER = ["USD", "EUR", "GBP", "JPY", "CNY"]
QUOTED_PER_USD = ("JPY", "CNY")

Change = Tuple[int, Optional[float], float]


# ----------------------------------------------------------------------------- files


class DataFiles:
    """Locations of the files maintained by this script."""

    def __init__(
        self, data_dir: Path = DEFAULT_DATA_DIR, docs: Path = DEFAULT_DOCS, readme: Path = DEFAULT_README
    ) -> None:
        self.data_dir = Path(data_dir)
        self.docs = Path(docs)
        self.readme = Path(readme)

    def path(self, name: str) -> Path:
        return self.data_dir / f"{name}.json"

    def load(self, name: str) -> dict:
        with open(self.path(name), encoding="utf-8") as f:
            return json.load(f)

    def save(self, name: str, data: dict) -> None:
        with open(self.path(name), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")


def _sorted_years(values: dict) -> dict:
    return {str(year): values[str(year)] for year in sorted(int(y) for y in values)}


def _currencies(data: dict) -> List[str]:
    codes = [code for code in data if not code.startswith("_")]
    return sorted(
        codes, key=lambda c: (CURRENCY_ORDER.index(c) if c in CURRENCY_ORDER else len(CURRENCY_ORDER), c)
    )


def _tidy(value: float) -> float:
    """Drop floating point noise (``1130.6000000000001`` -> ``1130.6``)."""
    short = float(f"{value:.15g}")
    return short if abs(short - value) <= 2 * math.ulp(value) else float(value)


def _touch(data: dict) -> None:
    data.setdefault("_metadata", {})["last_updated"] = datetime.date.today().isoformat()


# --------------------------------------------------------------------------- parsing


def parse_fred_csv(text: str) -> Dict[str, float]:
    """Parse a FRED ``fredgraph.csv`` download into ``{date: value}`` (missing values skipped)."""
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if not header or len(header) < 2:
        raise ValueError("Unexpected FRED CSV format: missing header")
    observations = {}
    for row in reader:
        if len(row) < 2:
            continue
        date, raw = row[0].strip(), row[1].strip()
        if raw in ("", "."):
            continue
        observations[date] = float(raw)
    return observations


def annual_series(observations: Dict[str, float]) -> Dict[int, float]:
    """``{"2025-01-01": x}`` -> ``{2025: x}`` for annual FRED series."""
    return {int(date[:4]): value for date, value in observations.items()}


def annual_average_inflation(monthly: Dict[str, float], min_months: int = 11) -> Dict[int, float]:
    """Inflation in percent from a monthly price index, BLS style.

    The annual average index (rounded to three decimals, as published by BLS) is
    compared with that of the previous year. Years with fewer than ``min_months``
    observations (the current year, or gaps) are skipped. ``min_months=11``
    accepts 2025, for which October was not collected.
    """
    by_year: Dict[int, List[float]] = {}
    for date, value in monthly.items():
        by_year.setdefault(int(date[:4]), []).append(value)
    averages = {year: round(sum(v) / len(v), 3) for year, v in by_year.items() if len(v) >= min_months}
    return {
        year: round((averages[year] / averages[year - 1] - 1) * 100, 2)
        for year in sorted(averages)
        if year - 1 in averages
    }


def usd_per_unit(value: float, quoted_per_usd: bool) -> float:
    """Exchange rate in the storage convention (USD per unit of currency)."""
    if value <= 0:
        raise ValueError(f"Exchange rates must be positive, got {value}")
    return float(f"{1 / value:.8g}") if quoted_per_usd else round(value, 4)


# -------------------------------------------------------------------------- updating


def _merge(target: dict, new: Dict[int, float], since: int) -> List[Change]:
    changes = []
    for year in sorted(new):
        if year < since:
            continue
        old = target.get(str(year))
        if old is None or abs(old - new[year]) > 1e-12:
            changes.append((year, old, new[year]))
            target[str(year)] = new[year]
    return changes


def _mark_historical(inflation: dict, currency: str, year: int) -> None:
    projected = inflation.setdefault("_metadata", {}).setdefault("projected_from", {})
    if currency in projected and year >= projected[currency]:
        projected[currency] = year + 1


def set_inflation(files: DataFiles, currency: str, year: int, rate: float) -> None:
    """Set the (historical) inflation rate of one year in percent."""
    if not -50 < rate < 100:
        raise ValueError(f"Implausible inflation rate: {rate} %")
    data = files.load("inflation")
    data[currency] = _sorted_years({**data.get(currency, {}), str(year): rate})
    _mark_historical(data, currency, year)
    _touch(data)
    files.save("inflation", data)


def set_exchange_rate(
    files: DataFiles, currency: str, year: int, value: float, per_usd: bool = False
) -> None:
    """Set the annual average exchange rate of one year."""
    data = files.load("exchange_rates")
    rate = usd_per_unit(value, per_usd)
    data[currency] = _sorted_years({**data.get(currency, {}), str(year): rate})
    _touch(data)
    files.save("exchange_rates", data)


def http_get(url: str, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "energyunits-data-update"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def fetch(
    files: DataFiles,
    get: Callable[[str, float], str] = http_get,
    since: int = 2000,
    write: bool = False,
    timeout: float = 30,
    out=sys.stdout,
) -> Dict[str, List[Change]]:
    """Download FRED data, report differences and optionally write them."""
    fx = files.load("exchange_rates")
    inflation = files.load("inflation")
    changes: Dict[str, List[Change]] = {}

    for currency, (series, per_usd) in FRED_EXCHANGE_RATES.items():
        observations = annual_series(parse_fred_csv(get(FRED_CSV_URL.format(series=series), timeout)))
        rates = {year: usd_per_unit(value, per_usd) for year, value in observations.items()}
        target = fx.setdefault(currency, {})
        changes[f"exchange rate {currency} (USD per {currency})"] = _merge(target, rates, since)
        fx[currency] = _sorted_years(target)

    monthly = parse_fred_csv(get(FRED_CSV_URL.format(series=FRED_US_CPI), timeout))
    usd_rates = annual_average_inflation(monthly)
    target = inflation.setdefault("USD", {})
    changes["inflation USD (%)"] = _merge(target, usd_rates, since)
    inflation["USD"] = _sorted_years(target)
    for year in usd_rates:
        if year >= since:
            _mark_historical(inflation, "USD", year)

    for label, rows in changes.items():
        print(f"\n{label}:", file=out)
        if not rows:
            print("  no changes", file=out)
        for year, old, new in rows:
            print(f"  {year}: {'(new)' if old is None else old} -> {new}", file=out)

    if write:
        if any(changes.values()):
            _touch(fx)
            _touch(inflation)
        files.save("exchange_rates", fx)
        files.save("inflation", inflation)
        print("\nWritten. Now set the other inflation rates by hand and run `sync`:", file=out)
    else:
        print("\nNothing written (use --write). Inflation rates to update by hand:", file=out)
    for currency, source in MANUAL_INFLATION_SOURCES.items():
        print(f"  {currency}: {source}", file=out)
    return changes


# ------------------------------------------------------------------- derived data


def static_currency_factors(units: dict, fx: dict) -> Dict[str, float]:
    """Static currency factors (USD per unit) from the most recent exchange rates."""
    latest = {"USD": 1.0}
    for code in _currencies(fx):
        if fx[code]:
            latest[code] = fx[code][max(fx[code], key=int)]
    currency_units = units.get("currency_units", {})
    factors = {}
    for atom, info in currency_units.items():
        if info["currency"] in latest:
            factors[atom] = _tidy(float(info.get("scale", 1.0)) * latest[info["currency"]])
    for atom, dimension in units["dimensions"].items():
        if dimension == "CURRENCY" and atom not in currency_units and atom in latest:
            factors[atom] = latest[atom]
    return factors


def inflation_table(inflation: dict) -> str:
    codes = _currencies(inflation)
    projected = inflation.get("_metadata", {}).get("projected_from", {})
    years = sorted({int(y) for code in codes for y in inflation[code]})
    lines = [
        "| Year | " + " | ".join(codes) + " |",
        "|------|" + "|".join("----:" for _ in codes) + "|",
    ]
    for year in years:
        marker = "*" if any(year >= projected.get(code, math.inf) for code in codes) else ""
        cells = [
            f"{inflation[code][str(year)]:.2f}" if str(year) in inflation[code] else "" for code in codes
        ]
        lines.append(f"| {year}{marker} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def exchange_rate_table(fx: dict) -> str:
    codes = _currencies(fx)
    headers = [f"{c} ({c} per USD)" if c in QUOTED_PER_USD else f"{c} (USD per {c})" for c in codes]
    lines = [
        "| Year | " + " | ".join(headers) + " |",
        "|------|" + "|".join("-" * (len(h) + 1) + ":" for h in headers) + "|",
    ]
    years = sorted({int(y) for code in codes for y in fx[code]})
    for year in years:
        cells = []
        for code in codes:
            value = fx[code].get(str(year))
            if value is None:
                cells.append("")
            elif code in QUOTED_PER_USD:
                cells.append(str(round(1 / value, 4)))
            else:
                cells.append(f"{value:.4f}")
        lines.append(f"| {year} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _number(value: Optional[float], fmt: str = "") -> str:
    """Format a value as written in the data (``48.0`` stays ``48.0``); ``–`` if missing."""
    if value is None:
        return "–"
    return format(value, fmt) if fmt else str(value)


def _fuels(substances: dict) -> List[Tuple[str, dict]]:
    return [(k, v) for k, v in substances.items() if not k.startswith("_") and v.get("lhv") is not None]


def fuel_table(substances: dict, with_ranges: bool) -> str:
    """Markdown table of fuel properties (with IPCC ranges for DATA_SOURCES.md)."""
    lhv_title, co2_title = ("LHV (MJ/kg) [IPCC range]", "kg CO2/GJ [IPCC range]")
    if not with_ranges:
        lhv_title, co2_title = ("LHV (MJ/kg)", "kg CO2/GJ (LHV)")
    header = f"| Substance | IPCC category | {lhv_title} | HHV (MJ/kg) | {co2_title} | Density (kg/m3) |"
    lines = [header, "|-----------|---------------|------:|------:|------:|------:|"]
    for key, props in _fuels(substances):
        lhv = _number(props["lhv"])
        co2 = _number(props.get("carbon_intensity"), ".1f")
        if with_ranges and props.get("lhv_range"):
            lhv += " [{}–{}]".format(*(_number(v) for v in props["lhv_range"]))
        if with_ranges and props.get("carbon_intensity_range"):
            co2 += " [{}–{}]".format(*(_number(v, ".1f") for v in props["carbon_intensity_range"]))
        if props.get("biogenic"):
            co2 += " (biogenic)"
        cells = [
            f"`{key}`",
            props.get("ipcc_category") or "–",
            lhv,
            _number(props["hhv"]),
            co2,
            _number(props.get("density")),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _replace_generated(text: str, name: str, content: str) -> str:
    begin = f"<!-- BEGIN GENERATED {name}"
    end = f"<!-- END GENERATED {name} -->"
    start = text.index(begin)
    start = text.index("\n", start) + 1
    stop = text.index(end, start)
    return text[:start] + content + "\n" + text[stop:]


def derived_outputs(files: DataFiles) -> Tuple[dict, str, str]:
    """``units.json`` content, ``DATA_SOURCES.md`` and ``README.md`` text as ``sync`` would write them."""
    units = files.load("units")
    fx = files.load("exchange_rates")
    inflation = files.load("inflation")
    substances = files.load("substances")
    units = json.loads(json.dumps(units))
    units["conversion_factors"].update(static_currency_factors(units, fx))
    docs = files.docs.read_text(encoding="utf-8")
    docs = _replace_generated(docs, "inflation-table", inflation_table(inflation))
    docs = _replace_generated(docs, "exchange-rate-table", exchange_rate_table(fx))
    docs = _replace_generated(docs, "fuel-table", fuel_table(substances, with_ranges=True))
    readme = files.readme.read_text(encoding="utf-8")
    readme = _replace_generated(readme, "substance-table", fuel_table(substances, with_ranges=False))
    return units, docs, readme


def sync(files: DataFiles) -> List[str]:
    """Write derived data; returns the names of the files that changed."""
    units, docs, readme = derived_outputs(files)
    changed = []
    if units != files.load("units"):
        files.save("units", units)
        changed.append(str(files.path("units")))
    for path, text in ((files.docs, docs), (files.readme, readme)):
        if text != path.read_text(encoding="utf-8"):
            path.write_text(text, encoding="utf-8")
            changed.append(str(path))
    return changed


# ------------------------------------------------------------------------ validation


def validate(files: DataFiles) -> List[str]:
    """Problems with the economic data (empty list if everything is fine)."""
    problems = []
    fx = files.load("exchange_rates")
    inflation = files.load("inflation")
    units = files.load("units")

    for name, data in (("exchange_rates", fx), ("inflation", inflation)):
        for code in _currencies(data):
            years = sorted(int(y) for y in data[code])
            if years and years != list(range(years[0], years[-1] + 1)):
                problems.append(f"{name}.json: {code} has gaps between {years[0]} and {years[-1]}")

    for code in _currencies(fx):
        values = [fx[code][y] for y in sorted(fx[code], key=int)]
        if any(v <= 0 for v in values):
            problems.append(f"exchange_rates.json: {code} has non-positive rates")
            continue
        for previous, current in zip(values, values[1:]):
            if not 0.6 < current / previous < 1.6:
                problems.append(f"exchange_rates.json: {code} jumps from {previous} to {current}")
        if units["dimensions"].get(code) != "CURRENCY":
            problems.append(f"units.json: no currency unit for {code}, which has exchange rates")

    projected = inflation.get("_metadata", {}).get("projected_from", {})
    for code in _currencies(inflation):
        rates = inflation[code]
        if any(not -20 < rate < 50 for rate in rates.values()):
            problems.append(f"inflation.json: {code} has implausible rates")
        if code in projected and rates and projected[code] > max(int(y) for y in rates) + 1:
            problems.append(f"inflation.json: projected_from of {code} is after the last year")

    units_expected, docs_expected, readme_expected = derived_outputs(files)
    if units_expected != units:
        problems.append("units.json: static currency factors are out of date (run `sync`)")
    for path, expected in ((files.docs, docs_expected), (files.readme, readme_expected)):
        if expected != path.read_text(encoding="utf-8"):
            problems.append(f"{path.name}: generated tables are out of date (run `sync`)")
    return problems


# ------------------------------------------------------------------------------ CLI


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="directory with the JSON data"
    )
    parser.add_argument("--docs", type=Path, default=DEFAULT_DOCS, help="DATA_SOURCES.md to update")
    parser.add_argument("--readme", type=Path, default=DEFAULT_README, help="README.md to update")
    commands = parser.add_subparsers(dest="command", required=True)

    fetch_parser = commands.add_parser("fetch", help="download FRED data and compare")
    fetch_parser.add_argument("--write", action="store_true", help="write the downloaded values")
    fetch_parser.add_argument("--since", type=int, default=2000, help="first year to update")
    fetch_parser.add_argument("--timeout", type=float, default=30, help="download timeout in seconds")

    set_parser = commands.add_parser("set", help="set one value by hand")
    set_parser.add_argument("kind", choices=["inflation", "fx"])
    set_parser.add_argument("currency")
    set_parser.add_argument("year", type=int)
    set_parser.add_argument("value", type=float, help="inflation in percent, or exchange rate")
    set_parser.add_argument("--per-usd", action="store_true", help="exchange rate is quoted as units per USD")

    commands.add_parser("sync", help="regenerate derived data")
    commands.add_parser("check", help="validate data and derived files")

    args = parser.parse_args(argv)
    files = DataFiles(args.data_dir, args.docs, args.readme)

    if args.command == "fetch":
        try:
            fetch(files, since=args.since, write=args.write, timeout=args.timeout)
        except (urllib.error.URLError, OSError, ValueError) as error:
            print(f"Download failed: {error}\nEnter the values with `set` instead.", file=sys.stderr)
            return 1
        return 0
    if args.command == "set":
        currency = args.currency.upper()
        if args.kind == "inflation":
            set_inflation(files, currency, args.year, args.value)
        else:
            set_exchange_rate(files, currency, args.year, args.value, per_usd=args.per_usd)
        print(f"Set {args.kind} {currency} {args.year} = {args.value}. Run `sync` afterwards.")
        return 0
    if args.command == "sync":
        changed = sync(files)
        print("\n".join(f"updated {name}" for name in changed) or "everything up to date")
        return 0

    problems = validate(files)
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    if not problems:
        print("data OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
