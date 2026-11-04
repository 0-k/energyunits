# Release Process for EnergyUnits

Releases are published to PyPI by GitHub Actions when a GitHub release is
published (`.github/workflows/publish.yml`), using PyPI trusted publishing.

## One-time setup

### 1. Trusted publishing on PyPI and TestPyPI

On <https://pypi.org> (and <https://test.pypi.org> for test releases): Account
settings -> Publishing -> *Add a new pending publisher*:

| Field | PyPI | TestPyPI |
|-------|------|----------|
| PyPI project name | `energyunits` | `energyunits` |
| Owner | `0-k` | `0-k` |
| Repository name | `energyunits` | `energyunits` |
| Workflow name | `publish.yml` | `publish-test.yml` |
| Environment name | `pypi` | `testpypi` |

### 2. GitHub environments

Repository Settings -> Environments: create `pypi` and `testpypi`. Optionally add a
protection rule (required reviewer) to `pypi`.

### 3. Optional: Codecov and Read the Docs

- Add a `CODECOV_TOKEN` repository secret for coverage uploads (CI does not fail
  without it).
- Import the repository on <https://readthedocs.org>; `.readthedocs.yaml` is ready.

## Releasing a version

1. **Bump the version** in `energyunits/__init__.py` (`__version__ = "X.Y.Z"`).
   It is the single source of truth; `pyproject.toml` reads it.
2. **Update `CHANGELOG.md`**: add a `## [X.Y.Z] - YYYY-MM-DD` section and the link at
   the bottom.
3. **Check locally**:
   ```bash
   pip install -e ".[dev]"
   pytest
   black --check energyunits tests && isort --check-only energyunits tests && flake8 energyunits
   rm -rf dist && python -m build && twine check --strict dist/*
   ```
4. **Merge to `master`** via a pull request and wait for CI to pass.
5. **Optional: test on TestPyPI.** Actions -> "Publish to TestPyPI" -> Run workflow,
   then:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple energyunits
   ```
   A version number can only be uploaded once per index.
6. **Create a GitHub release** with tag `vX.Y.Z` (exactly matching `__version__`)
   targeting `master`, and paste the changelog section as release notes.
7. **Publishing runs automatically.** The workflow checks that the tag matches the
   package version, runs the tests, builds the sdist and wheel, checks them with
   twine and uploads them to PyPI.
8. **Verify**:
   ```bash
   pip install --upgrade energyunits
   python -c "import energyunits; print(energyunits.__version__)"
   ```

## Data updates

Exchange rates and inflation should be refreshed once a year when the annual
averages for the previous year are published (Federal Reserve G.5A in early
January; BLS, Eurostat, ONS, Statistics Bureau of Japan and NBS in January/February):

1. Update `energyunits/data/exchange_rates.json` and `inflation.json` (move the
   `projected_from` years forward).
2. Update the static currency factors in `units.json` to the most recent annual
   averages (including the `k`/`M`/`bn` prefixed units). `tests/test_data_integrity.py`
   fails if they disagree.
3. Update the tables in `DATA_SOURCES.md` and note the change in `CHANGELOG.md`.

## Versioning

EnergyUnits follows [Semantic Versioning](https://semver.org/). Before 1.0, minor
versions may contain breaking changes, which are listed in the changelog.

## Troubleshooting

- **`invalid-publisher` / authentication errors**: the trusted publisher on PyPI does
  not match the workflow file name or environment name above.
- **"Release tag does not match package version"**: the tag must be `v` +
  `__version__`, e.g. `v0.3.0`.
- **`File already exists`**: a version cannot be re-uploaded; bump the version.
