import allure
import pytest
from playwright.sync_api import Page, expect


BLOCKED_SITES = [
    ("gemini.google.com", "https://gemini.google.com"),
]

ALLOWED_SITES = [
    ("chatgpt.com", "https://chatgpt.com"),
]


def capture_rule_action(page: Page, url: str, timeout: int = 15000) -> str:
    """Navigate to url and capture the Prompt Security get-rule-action API response."""
    with page.expect_response(
        lambda r: "get-rule-action" in r.url, timeout=timeout
    ) as response_info:
        page.goto(url)

    try:
        body = response_info.value.json()
        return body.get("ruleInfo", {}).get("action")
    except Exception:
        return None


@allure.feature("Extension Functionality")
@allure.story("Block GenAI Applications")
@pytest.mark.flaky(reruns=2, reruns_delay=5)
@pytest.mark.parametrize("site_name,url", BLOCKED_SITES)
def test_site_is_blocked(configured_extension, screenshot_helper, site_name, url):
    page: Page = configured_extension.new_page()
    try:
        with allure.step(f"Navigate to {site_name} and capture API response"):
            action = capture_rule_action(page, url)
            page.wait_for_url("**/pageOverlay.html**", timeout=60000)
            expect(page.locator("#title-text")).to_be_visible(timeout=10000)

        with allure.step("Assert Prompt Security API returned Block action"):
            assert action == "Block", f"Expected API action 'Block', got: {action!r}"

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
        with allure.step(f"Navigate to {site_name} and capture API response"):
            action = capture_rule_action(page, url)
            page.wait_for_load_state("networkidle", timeout=30000)

        with allure.step("Assert Prompt Security API did not block access"):
            assert action is not None, "Expected an API response from Prompt Security, got none"
            assert action != "Block", f"Expected API action to allow access, got: {action!r}"

        with allure.step(f"Capture screenshot of {site_name}"):
            screenshot_helper(page, f"{site_name.replace('.', '_')}_allowed.png")

        with allure.step("Verify block overlay is not shown"):
            expect(page.locator("#title-text")).not_to_be_visible(timeout=5000)
    finally:
        page.close()
