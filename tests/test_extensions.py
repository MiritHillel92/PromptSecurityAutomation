import allure
import pytest
from playwright.sync_api import Page, expect

BLOCKED_SITES = [
    ("gemini.google.com", "https://gemini.google.com"),
]

ALLOWED_SITES = [
    ("chatgpt.com", "https://chatgpt.com"),
]


@allure.feature("Extension Functionality")
@allure.story("Block GenAI Applications")
@pytest.mark.parametrize("site_name,url", BLOCKED_SITES)
def test_site_is_blocked(configured_extension, screenshot_helper, site_name, url):
    page: Page = configured_extension.new_page()
    try:
        with allure.step(f"Navigate to blocked site: {site_name}"):
            page.goto(url)
            # The extension redirects the tab to a chrome-extension pageOverlay URL.
            # Wait for the URL to change away from the original site.
            page.wait_for_url(
                lambda u: "chrome-extension://" in u,
                timeout=30000,
            )
            expect(page.locator("#title-text")).to_be_visible(timeout=10000)

        with allure.step(f"Capture screenshot of {site_name}"):
            screenshot_helper(page, f"{site_name.replace('.', '_')}_blocked.png")
    finally:
        page.close()


@allure.feature("Extension Functionality")
@allure.story("Allow GenAI Applications")
@pytest.mark.parametrize("site_name,url", ALLOWED_SITES)
def test_site_is_allowed(configured_extension, screenshot_helper, site_name, url):
    page: Page = configured_extension.new_page()
    try:
        with allure.step(f"Navigate to allowed site: {site_name}"):
            page.goto(url)
            page.wait_for_selector(
                "#prompt-textarea, [data-testid='send-button']",
                state="visible",
                timeout=30000,
            )

        with allure.step(f"Capture screenshot of {site_name}"):
            screenshot_helper(page, f"{site_name.replace('.', '_')}_allowed.png")

        with allure.step("Verify access is allowed"):
            expect(page.locator("#title-text")).not_to_be_visible(timeout=5000)
    finally:
        page.close()
