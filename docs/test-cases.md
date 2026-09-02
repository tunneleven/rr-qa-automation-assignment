# Test Cases

Test cases will be finalized after exploratory DOM and network reconnaissance.

## Template

| Field | Value |
|---|---|
| ID | `TC-AREA-###` |
| Title | Clear expected behavior |
| Priority | Critical / High / Medium / Low |
| Type | Smoke / UI / Browser API / Negative |
| Preconditions | Required application state |
| Test data | Explicit inputs and boundaries |
| Steps | Numbered user actions |
| Expected result | Observable UI and/or API outcome |
| Automation | Test node ID once implemented |

## Initial coverage inventory

| Area | Planned coverage |
|---|---|
| Categories | Popular, Trending, Newest, Top Rated |
| Title | Existing, partial, no-match, and special-character queries |
| Type | Movies and TV Shows |
| Release year | Valid value, boundaries, and invalid/empty input |
| Rating | Valid value and lower/upper boundaries |
| Genre | Representative genres and result consistency |
| Combinations | Pairwise/high-risk combinations rather than every permutation |
| Pagination | Next/previous, page changes, retained filters, and late pages |
| Routing | Direct slug access and browser refresh |
| Network | Request parameters, response status/schema, and UI consistency |
