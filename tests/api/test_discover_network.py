"""Browser request/response and API-to-UI consistency scenarios."""

import pytest

from pages.discover_page import DiscoverPage
from pages.endpoints import DISCOVER_MOVIE, POPULAR_MOVIE, SEARCH_MOVIE
from tests.assertions import (
    assert_listing_response,
    assert_query_parameters,
    assert_results_are_rendered,
)


@pytest.mark.api
@pytest.mark.regression
def test_popular_response_is_rendered_as_movie_cards(discover_page: DiscoverPage) -> None:
    """The popular endpoint response is rendered without losing movie fields."""
    response = discover_page.open()
    payload = assert_listing_response(discover_page, response, POPULAR_MOVIE)

    assert_query_parameters(discover_page, response, {"page": "1"})
    assert_results_are_rendered(discover_page, payload, title_field="title")
    assert all(result.get("release_date") for result in payload["results"])


@pytest.mark.api
@pytest.mark.regression
def test_genre_request_response_and_ui_are_consistent(discover_page: DiscoverPage) -> None:
    """The selected genre is sent to the API and retained in rendered results."""
    discover_page.open()
    response = discover_page.select_genre("Action")
    payload = assert_listing_response(discover_page, response, DISCOVER_MOVIE)

    assert_query_parameters(discover_page, response, {"with_genres": "28"})
    assert_results_are_rendered(discover_page, payload, title_field="title")
    assert all(28 in result["genre_ids"] for result in payload["results"])


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize(
    "stars",
    [
        pytest.param(1, id="one-star"),
        pytest.param(4, id="four-stars"),
        pytest.param(5, id="five-stars"),
    ],
)
def test_rating_request_response_and_ui_are_consistent(
    discover_page: DiscoverPage,
    stars: int,
) -> None:
    """The rating boundary is sent and every returned record meets it."""
    discover_page.open()
    response = discover_page.select_rating(stars)
    payload = assert_listing_response(discover_page, response, DISCOVER_MOVIE)

    assert_query_parameters(discover_page, response, {"vote_average.gte": str(stars)})
    assert_results_are_rendered(discover_page, payload, title_field="title")
    assert all(result["vote_average"] >= stars for result in payload["results"])


@pytest.mark.api
@pytest.mark.regression
def test_search_request_response_and_ui_are_consistent(discover_page: DiscoverPage) -> None:
    """The search query reaches the movie endpoint and its titles reach the UI."""
    discover_page.open()
    response = discover_page.search("Batman")
    payload = assert_listing_response(discover_page, response, SEARCH_MOVIE)

    assert_query_parameters(discover_page, response, {"query": "Batman"})
    assert_results_are_rendered(discover_page, payload, title_field="title")
    assert payload["total_results"] >= len(payload["results"])
