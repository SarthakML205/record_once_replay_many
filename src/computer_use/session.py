from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from playwright.sync_api import Browser, Page, sync_playwright

from src.computer_use.browser import observe, perform, wait_quiet
from src.guardrails.policy import url_allowed


class ComputerSession:
    def __init__(self, page: Page):
        self.page = page

    @property
    def url(self) -> str:
        return self.page.url

    def observe(self) -> dict:
        return observe(self.page)

    def act(self, action: str, locator=None, value: str | None = None, url: str | None = None) -> str:
        result = perform(self.page, action, locator, value, url)
        wait_quiet(self.page)
        return result


@contextmanager
def launch_session(start_url: str, *, headless: bool = True) -> Iterator[ComputerSession]:
    if not url_allowed(start_url):
        raise ValueError(f"Start URL is not allowlisted: {start_url}")
    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.goto(start_url, wait_until="domcontentloaded")
        try:
            yield ComputerSession(page)
        finally:
            context.close()
            browser.close()
