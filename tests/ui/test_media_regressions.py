"""Media-data boundary and media-type search regressions."""

import pytest
from playwright.sync_api import Route, expect

from pages.discover_page import DiscoverPage

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
    reason="BUG-004: a null poster path renders a broken image instead of a fallback",
)
def test_missing_poster_result_uses_a_user_facing_fallback(
    discover_page: DiscoverPage,
) -> None:
    """Records without posters keep their content without broken images."""
    discover_page.open()
    discover_page.page.route("**/3/search/movie**", fulfill_missing_poster_search)
    try:
        response = discover_page.search("__qa_missing_poster_boundary__")
    finally:
        discover_page.page.unroute("**/3/search/movie**", fulfill_missing_poster_search)

    payload = discover_page.response_json(response)
    missing_poster_results = [
        result for result in payload["results"] if result.get("poster_path") is None
    ]

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/search/movie"
    assert discover_page.response_query(response)["query"] == ["__qa_missing_poster_boundary__"]
    assert len(missing_poster_results) >= 2
    expect(discover_page.result_items).to_have_count(len(payload["results"]))
    assert discover_page.card_titles() == [result["title"] for result in payload["results"]]

    for index, result in enumerate(payload["results"]):
        if result.get("poster_path") is None:
            poster = discover_page.result_items.nth(index).locator('img[alt="Movie Poster"]')
            assert not poster.count() or poster.first.evaluate(
                "image => image.complete && image.naturalWidth > 0"
            )


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
@pytest.mark.xfail(
    strict=True,
    reason="BUG-006: TV search calls the movie endpoint and renders movie fields in TV cards",
)
def test_tv_search_uses_tv_endpoint_and_renders_tv_fields(
    discover_page: DiscoverPage,
) -> None:
    """TV search uses TV response fields and gives every card a title."""
    discover_page.open()
    discover_page.select_type("TV Shows")
    response = discover_page.search("Batman")
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/search/tv"
    assert discover_page.response_query(response)["query"] == ["Batman"]
    assert payload["results"]
    assert all(result.get("name") and result.get("first_air_date") for result in payload["results"])
    expect(discover_page.result_items).to_have_count(len(payload["results"]))
    assert discover_page.card_titles() == [result["name"] for result in payload["results"]]
    assert all(discover_page.card_titles())
