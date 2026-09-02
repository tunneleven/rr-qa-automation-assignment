"""Shared pytest and Playwright fixtures."""

import logging

import pytest
from playwright.sync_api import Page

from pages.discover_page import DiscoverPage
from utils.structured_logging import log_action

# Failures raised inside the shared helpers keep pytest's detailed assertion output.
pytest.register_assert_rewrite("tests.assertions")

LOGGER = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict) -> dict:
    """Use Chromium networking settings that keep the external API reliable."""
    args = list(browser_type_launch_args.get("args", []))
    if "--disable-ipv6" not in args:
        args.append("--disable-ipv6")
    return {**browser_type_launch_args, "args": args}


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
    log_action(LOGGER, "create_page_object", page_object="DiscoverPage")
    return DiscoverPage(page)
