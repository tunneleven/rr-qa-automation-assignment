"""Page object for the TMDB Discover application."""

import logging

from playwright.sync_api import Page

LOGGER = logging.getLogger(__name__)


class DiscoverPage:
    """Expose user-facing actions for the movie and TV discovery page.

    Locators and filter actions will be added after DOM/network reconnaissance.
    Assertions intentionally remain in tests so failures describe expected behavior.
    """

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self, path: str = "/") -> None:
        """Navigate relative to pytest's configured base URL."""
        LOGGER.info("Opening application path: %s", path)
        self.page.goto(path)
