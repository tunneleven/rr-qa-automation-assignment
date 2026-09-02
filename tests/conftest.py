"""Shared pytest and Playwright fixtures."""

import logging

import pytest
from playwright.sync_api import Page

from pages.discover_page import DiscoverPage

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Use a consistent desktop context while preserving plugin defaults."""
    return {
        **browser_context_args,
        "locale": "en-US",
        "viewport": {"width": 1440, "height": 900},
    }


@pytest.fixture
def discover_page(page: Page) -> DiscoverPage:
    """Provide the application page object with a fresh browser context."""
    LOGGER.info("Creating Discover page object")
    return DiscoverPage(page)
