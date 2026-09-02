# Test Cases

These cases cover the exploratory findings recorded in [`docs/defects.md`](defects.md). The cases are written around observable behavior and browser requests so they can be automated without depending on volatile movie titles or counts. The current manual coverage and observed outcomes are summarized in [`coverage-matrix.md`](coverage-matrix.md).

## Implemented automation

| Coverage | Automated test |
|---|---|
| Homepage smoke | [`tests/ui/test_smoke.py::test_homepage_loads_default_movie_results`](../tests/ui/test_smoke.py) |
| Popular, Trend, Newest, and Top rated navigation | [`tests/ui/test_categories.py::test_category_navigation_loads_results`](../tests/ui/test_categories.py) |
| Movie and TV Shows type selection | [`tests/ui/test_categories.py::test_media_type_filter_loads_matching_result_fields`](../tests/ui/test_categories.py) |
| Single, multi-select, and TV genre filters | [`tests/ui/test_filters.py`](../tests/ui/test_filters.py) |
| Full- and half-star rating boundaries, title search, special-character search, and no-result search | [`tests/ui/test_filters.py`](../tests/ui/test_filters.py) |
| Valid year-range and year-boundary checks | [`tests/ui/test_filters.py`](../tests/ui/test_filters.py) |
| API request/response and UI consistency | [`tests/api/test_discover_network.py`](../tests/api/test_discover_network.py) |
| Normal, filtered, and known-defect pagination cases | [`tests/ui/test_pagination.py`](../tests/ui/test_pagination.py) |
| Direct category routes | Strict expected failures for [`BUG-002`](defects.md#bug-002--direct-category-routes-return-a-404) in [`tests/ui/test_routes.py`](../tests/ui/test_routes.py) |
| Missing-poster fallback and TV search | Strict expected failures for [`BUG-004`](defects.md#bug-004--results-without-a-poster-render-a-broken-image) and [`BUG-006`](defects.md#bug-006--tv-search-uses-the-movie-endpoint-and-renders-incomplete-cards) in [`tests/ui/test_media_regressions.py`](../tests/ui/test_media_regressions.py) |
| Known pagination, retained-page, and year regressions | Strict expected failures for [`BUG-001`](defects.md#bug-001--pagination-exposes-unsupported-page-numbers-and-enters-an-error-state), [`BUG-003`](defects.md#bug-003--category-navigation-retains-an-invalid-page-after-a-pagination-error), and [`BUG-005`](defects.md#bug-005--year-filter-displays-results-outside-the-visible-range) |

## Documented cases

### `TC-RATING-001` — Rating filter supports full- and half-star boundaries

| Field | Value |
|---|---|
| Priority | Medium |
| Type | UI / Browser API / Boundary / Regression |
| Preconditions | Popular movie results are loaded with default filters |
| Test data | Full-star values `1.0`, `4.0`, and `5.0`; half-star values `3.5` and `4.5` |
| Automation | [`test_rating_filter_renders_results_at_or_above_selected_boundary`](../tests/ui/test_filters.py) and [`test_rating_request_response_and_ui_are_consistent`](../tests/api/test_discover_network.py) |

**Steps**

1. Open the Popular movie listing.
2. Select a full-star value using the right half of its star, or a half-star value using the left half of the next star.
3. Inspect the browser request's `vote_average.gte` and `vote_average.lte` parameters.
4. Compare the API ratings with the selected threshold and the rendered movie cards.
5. Repeat for the parametrized full- and half-star values.

**Expected result**

The selected rating is sent in 0.5-star increments and the upper bound remains `5`. Every returned movie meets the lower bound, and the same number and titles of API results are rendered in the UI. If the exact five-star boundary returns no live results, the UI shows its explicit empty state with zero cards and no application error.

---

### `TC-PAGE-001` — Pagination must not offer pages unsupported by the service

| Field | Value |
|---|---|
| Priority | High |
| Type | UI / Browser API / Negative / Regression |
| Preconditions | Popular movie results are loaded with default filters |
| Test data | Last page offered by the UI; service-supported range is 1–500 |
| Related defect | [`BUG-001`](defects.md#bug-001--pagination-exposes-unsupported-page-numbers-and-enters-an-error-state) |
| Automation | [`test_pagination_does_not_offer_pages_beyond_service_limit`](../tests/ui/test_pagination.py) and [`test_highest_offered_page_loads_results_and_becomes_active`](../tests/ui/test_pagination.py); strict expected failures while the defect is present |

**Steps**

1. Open the Popular movie listing.
2. Inspect the last page offered by the pagination control.
3. Compare that value with the service-supported maximum.
4. Select the last page offered by the UI.
5. Observe the browser request, response, displayed results, and active-page indicator.

**Expected result**

1. Every page offered by the UI is within the service-supported range.
2. Selecting an offered page returns a successful response.
3. Movie results remain visible and the selected page becomes active.
4. The application does not enter its generic error state.

---

### `TC-PAGE-002` — Category navigation recovers from an invalid page

| Field | Value |
|---|---|
| Priority | High |
| Type | UI / State transition / Negative / Regression |
| Preconditions | Popular listing is showing the generic error after an unsupported late-page request |
| Test data | Trend category; retained invalid page from `TC-PAGE-001` |
| Related defect | [`BUG-003`](defects.md#bug-003--category-navigation-retains-an-invalid-page-after-a-pagination-error) |
| Automation | [`test_category_navigation_resets_page_after_pagination_error`](../tests/ui/test_pagination.py); strict expected failure while the defect is present |

**Steps**

1. Trigger the late-page error from `TC-PAGE-001`.
2. Without reloading, click Trend in the top menu.
3. Inspect the request page number and the rendered view.

**Expected result**

Trend navigation resets to page 1 or another valid page and displays Trend results. The previous category's invalid page must not be reused.

---

### `TC-ROUTE-001` — Category routes support direct navigation and refresh

| Field | Value |
|---|---|
| Priority | High |
| Type | Routing / Smoke / Regression |
| Preconditions | None |
| Test data | `/popular`, `/trend`, `/new`, `/top` |
| Related defect | [`BUG-002`](defects.md#bug-002--direct-category-routes-return-a-404) |
| Automation | [`test_category_route_supports_direct_navigation`](../tests/ui/test_routes.py); strict expected failure while the defect is present |

**Steps**

1. Enter each category path directly in the address bar.
2. Load or refresh the page.
3. Compare the result with clicking the same category from the application.

**Expected result**

Each valid category path returns the application and renders the corresponding category. Direct navigation and client-side navigation produce equivalent results.

---

### `TC-MEDIA-001` — Missing posters use a user-facing fallback

| Field | Value |
|---|---|
| Priority | Medium |
| Type | UI / Data boundary |
| Preconditions | The application is loaded |
| Test data | A controlled valid search response containing multiple records with `poster_path: null`; `Seventeen: 1977` is one observed production example |
| Related defect | [`BUG-004`](defects.md#bug-004--results-without-a-poster-render-a-broken-image) |
| Automation | [`test_missing_poster_result_uses_a_user_facing_fallback`](../tests/ui/test_media_regressions.py); strict expected failure while the defect is present |

**Steps**

1. Enter `Seventeen: 1977` in the search field.
2. Wait for the result card.
3. Inspect the poster area and the card metadata.

**Expected result**

A missing poster uses a consistent placeholder or a cleanly omitted image area. No broken-image icon or raw alternative text is exposed.

---

### `TC-SEARCH-004` — Special-character title searches are encoded safely

| Field | Value |
|---|---|
| Priority | Medium |
| Type | UI / Browser API / Input boundary |
| Preconditions | The application is loaded |
| Test data | `Spider-Man: No Way Home` |
| Automation | [`test_search_filter_supports_special_characters`](../tests/ui/test_filters.py) |

**Expected result**

The punctuation is preserved in the request query, the API returns results, and the same titles are rendered in the cards.

---

### `TC-SEARCH-005` — TV search uses TV data and renders TV fields

| Field | Value |
|---|---|
| Priority | High |
| Type | UI / Browser API / Type combination / Regression |
| Preconditions | The application is loaded |
| Test data | Type `TV Shows`; query `Batman` |
| Related defect | [`BUG-006`](defects.md#bug-006--tv-search-uses-the-movie-endpoint-and-renders-incomplete-cards) |
| Automation | [`test_tv_search_uses_tv_endpoint_and_renders_tv_fields`](../tests/ui/test_media_regressions.py); strict expected failure while the defect is present |

**Steps**

1. Select `TV Shows` in the Type selector.
2. Enter `Batman` in the search field.
3. Inspect the search endpoint, response fields, and rendered cards.

**Expected result**

The request uses the TV search endpoint and the cards display TV names and first-air years. No card is missing its title.

---

### `TC-SEARCH-006` — Search pagination preserves the query

| Field | Value |
|---|---|
| Priority | Medium |
| Type | UI / Browser API / Pagination |
| Preconditions | A multi-page movie search result is loaded |
| Test data | Query `Batman`; page 2 |
| Automation | [`test_search_pagination_preserves_query`](../tests/ui/test_pagination.py) |

**Expected result**

The page-2 request keeps the original search query, returns results, and renders the returned titles without entering the error state.

---

### `TC-FILTER-001` — Year filter constrains the API and displayed results

| Field | Value |
|---|---|
| Priority | High |
| Type | UI / Browser API / Boundary / Regression |
| Preconditions | The application is loaded; the visible default end year is 2025 in the test environment |
| Test data | Start year `2025`; expected range `2025`–`2025` |
| Related defect | [`BUG-005`](defects.md#bug-005--year-filter-displays-results-outside-the-visible-range) |
| Automation | `test_year_filter_request_matches_visible_upper_bound` in `tests/ui/test_filters.py`; strict expected failure while `BUG-005` is present |

**Steps**

1. Select `2025` in the start-year selector.
2. Verify the visible start and end values.
3. Inspect the discover request's `release_date.gte` and `release_date.lte` parameters.
4. Check the release year shown on every returned card.

**Expected result**

The visible range and request agree: `gte=2025-01-01` and `lte=2025-12-31`. No displayed result has a release year outside 2025.

---

### `TC-GENRE-001` — Multiple genres and TV genres use the correct request schema

| Field | Value |
|---|---|
| Priority | Medium |
| Type | UI / Browser API / Combination |
| Preconditions | The application is loaded |
| Test data | Movie: `Action` + `Comedy`; TV Shows: `Drama` |
| Automation | [`test_multi_genre_filter_sends_all_selected_genres`](../tests/ui/test_filters.py) and [`test_tv_genre_filter_uses_tv_endpoint_and_tv_fields`](../tests/ui/test_filters.py) |

**Expected result**

Multiple movie genres remain selected and their IDs are sent together. A TV genre request uses `/3/discover/tv`, and TV cards expose `name` and `first_air_date`.

---

### `TC-FILTER-003` — A valid year range constrains the request and visible cards

| Field | Value |
|---|---|
| Priority | High |
| Type | UI / Browser API / Boundary |
| Preconditions | The application is loaded |
| Test data | Start year `2020`; end year `2024` |
| Related defect | [`BUG-005`](defects.md#bug-005--year-filter-displays-results-outside-the-visible-range) |
| Automation | [`test_year_filter_applies_both_selected_bounds`](../tests/ui/test_filters.py); strict expected failure while the defect is present |

**Expected result**

The controls, request parameters, API records, and displayed card years all remain within `2020`–`2024`.

---

### `TC-FILTER-002` — Invalid year ranges provide clear feedback

| Field | Value |
|---|---|
| Priority | Low |
| Type | UI / Negative / Boundary |
| Preconditions | End year is set to 2024 and start year is set to 2000 |
| Test data | Invalid start `2025`; equal end boundary `2000` |
| Related finding | [`OBS-001`](defects.md#obs-001--invalid-year-ranges-are-silently-rejected-candidate) |
| Automation | [`test_year_filter_rejects_invalid_range_without_changing_selection`](../tests/ui/test_filters.py) |

**Steps**

1. Select start year `2025`, which is later than the current end year `2024`.
2. Observe the control state, request activity, and any validation message.
3. Attempt to select end year `2000`, equal to the current start year.

**Expected result**

An invalid choice must not replace the existing valid range, trigger a request with an invalid range, or put the page into an error state. Clear validation feedback would be preferable; the automation currently verifies the safe no-op invariant.

**Current observation**

The invalid and equal selections were ignored without a request or validation message. The valid selection `start=2000`, `end=2024` worked, so the originally reported failure for an earlier start year was not reproduced.

---

## Control case

### `TC-PAGE-003` — A filtered result set below the service limit reaches its last page

| Field | Value |
|---|---|
| Priority | Medium |
| Type | UI / Browser API / Regression |
| Preconditions | Popular movie listing is loaded |
| Test data | Start year `2020`, end year `2024`, genre `Action` |
| Related defect | Boundary/control evidence for [`BUG-001`](defects.md#bug-001--pagination-exposes-unsupported-page-numbers-and-enters-an-error-state) |
| Automation | [`test_filtered_last_page_remains_usable`](../tests/ui/test_pagination.py) |

**Steps**

1. Apply the listed year and genre filters.
2. Inspect the reported page count.
3. Select the displayed last page, page `241` in the recorded run.

**Expected result**

The request succeeds, results remain visible, and the last page is usable when the reported page count is within the service limit.

**Observed result**

The recorded run displayed 241 pages and retained 9 movie cards after selecting page 241. See [`evidence/BUG-001/filtered-pagination.txt`](../evidence/BUG-001/filtered-pagination.txt).

---

### `TC-PAGE-004` — Normal pagination moves forward and backward

| Field | Value |
|---|---|
| Priority | Medium |
| Type | UI / Browser API / Regression |
| Preconditions | Popular movie results are loaded on page 1 |
| Test data | Next page, then previous page |
| Automation | [`test_pagination_moves_to_next_and_previous_page`](../tests/ui/test_pagination.py) |

**Expected result**

The next-page request loads page 2, the previous-page request returns to page 1, and both states retain usable results without the generic error view.

---

## Initial coverage inventory

| Area | Planned coverage |
|---|---|
| Categories | Popular, Trending, Newest, and Top Rated |
| Title | Existing, partial, no-match, and special-character queries |
| Type | Movies and TV Shows |
| Release year | Valid value, boundaries, and invalid/empty input |
| Rating | Valid value and lower/upper boundaries |
| Genre | Representative genres and result consistency |
| Combinations | Pairwise/high-risk combinations rather than every permutation |
| Pagination | Next/previous, page changes, retained filters, and late pages |
| Routing | Direct slug access and browser refresh |
| Network | Request parameters, response status/schema, and UI consistency |
