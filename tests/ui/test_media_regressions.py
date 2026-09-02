"""Media-data boundary and media-type search regressions."""

import pytest
from playwright.sync_api import Route, expect

from pages.discover_page import DiscoverPage
from pages.endpoints import SEARCH_MOVIE, SEARCH_TV, TV_TYPE
from tests.assertions import (
    assert_listing_response,
    assert_query_parameters,
    assert_results_are_rendered,
)
from tests.known_defects import KnownDefectError

SEARCH_MOVIE_PATTERN = f"**{SEARCH_MOVIE}**"

MISSING_POSTER_SEARCH_QUERY = "__qa_missing_poster_boundary__"

MISSING_POSTER_SEARCH_PAYLOAD = {
    "page": 1,
    "results": [
        {
            "id": 900001,
            "title": "Posterless boundary case A",
            "original_title": "Posterless boundary case A",
            "poster_path": None,
            "genre_ids": [28],
            "release_date": "2024-01-01",
            "vote_average": 6.5,
            "vote_count": 100,
            "popularity": 1.0,
            "adult": False,
            "backdrop_path": None,
            "original_language": "en",
            "video": False,
        },
        {
            "id": 900002,
            "title": "Posterless boundary case B",
            "original_title": "Posterless boundary case B",
            "poster_path": None,
            "genre_ids": [35],
            "release_date": "2023-01-01",
            "vote_average": 7.0,
            "vote_count": 100,
            "popularity": 1.0,
            "adult": False,
            "backdrop_path": None,
            "original_language": "en",
            "video": False,
        },
    ],
    "total_pages": 1,
    "total_results": 2,
}


def fulfill_missing_poster_search(route: Route) -> None:
    """Return multiple valid records without posters for a deterministic boundary check."""
    route.fulfill(
        status=200,
        headers={"access-control-allow-origin": "*"},
        json=MISSING_POSTER_SEARCH_PAYLOAD,
    )


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    raises=KnownDefectError,
    reason="BUG-004: a null poster path renders a broken image instead of a fallback",
)
def test_missing_poster_result_uses_a_user_facing_fallback(
    discover_page: DiscoverPage,
) -> None:
    """Records without posters keep their content without broken images."""
    discover_page.open()
    discover_page.page.route(SEARCH_MOVIE_PATTERN, fulfill_missing_poster_search)
    try:
        response = discover_page.search(MISSING_POSTER_SEARCH_QUERY)
    finally:
        discover_page.page.unroute(SEARCH_MOVIE_PATTERN, fulfill_missing_poster_search)

    payload = assert_listing_response(discover_page, response, SEARCH_MOVIE)
    results = payload["results"]
    missing_poster_indexes = [
        index for index, result in enumerate(results) if result.get("poster_path") is None
    ]

    assert_query_parameters(discover_page, response, {"query": MISSING_POSTER_SEARCH_QUERY})
    assert len(missing_poster_indexes) >= 2
    assert_results_are_rendered(discover_page, payload, title_field="title")

    broken_poster_indexes = []
    for index in missing_poster_indexes:
        poster = discover_page.card_poster(index)
        if not poster.count():
            continue

        image = poster.first
        raw_source = image.get_attribute("src")
        expect(image).to_be_visible()
        expect(image).to_have_js_property("complete", True)
        natural_width = image.evaluate("element => element.naturalWidth")

        if raw_source == "" and natural_width == 0:
            broken_poster_indexes.append(index)
            continue

        assert raw_source, f"poster {index} rendered without a usable source"
        assert natural_width > 0, f"poster {index} did not load its nonempty source: {raw_source}"

    if broken_poster_indexes:
        raise KnownDefectError(
            "BUG-004: null posters rendered visible images with empty sources "
            f"and zero natural width at indexes {broken_poster_indexes}"
        )


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    raises=KnownDefectError,
    reason="BUG-006: TV search calls the movie endpoint and renders movie fields in TV cards",
)
def test_tv_search_uses_tv_endpoint_and_renders_tv_fields(
    discover_page: DiscoverPage,
) -> None:
    """TV search uses TV response fields and gives every card a title."""
    discover_page.open()
    discover_page.select_type(TV_TYPE)
    response = discover_page.search("Batman")
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.selected_value("Type") == TV_TYPE
    assert_query_parameters(discover_page, response, {"query": "Batman"})

    response_path = discover_page.response_path(response)
    if response_path == SEARCH_MOVIE:
        assert payload["results"]
        assert all(
            result.get("title") and result.get("release_date") for result in payload["results"]
        )
        expect(discover_page.result_cards).to_have_count(len(payload["results"]))
        raise KnownDefectError("BUG-006: TV search sent its request to the movie endpoint")

    payload = assert_listing_response(discover_page, response, SEARCH_TV)
    assert_results_are_rendered(discover_page, payload, title_field="name")
    assert all(result.get("name") and result.get("first_air_date") for result in payload["results"])
