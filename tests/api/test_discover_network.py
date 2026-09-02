"""Browser request/response and API-to-UI consistency scenarios."""

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage


def assert_response_is_rendered(
    discover_page: DiscoverPage,
    response,
    title_field: str,
) -> dict:
    """Assert the response is successful and its result titles reach the UI."""
    payload = discover_page.response_json(response)
    results = payload["results"]

    assert response.status == 200
    assert results
    expect(discover_page.result_cards).to_have_count(len(results))
    assert discover_page.card_titles() == [result[title_field] for result in results]
    return payload


@pytest.mark.api
@pytest.mark.regression
def test_popular_response_is_rendered_as_movie_cards(discover_page: DiscoverPage) -> None:
    """The popular endpoint response is rendered without losing movie fields."""
    response = discover_page.open()
    query = discover_page.response_query(response)

    assert discover_page.response_path(response) == "/3/movie/popular"
    assert query["page"] == ["1"]
    payload = assert_response_is_rendered(discover_page, response, "title")
    assert all(result.get("release_date") for result in payload["results"])


@pytest.mark.api
@pytest.mark.regression
def test_genre_request_response_and_ui_are_consistent(discover_page: DiscoverPage) -> None:
    """The selected genre is sent to the API and retained in rendered results."""
    discover_page.open()
    response = discover_page.select_genre("Action")
    query = discover_page.response_query(response)

    assert discover_page.response_path(response) == "/3/discover/movie"
    assert query["with_genres"] == ["28"]
    payload = assert_response_is_rendered(discover_page, response, "title")
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
    query = discover_page.response_query(response)

    assert discover_page.response_path(response) == "/3/discover/movie"
    assert query["vote_average.gte"] == [str(stars)]
    payload = assert_response_is_rendered(discover_page, response, "title")
    assert all(result["vote_average"] >= stars for result in payload["results"])


@pytest.mark.api
@pytest.mark.regression
def test_search_request_response_and_ui_are_consistent(discover_page: DiscoverPage) -> None:
    """The search query reaches the movie endpoint and its titles reach the UI."""
    discover_page.open()
    response = discover_page.search("Batman")
    query = discover_page.response_query(response)

    assert discover_page.response_path(response) == "/3/search/movie"
    assert query["query"] == ["Batman"]
    payload = assert_response_is_rendered(discover_page, response, "title")
    assert payload["total_results"] >= len(payload["results"])
