"""Step definitions for the Create Customer UI (story #29).

The browser is the only interface under test. No REST calls and no database
access are used: customers are created through the form and verified in the
rendered page.
"""

import uuid

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

TIMEOUT = 10
INVALID_EMAIL = "not-an-email"


def _open_page(context):
    """Open the Customers admin page and wait for the form."""
    context.driver.get(f"{context.base_url.rstrip('/')}/")
    WebDriverWait(context.driver, TIMEOUT).until(
        EC.presence_of_element_located((By.ID, "customer-form"))
    )


def _unique(prefix):
    """Return a value guaranteed not to collide with existing customers."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _type(context, element_id, value):
    """Type a value into a form field."""
    element = context.driver.find_element(By.ID, element_id)
    element.clear()
    element.send_keys(value)


def _fill_required(context):
    """Fill the required fields with unique values."""
    context.first_name = _unique("Test")
    context.last_name = _unique("Customer")
    context.email = f"{context.first_name.lower()}@example.com"
    _type(context, "field-first-name", context.first_name)
    _type(context, "field-last-name", context.last_name)
    _type(context, "field-email", context.email)


def _set_active(context, active):
    """Set the Account status field."""
    Select(context.driver.find_element(By.ID, "field-active")).select_by_visible_text(
        "Active" if active else "Inactive"
    )


def _submit(context):
    """Submit the create form."""
    context.driver.find_element(By.ID, "save-customer").click()


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
        for row in driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr"):
            if name in row.text:
                return row
        return False

    return WebDriverWait(context.driver, TIMEOUT).until(_ready)


@given("I am on the Customers admin page")
def step_on_customers_page(context):
    """Open the admin page."""
    _open_page(context)


@given("the active status is enabled by default")
def step_active_status_default(context):
    """Verify the Account status defaults to Active."""
    selected = Select(
        context.driver.find_element(By.ID, "field-active")
    ).first_selected_option
    assert selected.text == "Active"


@given("the creation request will fail")
def step_creation_will_fail(context):
    """Block the create request so the UI must handle the failure."""
    context.driver.execute_cdp_cmd("Network.enable", {})
    context.driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": ["*/customers"]})


@when("I enter the customer's first name, last name, and email")
def step_enter_required(context):
    """Fill the required fields."""
    _fill_required(context)


@when("I enter valid customer details and submit the form")
def step_enter_valid_and_submit(context):
    """Fill valid details and submit."""
    _fill_required(context)
    _submit(context)


@when("I enter a customer with an invalid email address")
def step_enter_invalid_email(context):
    """Fill the required fields but use a malformed email."""
    _fill_required(context)
    _type(context, "field-email", INVALID_EMAIL)
    context.email = INVALID_EMAIL
    context.rows_before_submit = _count_rows(context)


REQUIRED_FIELD_IDS = {
    "first name": "field-first-name",
    "last name": "field-last-name",
    "email": "field-email",
}


def _count_rows(context):
    """Return the number of customer rows currently rendered."""
    return len(context.driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr"))


@when("I submit the form with a missing {field}")
def step_submit_missing(context, field):
    """Leave the named required field empty and submit."""
    _fill_required(context)
    context.driver.find_element(By.ID, REQUIRED_FIELD_IDS[field]).clear()
    context.rows_before_submit = _count_rows(context)
    _submit(context)


@when("I optionally enter an address")
def step_enter_address(context):
    """Fill the optional address field."""
    context.address = _unique("Address")
    _type(context, "field-address", context.address)


@when("I set the customer's active status")
def step_set_active(context):
    """Set the customer active."""
    _set_active(context, True)


@when("I set the active status to inactive")
def step_set_inactive(context):
    """Set the customer inactive."""
    _set_active(context, False)


@when("I leave the address blank")
def step_leave_address_blank(context):
    """Do not fill the address field."""
    context.address = ""


@when("I leave the active status unchanged")
def step_leave_active_unchanged(context):
    """Keep the default active status."""


@when("I submit the form")
def step_submit(context):
    """Submit the create form."""
    _submit(context)


@then("the customer is created successfully")
def step_created_successfully(context):
    """Verify the success message appears."""
    _wait_for_status(context, "created")


@then("the customer is not created")
def step_not_created(context):
    """Verify no new row was added after a rejected submission."""
    rows_after = _count_rows(context)
    assert rows_after == getattr(context, "rows_before_submit", rows_after), (
        "no new customer row should appear when creation is rejected"
    )


@then("the new customer appears in the UI")
def step_new_customer_appears(context):
    """Verify the created customer is listed."""
    _wait_for_row(context, context.first_name)


@then("the customer's saved details are displayed correctly")
def step_saved_details(context):
    """Verify the row shows the saved details."""
    row = _wait_for_row(context, context.first_name)
    assert context.last_name in row.text
    assert context.email in row.text
    if getattr(context, "address", ""):
        assert context.address in row.text


@then("the UI confirms that the customer was created successfully")
def step_ui_confirms(context):
    """Verify the success message is shown."""
    status = context.driver.find_element(By.ID, "form-status")
    assert "created" in status.text.lower()


@then("the UI identifies the required information that must be provided")
def step_required_information(context):
    """Verify the validation message identifies the required fields."""
    status = context.driver.find_element(By.ID, "form-status")
    assert "required" in status.text.lower()


@then("the UI identifies that the email address is invalid")
def step_invalid_email(context):
    """Verify the validation message says the email is not valid."""
    _wait_for_status(context, "valid email")


@then("the customer's address is empty")
def step_address_empty(context):
    """Verify the created customer has no address."""
    row = _wait_for_row(context, context.first_name)
    cells = row.find_elements(By.TAG_NAME, "td")
    assert cells[1].text.strip() == ""


@then("the customer's active status is True")
def step_active_true(context):
    """Verify the customer is shown as Active."""
    row = _wait_for_row(context, context.first_name)
    assert "Active" in row.text


@then("the customer's active status is False")
def step_active_false(context):
    """Verify the customer is shown as Inactive."""
    row = _wait_for_row(context, context.first_name)
    assert "Inactive" in row.text


@then("the UI communicates that the customer could not be created")
def step_could_not_create(context):
    """Verify the failure message is shown."""
    _wait_for_status(context, "unable")


@then("the UI does not indicate that the customer was created successfully")
def step_no_success(context):
    """Verify no success message is shown."""
    status = context.driver.find_element(By.ID, "form-status")
    assert "created." not in status.text.lower()
