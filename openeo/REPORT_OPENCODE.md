# Code Quality Report: `openeo/` folder

---

## 1. Structure & Organization

| Category | Assessment |
|---|---|
| Package layout | Reasonable: `src/` with submodules (`misc/`, `misc/soilgrids/`), separate test entry points at top level |
| Namespace packages | Three `__init__.py` files are empty — correct for namespace packages, but adds no value |
| Separation of concerns | Moderate: STAC construction (`stac_interface.py`, `misc/utils.py`), data source logic (`extract_geonetwork.py`), and conversion logic are split reasonably |
| Entry points | All logic lives in test scripts (`test_basic.py`, `test_multiple_assets.py`) — no dedicated `main.py` or executable entry point |

---

## 2. Architecture

| Issue | Severity | Details |
|---|---|---|
| `STACInterface` abstract base | Minor | `test_basic.py` and `test_multiple_assets.py` do **not** subclass `STACInterface` — they instantiate converters directly. The base class is effectively unused. |
| `ConvertSingleAsset.parallelize` bug | **High** | Line 69 of `convert_single_asset.py`: `if __name__ == 'convert'` will **never** be True (`__name__` is `'__main__'` when run directly, or the module name). Parallel execution path is dead code. |
| Hard-coded class attribute | Minor | `parallelize` is a class-level attribute controlled via CLI flag — better as an instance attribute or constructor parameter for thread safety. |
| Duplicate logic | Minor | `generate_urls()` in `misc/soilgrids/utils.py` is called from both `convert_single_asset.py` (line 41) and `convert_multiple_assets.py` (line 154) — acceptable since it's centralized. |
| `create_multiple_assets()` unused | Minor | `ConvertMultipleAssets.create_assets()` (line 175) is defined but never called. |

---

## 3. Error Handling

| Issue | Severity | Details |
|---|---|---|
| Generic exceptions | **Medium** | All errors use bare `Exception("message")` — should use specific exception types (`ValueError`, `RuntimeError`, `requests.HTTPError`, `rasterio.errors.RasterioIOError`). |
| No HTTP timeout | **Medium** | `requests.get()` in `extract_geonetwork.py:19` has no timeout — will hang indefinitely on network issues. |
| `check_response` assertion | Medium | `extract_geonetwork.py:38` checks `len(tmp) != 1` but a GeoNetwork query can legitimately return 0 or >1 results — should handle both gracefully. |
| `check_dataset` no-op | Minor | `extract_geonetwork.py:48-60` extracts keys but only returns `True` — validation is superficial, does not verify types or nested structure. |
| `manage_arguments` no-op | Minor | `misc/utils.py:156-161` logs a TODO but does nothing. |

---

## 4. Data Handling

| Issue | Severity | Details |
|---|---|---|
| Partial GeoNetwork integration | **Medium** | `convert_multiple_assets.py:82-86` has a TODO placeholder for `collection_providers` with empty strings — the code works but produces invalid STAC. |
| Band name extraction brittle | **Medium** | `misc/soilgrids/utils.py:12-25` expects exactly 4 underscore-separated tokens — breaks on filenames with different formats. No fallback or validation beyond a raw `Exception`. |
| Dead code — `generate_file_names()` | Minor | `misc/soilgrids/utils.py:32` is defined but never called. |
| `parse_bands()` deprecated but kept | Minor | `misc/utils.py:103` marked `@deprecated` but still present and called from commented-out code. |

---

## 5. Type Safety & Python Practices

