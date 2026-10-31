"""Step definitions for the List Customers UI (story #30).

The browser is the only interface under test. Customer records are seeded and
cleared through the existing REST API as test fixtures, because the Create
Customers UI (#29) does not exist yet. All assertions are made against the
rendered page.
"""

import requests
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 10

CUSTOMER_PAYLOADS = [
    {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "address": "1 Analytical Engine Way",
    },
    {
        "first_name": "Alan",
        "last_name": "Turing",
        "email": "alan@example.com",
        "address": "2 Bletchley Park",
    },
    {
        "first_name": "Grace",
        "last_name": "Hopper",
        "email": "grace@example.com",
        "address": "3 Compiler Lane",
    },
]


def _customers_api(context, path=""):
    """Build a URL for the Customers REST API."""
    return f"{context.base_url.rstrip('/')}/customers{path}"


def _reset_customers(context, payloads):
    """Delete all customers and create the supplied ones via the REST API."""
    existing = requests.get(_customers_api(context), timeout=TIMEOUT).json()
    for customer in existing:
        requests.delete(_customers_api(context, f"/{customer['id']}"), timeout=TIMEOUT)

    context.customers = []
    for payload in payloads:
        response = requests.post(
            _customers_api(context), json=payload, timeout=TIMEOUT
        )
        response.raise_for_status()
        context.customers.append(response.json())


@given("multiple customers exist in the system")
def step_multiple_customers_exist(context):
    """Seed several customers for the list scenarios."""
    _reset_customers(context, CUSTOMER_PAYLOADS)


@given("no customers exist in the system")
def step_no_customers_exist(context):
    """Ensure the Customers API has no records."""
    _reset_customers(context, [])


@given("the Customers API is unavailable")
def step_customers_api_unavailable(context):
    """Block the Customers API so the UI must handle the failure."""
    context.driver.execute_cdp_cmd("Network.enable", {})
    context.driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*/customers"]})


@when("an admin opens the Customers page")
@when("an admin attempts to view the customer list")
def step_open_customers_page(context):
    """Open the Customers admin UI in the browser."""
    context.driver.get(f"{context.base_url.rstrip('/')}/")


@then("all existing customers are displayed in the UI")
def step_all_customers_displayed(context):
    """Verify one table row is rendered per customer."""
    rows = WebDriverWait(context.driver, TIMEOUT).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#customers tbody tr"))
    )
    assert len(rows) == len(
        context.customers
    ), f"expected {len(context.customers)} rows, found {len(rows)}"


@then("their information is shown correctly")
def step_customer_information_correct(context):
    """Verify each row shows that customer's details."""
    rows = context.driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr")
    for customer, row in zip(context.customers, rows):
        text = row.text
        assert f"{customer['first_name']} {customer['last_name']}" in text
        assert customer["email"] in text
        if customer.get("address"):
            assert customer["address"] in text


@then("the UI displays an empty customer list")
def step_empty_customer_list(context):
    """Verify no rows are rendered."""
    rows = context.driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr")
    assert len(rows) == 0, f"expected no rows, found {len(rows)}"


@then("indicates that no customers are available")
def step_empty_message(context):
    """Verify the empty state message is visible."""
    message = WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "empty"))
    )
    assert "no customers available" in message.text.lower()


@then("the UI displays an appropriate error message")
def step_error_message(context):
    """Verify the error state message is visible."""
    error = WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "error"))
    )
    assert error.text.strip(), "expected a non-empty error message"
