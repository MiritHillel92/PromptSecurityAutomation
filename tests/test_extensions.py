import allure
import pytest
from playwright.sync_api import Page, expect


BLOCKED_SITES = [
    ("gemini.google.com", "https://gemini.google.com"),
]

ALLOWED_SITES = [
    ("chatgpt.com", "https://chatgpt.com"),
]


def capture_rule_action(context, page: Page, url: str) -> str:
    captured = {}

    def handle_response(response):
        if "get-rule-action" in response.url:
            try:
                body = response.json()
                if body.get("ruleInfo", {}).get("action"):
                    captured["action"] = body["ruleInfo"]["action"]
            except Exception:
                pass

    context.on("response", handle_response)
    page.goto(url)
    return captured.get("action")


@allure.feature("Extension Functionality")
@allure.story("Block GenAI Applications")
@pytest.mark.flaky(reruns=2, reruns_delay=5)
@pytest.mark.parametrize("site_name,url", BLOCKED_SITES)
def test_site_is_blocked(configured_extension, screenshot_helper, site_name, url):
    page: Page = configured_extension.new_page()
    try:
        with allure.step(f"Navigate to blocked site and capture API response: {site_name}"):
            action = capture_rule_action(configured_extension, page, url)
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
        with allure.step(f"Navigate to allowed site and capture API response: {site_name}"):
            action = capture_rule_action(configured_extension, page, url)
            page.wait_for_load_state("networkidle", timeout=30000)

        with allure.step("Assert Prompt Security API did not return Block action"):
            assert action != "Block", f"Expected API action to allow, got: {action!r}"

        with allure.step(f"Capture screenshot of {site_name}"):
            screenshot_helper(page, f"{site_name.replace('.', '_')}_allowed.png")

        with allure.step("Verify block overlay is not shown"):
            expect(page.locator("#title-text")).not_to_be_visible(timeout=5000)
    finally:
        page.close()
