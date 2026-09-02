"""Pagination and retained-filter state regression scenarios."""

from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage

SERVICE_MAX_PAGE = 500


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
def test_pagination_moves_to_next_and_previous_page(discover_page: DiscoverPage) -> None:
    """Users can move forward and back while results and page state stay usable."""
    discover_page.open()
    next_response = discover_page.next_page()
    next_payload = discover_page.response_json(next_response)

    assert next_response.status == 200
    assert discover_page.response_path(next_response) == "/3/movie/popular"
    assert discover_page.response_query(next_response)["page"] == ["2"]
    assert next_payload["results"]
    assert discover_page.current_page_number() == 2
    expect(discover_page.result_items).to_have_count(len(next_payload["results"]))
    expect(discover_page.error_message).not_to_be_visible()

    previous_response = discover_page.previous_page()
    previous_payload = discover_page.response_json(previous_response)

    assert previous_response.status == 200
    assert discover_page.response_path(previous_response) == "/3/movie/popular"
    assert discover_page.response_query(previous_response)["page"] == ["1"]
    assert previous_payload["results"]
    assert discover_page.current_page_number() == 1
    expect(discover_page.result_items).to_have_count(len(previous_payload["results"]))
    expect(discover_page.error_message).not_to_be_visible()


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
def test_search_pagination_preserves_query(discover_page: DiscoverPage) -> None:
    """Moving through search pages keeps the query and renders the next result set."""
    discover_page.open()
    search_response = discover_page.search("Batman")
    search_payload = discover_page.response_json(search_response)

    assert search_response.status == 200
    assert search_payload["total_pages"] > 1
    assert discover_page.pagination_page_numbers()

    response = discover_page.select_page(2, endpoint="/3/search/movie")
    query = discover_page.response_query(response)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/search/movie"
    assert query["query"] == ["Batman"]
    assert query["page"] == ["2"]
    assert payload["results"]
    assert discover_page.current_page_number() == 2
    assert discover_page.card_titles() == [result["title"] for result in payload["results"]]
    expect(discover_page.result_items).to_have_count(len(payload["results"]))
    expect(discover_page.error_message).not_to_be_visible()


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
def test_filtered_last_page_remains_usable(discover_page: DiscoverPage) -> None:
    """A filtered listing can reach its displayed last page within the service limit."""
    discover_page.open()
    discover_page.select_year_start(2020)
    discover_page.select_year_end(2024)
    discover_page.select_genre("Action")

    page_numbers = discover_page.pagination_page_numbers()
    assert page_numbers
    last_page = max(page_numbers)
    assert 1 < last_page <= SERVICE_MAX_PAGE

    response = discover_page.select_page(last_page, endpoint="/3/discover/movie")
    query = discover_page.response_query(response)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/discover/movie"
    assert query["page"] == [str(last_page)]
    assert query["release_date.gte"] == ["2020-01-01"]
    assert query["release_date.lte"] == ["2024-12-31"]
    assert query["with_genres"] == ["28"]
    assert payload["results"]
    assert discover_page.current_page_number() == last_page
    expect(discover_page.result_items).to_have_count(len(payload["results"]))
    expect(discover_page.error_message).not_to_be_visible()


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    reason="BUG-001: pagination exposes page numbers above the service maximum of 500",
)
def test_pagination_does_not_offer_pages_beyond_service_limit(
    discover_page: DiscoverPage,
) -> None:
    """Every numeric page exposed by the UI is supported by the listing service."""
    discover_page.open()
    page_numbers = discover_page.pagination_page_numbers()

    assert page_numbers
    assert all(1 <= page_number <= SERVICE_MAX_PAGE for page_number in page_numbers)


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    reason="BUG-001: selecting the displayed final page sends an unsupported page number",
)
def test_highest_offered_page_loads_results_and_becomes_active(
    discover_page: DiscoverPage,
) -> None:
    """Selecting the highest offered page succeeds and keeps results visible."""
    discover_page.open()
    page_numbers = discover_page.pagination_page_numbers()
    assert page_numbers
    last_page = max(page_numbers)

    response = discover_page.select_page(last_page)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_query(response)["page"] == [str(last_page)]
    assert payload["results"]
    expect(discover_page.result_items).to_have_count(len(payload["results"]))
    expect(discover_page.error_message).not_to_be_visible()
    assert discover_page.current_page_number() == last_page


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    reason="BUG-003: category navigation reuses the invalid page after a pagination error",
)
def test_category_navigation_resets_page_after_pagination_error(
    discover_page: DiscoverPage,
) -> None:
    """A failed page request must not determine the next category's page."""
    discover_page.open()
    page_numbers = discover_page.pagination_page_numbers()
    assert page_numbers
    discover_page.select_page(max(page_numbers))
    expect(discover_page.error_message).to_be_visible()

    category_responses: list[tuple[int, str]] = []

    def record_category_response(response) -> None:
        if DiscoverPage._is_api_response(response, "/3/trending/movie/week"):
            category_responses.append((response.status, response.url))

    discover_page.page.on("response", record_category_response)
    try:
        discover_page.page.get_by_role("link", name="Trend", exact=True).click()
        discover_page.page.wait_for_load_state("networkidle", timeout=60_000)
    finally:
        discover_page.page.remove_listener("response", record_category_response)

    assert discover_page.page.url.endswith("/trend")
    assert category_responses
    assert all(
        status == 200 and parse_qs(urlparse(url).query)["page"] == ["1"]
        for status, url in category_responses
    )
    expect(discover_page.result_items.first).to_be_visible()
    expect(discover_page.error_message).not_to_be_visible()
