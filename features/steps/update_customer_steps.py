"""Step definitions for the Update Customer UI (story #28).

The browser is the only interface under test. Customer records are seeded and
cleared through the existing REST API as test fixtures; all interactions and
assertions are performed against the rendered page.
"""

import requests
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 10

CUSTOMER = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "address": "1 Analytical Engine Way",
    "active": True,
}

UPDATED = {
    "first_name": "Augusta",
    "last_name": "King",
    "email": "augusta@example.com",
    "address": "9 Countess Road",
}


def _api(context, path=""):
    """Build a URL for the Customers REST API."""
    return f"{context.base_url.rstrip('/')}/customers{path}"


def _clear_customers(context):
    """Delete every customer through the REST API."""
    for customer in requests.get(_api(context), timeout=TIMEOUT).json():
        requests.delete(_api(context, f"/{customer['id']}"), timeout=TIMEOUT)


def _create_customer(context, payload):
    """Create a customer through the REST API."""
    response = requests.post(_api(context), json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def _open_customers_page(context):
    """Open the Customers admin UI."""
    context.driver.get(f"{context.base_url.rstrip('/')}/")


def _row_for(context, customer):
    """Wait for and return the table row for a customer."""
    return WebDriverWait(context.driver, TIMEOUT).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                f"#customers tbody tr[data-customer-id='{customer['id']}']",
            )
        )
    )


def _start_editing(context, customer):
    """Click the Edit control for a customer."""
    _row_for(context, customer).find_element(By.CSS_SELECTOR, ".edit-btn").click()


def _fill_form(context, values):
    """Type the supplied values into the edit form."""
    fields = {
        "field-first-name": values["first_name"],
        "field-last-name": values["last_name"],
        "field-email": values["email"],
        "field-address": values.get("address", ""),
    }
    for element_id, value in fields.items():
        element = context.driver.find_element(By.ID, element_id)
        element.clear()
        element.send_keys(value)


def _wait_for_form_status(context, success):
    """Wait until the form status message reflects success or failure."""

    def _ready(driver):
        status = driver.find_element(By.ID, "form-status")
        if status.get_attribute("hidden") is not None:
            return False
        text = status.text.lower()
        if success:
            return text or False
        return ("unable" in text or "error" in text) and text

    return WebDriverWait(context.driver, TIMEOUT).until(_ready)


def _row_text(context, customer_id):
    """Return the rendered text of a customer row."""
    row = WebDriverWait(context.driver, TIMEOUT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, f"#customers tbody tr[data-customer-id='{customer_id}']")
        )
    )
    return row.text


@given("a customer exists")
def step_customer_exists(context):
    """Seed a single customer."""
    _clear_customers(context)
    context.customer = _create_customer(context, CUSTOMER)


@given("I have opened a customer's edit form")
def step_open_edit_form(context):
    """Seed a customer, open the page, and start editing."""
    _clear_customers(context)
    context.customer = _create_customer(context, CUSTOMER)
    _open_customers_page(context)
    _start_editing(context, context.customer)


@given("the customer has previously saved details")
def step_customer_has_saved_details(context):
    """The customer retains the details it was seeded with."""
    assert context.customer["first_name"] == CUSTOMER["first_name"]
    assert context.customer["last_name"] == CUSTOMER["last_name"]


@when("I select that customer for editing")
def step_select_customer(context):
    """Open the page and click Edit for the seeded customer."""
    _open_customers_page(context)
    _start_editing(context, context.customer)


@then("the customer's current details are displayed in an editable form")
def step_details_displayed(context):
    """Verify the edit form is populated and editable."""
    first_name = context.driver.find_element(By.ID, "field-first-name")
    assert first_name.get_attribute("value") == context.customer["first_name"]
    last_name = context.driver.find_element(By.ID, "field-last-name")
    assert last_name.get_attribute("value") == context.customer["last_name"]
    email = context.driver.find_element(By.ID, "field-email")
    assert email.get_attribute("value") == context.customer["email"]
    assert first_name.is_enabled()


@when("I change the customer's details and save the changes")
def step_change_and_save(context):
    """Change the details and submit the update."""
    _fill_form(context, UPDATED)
    context.driver.find_element(By.ID, "save-customer").click()
    _wait_for_form_status(context, success=True)


@when("I change the customer's details and cancel editing")
def step_change_and_cancel(context):
    """Change the details and cancel."""
    _fill_form(context, UPDATED)
    context.driver.find_element(By.ID, "cancel-customer").click()


@when("I save the changes and the update fails")
def step_save_fails(context):
    """Block the update request and attempt to save."""
    context.driver.execute_cdp_cmd("Network.enable", {})
    context.driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*/customers/*"]})
    _fill_form(context, UPDATED)
    context.driver.find_element(By.ID, "save-customer").click()
    _wait_for_form_status(context, success=False)


@then("the UI indicates that the update succeeded")
def step_update_succeeded(context):
    """Verify the success message is shown."""
    status = context.driver.find_element(By.ID, "form-status")
    assert "updated" in status.text.lower()


@then("the updated details are displayed for that customer")
def step_updated_displayed(context):
    """Verify the table shows the new details."""
    text = _row_text(context, context.customer["id"])
    assert f"{UPDATED['first_name']} {UPDATED['last_name']}" in text
    assert UPDATED["email"] in text


@then("the saved details remain correct when I reload the page")
def step_saved_details_persist(context):
    """Verify the update persists after a reload."""
    context.driver.refresh()
    text = _row_text(context, context.customer["id"])
    assert f"{UPDATED['first_name']} {UPDATED['last_name']}" in text


@then("the unsaved changes are discarded")
def step_changes_discarded(context):
    """Verify the cancelled changes are gone from the form."""
    first_name = context.driver.find_element(By.ID, "field-first-name")
    assert first_name.get_attribute("value") != UPDATED["first_name"]


@then("the customer's previously saved details remain unchanged")
def step_original_unchanged(context):
    """Verify the stored customer still has the original details."""
    context.driver.refresh()
    text = _row_text(context, context.customer["id"])
    assert f"{CUSTOMER['first_name']} {CUSTOMER['last_name']}" in text


@then("the UI communicates that the update was unsuccessful")
def step_update_unsuccessful(context):
    """Verify the failure message is shown."""
    status = context.driver.find_element(By.ID, "form-status")
    assert "unable" in status.text.lower()


@then("the UI does not indicate that the changes were saved successfully")
def step_no_success_indication(context):
    """Verify no success message is shown."""
    status = context.driver.find_element(By.ID, "form-status")
    assert "updated." not in status.text.lower()
