"""Page object for the TMDB Discover application."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import Locator, Page, Response
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.endpoints import (
    API_HOST,
    CATEGORIES,
    CATEGORY_BY_LABEL,
    CATEGORY_BY_ROUTE,
    DISCOVER_MOVIE,
    DISCOVER_TV,
    MEDIA_TYPE_ENDPOINTS,
    POPULAR_MOVIE,
    SEARCH_MOVIE,
    SEARCH_TV,
    TV_TYPE,
    Category,
)
from utils.structured_logging import log_action

LOGGER = logging.getLogger(__name__)

API_TIMEOUT_MS = 60_000
UI_TIMEOUT_MS = 30_000
SETTLE_TIMEOUT_MS = 5_000

POSTER_SELECTOR = 'img[alt="Movie Poster"]'

CARD_TITLE_INDEX = 0
CARD_METADATA_INDEX = 1


class DiscoverPage:
    """Expose user-facing actions and stable locators for the discovery page."""

    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def search_input(self) -> Locator:
        """Return the visible title search field."""
        return self.page.get_by_placeholder("SEARCH", exact=True)

    @property
    def result_cards(self) -> Locator:
        """Return result card containers, including cards without a poster image."""
        return self.page.locator("div.grid").first.locator(":scope > div")

    @property
    def poster_images(self) -> Locator:
        """Return poster images rendered inside result cards."""
        return self.result_cards.locator(POSTER_SELECTOR)

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
        log_action(LOGGER, "open", path=path)
        with self.page.expect_response(
            lambda response: self.is_api_response(response, POPULAR_MOVIE),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self.page.goto(path, wait_until="domcontentloaded", timeout=API_TIMEOUT_MS)

        response = response_info.value
        self.wait_for_cards()
        return response

    def open_direct(self, path: str) -> Response | None:
        """Navigate directly to a client-side route without assuming it exists."""
        log_action(LOGGER, "open_direct", path=path)
        return self.page.goto(path, wait_until="domcontentloaded", timeout=API_TIMEOUT_MS)

    def reload(self) -> Response | None:
        """Reload the current route without assuming the application loads again."""
        log_action(LOGGER, "reload", url=self.page.url)
        return self.page.reload(wait_until="domcontentloaded", timeout=API_TIMEOUT_MS)

    def navigate_category(self, category: str) -> Response:
        """Click an in-app category and return its API response."""
        target = self._category(category)
        log_action(LOGGER, "navigate_category", category=target.label)
        with self.page.expect_response(
            lambda response: self.is_api_response(response, target.endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self.page.get_by_role("link", name=target.label, exact=True).click()

        response = response_info.value
        self.wait_for_result_state()
        return response

    def navigate_category_fresh(self, category: str) -> Response:
        """Click a category and guarantee a listing request, even when it is active.

        The application requests a listing only when the active category changes,
        so an already-active category is first left through a different one.
        """
        target = self._category(category)
        if self.active_category() == target:
            detour = next(other for other in CATEGORIES if other != target)
            self.navigate_category(detour.label)
        return self.navigate_category(target.label)

    def select_type(self, type_name: str) -> Response:
        """Select Movie or TV Shows and return the resulting popular response."""
        endpoint = self._type_endpoint(type_name)
        log_action(LOGGER, "select_type", type=type_name)
        with self.page.expect_response(
            lambda response: self.is_api_response(response, endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self._choose_option("Type", type_name)

        response = response_info.value
        self.wait_for_result_state()
        return response

    def select_type_fresh(self, type_name: str) -> Response:
        """Select a media type and guarantee a request, even when it is selected.

        Like the category links, the type control requests a listing only when
        the selection changes, so an active type is left through the other one.
        """
        self._type_endpoint(type_name)
        if self.selected_value("Type") == type_name:
            detour = next(other for other in MEDIA_TYPE_ENDPOINTS if other != type_name)
            self.select_type(detour)
        return self.select_type(type_name)

    def select_genre(self, genre: str) -> Response:
        """Select a genre and return the resulting discover response."""
        endpoint = self._discover_endpoint()
        log_action(LOGGER, "select_genre", genre=genre)
        with self.page.expect_response(
            lambda response: self.is_api_response(response, endpoint),
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
        log_action(LOGGER, "select_rating", stars=stars)
        with self.page.expect_response(
            lambda response: self.is_api_response(response, endpoint),
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
        log_action(LOGGER, "search", query=query)
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
        log_action(LOGGER, "try_select_year", year=year, position=position)
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
        multi_value_count = multi_values.count()
        if multi_value_count:
            return [
                multi_values.nth(index).locator(":scope > div").first.inner_text()
                for index in range(multi_value_count)
            ]
        return [self.selected_value(label)]

    def selected_years(self) -> list[str]:
        """Return the visible start and end year values."""
        return self._year_row().locator('div[class*="-singleValue"]').all_inner_texts()

    def active_category(self) -> Category | None:
        """Return the category matching the current route, when there is one."""
        return CATEGORY_BY_ROUTE.get(urlparse(self.page.url).path)

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
        log_action(LOGGER, "select_page", page=page_number, endpoint=endpoint)
        with self.page.expect_response(
            lambda response: self.is_api_response(response, endpoint),
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
        """Return the title line from every rendered result card."""
        return self._card_paragraphs(CARD_TITLE_INDEX)

    def card_metadata(self) -> list[str]:
        """Return the metadata line from every rendered result card."""
        return self._card_paragraphs(CARD_METADATA_INDEX)

    def card_release_years(self) -> list[str]:
        """Return the year shown at the end of every card's metadata line."""
        return [metadata.rsplit(", ", maxsplit=1)[-1] for metadata in self.card_metadata()]

    def card_poster(self, index: int) -> Locator:
        """Return the poster image of one card, which the app may not render."""
        return self.result_cards.nth(index).locator(POSTER_SELECTOR)

    def wait_for_cards(self) -> None:
        """Wait until at least one result card is rendered."""
        self.result_cards.first.wait_for(state="visible", timeout=UI_TIMEOUT_MS)

    def wait_for_result_state(self) -> None:
        """Wait until results, an empty state, or the app error state is visible."""
        result_state = self.result_cards.first.or_(self.no_results_message).or_(self.error_message)
        result_state.wait_for(state="visible", timeout=UI_TIMEOUT_MS)

    def response_query(self, response: Response) -> dict[str, list[str]]:
        """Return decoded query parameters from an API response URL."""
        return parse_qs(urlparse(response.url).query)

    @contextmanager
    def recording_responses(self, endpoint: str) -> Iterator[list[Response]]:
        """Record every API response for `endpoint` while the block runs."""
        recorded: list[Response] = []

        def record(response: Response) -> None:
            if self.is_api_response(response, endpoint):
                recorded.append(response)

        self.page.on("response", record)
        try:
            yield recorded
        finally:
            self.page.remove_listener("response", record)

    def wait_for_page_request_other_than(
        self,
        endpoint: str,
        page_number: int = 1,
    ) -> Response | None:
        """Wait briefly for a listing request that asks for an unexpected page.

        A listing can request a stale page just after the response that renders
        the results, so waiting for that specific event keeps such a request
        inside a `recording_responses` block. Returns None when none arrives.
        """

        def asks_for_another_page(response: Response) -> bool:
            if not self.is_api_response(response, endpoint):
                return False
            return self.response_query(response).get("page") != [str(page_number)]

        try:
            return self.page.wait_for_event(
                "response",
                predicate=asks_for_another_page,
                timeout=SETTLE_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError:
            return None

    @staticmethod
    def is_api_response(response: Response, path: str) -> bool:
        """Return whether the response is a TMDB API GET for the given path."""
        parsed_url = urlparse(response.url)
        return (
            parsed_url.hostname == API_HOST
            and parsed_url.path == path
            and response.request.method == "GET"
        )

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
        log_action(LOGGER, "select_pagination_control", control=label, endpoint=endpoint)
        with self.page.expect_response(
            lambda response: self.is_api_response(response, endpoint),
            timeout=API_TIMEOUT_MS,
        ) as response_info:
            self.page.get_by_role("button", name=label, exact=True).click()

        response = response_info.value
        self.wait_for_result_state()
        return response

    def _select_year(self, year: int, position: int) -> Response:
        endpoint = self._discover_endpoint()
        log_action(LOGGER, "select_year", boundary="start" if position == 0 else "end", year=year)
        with self.page.expect_response(
            lambda response: self.is_api_response(response, endpoint),
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
        return self._control_for("Year")

    @staticmethod
    def _category(label: str) -> Category:
        try:
            return CATEGORY_BY_LABEL[label]
        except KeyError as exc:
            raise ValueError(f"Unsupported category: {label}") from exc

    @staticmethod
    def _type_endpoint(type_name: str) -> str:
        try:
            return MEDIA_TYPE_ENDPOINTS[type_name]
        except KeyError as exc:
            raise ValueError(f"Unsupported type: {type_name}") from exc

    def _discover_endpoint(self) -> str:
        return DISCOVER_TV if self.selected_value("Type") == TV_TYPE else DISCOVER_MOVIE

    def _listing_endpoint(self) -> str:
        active_category = self.active_category()
        return active_category.endpoint if active_category else POPULAR_MOVIE

    def _card_paragraphs(self, index: int) -> list[str]:
        """Return one paragraph per card, addressed by its position inside the card.

        The demo markup gives card text no role, label, or test id, so paragraph
        order is the only available way to separate the title from the metadata.
        """
        return [card.locator("p").nth(index).inner_text() for card in self.result_cards.all()]

    @staticmethod
    def _is_search_api_response(response: Response) -> bool:
        parsed_url = urlparse(response.url)
        return (
            parsed_url.hostname == API_HOST
            and parsed_url.path in {SEARCH_MOVIE, SEARCH_TV}
            and response.request.method == "GET"
        )
