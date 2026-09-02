"""Individual filter scenarios and their user-visible results."""

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage
from pages.endpoints import DISCOVER_MOVIE, DISCOVER_TV, SEARCH_MOVIE, TV_TYPE
from tests.assertions import (
    assert_listing_response,
    assert_query_parameters,
    assert_results_are_rendered,
)


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize(
    ("genre", "genre_id"),
    [pytest.param("Action", "28", id="action")],
)
def test_genre_filter_renders_results_for_selected_genre(
    discover_page: DiscoverPage,
    genre: str,
    genre_id: str,
) -> None:
    """Selecting a genre sends the genre constraint and renders results."""
    discover_page.open()
    response = discover_page.select_genre(genre)
    payload = assert_listing_response(discover_page, response, DISCOVER_MOVIE)

    assert_query_parameters(discover_page, response, {"with_genres": genre_id})
    assert discover_page.selected_values("Genre") == [genre]
    assert_results_are_rendered(discover_page, payload)
    assert all(
        genre_id in {str(value) for value in result["genre_ids"]} for result in payload["results"]
    )


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
def test_multi_genre_filter_sends_all_selected_genres(
    discover_page: DiscoverPage,
) -> None:
    """Selecting two genres sends both IDs and keeps both selections visible."""
    discover_page.open()
    discover_page.select_genre("Action")
    response = discover_page.select_genre("Comedy")
    payload = assert_listing_response(discover_page, response, DISCOVER_MOVIE)
    sent_genres = discover_page.response_query(response)["with_genres"][0]

    assert set(sent_genres.split(",")) == {"28", "35"}
    assert set(discover_page.selected_values("Genre")) == {"Action", "Comedy"}
    assert_results_are_rendered(discover_page, payload)


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
def test_tv_genre_filter_uses_tv_endpoint_and_tv_fields(
    discover_page: DiscoverPage,
) -> None:
    """A genre filter for TV Shows uses TV results and TV-specific fields."""
    discover_page.open()
    discover_page.select_type(TV_TYPE)
    response = discover_page.select_genre("Drama")
    payload = assert_listing_response(discover_page, response, DISCOVER_TV)

    assert_query_parameters(discover_page, response, {"with_genres": "18"})
    assert discover_page.selected_value("Type") == TV_TYPE
    assert discover_page.selected_values("Genre") == ["Drama"]
    assert_results_are_rendered(discover_page, payload, title_field="name")
    assert all(result.get("name") and result.get("first_air_date") for result in payload["results"])


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize(
    "rating",
    [
        pytest.param(1.0, id="one-star"),
        pytest.param(3.5, id="three-and-a-half-stars"),
        pytest.param(4.0, id="four-stars"),
        pytest.param(4.5, id="four-and-a-half-stars"),
        pytest.param(5.0, id="five-stars"),
    ],
)
def test_rating_filter_renders_results_at_or_above_selected_boundary(
    discover_page: DiscoverPage,
    rating: float,
) -> None:
    """Selecting a full or half star sends the lower bound and renders matching results."""
    discover_page.open()
    response = discover_page.select_rating(rating)
    payload = assert_listing_response(discover_page, response, DISCOVER_MOVIE)

    assert_query_parameters(
        discover_page,
        response,
        {"vote_average.gte": f"{rating:g}", "vote_average.lte": "5"},
    )
    assert_results_are_rendered(discover_page, payload)
    assert all(result["vote_average"] >= rating for result in payload["results"])


@pytest.mark.regression
@pytest.mark.ui
def test_search_filter_renders_matching_movie_titles(discover_page: DiscoverPage) -> None:
    """A partial title search renders the same movie titles returned by the API."""
    discover_page.open()
    response = discover_page.search("Batman")
    payload = assert_listing_response(discover_page, response, SEARCH_MOVIE)

    assert_query_parameters(discover_page, response, {"query": "Batman"})
    assert payload["total_results"] > 0
    assert_results_are_rendered(discover_page, payload, title_field="title")


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
def test_search_filter_supports_special_characters(
    discover_page: DiscoverPage,
) -> None:
    """A title containing punctuation is encoded and rendered correctly."""
    query_text = "Spider-Man: No Way Home"
    discover_page.open()
    response = discover_page.search(query_text)
    payload = assert_listing_response(discover_page, response, SEARCH_MOVIE)

    assert_query_parameters(discover_page, response, {"query": query_text})
    assert payload["total_results"] > 0
    assert_results_are_rendered(discover_page, payload, title_field="title")


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    reason="BUG-005: the API response can contain results outside the selected year range",
)
def test_year_filter_applies_both_selected_bounds(discover_page: DiscoverPage) -> None:
    """A valid year range is reflected in the request and every visible result."""
    discover_page.open()
    discover_page.select_year_start(2020)
    response = discover_page.select_year_end(2024)
    payload = assert_listing_response(discover_page, response, DISCOVER_MOVIE)

    assert discover_page.selected_years() == ["2020", "2024"]
    assert_query_parameters(
        discover_page,
        response,
        {"release_date.gte": "2020-01-01", "release_date.lte": "2024-12-31"},
    )
    assert_results_are_rendered(discover_page, payload)
    assert all(2020 <= int(result["release_date"][:4]) <= 2024 for result in payload["results"])

    visible_years = discover_page.card_release_years()
    assert all(year.isdigit() for year in visible_years)
    assert all(2020 <= int(year) <= 2024 for year in visible_years)


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.negative
def test_year_filter_rejects_invalid_range_without_changing_selection(
    discover_page: DiscoverPage,
) -> None:
    """An invalid year choice cannot replace an already valid range."""
    discover_page.open()
    discover_page.select_year_start(2020)
    discover_page.select_year_end(2024)
    expected_years = ["2020", "2024"]

    discover_page.try_select_year(2025, position=0)
    discover_page.try_select_year(2019, position=1)

    assert discover_page.selected_years() == expected_years
    expect(discover_page.result_cards.first).to_be_visible()
    expect(discover_page.error_message).not_to_be_visible()


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.negative
def test_search_filter_shows_empty_state_for_no_results(discover_page: DiscoverPage) -> None:
    """A search with no matches shows an explicit empty state rather than an error."""
    discover_page.open()
    response = discover_page.search("__qa_no_match_20260901__")
    payload = assert_listing_response(discover_page, response, SEARCH_MOVIE)

    assert payload["total_results"] == 0
    expect(discover_page.no_results_message).to_be_visible()
    expect(discover_page.result_cards).to_have_count(0)
    expect(discover_page.error_message).not_to_be_visible()


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.xfail(
    strict=True,
    reason="BUG-005: the visible year end is 2025 but the request uses the current year",
)
def test_year_filter_request_matches_visible_upper_bound(discover_page: DiscoverPage) -> None:
    """The selected 2025 start year should not expand the visible 2025 end year."""
    discover_page.open()
    response = discover_page.select_year_start(2025)

    assert discover_page.selected_years() == ["2025", "2025"]
    assert_query_parameters(
        discover_page,
        response,
        {"release_date.gte": "2025-01-01", "release_date.lte": "2025-12-31"},
    )
    assert all(year == "2025" for year in discover_page.card_release_years())
