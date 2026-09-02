"""Direct-navigation and refresh regression scenarios."""

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage
from pages.endpoints import CATEGORIES, RESULTS_PER_PAGE
from tests.known_defects import KnownDefectError

DIRECT_ROUTE_CASES = tuple(
    pytest.param(category.route, id=category.test_id) for category in CATEGORIES
)


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize("route", DIRECT_ROUTE_CASES)
@pytest.mark.xfail(
    strict=True,
    raises=KnownDefectError,
    reason="BUG-002: direct category routes return the hosting provider's 404 page",
)
def test_category_route_supports_direct_navigation(
    discover_page: DiscoverPage,
    route: str,
) -> None:
    """A valid category route loads the application when opened directly."""
    application_response = discover_page.page.request.get("/")
    assert application_response.status == 200

    document_response = discover_page.open_direct(route)
    assert document_response is not None
    if document_response.status == 404:
        raise KnownDefectError(f"BUG-002: direct navigation to {route} returned HTTP 404")
    assert document_response.status == 200
    discover_page.wait_for_cards()
    assert discover_page.page.url.endswith(route)
    expect(discover_page.result_cards).to_have_count(RESULTS_PER_PAGE)
    assert all(discover_page.card_titles())
    expect(discover_page.error_message).not_to_be_visible()

    reload_response = discover_page.reload()

    assert reload_response is not None
    if reload_response.status == 404:
        raise KnownDefectError(f"BUG-002: refreshing {route} returned HTTP 404")
    assert reload_response.status == 200
    discover_page.wait_for_cards()
    assert discover_page.page.url.endswith(route)
    expect(discover_page.result_cards).to_have_count(RESULTS_PER_PAGE)
    expect(discover_page.error_message).not_to_be_visible()
