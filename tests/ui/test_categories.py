"""Category and media-type navigation scenarios."""

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage

CATEGORY_CASES = (
    pytest.param("Popular", "/popular", "/3/movie/popular", id="popular"),
    pytest.param("Trend", "/trend", "/3/trending/movie/week", id="trend"),
    pytest.param("Newest", "/new", "/3/movie/now_playing", id="newest"),
    pytest.param("Top rated", "/top", "/3/movie/top_rated", id="top-rated"),
)

MEDIA_TYPE_CASES = (
    pytest.param("Movie", "/3/movie/popular", "title", "release_date", id="movie"),
    pytest.param("TV Shows", "/3/tv/popular", "name", "first_air_date", id="tv-shows"),
)


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize(("category", "route", "endpoint"), CATEGORY_CASES)
def test_category_navigation_loads_results(
    discover_page: DiscoverPage,
    category: str,
    route: str,
    endpoint: str,
) -> None:
    """Each in-app category link requests and renders its corresponding listing."""
    discover_page.open()
    if category == "Popular":
        discover_page.navigate_category("Trend")
    response = discover_page.navigate_category(category)

    assert response.status == 200
    assert discover_page.response_path(response) == endpoint
    assert discover_page.page.url.endswith(route)
    expect(discover_page.result_cards).to_have_count(20)
    assert all(discover_page.card_titles())
    assert not discover_page.error_message.is_visible()


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize(("type_name", "endpoint", "title_field", "date_field"), MEDIA_TYPE_CASES)
def test_media_type_filter_loads_matching_result_fields(
    discover_page: DiscoverPage,
    type_name: str,
    endpoint: str,
    title_field: str,
    date_field: str,
) -> None:
    """Movie and TV selections load results using their own response schemas."""
    discover_page.open()
    if type_name == "Movie":
        discover_page.select_type("TV Shows")
    response = discover_page.select_type(type_name)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == endpoint
    assert discover_page.selected_value("Type") == type_name
    assert len(payload["results"]) == 20
    assert all(result.get(title_field) for result in payload["results"])
    assert all(result.get(date_field) for result in payload["results"])
    expect(discover_page.result_cards).to_have_count(len(payload["results"]))
    assert all(discover_page.card_titles())
