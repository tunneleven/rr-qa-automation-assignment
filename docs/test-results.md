# Test Results

## 2026-09-01 — Exploratory browser/network and regression automation execution

- **Target:** `https://tmdb-discover.surge.sh`
- **Environment:** Linux x86_64; Python 3.12.3; Playwright 1.62.0; Chromium `151.0.7922.34`
- **Method:** Clean-browser exploratory checks with browser request/response capture and screenshots, followed by the pytest/Playwright regression suite
- **Evidence:** [`../evidence/`](../evidence/)
- **Automation status:** Phase 1–6 automation is implemented for smoke, category, type, individual-filter, combination, pagination, browser-network consistency, and confirmed-defect regression coverage. Confirmed defects are retained as strict expected failures.

| Result | Count |
|---|---:|
| Confirmed failing observations | 6 |
| Candidate observations | 1 |
| Passing control cases | 1 |
| Automated tests collected | 37 |
| Automated tests passed | 13 |
| Automated expected failures | 11 |
| Environmental/inconclusive failures | 13 |

### Findings

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

### Automated coverage executed

**Command:** `uv run pytest -q --tb=short`

**Latest full-suite result:** `13 passed, 13 failed, 11 xfailed` in 13 minutes 57 seconds.

The 13 failures were setup/network symptoms during the live run: 12 initial popular-listing response timeouts and one missing genre option after the external genre data was unavailable. No new product assertion failure was recorded. Targeted reruns of the added cases passed when the live API was available; the valid-range case reproduced `BUG-005` as an expected failure.

| Automated area | Test module |
|---|---|
| Homepage smoke | [`tests/ui/test_smoke.py`](../tests/ui/test_smoke.py) |
| Category navigation and media type | [`tests/ui/test_categories.py`](../tests/ui/test_categories.py) |
| Individual genre, rating, search, no-result, and year-boundary checks | [`tests/ui/test_filters.py`](../tests/ui/test_filters.py) |
| Request/response and UI consistency | [`tests/api/test_discover_network.py`](../tests/api/test_discover_network.py) |
| Pagination and retained-page regressions | [`tests/ui/test_pagination.py`](../tests/ui/test_pagination.py) |
| Direct category-route regression | [`tests/ui/test_routes.py`](../tests/ui/test_routes.py) |
| Missing-poster and TV-search regressions | [`tests/ui/test_media_regressions.py`](../tests/ui/test_media_regressions.py) |

The eleven known-defect regression instances are intentional strict `xfail`s for [`BUG-001`](defects.md#bug-001--pagination-exposes-unsupported-page-numbers-and-enters-an-error-state), [`BUG-002`](defects.md#bug-002--direct-category-routes-return-a-404), [`BUG-003`](defects.md#bug-003--category-navigation-retains-an-invalid-page-after-a-pagination-error), [`BUG-004`](defects.md#bug-004--results-without-a-poster-render-a-broken-image), [`BUG-005`](defects.md#bug-005--year-filter-displays-results-outside-the-visible-range), and [`BUG-006`](defects.md#bug-006--tv-search-uses-the-movie-endpoint-and-renders-incomplete-cards). An `XPASS` will correctly fail the suite after a defect is fixed so its marker can be removed.

### Limitations and follow-up

- The TMDB data and page totals are live and may change; evidence records the values observed on 2026-09-01.
- The supplied API credential is redacted from committed evidence.
- The live TMDB API can intermittently reset connections; classify response-wait and missing-option setup errors separately from product assertions.
- Retest and remove each strict `xfail` after the corresponding defect is fixed.
- The filtered last-page control case (`TC-PAGE-003`) and invalid-range safe-no-op case (`TC-FILTER-002`) are now automated.
- Revisit the desired validation message for `OBS-001` after product-owner clarification.

## Execution template

### YYYY-MM-DD — Test run title

- **Commit:** SHA
- **Target:** `https://tmdb-discover.surge.sh`
- **Environment:** OS, Python, browser/version
- **Command:** Exact command used
- **Duration:** Total duration

| Result | Count |
|---|---:|
| Passed | 0 |
| Failed | 0 |
| Expected failure | 0 |
| Skipped | 0 |

### Failures and defects

| Test | Result | Defect | Evidence |
|---|---|---|---|
| — | — | — | — |

### Observations

Record environmental instability, data assumptions, residual risks, and follow-up work.
