# Filter coverage matrix

## Purpose and scope

This is the first focused coverage pass after the initial defect exploration. It covers representative happy paths, boundaries, negative inputs, and pairwise combinations for the filters. It is not an exhaustive test of every genre, title, or combination.

- **Target:** `https://tmdb-discover.surge.sh/`
- **Observed:** 2026-09-01
- **Environment:** Linux x86_64; Python 3.12.3; Playwright 1.62.0; Chromium `151.0.7922.34`
- **API credentials:** omitted from all recorded requests
- **Detailed run record:** [`evidence/COVERAGE-001/run-summary.txt`](../evidence/COVERAGE-001/run-summary.txt)

### Result key

- **PASS:** request, response data, and relevant UI behavior met the case expectation.
- **PARTIAL:** the final state met the expectation, but an intermediate request or state needs attention.
- **FAIL:** the request or displayed result contradicted the case expectation.
- **PASS + defect:** the filter itself worked, but a separate already-recorded defect was observed in the same flow.

## Area-level coverage

| Area | Representative coverage completed | Remaining coverage |
|---|---|---|
| Type | Movie default; TV Shows; TV genre schema | Retest after any type-state fix; all category/type combinations |
| Genre | Movie Action; multi-select Action + Comedy; TV Drama | Every genre; explicit AND/OR product semantics for multi-select |
| Rating | 1.0, 3.5, 4.0, 4.5, and 5.0 boundaries, including explicit half-star interactions | Clear/zero rating and broader coverage of the product's rating scale |
| Search | Partial, no-match, special-character, and TV search; search pagination | Empty query, long input, and Unicode beyond the punctuation case |
| Year | Valid range; visible 2025 boundary; invalid-range candidate | More boundary dates and behavior after refresh/category changes |
| Combinations | Genre + rating; year + genre; TV + genre + rating; search after genre | Broader pairwise matrix after expected search-reset behavior is confirmed |
| Pagination/routing | Normal next/previous; search pagination; filtered last page; known defect cases | Retest after fixes; exhaustive page-control states and route/type combinations |

## Automation expansion

The following executable cases were added beyond the original defect-focused checks:

| Area | Automated coverage |
|---|---|
| Genre | Multi-select movie genres and TV genre response fields |
| Rating | Full- and half-star boundaries at 1.0, 3.5, 4.0, 4.5, and 5.0 |
| Search | Punctuation/special-character query and pagination with the query retained |
| Year | Valid two-sided range and invalid selections that must not replace a valid range |
| Pagination | Next/previous navigation and a filtered listing's displayed last page |

These cases complement, rather than replace, the strict expected-failure regressions for confirmed defects.

## Detailed matrix

The API column records the relevant request or request sequence with the API key removed. `UI result` records the observable state after the action; card counts are live-data observations and may change.