| Issue | Severity | Details |
|---|---|---|
| Inconsistent typing | Medium | `create_collection()` in `misc/utils.py:24` declares `providers: list[str]` but providers should be dicts per STAC spec — type hint is misleading. |
| Mutable default-like class attribute | Minor | `ConvertSingleAsset.parallelize = False` is a class attribute mutated at runtime. |
| Variable name typo | Minor | `misc/soilgrids/utils.py:42,56`: `variables_name` instead of `variable_name`. |
| `__pycache__` committed | Minor | Bytecode files exist in the repo (`__pycache__/` present in `git ls-files`). Should be in `.gitignore`. |
| No `if __name__ == "__main__"` guards | Minor | `stac_interface.py`, `convert_single_asset.py`, `convert_multiple_assets.py`, `extract_geonetwork.py`, `misc/utils.py`, `misc/soilgrids/utils.py`, `misc/soilgrids/constants.py` lack module-level guards. |

---

## 6. Logging

| Issue | Severity | Details |
|---|---|---|
| Logging on every path | Minor | Almost every method calls `logger.info()` or `logger.debug()` — helpful for debugging but `logger.debug()` calls in `convert_single_asset.py` (line 101) may be excessive. |
| `logger.exception()` for global handler | Good | `stac_interface.py:29` correctly uses `logger.exception()` to capture stack traces. |

---

## 7. Testing

| Issue | Severity | Details |
|---|---|---|
| No unit tests | **High** | The `test_*.py` files are **integration/CLI scripts**, not unit tests. No use of `pytest`, `unittest`, or any test framework. Zero automated test coverage. |
| No CI/CD | **High** | No `tox.ini`, `pytest.ini`, `Makefile`, or GitHub Actions workflow. |
| Manual testing only | High | README documents manual CLI invocation — no programmatic verification of STAC output validity. |
| No STAC validation | Medium | While `stac-validator` is listed as an optional dependency, no validation step is wired into the build or test process. |

---

## 8. Documentation

| Issue | Severity | Details |
|---|---|---|
| README is thorough | Good | `openeo/README.md` is 372 lines with setup instructions, API links, catalog hierarchy diagrams (Mermaid), and STAC API examples. One of the strongest parts of the project. |
| `TODO.md` exists | Good | Planned work is tracked explicitly. |
| Inline comments sparse | Minor | Core conversion logic lacks inline comments explaining STAC construction decisions. Docstrings are present but brief. |

---

## 9. Dependencies

| Package | Used In | Notes |
|---|---|---|
| `pystac` | Core | STAC catalog construction |
| `rasterio` | Core | GeoTIFF reading/metadata extraction |
| `shapely` | Core | Geometry operations |
| `requests` | `extract_geonetwork.py` | GeoNetwork API calls |
| `openeo`, `soilgrids` | README only | Optional, listed in setup but not imported |
| `stac-validator` | README only | Listed as optional, never used |

---

## 10. Summary Scores

| Category | Score (1-5) | Notes |
|---|---|---|
| Structure | 3 | Reasonable layout, but unused base class and test scripts mixed with source |
| Architecture | 2 | Dead code (parallel execution), unused base class, partial GeoNetwork integration |
| Error handling | 2 | Generic exceptions, no HTTP timeout, superficial validation |
| Type safety | 2 | Misleading type hints, no `mypy`/static analysis, typos |
| Testing | 1 | No unit tests, no CI, no automated validation |
| Documentation | 4 | Excellent README, TODO tracking |
| Maintainability | 2 | No linting, no formatting config, bytecode in repo, no static analysis |

---

## Key Recommendations (priority order)

1. **Add unit tests** — at minimum, test `Utils.check_key()`, `generate_urls()`, `extract_band_from_name()` with pytest
2. **Fix the parallel execution bug** — change `if __name__ == 'convert'` to `if __name__ == '__main__'` or remove dead code
3. **Add HTTP timeouts** — `requests.get(url, timeout=30)` in `extract_geonetwork.py`
4. **Replace bare `Exception`** with specific exception types
5. **Add `.gitignore` rule for `__pycache__/`** at the repo root
6. **Implement STAC validation** — integrate `stac-validator` or `pystac.validate()` into CI
7. **Remove or complete the `STACInterface` base class** — either use it properly or delete it
8. **Add `pyproject.toml`** with `ruff`/`black`, `mypy`, and `pytest` configuration
