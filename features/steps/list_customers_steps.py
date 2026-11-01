"""Step definitions for the List Customers UI (story #30).

The browser is the only interface under test. Test customers are created
through the web UI and no REST calls or database access are used anywhere in
these steps.
"""

import uuid

from behave import given, when, then
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

TIMEOUT = 10

CUSTOMER_SEEDS = [
    {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "address": "1 Analytical Engine Way",
    },
    {
        "first_name": "Alan",
        "last_name": "Turing",
        "address": "2 Bletchley Park",
    },
    {
        "first_name": "Grace",
        "last_name": "Hopper",
        "address": "3 Compiler Lane",
    },
]


def _unique(prefix):
    """Return a value guaranteed not to collide with existing customers."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _make_customer(seed):
    """Build a unique customer payload from a seed record."""
    first_name = _unique(seed["first_name"])
    return {
        "first_name": first_name,
        "last_name": seed["last_name"],
        "email": f"{first_name.lower()}@example.com",
        "address": seed.get("address"),
        "active": seed.get("active", True),
    }


def _open_page(context):
    """Open the Customers admin page and wait for the create form."""
    context.driver.get(f"{context.base_url.rstrip('/')}/")
    WebDriverWait(context.driver, TIMEOUT).until(
        EC.presence_of_element_located((By.ID, "customer-form"))
    )


def _type(context, element_id, value):
    """Type a value into a form field."""
    element = context.driver.find_element(By.ID, element_id)
    element.clear()
    element.send_keys(value)


def _wait_for_row(context, name):
    """Wait for and return the table row containing the given name.

    The table is re-rendered after every load, so rows can go stale while
    they are being inspected; that simply means we are not done polling yet.
    """

    def _ready(driver):
        try:
            for row in driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr"):
                if name in row.text:
                    return True
        except StaleElementReferenceException:
            return False
        return False

    WebDriverWait(context.driver, TIMEOUT).until(_ready)


def _row_text(context, name):
    """Wait for and return the rendered text of the row for a customer."""

    def _ready(driver):
        try:
            for row in driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr"):
                if name in row.text:
                    return row.text
        except StaleElementReferenceException:
            return False
        return False

    return WebDriverWait(context.driver, TIMEOUT).until(_ready)


def _create_customer(context, customer):
    """Create a customer through the web UI form."""
    _open_page(context)
    _type(context, "field-first-name", customer["first_name"])
    _type(context, "field-last-name", customer["last_name"])
    _type(context, "field-email", customer["email"])
    if customer.get("address"):
        _type(context, "field-address", customer["address"])
    Select(context.driver.find_element(By.ID, "field-active")).select_by_visible_text(
        "Active" if customer.get("active", True) else "Inactive"
    )
    context.driver.find_element(By.ID, "save-customer").click()
    _wait_for_row(context, customer["first_name"])


def _wait_for_list_settled(context):
    """Wait until the customer table has finished rendering."""

    def _settled(driver):
        rows = driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr")
        if rows:
            return True
        empty = driver.find_element(By.ID, "empty")
        if empty.get_attribute("hidden") is None:
            return True
        error = driver.find_element(By.ID, "error")
        return error.get_attribute("hidden") is None

    return WebDriverWait(context.driver, TIMEOUT).until(_settled)


@given("multiple customers exist in the system")
def step_multiple_customers_exist(context):
    """Create several customers through the web UI."""
    context.customers = []
    for seed in CUSTOMER_SEEDS:
        customer = _make_customer(seed)
        _create_customer(context, customer)
        context.customers.append(customer)


@given("no customers exist in the system")
def step_no_customers_exist(context):
    """No test data is created; the environment must start empty.

    This scenario relies on the BDD suite running against an isolated
    database. The tests never talk to the service API or the database
    directly, so they cannot clear records themselves.
    """


@given("the Customers API is unavailable")
def step_customers_api_unavailable(context):
    """Block the Customers API so the UI must handle the failure."""
    context.driver.get(f"{context.base_url.rstrip('/')}/")
    context.driver.execute_cdp_cmd("Network.enable", {})
    context.driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*/customers"]})


@when("an admin opens the Customers page")
def step_open_customers_page(context):
    """Open the Customers admin UI in the browser."""
    _open_page(context)


@when("an admin attempts to view the customer list")
def step_attempt_view_list(context):
    """Open the Customers admin UI even though the API is unavailable."""
    _open_page(context)


@then("all existing customers are displayed in the UI")
def step_all_customers_displayed(context):
    """Verify each created customer appears in the table."""
    for customer in context.customers:
        _wait_for_row(context, customer["first_name"])


@then("their information is shown correctly")
def step_customer_information_correct(context):
    """Verify each row shows that customer's details."""
    for customer in context.customers:
        text = _row_text(context, customer["first_name"])
        assert f"{customer['first_name']} {customer['last_name']}" in text
        assert customer["email"] in text
        if customer.get("address"):
            assert customer["address"] in text


@then("the UI displays an empty customer list")
def step_empty_customer_list(context):
    """Verify no rows are rendered once the table has finished loading."""
    _wait_for_list_settled(context)
    rows = context.driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr")
    assert len(rows) == 0, (
        f"expected an empty customer list, found {len(rows)} rows; "
        "run the BDD suite against an isolated database"
    )


@then("indicates that no customers are available")
def step_empty_message(context):
    """Verify the empty state message is visible."""
    message = WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "empty"))
    )
    assert "no customers available" in message.text.lower()


@then("the UI displays an appropriate error message")
def step_error_message(context):
    """Verify an error is shown and no customers are rendered as success."""
    error = WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "error"))
    )
    assert error.text.strip(), "expected a non-empty error message"
    rows = context.driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr")
    assert len(rows) == 0, (
        f"expected no customers when the API is unavailable, found {len(rows)}"
    )
    empty = context.driver.find_element(By.ID, "empty")
    assert empty.get_attribute("hidden") is not None, (
        "the UI must not show an empty-list state when the request failed"
    )
