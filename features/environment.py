"""Behave hooks for browser-based CustomerHub tests."""

import os

from selenium import webdriver


def before_all(context):
    """Initialize shared BDD configuration."""
    context.bdd_environment_ready = True
    context.base_url = os.getenv(
        "BASE_URL",
        "http://127.0.0.1:8080",
    )


def before_scenario(context, scenario):
    """Initialize a browser for each scenario."""
    assert context.bdd_environment_ready is True
    if scenario.feature.filename.endswith("deployed_service.feature"):
        return

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1000")

    context.driver = webdriver.Chrome(options=options)
    context.driver.implicitly_wait(3)


def after_scenario(context, scenario):
    """Always close the browser after a scenario."""
    driver = getattr(context, "driver", None)

    if driver is not None:
        driver.quit()
