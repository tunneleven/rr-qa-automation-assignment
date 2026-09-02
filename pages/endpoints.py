"""Application routes and TMDB endpoints shared by page objects and tests.

Keeping these in one module means a route or endpoint change is a single edit
instead of a hunt through page objects and parametrized test cases.
"""

from __future__ import annotations

from dataclasses import dataclass

API_HOST = "api.themoviedb.org"
API_BASE_URL = f"https://{API_HOST}"

RESULTS_PER_PAGE = 20
"""Number of records TMDB returns for a full listing page."""

SERVICE_MAX_PAGE = 500
"""Highest page number the TMDB listing endpoints accept."""

POPULAR_MOVIE = "/3/movie/popular"
POPULAR_TV = "/3/tv/popular"
DISCOVER_MOVIE = "/3/discover/movie"
DISCOVER_TV = "/3/discover/tv"
SEARCH_MOVIE = "/3/search/movie"
SEARCH_TV = "/3/search/tv"

MOVIE_TYPE = "Movie"
TV_TYPE = "TV Shows"

MEDIA_TYPE_ENDPOINTS = {
    MOVIE_TYPE: POPULAR_MOVIE,
    TV_TYPE: POPULAR_TV,
}


@dataclass(frozen=True)
class Category:
    """A category link, the route it opens, and the listing endpoint it calls."""

    label: str
    route: str
    endpoint: str

    @property
    def test_id(self) -> str:
        """Return the label as a pytest parameter identifier."""
        return self.label.lower().replace(" ", "-")


CATEGORIES: tuple[Category, ...] = (
    Category("Popular", "/popular", POPULAR_MOVIE),
    Category("Trend", "/trend", "/3/trending/movie/week"),
    Category("Newest", "/new", "/3/movie/now_playing"),
    Category("Top rated", "/top", "/3/movie/top_rated"),
)

CATEGORY_BY_LABEL = {category.label: category for category in CATEGORIES}
CATEGORY_BY_ROUTE = {category.route: category for category in CATEGORIES}
