# Prompt Security Extension – Automation Tests

An end-to-end test suite that verifies the **Prompt Security browser extension** correctly blocks and allows GenAI sites according to your organisation's policy.

The tests use [Playwright](https://playwright.dev/python/) to drive a real Chromium browser with the extension loaded, and [Allure](https://allurereport.org/) to generate a rich test report published to GitHub Pages after every run.

---

## What the tests verify

| Test | Site | Expected behaviour |
|---|---|---|
| `test_site_is_blocked` | gemini.google.com | Extension redirects to the block page (`type=blockPage`) |
| `test_site_is_blocked` | claude.ai | Extension redirects to the block page (`type=blockPage`) |
| `test_site_is_allowed` | chatgpt.com | Site loads normally, no block overlay appears |

Each test also captures a screenshot attached to the Allure report.

---

## Project structure

```
.
├── extension/          # The Prompt Security Chrome extension (pre-built)
├── tests/
│   ├── conftest.py     # Playwright fixtures: browser launch, extension config
│   └── test_extensions.py  # Test cases
├── .github/
│   └── workflows/
│       └── test.yml   # CI pipeline (GitHub Actions)
├── .env.example        # Template for local environment variables
├── requirements.txt    # Python dependencies
└── README.md
```

---

## Running locally

### 1. Prerequisites

- Python 3.11+
- Google Chrome (Playwright will install Chromium for you)

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium --with-deps
```

### 3. Set up environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` and set:

```
PROMPT_SECURITY_API_KEY=your-api-key-here
PROMPT_SECURITY_API_DOMAIN=eu.prompt.security
```

> `PROMPT_SECURITY_API_DOMAIN` defaults to `eu.prompt.security` if not set.

### 4. Run the tests

```bash
# Run all tests
pytest tests/ -v

# Run with Allure report
pytest tests/ -v --alluredir=allure-results
allure serve allure-results
```

> **Note:** The tests open a real browser window (headless mode is not supported because Chrome extensions require a real display).

---

## CI / GitHub Actions

Every push and pull request to `main` triggers the pipeline automatically.

### How it works

1. **Test job** — installs dependencies, launches a virtual display (Xvfb), runs the tests, uploads results as artifacts.
2. **Publish-report job** — downloads the results, generates the Allure HTML report, and deploys it to GitHub Pages.

### Required GitHub secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|---|---|
| `PROMPT_SECURITY_API_KEY` | Your Prompt Security API key |

### Optional GitHub variable

Go to **Settings → Secrets and variables → Actions → Variables** and add:

| Variable | Default | Description |
|---|---|---|
| `PROMPT_SECURITY_API_DOMAIN` | `eu.prompt.security` | Override the API domain |

### Test report

After each run the Allure report is published at:

**https://MiritHillel92.github.io/PromptSecurityAutomation/**

A direct link also appears in the **Summary** tab of every GitHub Actions run.

---

## How the extension is tested

The Prompt Security extension runs as a Chrome service worker. When you navigate to a site, the extension calls the Prompt Security API to decide whether to block or allow it.

- **Block decision** → the extension redirects the tab to its own `pageOverlay.html` page with `type=blockPage` in the URL. The test asserts this redirect happened and the correct domain is in the URL.
- **Allow decision** → the tab stays on the original site. The test asserts the URL is still on the target site and no block overlay is visible.

---

## Test logs in Allure

Every test produces a `test.log` attachment visible in the Allure report under the test's **Attachments** tab. The log includes:

- **Timestamped navigation events** — when the browser navigated and how long the redirect or page load took (in seconds)
- **Assertion results** — confirmation that URL checks passed

The log is collected for the full duration of the test and attached at teardown, so it is present even when the test fails.

---

## Flakiness handling

The block test has a retry policy (`--reruns 2 --reruns-delay 5`) because the Prompt Security API call can occasionally be slow in CI. If the test fails it will automatically retry up to 2 times before reporting a failure.
