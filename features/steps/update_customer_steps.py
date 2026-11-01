"""Step definitions for the Update Customer UI (story #28).

The browser is the only interface under test. Test customers are created
through the create form and edited through the edit form; no REST calls or
database access are used anywhere in these steps.
"""

import uuid

from behave import given, when, then
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

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


def _unique(prefix):
    """Return a value guaranteed not to collide with existing customers."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _make_customer(base):
    """Build a unique customer payload from a seed record."""
    first_name = _unique(base["first_name"])
    return {
        "first_name": first_name,
        "last_name": base["last_name"],
        "email": f"{first_name.lower()}@example.com",
        "address": base.get("address"),
        "active": base.get("active", True),
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


def _set_active(context, active):
    """Set the Account status field."""
    Select(context.driver.find_element(By.ID, "field-active")).select_by_visible_text(
        "Active" if active else "Inactive"
    )


def _wait_for_status(context, text):
    """Wait until the form status contains the given text."""

    def _ready(driver):
        status = driver.find_element(By.ID, "form-status")
        if status.get_attribute("hidden") is not None:
            return False
        return text in status.text.lower() and status.text

    return WebDriverWait(context.driver, TIMEOUT).until(_ready)


def _wait_for_row(context, name):
    """Wait for and return the table row containing the given name."""

    def _ready(driver):
        try:
            for row in driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr"):
                if name in row.text:
                    return True
        except StaleElementReferenceException:
            return False
        return False

    WebDriverWait(context.driver, TIMEOUT).until(_ready)


def _row_text(context, customer):
    """Wait for and return the rendered text of the row for a customer."""

    def _ready(driver):
        try:
            for row in driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr"):
                if row.get_attribute("data-customer-id") == str(customer["id"]):
                    return row.text
        except StaleElementReferenceException:
            return False
        return False

    return WebDriverWait(context.driver, TIMEOUT).until(_ready)


def _row(context, customer):
    """Wait for and return the row element for a customer by id."""
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
    _row(context, customer).find_element(By.CSS_SELECTOR, ".edit-btn").click()


def _create_customer(context, payload):
    """Create a customer through the create form and return it with its id."""
    _open_page(context)
    _type(context, "field-first-name", payload["first_name"])
    _type(context, "field-last-name", payload["last_name"])
    _type(context, "field-email", payload["email"])
    _type(context, "field-address", payload.get("address", ""))
    _set_active(context, payload.get("active", True))
    context.driver.find_element(By.ID, "save-customer").click()
    _wait_for_status(context, "created")
    _wait_for_row(context, payload["first_name"])
    customer = dict(payload)
    customer["id"] = _row_by_name(context, payload["first_name"]).get_attribute(
        "data-customer-id"
    )
    return customer


def _row_by_name(context, name):
    """Wait for and return the row element containing the given name."""

    def _ready(driver):
        try:
            for row in driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr"):
                if name in row.text:
                    return row
        except StaleElementReferenceException:
            return False
        return False

    return WebDriverWait(context.driver, TIMEOUT).until(_ready)


def _fill_form(context, values):
    """Type the supplied values into the form."""
    fields = {
        "field-first-name": values["first_name"],
        "field-last-name": values["last_name"],
        "field-email": values["email"],
        "field-address": values.get("address", ""),
    }
    for element_id, value in fields.items():
        _type(context, element_id, value)


@given("a customer exists")
def step_customer_exists(context):
    """Create a single customer through the web UI."""
    context.customer = _create_customer(context, _make_customer(CUSTOMER))


@given("I have opened a customer's edit form")
def step_open_edit_form(context):
    """Create a customer and start editing it through the web UI."""
    context.customer = _create_customer(context, _make_customer(CUSTOMER))
    _start_editing(context, context.customer)


@given("the customer has previously saved details")
def step_customer_has_saved_details(context):
    """The customer retains the details it was created with."""
    assert context.customer["first_name"]
    assert context.customer["last_name"]
    assert context.customer["email"]


@when("I select that customer for editing")
def step_select_customer(context):
    """Open the page and click Edit for the created customer."""
    _open_page(context)
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
    _wait_for_status(context, "updated")


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
    _wait_for_status(context, "unable")


@then("the UI indicates that the update succeeded")
def step_update_succeeded(context):
    """Verify the success message is shown."""
    status = context.driver.find_element(By.ID, "form-status")
    assert "updated" in status.text.lower()


@then("the updated details are displayed for that customer")
def step_updated_displayed(context):
    """Verify the table shows the new details."""
    text = _row_text(context, context.customer)
    assert f"{UPDATED['first_name']} {UPDATED['last_name']}" in text
    assert UPDATED["email"] in text


@then("the saved details remain correct when I reload the page")
def step_saved_details_persist(context):
    """Verify the update persists after a reload."""
    context.driver.refresh()
    _wait_for_row(context, UPDATED["first_name"])
    text = _row_text(context, context.customer)
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
    _wait_for_row(context, context.customer["first_name"])
    text = _row_text(context, context.customer)
    assert f"{context.customer['first_name']} {context.customer['last_name']}" in text


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
