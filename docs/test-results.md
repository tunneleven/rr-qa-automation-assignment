# Test Results

## 2026-09-02 — Full regression execution

- **Target:** `https://tmdb-discover.surge.sh`
- **Execution window:** 2026-09-02 11:42:15–11:44:27 (UTC+07:00)
- **Environment:** Linux x86_64; Python 3.12.3; Playwright 1.62.0; Chromium `151.0.7922.34`
- **Command:** `uv run pytest -q --tb=short --junitxml=artifacts/junit.xml`
- **Duration:** 131.71 seconds (2 minutes 11 seconds)
- **Reports:** `artifacts/report.html` (committed) and `artifacts/junit.xml` (regenerated locally and intentionally not tracked)

### Test outcome

| Result | Count |
|---|---:|
| Tests collected | 41 |
| Passed | 30 |
| Expected failures | 11 |
| Failed | 0 |
| Skipped | 0 |

All planned non-defect scenarios passed. The 11 expected failures are strict regression checks for the six documented product defects. Each XFAIL accepts only the dedicated exception raised after its documented defect signature is observed; unrelated failures remain ordinary failures.

### Expected failures

| Defect | Expected-failure tests |
|---|---:|
| [`BUG-001`](defects.md#bug-001--pagination-exposes-unsupported-page-numbers-and-enters-an-error-state) | 2 |
| [`BUG-002`](defects.md#bug-002--direct-category-routes-return-a-404) | 4 |
| [`BUG-003`](defects.md#bug-003--category-navigation-retains-an-invalid-page-after-a-pagination-error) | 1 |
| [`BUG-004`](defects.md#bug-004--results-without-a-poster-render-a-broken-image) | 1 |
| [`BUG-005`](defects.md#bug-005--year-filter-displays-results-outside-the-visible-range) | 2 |
| [`BUG-006`](defects.md#bug-006--tv-search-uses-the-movie-endpoint-and-renders-incomplete-cards) | 1 |

### Functional findings

| Test case | Result | Finding | Evidence |
|---|---|---|---|
| `TC-PAGE-001` | Failed | [`BUG-001`](defects.md#bug-001--pagination-exposes-unsupported-page-numbers-and-enters-an-error-state) | [`evidence/BUG-001/`](../evidence/BUG-001/) |
| `TC-PAGE-002` | Failed | [`BUG-003`](defects.md#bug-003--category-navigation-retains-an-invalid-page-after-a-pagination-error) | [`evidence/BUG-003/`](../evidence/BUG-003/) |
| `TC-ROUTE-001` | Failed | [`BUG-002`](defects.md#bug-002--direct-category-routes-return-a-404) | [`evidence/BUG-002/`](../evidence/BUG-002/) |
| `TC-MEDIA-001` | Failed | [`BUG-004`](defects.md#bug-004--results-without-a-poster-render-a-broken-image) | [`evidence/BUG-004/`](../evidence/BUG-004/) |
| `TC-FILTER-001` | Failed | [`BUG-005`](defects.md#bug-005--year-filter-displays-results-outside-the-visible-range) | [`evidence/BUG-005/`](../evidence/BUG-005/) |
| `TC-SEARCH-005` | Failed | [`BUG-006`](defects.md#bug-006--tv-search-uses-the-movie-endpoint-and-renders-incomplete-cards) | [`evidence/BUG-006/`](../evidence/BUG-006/) |
| `TC-FILTER-002` | Candidate | [`OBS-001`](defects.md#obs-001--invalid-year-ranges-are-silently-rejected-candidate) | [`evidence/OBS-001/`](../evidence/OBS-001/) |
| `TC-PAGE-003` | Passed control | Filtered page 241 remained usable | [`evidence/BUG-001/filtered-pagination.txt`](../evidence/BUG-001/filtered-pagination.txt) |

### Automated coverage

| Automated area | Test module |
|---|---|
| Homepage smoke | [`tests/ui/test_smoke.py`](../tests/ui/test_smoke.py) |
| Category navigation and media type | [`tests/ui/test_categories.py`](../tests/ui/test_categories.py) |
| Individual genre, full- and half-star rating, search, no-result, and year-boundary checks | [`tests/ui/test_filters.py`](../tests/ui/test_filters.py) |
| Request/response and UI consistency | [`tests/api/test_discover_network.py`](../tests/api/test_discover_network.py) |
| Pagination and retained-page regressions | [`tests/ui/test_pagination.py`](../tests/ui/test_pagination.py) |
| Direct category-route regression | [`tests/ui/test_routes.py`](../tests/ui/test_routes.py) |
| Missing-poster and TV-search regressions | [`tests/ui/test_media_regressions.py`](../tests/ui/test_media_regressions.py) |

### Follow-up

- Retest and remove each strict `xfail` after the corresponding defect is fixed; strict XPASS keeps that review visible in CI.
- The filtered last-page control case (`TC-PAGE-003`) and invalid-range safe-no-op case (`TC-FILTER-002`) are automated.
- Revisit the desired validation message for `OBS-001` after product-owner clarification.
- Live TMDB data and page totals may change between executions.
