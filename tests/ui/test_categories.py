"""Category and media-type navigation scenarios."""

import pytest

from pages.discover_page import DiscoverPage
from pages.endpoints import (
    CATEGORIES,
    MEDIA_TYPE_ENDPOINTS,
    MOVIE_TYPE,
    RESULTS_PER_PAGE,
    TV_TYPE,
    Category,
)
from tests.assertions import assert_listing_response, assert_results_are_rendered

CATEGORY_CASES = tuple(pytest.param(category, id=category.test_id) for category in CATEGORIES)

MEDIA_TYPE_CASES = (
    pytest.param(MOVIE_TYPE, "title", "release_date", id="movie"),
    pytest.param(TV_TYPE, "name", "first_air_date", id="tv-shows"),
)


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize("category", CATEGORY_CASES)
def test_category_navigation_loads_results(
    discover_page: DiscoverPage,
    category: Category,
) -> None:
    """Each in-app category link requests and renders its corresponding listing."""
    discover_page.open()
    response = discover_page.navigate_category_fresh(category.label)
    payload = assert_listing_response(discover_page, response, category.endpoint)

    assert discover_page.page.url.endswith(category.route)
    assert len(payload["results"]) == RESULTS_PER_PAGE
    assert_results_are_rendered(discover_page, payload, title_field="title")


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize(("type_name", "title_field", "date_field"), MEDIA_TYPE_CASES)
def test_media_type_filter_loads_matching_result_fields(
    discover_page: DiscoverPage,
    type_name: str,
    title_field: str,
    date_field: str,
) -> None:
    """Movie and TV selections load results using their own response schemas."""
    discover_page.open()
    response = discover_page.select_type_fresh(type_name)
    payload = assert_listing_response(discover_page, response, MEDIA_TYPE_ENDPOINTS[type_name])

    assert discover_page.selected_value("Type") == type_name
    assert len(payload["results"]) == RESULTS_PER_PAGE
    assert all(result.get(title_field) for result in payload["results"])
    assert all(result.get(date_field) for result in payload["results"])
    assert_results_are_rendered(discover_page, payload, title_field=title_field)
