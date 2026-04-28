import os
import allure
import pytest
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXTENSION_PATH = os.path.join(BASE_DIR, "extension")
EXTENSION_ID = "iidnankcocecmgpcafggbgbmkbcldmno"

API_KEY = os.environ.get("PROMPT_SECURITY_API_KEY", "")
API_DOMAIN = os.environ.get("PROMPT_SECURITY_API_DOMAIN", "eu.prompt.security")

SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")


def save_screenshot(page, file_name: str) -> str:
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    path = os.path.join(SCREENSHOTS_DIR, file_name)
    page.screenshot(path=path)
    allure.attach.file(path, name=file_name, attachment_type=allure.attachment_type.PNG)
    return path


@pytest.fixture(scope="session")
def configured_extension(tmp_path_factory):
    if not API_KEY:
        pytest.fail("PROMPT_SECURITY_API_KEY environment variable is not set")

    user_data_dir = tmp_path_factory.mktemp("playwright_user_data")

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

        context.service_workers[0].evaluate("() => self.registration.ready")

        with allure.step("Configure extension with API credentials"):
            page = context.new_page()
            page.goto(
                f"chrome-extension://{EXTENSION_ID}/html/popup.html",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_selector("#apiDomain", state="visible", timeout=30000)
            page.fill("#apiDomain", API_DOMAIN)
            page.fill("#apiKey", API_KEY)
            page.click("#saveButton")
            page.wait_for_selector("#message", state="hidden", timeout=30000)
            page.close()

        with allure.step("Verify extension credentials were saved"):
            page = context.new_page()
            page.goto(
                f"chrome-extension://{EXTENSION_ID}/html/popup.html",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_selector("#apiDomain", state="visible", timeout=30000)
            assert page.input_value("#apiDomain") == API_DOMAIN, (
                f"Extension config not saved correctly: apiDomain shows {page.input_value('#apiDomain')!r}"
            )
            assert page.input_value("#apiKey") == API_KEY, (
                f"Extension config not saved correctly: apiKey shows {page.input_value('#apiKey')!r}"
            )
            page.close()

        yield context
        context.close()


@pytest.fixture(scope="function")
def page_logger(request):
    log_lines = []

    def log(msg: str):
        entry = f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}"
        log_lines.append(entry)

    def attach_log():
        if log_lines:
            allure.attach(
                "\n".join(log_lines),
                name="test.log",
                attachment_type=allure.attachment_type.TEXT,
            )

    request.addfinalizer(attach_log)
    return log


@pytest.fixture(scope="function")
def screenshot_helper():
    return save_screenshot
