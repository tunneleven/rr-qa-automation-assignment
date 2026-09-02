"""Pagination and retained-filter state regression scenarios."""

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage
from pages.endpoints import (
    CATEGORY_BY_LABEL,
    DISCOVER_MOVIE,
    POPULAR_MOVIE,
    SEARCH_MOVIE,
    SERVICE_MAX_PAGE,
)
from tests.assertions import (
    assert_listing_response,
    assert_query_parameters,
    assert_results_are_rendered,
)
from tests.known_defects import KnownDefectError

TREND_CATEGORY = CATEGORY_BY_LABEL["Trend"]


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
def test_pagination_moves_to_next_and_previous_page(discover_page: DiscoverPage) -> None:
    """Users can move forward and back while results and page state stay usable."""
    discover_page.open()
    next_response = discover_page.next_page()
    next_payload = assert_listing_response(discover_page, next_response, POPULAR_MOVIE)

    assert_query_parameters(discover_page, next_response, {"page": "2"})
    assert discover_page.current_page_number() == 2
    assert_results_are_rendered(discover_page, next_payload, title_field="title")

    previous_response = discover_page.previous_page()
    previous_payload = assert_listing_response(discover_page, previous_response, POPULAR_MOVIE)

    assert_query_parameters(discover_page, previous_response, {"page": "1"})
    assert discover_page.current_page_number() == 1
    assert_results_are_rendered(discover_page, previous_payload, title_field="title")


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
def test_search_pagination_preserves_query(discover_page: DiscoverPage) -> None:
    """Moving through search pages keeps the query and renders the next result set."""
    discover_page.open()
    search_response = discover_page.search("Batman")
    search_payload = assert_listing_response(discover_page, search_response, SEARCH_MOVIE)

    assert search_payload["total_pages"] > 1
    assert discover_page.pagination_page_numbers()

    response = discover_page.select_page(2, endpoint=SEARCH_MOVIE)
    payload = assert_listing_response(discover_page, response, SEARCH_MOVIE)

    assert_query_parameters(discover_page, response, {"query": "Batman", "page": "2"})
    assert discover_page.current_page_number() == 2
    assert_results_are_rendered(discover_page, payload, title_field="title")


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

    response = discover_page.select_page(last_page, endpoint=DISCOVER_MOVIE)
    payload = assert_listing_response(discover_page, response, DISCOVER_MOVIE)

    assert_query_parameters(
        discover_page,
        response,
        {
            "page": str(last_page),
            "release_date.gte": "2020-01-01",
            "release_date.lte": "2024-12-31",
            "with_genres": "28",
        },
    )
    assert discover_page.current_page_number() == last_page
    assert_results_are_rendered(discover_page, payload, title_field="title")


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    raises=KnownDefectError,
    reason="BUG-001: pagination exposes page numbers above the service maximum of 500",
)
def test_pagination_does_not_offer_pages_beyond_service_limit(
    discover_page: DiscoverPage,
) -> None:
    """Every numeric page exposed by the UI is supported by the listing service."""
    discover_page.open()
    page_numbers = discover_page.pagination_page_numbers()

    assert page_numbers
    assert all(page_number >= 1 for page_number in page_numbers)
    if any(page_number > SERVICE_MAX_PAGE for page_number in page_numbers):
        raise KnownDefectError("BUG-001: pagination exposes a page above the service limit")


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    raises=KnownDefectError,
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

    assert discover_page.response_path(response) == POPULAR_MOVIE
    assert_query_parameters(discover_page, response, {"page": str(last_page)})
    if last_page > SERVICE_MAX_PAGE and response.status == 400:
        error_payload = discover_page.response_json(response)
        assert error_payload.get("status_code") == 22
        expect(discover_page.error_message).to_be_visible()
        raise KnownDefectError("BUG-001: the highest offered page receives service error 22")

    payload = assert_listing_response(discover_page, response, POPULAR_MOVIE)
    assert discover_page.current_page_number() == last_page
    assert_results_are_rendered(discover_page, payload, title_field="title")


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    raises=KnownDefectError,
    reason="BUG-003: category navigation reuses the invalid page after a pagination error",
)
def test_category_navigation_resets_page_after_pagination_error(
    discover_page: DiscoverPage,
) -> None:
    """A failed page request must not determine the next category's page."""
    discover_page.open()
    page_numbers = discover_page.pagination_page_numbers()
    assert page_numbers
    unsupported_page = max(page_numbers)
    unsupported_response = discover_page.select_page(unsupported_page)
    assert unsupported_page > SERVICE_MAX_PAGE
    assert unsupported_response.status == 400
    assert discover_page.response_json(unsupported_response).get("status_code") == 22
    expect(discover_page.error_message).to_be_visible()

    # Every trending request is recorded, because the stale page number can be
    # sent either side of the response that renders the category.
    with discover_page.recording_responses(TREND_CATEGORY.endpoint) as category_responses:
        discover_page.navigate_category(TREND_CATEGORY.label)
        discover_page.wait_for_page_request_other_than(TREND_CATEGORY.endpoint)

    assert discover_page.page.url.endswith(TREND_CATEGORY.route)
    assert category_responses

    successful_page_one_response = next(
        (
            response
            for response in category_responses
            if response.status == 200
            and discover_page.response_query(response).get("page") == ["1"]
        ),
        None,
    )
    assert successful_page_one_response is not None
    successful_payload = assert_listing_response(
        discover_page,
        successful_page_one_response,
        TREND_CATEGORY.endpoint,
    )
    assert_query_parameters(discover_page, successful_page_one_response, {"page": "1"})

    documented_stale_responses = []
    for response in category_responses:
        if (
            discover_page.response_query(response).get("page") == [str(unsupported_page)]
            and response.status == 400
            and discover_page.response_json(response).get("status_code") == 22
        ):
            documented_stale_responses.append(response)

    try:
        assert_results_are_rendered(
            discover_page,
            successful_payload,
            title_field="title",
        )
    except AssertionError as recovery_failure:
        final_error_state = (
            discover_page.error_message.is_visible() and discover_page.result_cards.count() == 0
        )
        if documented_stale_responses and final_error_state:
            raise KnownDefectError(
                "BUG-003: the rejected stale page request determined the final error state"
            ) from recovery_failure
        raise

    # A stale request that loses the response race is still unexpected, but it
    # is not the documented final-state defect and must fail as an ordinary assertion.
    for response in category_responses:
        assert response.status == 200
        assert_query_parameters(discover_page, response, {"page": "1"})
