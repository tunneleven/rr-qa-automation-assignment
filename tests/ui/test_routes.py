"""Direct-navigation and refresh regression scenarios."""

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage
from pages.endpoints import CATEGORIES, RESULTS_PER_PAGE

DIRECT_ROUTE_CASES = tuple(
    pytest.param(category.route, id=category.test_id) for category in CATEGORIES
)


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize("route", DIRECT_ROUTE_CASES)
@pytest.mark.xfail(
    strict=True,
    reason="BUG-002: direct category routes return the hosting provider's 404 page",
)
def test_category_route_supports_direct_navigation(
    discover_page: DiscoverPage,
    route: str,
) -> None:
    """A valid category route loads the application when opened directly."""
    document_response = discover_page.open_direct(route)

    assert document_response is not None
    assert document_response.status == 200
    discover_page.wait_for_cards()
    assert discover_page.page.url.endswith(route)
    expect(discover_page.result_cards).to_have_count(RESULTS_PER_PAGE)
    assert all(discover_page.card_titles())
    expect(discover_page.error_message).not_to_be_visible()

    reload_response = discover_page.reload()

    assert reload_response is not None
    assert reload_response.status == 200
    discover_page.wait_for_cards()
    assert discover_page.page.url.endswith(route)
    expect(discover_page.result_cards).to_have_count(RESULTS_PER_PAGE)
    expect(discover_page.error_message).not_to_be_visible()
