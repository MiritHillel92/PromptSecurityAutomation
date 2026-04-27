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
            # Poll for the block text via locator — avoids JS string injection which
            # Gemini rejects via Trusted Types CSP.
            expect(page.get_by_text("Access Denied", exact=False)).to_be_visible(timeout=15000)

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
            # networkidle never fires on chatgpt.com due to persistent websocket connections
            page.wait_for_load_state("load")

        with allure.step(f"Capture screenshot of {site_name}"):
            screenshot_helper(page, f"{site_name.replace('.', '_')}_allowed.png")

        with allure.step("Verify access is allowed"):
            # Use locator with retry so a slow extension injection doesn't cause a false pass
            expect(page.get_by_text("Access Denied", exact=False)).not_to_be_visible(timeout=5000)
    finally:
        page.close()
