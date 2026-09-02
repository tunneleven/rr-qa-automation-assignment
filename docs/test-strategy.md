# Test Strategy

## Objective

Evaluate the reliability of filtering and pagination in the TMDB Discover demo through maintainable UI tests and browser-network assertions.

## Scope

### In scope

- Categories: Popular, Trending, Newest, and Top Rated
- Title, media type, release year, rating, and genre filters
- Filter combinations and result consistency
- Pagination, direct routes, and refresh behavior
- Requests initiated by browser interactions and their responses
- Negative, boundary, and known-defect scenarios

### Out of scope

- Correctness or availability of the upstream TMDB data/service beyond the contract exposed to the browser
- Pixel-perfect visual comparison, performance/load testing, and a full accessibility audit
- Exhaustive testing of every genre and filter permutation; representative pairwise combinations are used first
- Features outside discovery, navigation, filtering, and pagination unless the requirements expand

## Current phase

Manual exploration and the representative coverage matrix are complete. Phases 1–6 of automation are implemented with pytest and Playwright: homepage smoke, category/type navigation, individual filters, valid filter combinations, browser request/response-to-UI consistency, normal pagination, and regression checks for the confirmed pagination, routing, media, and TV-search defects. Confirmed defects are retained as strict expected failures until fixed.

## Test levels

- **Smoke:** application availability and critical result rendering
- **UI functional:** visible behavior for filters and pagination
- **Browser API:** request parameters, status, schema, and UI/response consistency
- **Negative:** invalid, empty, boundary, direct-route, and late-page behavior

## Test design techniques

- Equivalence partitioning
- Boundary value analysis
- Decision tables for meaningful filter combinations
- State-transition testing for pagination and route changes
- Error guessing based on the assignment's known issues

## Automation principles

- Prefer accessible role, label, and text locators over implementation-specific CSS.
- Use Playwright web-first assertions and automatic waiting; avoid fixed sleeps.
- Keep selectors and reusable actions in page objects; keep assertions in tests.
- Give every test a single, observable purpose and isolated browser context.
- Parametrize equivalent scenarios instead of duplicating test logic.
- Log business actions and API observations, not low-value implementation noise.
- Retain traces and screenshots on failure and create a self-contained HTML report.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Shared demo environment or changing data | Assert stable invariants rather than exact volatile result counts |
| Third-party/API instability | Capture response status and diagnostics; distinguish product failures from environment failures |
| Weak or changing selectors | Prefer user-facing locators and centralize them in the page object |
| Known broken routes/pages | Document defects and use `xfail(strict=True)` only after a defect is confirmed |

## Environments

Record browser, operating system, Python version, execution date, and target URL in each test-results report.

## Entry and exit criteria

### Entry

- Target application is reachable.
- Test dependencies and Chromium are installed.
- Exploratory DOM/network reconnaissance is complete for the scenario under test.

### Exit

- Planned high-priority scenarios have executed.
- Failures have diagnostic artifacts.
- Confirmed product defects are documented and linked to test evidence.
- Setup and execution are reproducible from the README.
