# Defect Report

## Triage summary

| ID | Finding | Status | Severity | Priority |
|---|---|---|---|---|
| [`BUG-001`](#bug-001--pagination-exposes-unsupported-page-numbers-and-enters-an-error-state) | Pagination exposes unsupported page numbers | Confirmed | Medium | High |
| [`BUG-002`](#bug-002--direct-category-routes-return-a-404) | Direct category routes return 404 | Confirmed | Medium | High |
| [`BUG-003`](#bug-003--category-navigation-retains-an-invalid-page-after-a-pagination-error) | Category navigation retains an invalid page after a pagination error | Confirmed | Medium | High |
| [`BUG-004`](#bug-004--results-without-a-poster-render-a-broken-image) | Results without a poster render a broken image | Confirmed | Low | Medium |
| [`BUG-005`](#bug-005--year-filter-displays-results-outside-the-visible-range) | Year filter displays results outside the visible range | Confirmed | High | High |
| [`BUG-006`](#bug-006--tv-search-uses-the-movie-endpoint-and-renders-incomplete-cards) | TV search uses the movie endpoint and renders incomplete cards | Confirmed | High | High |
| `OBS-001` | Invalid year ranges are silently rejected | Candidate; needs clarification | Low | Low |

**Environment for controlled reproductions:** `https://tmdb-discover.surge.sh/`; Linux x86_64; Playwright 1.62.0; Chromium `151.0.7922.34`; 2026-09-01. API credentials are redacted from committed evidence.

---

## `BUG-001` — Pagination exposes unsupported page numbers and enters an error state

- **Status:** Confirmed; reproduced
- **Severity:** Medium
- **Priority:** High
- **Related tests:** `TC-PAGE-001`, `TC-PAGE-002`
- **Known issue:** Yes — independently confirms the late-page pagination issue described in the assignment
- **Reproducibility:** Reproduced in a clean controlled browser run

**Preconditions**

1. The application is reachable.
2. The Popular movie listing is loaded with its default filters.

**Steps to reproduce**

1. Open `https://tmdb-discover.surge.sh/`.
2. Scroll to the pagination controls below the movie results.
3. Observe that the final links include `58696`, `58697`, and `58698`.
4. Select page `58698`.

**Expected result**

- The UI exposes only page numbers supported by the service.
- Selecting an exposed page loads results and marks that page as active.
- A page above the service limit is not offered. The service error identifies the maximum as page `500`.

**Actual result**

- The UI exposes page `58698`.
- Selecting it sends `GET /3/movie/popular?page=58698`.
- The service returns HTTP `400`, status code `22`: `Invalid page: Pages start at 1 and max at 500.`
- The results are replaced by `Something went wrong! Please try again later.` and a Retry button.

**Evidence**

- [`01-unsupported-page-numbers.png`](../evidence/BUG-001/01-unsupported-page-numbers.png) — browser capture showing the unsupported late-page links
- [`02-error-after-selecting-last-page.png`](../evidence/BUG-001/02-error-after-selecting-last-page.png) — browser capture showing the resulting error state
- [`network-response.txt`](../evidence/BUG-001/network-response.txt) — redacted HTTP 400 response
- [`filtered-pagination.txt`](../evidence/BUG-001/filtered-pagination.txt) — control case showing a 241-page filtered result set reaches its displayed last page
- [`04-filtered-last-page-control.png`](../evidence/BUG-001/04-filtered-last-page-control.png) — filtered control capture

**Impact**

Users are offered navigation controls that cannot succeed. Selecting a late page removes the current results and interrupts browsing with a generic error. Early pages remain usable, so the defect does not block the entire discovery flow.

**Diagnostic note**

The filtered control case is important: with `start=2020`, `end=2024`, and genre `Action`, the service reported 241 pages and page 241 loaded successfully. The failure is therefore associated with result sets whose reported page count exceeds the service's maximum, not with every last-page interaction.

---

## `BUG-002` — Direct category routes return a 404

- **Status:** Confirmed; reproduced
- **Severity:** Medium
- **Priority:** High
- **Related test:** `TC-ROUTE-001`
- **Reproducibility:** Reproduced for `/popular`, `/trend`, `/new`, and `/top` by direct browser navigation

**Preconditions**

1. None; use a new browser context or address-bar navigation.

**Steps to reproduce**

1. Enter `https://tmdb-discover.surge.sh/popular` directly in the address bar and load it.
2. Repeat with `/trend`, `/new`, or `/top`.

**Expected result**

Each valid category URL renders the application, both when opened directly and when refreshed. The result should match the corresponding in-app navigation.

**Actual result**

Direct navigation to each category path returns the Surge page `page not found` with HTTP `404`. The same routes work when reached by clicking the links inside the already loaded application; for example, clicking Trend from `/` renders Trend results.

**Evidence**

- [`direct-routes.txt`](../evidence/BUG-002/direct-routes.txt) — direct navigation status and client-side control result
- [`01-direct-popular-404.png`](../evidence/BUG-002/01-direct-popular-404.png) — direct `/popular` capture

**Impact**

Users cannot bookmark, share, refresh, or reopen a category URL directly. A link copied from the application becomes a 404 when opened in a new navigation.

**Notes**

This is a single-page-application hosting/configuration defect. If direct deep links are intentionally out of scope, product requirements should explicitly say so; the visible category URLs currently imply that they are valid entry points.

---

## `BUG-003` — Category navigation retains an invalid page after a pagination error

- **Status:** Confirmed; reproduced
- **Severity:** Medium
- **Priority:** High
- **Related tests:** `TC-PAGE-001`, `TC-PAGE-002`
- **Related defect:** [`BUG-001`](#bug-001--pagination-exposes-unsupported-page-numbers-and-enters-an-error-state)
- **Reproducibility:** Reproduced in a clean controlled browser run

**Preconditions**

1. Start on the default Popular listing.
2. Trigger [`BUG-001`](#bug-001--pagination-exposes-unsupported-page-numbers-and-enters-an-error-state) by selecting page `58698`.

**Steps to reproduce**

1. After the generic pagination error appears, click the Trend link in the top menu without reloading.

**Expected result**

Trend navigation resets to a valid page, normally page 1, and displays Trend results. A failed request from the previous category must not determine the page requested for the new category.

**Actual result**

- The URL changes to `/trend`.
- The browser requests `/3/trending/movie/week?page=58698`, which the service rejects with HTTP `400`.
- The Trend view remains in the generic error state instead of loading Trend results. The same retained-page/error behavior was also observed when navigating to Newest and Top rated.

**Evidence**

- [`01-category-after-pagination-error.png`](../evidence/BUG-003/01-category-after-pagination-error.png) — Trend view after the failed pagination flow
- [`network-response.txt`](../evidence/BUG-003/network-response.txt) — redacted Trend requests and responses
- [`menu-navigation-matrix.txt`](../evidence/BUG-003/menu-navigation-matrix.txt) — follow-up checks for Trend, Newest, and Top rated

**Impact**

One invalid pagination action can leave category navigation unusable until the user reloads or otherwise resets the application state. This compounds the impact of `BUG-001` and makes recovery unclear.

---

## `BUG-004` — Results without a poster render a broken image

- **Status:** Confirmed; reproduced
- **Severity:** Low
- **Priority:** Medium
- **Related test:** `TC-MEDIA-001`
- **Reproducibility:** Reproduced with the deterministic search `Seventeen: 1977`

**Preconditions**

1. The application is loaded.

**Steps to reproduce**

1. Activate the search field.
2. Enter `Seventeen: 1977`.
3. Wait for the single search result to render.

**Expected result**

A result whose source record has no poster should show a consistent placeholder or omit the image area without exposing a broken-image icon or raw alternative text. The title and metadata should remain readable.

**Actual result**

The search response contains `poster_path: null`. The result card renders an image with an empty source; Chromium reports zero natural image dimensions and displays a broken-image icon with the alt text `Movie Poster`.

**Evidence**

- [`01-missing-poster.png`](../evidence/BUG-004/01-missing-poster.png) — browser capture of the broken poster state
- [`network-response.txt`](../evidence/BUG-004/network-response.txt) — redacted search response and image state

**Impact**

The result card has a visibly broken media element and poor presentation. The title remains available, so discovery is degraded rather than completely blocked.

**Notes**

The missing poster is valid upstream data; the application defect is the absence of a user-facing fallback for that data condition.

---

## `BUG-005` — Year filter displays results outside the visible range

- **Status:** Confirmed; reproduced
- **Severity:** High
- **Priority:** High
- **Related test:** `TC-FILTER-001`
- **Reproducibility:** Reproduced in a clean controlled browser run

**Preconditions**

1. The application is loaded on 2026-09-01.
2. The visible default year range is `1900`–`2025`.

**Steps to reproduce**

1. Open the year start selector.
2. Select `2025`.
3. Observe the visible range and the returned movie cards.

**Expected result**

With the visible range set to `2025`–`2025`, every displayed movie has a 2025 release year. The request's upper bound is `2025-12-31`.

**Actual result**

- The controls display `2025`–`2025`.
- The browser sends `release_date.gte=2025-01-01` but `release_date.lte=2026-12-31`.
- The response and UI include 2026 titles such as *The Odyssey*, *Yellow Eyes*, and *Avengers: Doomsday*.
- In a second reproduction using `2020`–`2024` plus Action, the final request contained the visible year bounds but the response and UI included displayed release years `1997` and `2010`.

**Evidence**

- [`01-year-filter-mismatch.png`](../evidence/BUG-005/01-year-filter-mismatch.png) — visible `2025`–`2025` controls alongside 2026 results
- [`network-response.txt`](../evidence/BUG-005/network-response.txt) — redacted request, response totals, and example release dates
- [`run-summary.txt`](../evidence/COVERAGE-001/run-summary.txt) — year + genre combination observation

**Impact**

Users cannot rely on the year filter to constrain discovery results. This undermines the core filtering function and may cause incorrect search or reporting decisions.

**Diagnostic note**

The application's default state uses the current year (`2026`), while the selectable year list and visible end selector stop at `2025`. When the start year is changed to 2025, the hidden current-year upper bound remains in the API request.

---

## `BUG-006` — TV search uses the movie endpoint and renders incomplete cards

- **Status:** Confirmed; reproduced
- **Severity:** High
- **Priority:** High
- **Related test:** `TC-SEARCH-005`
- **Reproducibility:** Reproduced with TV Shows selected and the search query `Batman`

**Preconditions**

1. The application is loaded.

**Steps to reproduce**

1. Select `TV Shows` in the Type selector.
2. Enter `Batman` in the search field.
3. Wait for the search results to render.
4. Inspect the request endpoint and the result cards.

**Expected result**

The application sends a TV search request, maps TV fields (`name` and `first_air_date`), and displays TV titles and first-air years.

**Actual result**

- The application sends `GET /3/search/movie?query=Batman&page=1` after selecting TV Shows.
- The movie response returns `title` and `release_date`, while the TV card mapping expects `name` and `first_air_date`.
- Twenty cards render with posters and genre/year metadata but no titles.

**Evidence**

- [`01-tv-search-wrong-results.png`](../evidence/BUG-006/01-tv-search-wrong-results.png) — TV search result cards with missing titles
- [`network-response.txt`](../evidence/BUG-006/network-response.txt) — redacted request and response-field mismatch
- [`run-summary.txt`](../evidence/COVERAGE-001/run-summary.txt) — coverage-matrix execution record

**Impact**

TV users receive movie search data in a TV context and cannot identify the returned cards by title. Search is materially degraded for the TV type.

**Diagnostic note**

The TV popular flow uses `/3/tv/popular`, so the type selector itself works. The defect is isolated to the TV search path.

---

## `OBS-001` — Invalid year ranges are silently rejected (candidate)

- **Status:** Candidate; needs product clarification
- **Severity/Priority:** Low / Low
- **Related test:** `TC-FILTER-002`
- **Reproducibility:** The silent rejection was reproduced for invalid and equal boundaries; the reported valid case was not reproduced as a failure

**Finding**

The report that selecting a start year earlier than the end year fails was not reproduced. Setting end year `2024` and then start year `2000` correctly changed the visible range to `2000`–`2024` and sent a new request.

A separate invalid case is silent: with the range at `2000`–`2024`, selecting start year `2025` leaves the range unchanged, sends no request, and shows no validation message. Selecting an equal end boundary behaves the same way.

**Expected behavior to clarify**

The product should either disable invalid options, show a validation message, or document that invalid selections are intentionally ignored. Until that expectation is confirmed, this remains an observation rather than a confirmed defect.

**Evidence**

- [`01-year-range-state.png`](../evidence/OBS-001/01-year-range-state.png) — resulting range after the attempted invalid selection
- [`reproduction.txt`](../evidence/OBS-001/reproduction.txt) — valid control and invalid/equal-boundary observations

---

## Defect report template

### `BUG-###` — Concise title

- **Status:** New / Confirmed / Fixed / Closed / Candidate
- **Severity:** Critical / High / Medium / Low
- **Priority:** High / Medium / Low
- **Environment:** URL, browser/version, OS, execution date
- **Related test:** Test case and automation node ID
- **Known issue:** Yes / No
- **Reproducibility:** Attempts and observed frequency

**Preconditions**

1. Required starting state.

**Steps to reproduce**

1. First action.
2. Second action.

**Expected result**

Describe the observable correct behavior.

**Actual result**

Describe the observed behavior without interpretation.

**Evidence**

Screenshot, trace, video, logs, or redacted network response path.

**Impact**

Describe who is affected, what they cannot do, and whether a workaround exists.

**Notes**

Frequency, workaround, assumptions, and relevant diagnostics.
