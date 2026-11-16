"""Behave hooks for browser-based CustomerHub tests."""

import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service


def before_all(context):
    """Initialize shared BDD configuration."""
    context.bdd_environment_ready = True
    context.base_url = os.getenv(
        "BASE_URL",
        "http://127.0.0.1:8080",
    )


def before_scenario(context, scenario):
    """Initialize a browser for each scenario."""
    context.test_customer_id = None
    context.driver = None
    assert context.bdd_environment_ready is True
    if scenario.feature.filename.endswith("deployed_service.feature"):
        return

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1000")
    chrome_binary = os.getenv("CHROME_BINARY")
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")

    if chrome_binary:
        options.binary_location = chrome_binary

    if chromedriver_path:
        context.driver = webdriver.Chrome(
            service=Service(chromedriver_path),
            options=options,
        )
    else:
        context.driver = webdriver.Chrome(options=options)
    context.driver.implicitly_wait(3)


def after_scenario(context, scenario):
    """Close the browser and clean up scenario-owned test data."""
    driver = getattr(context, "driver", None)

    if driver is not None:
        driver.quit()
        context.driver = None

    customer_id = getattr(context, "test_customer_id", None)

    if customer_id is not None:
        from urllib import request

        url = f"{context.base_url.rstrip('/')}" f"/api/customers/{customer_id}"

        req = request.Request(url, method="DELETE")

        try:
            with request.urlopen(req, timeout=10) as response:
                if response.status not in (200, 202, 204):
                    raise AssertionError(
                        f"Unexpected cleanup status: {response.status}"
                    )
        finally:
            context.test_customer_id = None
