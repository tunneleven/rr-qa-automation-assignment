"""Individual filter scenarios and their user-visible results."""

import pytest
from playwright.sync_api import expect

from pages.discover_page import DiscoverPage


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
    query = discover_page.response_query(response)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/discover/movie"
    assert query["with_genres"] == [genre_id]
    assert discover_page.selected_values("Genre") == [genre]
    assert payload["results"]
    assert all(
        genre_id in {str(value) for value in result["genre_ids"]} for result in payload["results"]
    )
    expect(discover_page.result_cards).to_have_count(len(payload["results"]))
    assert all(discover_page.card_titles())


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
    query = discover_page.response_query(response)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/discover/movie"
    assert set(query["with_genres"][0].split(",")) == {"28", "35"}
    assert set(discover_page.selected_values("Genre")) == {"Action", "Comedy"}
    assert payload["results"]
    expect(discover_page.result_cards).to_have_count(len(payload["results"]))
    assert all(discover_page.card_titles())


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.api
def test_tv_genre_filter_uses_tv_endpoint_and_tv_fields(
    discover_page: DiscoverPage,
) -> None:
    """A genre filter for TV Shows uses TV results and TV-specific fields."""
    discover_page.open()
    discover_page.select_type("TV Shows")
    response = discover_page.select_genre("Drama")
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/discover/tv"
    assert discover_page.response_query(response)["with_genres"] == ["18"]
    assert discover_page.selected_value("Type") == "TV Shows"
    assert discover_page.selected_values("Genre") == ["Drama"]
    assert payload["results"]
    assert all(result.get("name") and result.get("first_air_date") for result in payload["results"])
    assert discover_page.card_titles() == [result["name"] for result in payload["results"]]
    expect(discover_page.result_cards).to_have_count(len(payload["results"]))


@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize(
    "stars",
    [
        pytest.param(1, id="one-star"),
        pytest.param(4, id="four-stars"),
        pytest.param(5, id="five-stars"),
    ],
)
def test_rating_filter_renders_results_at_or_above_selected_boundary(
    discover_page: DiscoverPage,
    stars: int,
) -> None:
    """Selecting a rating sends the lower bound and renders matching results."""
    discover_page.open()
    response = discover_page.select_rating(stars)
    query = discover_page.response_query(response)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/discover/movie"
    assert query["vote_average.gte"] == [str(stars)]
    assert query["vote_average.lte"] == ["5"]
    assert payload["results"]
    assert all(result["vote_average"] >= stars for result in payload["results"])
    expect(discover_page.result_cards).to_have_count(len(payload["results"]))
    assert all(discover_page.card_titles())


@pytest.mark.regression
@pytest.mark.ui
def test_search_filter_renders_matching_movie_titles(discover_page: DiscoverPage) -> None:
    """A partial title search renders the same movie titles returned by the API."""
    discover_page.open()
    response = discover_page.search("Batman")
    query = discover_page.response_query(response)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/search/movie"
    assert query["query"] == ["Batman"]
    assert payload["total_results"] > 0
    assert discover_page.card_titles() == [result["title"] for result in payload["results"]]
    expect(discover_page.result_cards).to_have_count(len(payload["results"]))


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
    query = discover_page.response_query(response)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/search/movie"
    assert query["query"] == [query_text]
    assert payload["total_results"] > 0
    assert discover_page.card_titles() == [result["title"] for result in payload["results"]]
    expect(discover_page.result_cards).to_have_count(len(payload["results"]))


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
    query = discover_page.response_query(response)
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert discover_page.response_path(response) == "/3/discover/movie"
    assert discover_page.selected_years() == ["2020", "2024"]
    assert query["release_date.gte"] == ["2020-01-01"]
    assert query["release_date.lte"] == ["2024-12-31"]
    assert payload["results"]
    assert all(2020 <= int(result["release_date"][:4]) <= 2024 for result in payload["results"])

    visible_years = []
    for metadata in discover_page.card_metadata():
        visible_year = metadata.rsplit(", ", maxsplit=1)[-1]
        assert visible_year.isdigit()
        visible_years.append(int(visible_year))
    assert all(2020 <= year <= 2024 for year in visible_years)
    expect(discover_page.result_cards).to_have_count(len(payload["results"]))


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
    payload = discover_page.response_json(response)

    assert response.status == 200
    assert payload["total_results"] == 0
    expect(discover_page.no_results_message).to_be_visible()
    expect(discover_page.result_cards).to_have_count(0)
    assert not discover_page.error_message.is_visible()


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
    query = discover_page.response_query(response)

    assert discover_page.selected_years() == ["2025", "2025"]
    assert query["release_date.gte"] == ["2025-01-01"]
    assert query["release_date.lte"] == ["2025-12-31"]
    assert all(metadata.endswith(", 2025") for metadata in discover_page.card_metadata())
