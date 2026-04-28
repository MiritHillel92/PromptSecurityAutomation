import time
import allure
import pytest
from playwright.sync_api import Page, expect


BLOCKED_SITES = [
    ("gemini.google.com", "https://gemini.google.com"),
    ("claude.ai", "https://claude.ai"),
]

ALLOWED_SITES = [
    ("chatgpt.com", "https://chatgpt.com"),
]


@allure.feature("Extension Functionality")
@allure.story("Block GenAI Applications")
@pytest.mark.flaky(reruns=2, reruns_delay=5)
@pytest.mark.parametrize("site_name,url", BLOCKED_SITES)
def test_site_is_blocked(configured_extension, screenshot_helper, page_logger, site_name, url):
    page: Page = configured_extension.new_page()
    try:
        with allure.step(f"Navigate to {site_name} and wait for block redirect"):
            page_logger(f"Navigating to {url}")
            t0 = time.monotonic()
            page.goto(url)
            page_logger("Waiting for redirect to pageOverlay.html")
            page.wait_for_url("**/pageOverlay.html**", timeout=60000)
            page_logger(f"Redirected to block page in {time.monotonic() - t0:.2f}s — URL: {page.url}")
            t1 = time.monotonic()
            expect(page.locator("#title-text")).to_be_visible(timeout=10000)
            page_logger(f"Block overlay title visible in {time.monotonic() - t1:.2f}s")

        with allure.step("Assert API block decision is reflected in redirect URL"):
            current_url = page.url
            assert "type=blockPage" in current_url, (
                f"Expected 'type=blockPage' in redirect URL, got: {current_url!r}"
            )
            assert f"domain={site_name}" in current_url, (
                f"Expected 'domain={site_name}' in redirect URL, got: {current_url!r}"
            )
            page_logger("URL assertions passed: type=blockPage and correct domain present")

        with allure.step(f"Capture screenshot of {site_name}"):
            screenshot_helper(page, f"{site_name.replace('.', '_')}_blocked.png")
            page_logger("Screenshot captured")
    finally:
        page.close()


@allure.feature("Extension Functionality")
@allure.story("Allow GenAI Applications")
@pytest.mark.parametrize("site_name,url", ALLOWED_SITES)
def test_site_is_allowed(configured_extension, screenshot_helper, page_logger, site_name, url):
    page: Page = configured_extension.new_page()
    try:
        with allure.step(f"Navigate to {site_name}"):
            page_logger(f"Navigating to {url}")
            t0 = time.monotonic()
            page.goto(url)
            page.wait_for_load_state("networkidle", timeout=30000)
            page_logger(f"Page loaded in {time.monotonic() - t0:.2f}s — URL: {page.url}")

        with allure.step("Assert site was not redirected to block page"):
            current_url = page.url
            assert "pageOverlay.html" not in current_url, (
                f"Site was unexpectedly blocked, redirected to: {current_url!r}"
            )
            assert site_name in current_url, (
                f"Expected to stay on {site_name}, got: {current_url!r}"
            )
            page_logger("URL assertions passed: site not redirected to block page")

        with allure.step("Verify block overlay is not shown"):
            expect(page.locator("#title-text")).not_to_be_visible(timeout=5000)
            page_logger("Block overlay is not visible — site is allowed")

        with allure.step(f"Capture screenshot of {site_name}"):
            screenshot_helper(page, f"{site_name.replace('.', '_')}_allowed.png")
            page_logger("Screenshot captured")
    finally:
        page.close()