| ID | Input | Expected API request/response | Expected UI result | Observed UI/result | Status |
|---|---|---|---|---|---|
| `TYPE-001` | Default `Movie` | `GET /3/movie/popular?page=1` returns 200 | Movie results render | 20 movie cards rendered; no application error | **PASS** |
| `TYPE-002` | Select `TV Shows` | `GET /3/tv/popular?page=1` returns 200 | TV results render | TV Shows remained selected; 20 TV cards rendered; no error | **PASS** |
| `GENRE-001` | Movie + `Action` | `GET /3/discover/movie?...&with_genres=28` returns 200; sample records include genre 28 | Action is selected; returned movies satisfy the genre constraint | Action chip selected; 20 cards rendered; sample records contained genre 28 | **PASS** |
| `GENRE-002` | Movie + `Action` + `Comedy` | Request sequence ends with `with_genres=28,35` and returns 200 | Both selected genres remain visible; cards render | Action and Comedy chips selected; final request contained `28,35`; 20 cards rendered | **PASS** |
| `GENRE-003` | TV Shows + `Drama` | Request sequence ends with `GET /3/discover/tv?...&with_genres=18` and returns 200 | Drama is selected; TV cards render | TV Shows and Drama selected; 20 TV cards rendered | **PASS** |
| `RATING-001` | `1.0` star (& up) | `GET /3/discover/movie?...&vote_average.gte=1&vote_average.lte=5&page=1` returns 200; sampled ratings are ≥1 | Results satisfy the lower bound | 20 cards rendered; sampled API ratings were ≥1 | **PASS** |
| `RATING-002` | `3.5` stars (& up) | `GET /3/discover/movie?...&vote_average.gte=3.5&vote_average.lte=5&page=1` returns 200; the left half of the fourth star is selected | Results satisfy the half-star lower bound | 20 cards rendered; sampled API ratings were ≥3.5 | **PASS** |
| `RATING-003` | `4.0` stars (& up) | `GET /3/discover/movie?...&vote_average.gte=4&vote_average.lte=5&page=1` returns 200; the right half of the fourth star is selected | Results satisfy the full-star lower bound | 20 cards rendered; sampled API ratings were ≥4 | **PASS** |
| `RATING-004` | `4.5` stars (& up) | `GET /3/discover/movie?...&vote_average.gte=4.5&vote_average.lte=5&page=1` returns 200; the left half of the fifth star is selected | Results satisfy the half-star lower bound | 20 cards rendered; sampled API ratings were ≥4.5 | **PASS** |
| `RATING-005` | `5.0` stars (& up) | `GET /3/discover/movie?...&vote_average.gte=5&vote_average.lte=5&page=1` returns 200; the right half of the fifth star is selected | Results satisfy the 5-star boundary or show no results | 20 cards rendered; sampled API ratings were 5 | **PASS** |
| `SEARCH-001` | Exact `Seventeen: 1977` | `GET /3/search/movie?query=Seventeen%3A+1977&page=1` returns 200 with one result | The matching title renders | One matching title rendered; its missing poster triggered [`BUG-004`](defects.md#bug-004--results-without-a-poster-render-a-broken-image) | **PASS + defect** |
| `SEARCH-002` | Partial `Batman` | `GET /3/search/movie?query=Batman&page=1` returns 200; 174 results across 9 pages in this run | Matching cards and pagination render | 20 matching cards and 9 pages rendered | **PASS** |
| `SEARCH-003` | No match `__qa_no_match_20260901__` | Search request returns 200 with `total_results=0` | UI says `No results found.` | `No results found.` displayed; no error | **PASS** |
| `SEARCH-004` | Special characters `Spider-Man: No Way Home` | Encoded query request returns 200 with two results | Matching cards render without encoding errors | Two matching cards rendered | **PASS** |
| `SEARCH-005` | TV Shows + `Batman` | TV search should use a TV search endpoint and TV fields | TV titles and first-air years render | App sent `/3/search/movie`; 20 cards rendered without titles | **FAIL — BUG-006** |
| `YEAR-001` | Start `2020`, end `2024` | Final request uses `gte=2020-01-01` and `lte=2024-12-31` | Final controls and results stay within 2020–2024 | Final state was correct, but an intermediate request used `lte=2026` while the visible end was 2025 | **PARTIAL — BUG-005** |
| `YEAR-002` | Select start `2025` while visible end is `2025` | Request should end at `lte=2025-12-31` | Only 2025 results render | Request used `lte=2026-12-31`; 2026 cards rendered | **FAIL — BUG-005** |
| `COMBO-001` | Action + rating 4 | Final discover request contains `with_genres=28` and `vote_average.gte=4`; response 200 | Results satisfy both selected constraints | Final request and sampled response satisfied both; 20 cards rendered | **PASS** |
| `COMBO-002` | 2020–2024 + Action | Final request contains year bounds and `with_genres=28`; response 200 | Results satisfy both year and genre constraints | Final request contained all parameters, but API/UI showed release years 1997 and 2010 | **FAIL — BUG-005** |
| `COMBO-003` | TV Shows + Drama + rating 4 | Final discover TV request contains `with_genres=18` and `vote_average.gte=4`; response 200 | TV results satisfy both constraints | Final request and sampled response satisfied both; 20 cards rendered | **PASS** |
| `COMBO-004` | Select Action, then search `Batman` | Search behavior must be explicit: combine filters or clear them visibly | Request and visible filters agree | Search request omitted genre and Action chip cleared; 20 cards rendered | **PASS** *(search-reset assumption)* |

## Decisions and follow-up

1. The type, genre, rating, search, and representative combination cases are covered manually and by the phase 1–3 automation suite.
2. `BUG-005` affects both the visible-current-year boundary and a year + genre result set; it is not limited to one selector action.
3. `BUG-006` was added after the TV search combination exposed a movie endpoint/TV rendering mismatch.
4. The confirmed pagination, retained-page, direct-route, missing-poster, and TV-search findings now have strict expected-failure regression tests.
5. Rating values are not shown on result cards, so rating verification currently relies on the browser response; full- and half-star selections are exercised through the control's left and right halves.
6. Multi-genre AND/OR semantics and whether search intentionally clears other filters need product confirmation.
7. The filtered last-page control case (`TC-PAGE-003`) is automated as `test_filtered_last_page_remains_usable`; exhaustive page-control states remain a follow-up item.
