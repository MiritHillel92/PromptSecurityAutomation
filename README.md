# Prompt Security Extension – Automation Tests

Playwright-based test suite that verifies the browser extension correctly **allows** `chatgpt.com` and **blocks** `gemini.google.com` according to policy.

## Prerequisites

- Python 3.11+

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy the env template and fill in your API key:

```bash
cp .env.example .env
# edit .env and set PROMPT_SECURITY_API_KEY
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PROMPT_SECURITY_API_KEY` | Yes | API key for the Prompt Security tenant |
| `PROMPT_SECURITY_API_DOMAIN` | No | API domain (default: `eu.prompt.security`) |
| `HEADLESS` | No | Set to `true` to run headlessly (default: `false`) |

## Running the Tests

```bash
# headed (default)
pytest tests/ -v

# headless
HEADLESS=true pytest tests/ -v

# with Allure report
pytest tests/ -v --alluredir=allure-results
allure serve allure-results
```

## CI (GitHub Actions)

Set `PROMPT_SECURITY_API_KEY` as a repository secret. The workflow installs dependencies, runs the suite headlessly, and uploads the Allure report as an artifact.
