"""Assertion helpers shared by the UI and browser-network suites.

These cover the invariants that nearly every scenario repeats: the listing
request succeeded, it carried the expected parameters, and its records reached
the UI. Scenario-specific expectations stay in the tests themselves.
"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Response, expect

from pages.discover_page import DiscoverPage


def assert_listing_response(
    discover_page: DiscoverPage,
    response: Response,
    endpoint: str,
) -> dict[str, Any]:
    """Assert the listing request succeeded against `endpoint` and return its payload."""
    assert response.status == 200, f"unexpected status for {response.url}"
    assert discover_page.response_path(response) == endpoint
    return discover_page.response_json(response)


def assert_query_parameters(
    discover_page: DiscoverPage,
    response: Response,
    expected: dict[str, str],
) -> None:
    """Assert each expected query parameter was sent with exactly the given value."""
    query = discover_page.response_query(response)
    for name, value in expected.items():
        assert query.get(name) == [value], f"unexpected {name}: {query.get(name)}"


def assert_results_are_rendered(
    discover_page: DiscoverPage,
    payload: dict[str, Any],
    *,
    title_field: str | None = None,
) -> None:
    """Assert every returned record is rendered as a titled card without an app error.

    Pass `title_field` to compare the cards with the payload title by title; omit
    it when only the presence of a title can be relied on.
    """
    results = payload["results"]

    assert results
    expect(discover_page.result_cards).to_have_count(len(results))
    if title_field is None:
        assert all(discover_page.card_titles())
    else:
        expected_titles = [result[title_field] for result in results]
        for index, expected_title in enumerate(expected_titles):
            expect(discover_page.card_title(index)).to_have_text(expected_title)
    expect(discover_page.error_message).not_to_be_visible()


def assert_results_or_empty_state(
    discover_page: DiscoverPage,
    payload: dict[str, Any],
    *,
    title_field: str,
) -> None:
    """Assert payload results render, or an empty payload renders the empty state."""
    if payload["results"]:
        assert_results_are_rendered(discover_page, payload, title_field=title_field)
        return

    expect(discover_page.no_results_message).to_be_visible()
    expect(discover_page.result_cards).to_have_count(0)
    expect(discover_page.error_message).not_to_be_visible()
