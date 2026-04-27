import json
import os
import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXTENSION_PATH = os.path.join(BASE_DIR, "extension")
EXTENSION_ID = "iidnankcocecmgpcafggbgbmkbcldmno"

API_KEY = os.environ.get("PROMPT_SECURITY_API_KEY", "")
API_DOMAIN = os.environ.get("PROMPT_SECURITY_API_DOMAIN", "eu.prompt.security")
CHATGPT_COOKIES = os.environ.get("CHATGPT_COOKIES", "")


def get_screenshot_directory() -> str:
    path = os.path.join(BASE_DIR, "screenshots")
    os.makedirs(path, exist_ok=True)
    return path


def save_screenshot(page, file_name: str) -> str:
    screenshot_path = os.path.join(get_screenshot_directory(), file_name)
    page.screenshot(path=screenshot_path)
    allure.attach.file(screenshot_path, name=file_name, attachment_type=allure.attachment_type.PNG)
    return screenshot_path


@pytest.fixture(scope="function")
def browser_context(tmp_path):
    if not API_KEY:
        pytest.fail("PROMPT_SECURITY_API_KEY environment variable is not set")

    user_data_dir = tmp_path / "playwright_user_data"

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            args=[
                f"--disable-extensions-except={EXTENSION_PATH}",
                f"--load-extension={EXTENSION_PATH}",
            ],
        )
        if not context.service_workers:
            context.wait_for_event("serviceworker", timeout=30000)
        yield context
        context.close()


@pytest.fixture(scope="function")
def configured_extension(browser_context):
    with allure.step("Configure extension with API credentials"):
        page = browser_context.new_page()
        page.goto("https://example.com")
        page.wait_for_load_state("networkidle")

        page.goto(
            f"chrome-extension://{EXTENSION_ID}/html/popup.html",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_selector("#apiDomain", state="visible", timeout=30000)
        page.wait_for_selector("#apiKey", state="visible", timeout=30000)

        page.fill("#apiDomain", API_DOMAIN)
        page.fill("#apiKey", API_KEY)
        page.click("#saveButton")
        # The popup hides #message when the backend config call succeeds.
        # Waiting for it to be hidden confirms the policy was fetched.
        page.wait_for_selector("#message", state="hidden", timeout=30000)

        page.close()
        page = browser_context.new_page()
        page.goto(
            f"chrome-extension://{EXTENSION_ID}/html/popup.html",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_selector("#apiDomain", state="visible", timeout=30000)
        saved_domain = page.input_value("#apiDomain")
        saved_key = page.input_value("#apiKey")
        assert saved_domain == API_DOMAIN, (
            f"Extension config not saved correctly: apiDomain field shows '{saved_domain!r}'"
        )
        assert saved_key == API_KEY, (
            f"Extension config not saved correctly: apiKey field shows '{saved_key!r}'"
        )

        page.close()

    if CHATGPT_COOKIES:
        page = browser_context.new_page()
        page.goto("https://chatgpt.com", wait_until="domcontentloaded")
        browser_context.add_cookies(json.loads(CHATGPT_COOKIES))
        page.close()

    return browser_context


@pytest.fixture(scope="function")
def screenshot_helper():
    return save_screenshot
