"""Critical application availability and initial-result scenarios."""

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage


@pytest.mark.smoke
@pytest.mark.ui
def test_homepage_loads_default_movie_results(discover_page: DiscoverPage) -> None:
    """The default entry point loads a usable page of movie results."""
    response = discover_page.open()

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/movie/popular"
    assert discover_page.page.url.endswith("/popular")
    expect(discover_page.page).to_have_title("Discover")
    expect(discover_page.result_cards).to_have_count(20)
    assert all(discover_page.card_titles())
    assert not discover_page.error_message.is_visible()

    for category in ("Popular", "Trend", "Newest", "Top rated"):
        expect(discover_page.page.get_by_role("link", name=category, exact=True)).to_be_visible()
