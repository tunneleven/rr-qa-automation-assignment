"""Critical application availability and initial-result scenarios."""

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage
from pages.endpoints import CATEGORIES, POPULAR_MOVIE, RESULTS_PER_PAGE
from tests.assertions import assert_listing_response, assert_results_are_rendered


@pytest.mark.smoke
@pytest.mark.ui
def test_homepage_loads_default_movie_results(discover_page: DiscoverPage) -> None:
    """The default entry point loads a usable page of movie results."""
    response = discover_page.open()
    payload = assert_listing_response(discover_page, response, POPULAR_MOVIE)

    assert discover_page.page.url.endswith("/popular")
    expect(discover_page.page).to_have_title("Discover")
    assert len(payload["results"]) == RESULTS_PER_PAGE
    assert_results_are_rendered(discover_page, payload)

    for category in CATEGORIES:
        category_link = discover_page.page.get_by_role("link", name=category.label, exact=True)
        expect(category_link).to_be_visible()
