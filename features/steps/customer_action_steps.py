"""BDD steps for activating and deactivating customers through the UI."""

import json
import uuid
from urllib import request

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException

TIMEOUT = 10


def api_request(context, method, path, data=None):
    """Send an API request for test setup or cleanup."""
    url = f"{context.base_url.rstrip('/')}{path}"

    payload = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Content-Type": "application/json"}

    req = request.Request(url, data=payload, headers=headers, method=method)

    with request.urlopen(req, timeout=TIMEOUT) as response:
        body = response.read()
        return json.loads(body) if body else None


def create_test_customer(context, active):
    """Create a uniquely identifiable customer for this scenario."""
    unique_id = uuid.uuid4().hex

    customer = api_request(
        context,
        "POST",
        "/api/customers",
        {
            "first_name": "ActionTest",
            "last_name": unique_id[:8],
            "email": f"action-{unique_id}@example.com",
            "address": "BDD Test Address",
            "active": active,
        },
    )

    context.test_customer = customer
    context.test_customer_id = customer["id"]


def customer_row(context):
    """Find the row belonging to this scenario's customer."""
    customer_id = context.test_customer_id
    email = context.test_customer["email"]

    def find_row(driver):
        rows = driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr")

        for row in rows:
            if email in row.text:
                return row

        return False

    return WebDriverWait(context.driver, TIMEOUT).until(find_row)


def displayed_status(context, expected):
    """Wait for the customer's displayed status."""

    def status_matches(driver):
        row = customer_row(context)
        status = row.find_element(By.CSS_SELECTOR, ".pill")
        return status.text == expected

    return WebDriverWait(
        context.driver,
        TIMEOUT,
        ignored_exceptions=(StaleElementReferenceException,),
    ).until(status_matches)


@given("an active customer exists for the action test")
def given_active_customer(context):
    create_test_customer(context, True)


@given("an inactive customer exists for the action test")
def given_inactive_customer(context):
    create_test_customer(context, False)


@given("I am viewing that customer in the admin UI")
def given_viewing_customer(context):
    context.driver.get(f"{context.base_url.rstrip('/')}/")
    customer_row(context)


@given("the customer action request will fail")
def given_action_failure(context):
    """Simulate an API failure through the browser."""
    context.driver.execute_cdp_cmd("Network.enable", {})
    context.driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {"urls": ["*/api/customers/*/deactivate"]},
    )


@when("I click the Deactivate button")
def when_deactivate(context):
    row = customer_row(context)
    row.find_element(By.XPATH, ".//button[.='Deactivate']").click()


@when("I click the Activate button")
def when_activate(context):
    row = customer_row(context)
    row.find_element(By.XPATH, ".//button[.='Activate']").click()


@then("the customer should be displayed as inactive")
def then_inactive(context):
    assert displayed_status(context, "Inactive")


@then("the customer should be displayed as active")
def then_active(context):
    assert displayed_status(context, "Active")


@then("the UI should confirm that the action succeeded")
def then_success(context):
    def success_visible(driver):
        element = driver.find_element(By.ID, "action-status")
        return (
            element.get_attribute("hidden") is None
            and "successfully" in element.text.lower()
        )

    assert WebDriverWait(context.driver, TIMEOUT).until(success_visible)


@then("the UI should display an action error")
def then_error(context):
    def error_visible(driver):
        element = driver.find_element(By.ID, "action-status")
        return (
            element.get_attribute("hidden") is None
            and "unable to" in element.text.lower()
        )

    assert WebDriverWait(context.driver, TIMEOUT).until(error_visible)


@then("the customer should still be displayed as active")
def then_still_active(context):
    """Verify that a failed action did not change the displayed status."""
    assert displayed_status(context, "Active")
