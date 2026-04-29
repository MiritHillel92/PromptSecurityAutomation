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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _navigate_and_wait_for_block(page: Page, site_name: str, url: str, log):
    with allure.step(f"Navigate to {site_name} and wait for block redirect"):
        log(f"Navigating to {url}")
        t0 = time.monotonic()
        page.goto(url)
        log("Waiting for redirect to pageOverlay.html")
        page.wait_for_url("**/pageOverlay.html**", timeout=60000)
        log(f"Redirected to block page in {time.monotonic() - t0:.2f}s — URL: {page.url}")
        t1 = time.monotonic()
        expect(page.locator("#title-text")).to_be_visible(timeout=10000)
        log(f"Block overlay title visible in {time.monotonic() - t1:.2f}s")


def _assert_block_url(page: Page, site_name: str, log):
    with allure.step("Assert API block decision is reflected in redirect URL"):
        current_url = page.url
        assert "type=blockPage" in current_url, (
            f"Expected 'type=blockPage' in redirect URL, got: {current_url!r}"
        )
        assert f"domain={site_name}" in current_url, (
            f"Expected 'domain={site_name}' in redirect URL, got: {current_url!r}"
        )
        log("URL assertions passed: type=blockPage and correct domain present")


def _navigate_and_wait_for_load(page: Page, site_name: str, url: str, log):
    with allure.step(f"Navigate to {site_name}"):
        log(f"Navigating to {url}")
        t0 = time.monotonic()
        page.goto(url)
        page.wait_for_load_state("networkidle", timeout=30000)
        log(f"Page loaded in {time.monotonic() - t0:.2f}s — URL: {page.url}")


def _assert_site_not_blocked(page: Page, site_name: str, log):
    with allure.step("Assert site was not redirected to block page"):
        current_url = page.url
        assert "pageOverlay.html" not in current_url, (
            f"Site was unexpectedly blocked, redirected to: {current_url!r}"
        )
        assert site_name in current_url, (
            f"Expected to stay on {site_name}, got: {current_url!r}"
        )
        log("URL assertions passed: site not redirected to block page")


def _assert_no_block_overlay(page: Page, log):
    with allure.step("Verify block overlay is not shown"):
        expect(page.locator("#title-text")).not_to_be_visible(timeout=5000)
        log("Block overlay is not visible — site is allowed")


def _capture_screenshot(page: Page, site_name: str, suffix: str, screenshot_helper, log):
    with allure.step(f"Capture screenshot of {site_name}"):
        page.wait_for_load_state("domcontentloaded")
        screenshot_helper(page, f"{site_name.replace('.', '_')}_{suffix}.png")
        log("Screenshot captured")


# ── Tests ─────────────────────────────────────────────────────────────────────

@allure.feature("Extension Functionality")
@allure.story("Block GenAI Applications")
@pytest.mark.flaky(reruns=2, reruns_delay=5)
@pytest.mark.parametrize("site_name,url", BLOCKED_SITES)
def test_site_is_blocked(configured_extension, screenshot_helper, page_logger, site_name, url):
    page: Page = configured_extension.new_page()
    try:
        _navigate_and_wait_for_block(page, site_name, url, page_logger)
        _assert_block_url(page, site_name, page_logger)
        _capture_screenshot(page, site_name, "blocked", screenshot_helper, page_logger)
    finally:
        page.close()


@allure.feature("Extension Functionality")
@allure.story("Allow GenAI Applications")
@pytest.mark.parametrize("site_name,url", ALLOWED_SITES)
def test_site_is_allowed(configured_extension, screenshot_helper, page_logger, site_name, url):
    page: Page = configured_extension.new_page()
    try:
        _navigate_and_wait_for_load(page, site_name, url, page_logger)
        _assert_site_not_blocked(page, site_name, page_logger)
        _assert_no_block_overlay(page, page_logger)
        _capture_screenshot(page, site_name, "allowed", screenshot_helper, page_logger)
    finally:
        page.close()
