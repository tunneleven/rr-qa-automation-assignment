"""Page object for the TMDB Discover application."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Locator, Page, Response

LOGGER = logging.getLogger(__name__)

API_HOST = "api.themoviedb.org"
API_TIMEOUT_MS = 60_000
UI_TIMEOUT_MS = 30_000


class DiscoverPage:
    """Expose user-facing actions and stable locators for the discovery page."""

    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def search_input(self) -> Locator:
        """Return the visible title search field."""
        return self.page.get_by_placeholder("SEARCH", exact=True)

    @property
    def result_items(self) -> Locator:
        """Return result card containers, including cards without a poster image."""
        return self.page.locator("div.grid").first.locator(":scope > div")

    @property
    def result_cards(self) -> Locator:
        """Return result card containers, regardless of poster availability."""
        return self.result_items

    @property
    def poster_images(self) -> Locator:
        """Return poster images rendered inside result cards."""
        return self.result_items.locator('img[alt="Movie Poster"]')

    @property
    def error_message(self) -> Locator:
        """Return the application-level error message, when it is rendered."""
        return self.page.get_by_text("Something went wrong! Please try again later.", exact=False)

    @property
    def no_results_message(self) -> Locator:
        """Return the empty-search message, when it is rendered."""
        return self.page.get_by_text("No results found.", exact=True)

    def open(self, path: str = "/") -> Response:
        """Open the application and wait for the initial popular-movies response."""
        LOGGER.info("Opening application path: %s", path)
        with self.page.expect_response(
            lambda response: self._is_api_response(response, "/3/movie/popular"),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self.page.goto(path, wait_until="domcontentloaded", timeout=API_TIMEOUT_MS)

        response = response_info.value
        self.wait_for_cards()
        return response

    def open_direct(self, path: str) -> Response | None:
        """Navigate directly to a client-side route without assuming it exists."""
        LOGGER.info("Opening direct application path: %s", path)
        return self.page.goto(path, wait_until="domcontentloaded", timeout=API_TIMEOUT_MS)

    def navigate_category(self, category: str) -> Response:
        """Click an in-app category and return its API response."""
        endpoints = {
            "Popular": "/3/movie/popular",
            "Trend": "/3/trending/movie/week",
            "Newest": "/3/movie/now_playing",
            "Top rated": "/3/movie/top_rated",
        }
        try:
            endpoint = endpoints[category]
        except KeyError as exc:
            raise ValueError(f"Unsupported category: {category}") from exc

        LOGGER.info("Navigating to category: %s", category)
        with self.page.expect_response(
            lambda response: self._is_api_response(response, endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self.page.get_by_role("link", name=category, exact=True).click()

        response = response_info.value
        self.wait_for_result_state()
        return response

    def select_type(self, type_name: str) -> Response:
        """Select Movie or TV Shows and return the resulting popular response."""
        endpoints = {"Movie": "/3/movie/popular", "TV Shows": "/3/tv/popular"}
        try:
            endpoint = endpoints[type_name]
        except KeyError as exc:
            raise ValueError(f"Unsupported type: {type_name}") from exc

        LOGGER.info("Selecting media type: %s", type_name)
        with self.page.expect_response(
            lambda response: self._is_api_response(response, endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self._choose_option("Type", type_name)

        response = response_info.value
        self.wait_for_result_state()
        return response

    def select_genre(self, genre: str) -> Response:
        """Select a genre and return the resulting discover response."""
        endpoint = self._discover_endpoint()
        LOGGER.info("Selecting genre: %s", genre)
        with self.page.expect_response(
            lambda response: self._is_api_response(response, endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self._choose_option("Genre", genre)

        response = response_info.value
        self.wait_for_result_state()
        return response

    def select_rating(self, stars: int) -> Response:
        """Select a rating boundary and return the resulting discover response."""
        if stars not in range(1, 6):
            raise ValueError("Rating must be between 1 and 5 stars")

        endpoint = self._discover_endpoint()
        LOGGER.info("Selecting rating: %s stars", stars)
        with self.page.expect_response(
            lambda response: self._is_api_response(response, endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self.page.locator(
                f'ul[role="radiogroup"] [role="radio"][aria-posinset="{stars}"]'
            ).click()

        response = response_info.value
        self.wait_for_result_state()
        return response

    def search(self, query: str) -> Response:
        """Search for a title and return the resulting search response."""
        LOGGER.info("Searching for title: %s", query)
        with self.page.expect_response(
            self._is_search_api_response,
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self.search_input.fill(query)

        response = response_info.value
        self.wait_for_result_state()
        return response

    def select_year_start(self, year: int) -> Response:
        """Select the start year and return the resulting discover response."""
        return self._select_year(year, position=0)

    def select_year_end(self, year: int) -> Response:
        """Select the end year and return the resulting discover response."""
        return self._select_year(year, position=1)

    def try_select_year(self, year: int, position: int) -> None:
        """Attempt a year selection without waiting for a response.

        This is useful for verifying that an invalid range cannot change state.
        """
        if position not in (0, 1):
            raise ValueError("Year position must be 0 (start) or 1 (end)")
        year_controls = self._year_row().locator(":scope > div")
        self._choose_option_from_control(year_controls.nth(position), str(year))

    def selected_value(self, label: str) -> str:
        """Return the selected single value for a labeled React Select control."""
        value = self._control_for(label).locator('div[class*="-singleValue"]')
        return value.inner_text()

    def selected_values(self, label: str) -> list[str]:
        """Return selected values for a single- or multi-select control."""
        control = self._control_for(label)
        multi_values = control.locator('div[class*="-multiValue"]')
        if multi_values.count():
            return [
                multi_values.nth(index).locator(":scope > div").first.inner_text()
                for index in range(multi_values.count())
            ]
        return [self.selected_value(label)]

    def selected_years(self) -> list[str]:
        """Return the visible start and end year values."""
        return self._year_row().locator('div[class*="-singleValue"]').all_inner_texts()

    def pagination_page_numbers(self) -> list[int]:
        """Return all numeric page buttons currently exposed by the UI."""
        labels = self.page.locator('a[role="button"][aria-label^="Page "]').evaluate_all(
            "elements => elements.map(element => element.getAttribute('aria-label'))"
        )
        page_numbers = []
        for label in labels:
            if not isinstance(label, str):
                continue
            match = re.fullmatch(r"Page (\d+)(?: is your current page)?", label)
            if match:
                page_numbers.append(int(match.group(1)))
        return page_numbers

    def select_page(self, page_number: int, endpoint: str | None = None) -> Response:
        """Select a numeric pagination control and return its listing response."""
        endpoint = endpoint or self._listing_endpoint()
        LOGGER.info("Selecting page: %s", page_number)
        with self.page.expect_response(
            lambda response: self._is_api_response(response, endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self.page.get_by_role(
                "button",
                name=re.compile(rf"^Page {page_number}(?: is your current page)?$"),
            ).click()

        response = response_info.value
        self.wait_for_result_state()
        return response

    def next_page(self, endpoint: str | None = None) -> Response:
        """Move to the next page and return its listing response."""
        return self._select_pagination_control("Next page", endpoint)

    def previous_page(self, endpoint: str | None = None) -> Response:
        """Move to the previous page and return its listing response."""
        return self._select_pagination_control("Previous page", endpoint)

    def current_page_number(self) -> int:
        """Return the numeric page marked as current by the pagination control."""
        label = self.page.locator('a[role="button"][aria-current="page"]').get_attribute(
            "aria-label"
        )
        if not label:
            raise AssertionError("No current pagination page is exposed")
        match = re.fullmatch(r"Page (\d+) is your current page", label)
        if not match:
            raise AssertionError(f"Unexpected current-page label: {label}")
        return int(match.group(1))

    def card_titles(self) -> list[str]:
        """Return the title paragraph from every rendered result card."""
        return [card.locator("p").first.inner_text() for card in self._card_list()]

    def card_metadata(self) -> list[str]:
        """Return the metadata paragraph from every rendered result card."""
        return [card.locator("p").nth(1).inner_text() for card in self._card_list()]

    def wait_for_cards(self) -> None:
        """Wait until at least one result card is rendered."""
        self.result_items.first.wait_for(state="visible", timeout=UI_TIMEOUT_MS)

    def wait_for_result_state(self) -> None:
        """Wait until results, an empty state, or the app error state is visible."""
        result_state = self.result_items.first.or_(self.no_results_message).or_(self.error_message)
        result_state.wait_for(state="visible", timeout=UI_TIMEOUT_MS)

    def response_query(self, response: Response) -> dict[str, list[str]]:
        """Return decoded query parameters from an API response URL."""
        return parse_qs(urlparse(response.url).query)

    @staticmethod
    def response_path(response: Response) -> str:
        """Return the path portion of an API response URL."""
        return urlparse(response.url).path

    @staticmethod
    def response_json(response: Response) -> dict[str, Any]:
        """Decode an API JSON response for assertions in tests."""
        return response.json()

    def _select_pagination_control(self, label: str, endpoint: str | None) -> Response:
        endpoint = endpoint or self._listing_endpoint()
        with self.page.expect_response(
            lambda response: self._is_api_response(response, endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self.page.get_by_role("button", name=label, exact=True).click()

        response = response_info.value
        self.wait_for_result_state()
        return response

    def _select_year(self, year: int, position: int) -> Response:
        endpoint = self._discover_endpoint()
        LOGGER.info("Selecting %s year: %s", "start" if position == 0 else "end", year)
        with self.page.expect_response(
            lambda response: self._is_api_response(response, endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            year_controls = self._year_row().locator(":scope > div")
            self._choose_option_from_control(year_controls.nth(position), str(year))

        response = response_info.value
        self.wait_for_result_state()
        return response

    def _choose_option(self, label: str, option: str) -> None:
        self._choose_option_from_control(self._control_for(label), option)

    def _choose_option_from_control(self, control: Locator, option: str) -> None:
        control.click()
        option_locator = self.page.locator('[id*="-option-"]').filter(has_text=option)
        option_locator.get_by_text(option, exact=True).click()

    def _control_for(self, label: str) -> Locator:
        label_node = self.page.locator("aside p").filter(has_text=label).first
        return label_node.locator("xpath=following-sibling::*[1]")

    def _year_row(self) -> Locator:
        label_node = self.page.locator("aside p").filter(has_text="Year").first
        return label_node.locator("xpath=following-sibling::*[1]")

    def _discover_endpoint(self) -> str:
        type_name = self.selected_value("Type")
        return "/3/discover/tv" if type_name == "TV Shows" else "/3/discover/movie"

    def _card_list(self) -> list[Locator]:
        return [self.result_items.nth(index) for index in range(self.result_items.count())]

    def _listing_endpoint(self) -> str:
        endpoints = {
            "/popular": "/3/movie/popular",
            "/trend": "/3/trending/movie/week",
            "/new": "/3/movie/now_playing",
            "/top": "/3/movie/top_rated",
        }
        return endpoints.get(urlparse(self.page.url).path, "/3/movie/popular")

    @staticmethod
    def _is_api_response(response: Response, path: str) -> bool:
        parsed_url = urlparse(response.url)
        return (
            parsed_url.hostname == API_HOST
            and parsed_url.path == path
            and response.request.method == "GET"
        )

    @staticmethod
    def _is_search_api_response(response: Response) -> bool:
        parsed_url = urlparse(response.url)
        return (
            parsed_url.hostname == API_HOST
            and parsed_url.path in {"/3/search/movie", "/3/search/tv"}
            and response.request.method == "GET"
        )
