"""Step definitions for the Read Customer UI (story #27)."""

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from customer_ui import (
    TIMEOUT,
    block_requests,
    create_customer,
    customer_row,
    new_customer,
    open_page,
)

# A customer id that no test database contains
MISSING_CUSTOMER_ID = 2147483647


def _wait_visible(context, element_id):
    """Wait for an element to be displayed and return it."""
    return WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )


def _text(context, element_id):
    """Return the displayed text of an element."""
    return context.driver.find_element(By.ID, element_id).text


@given("an inactive customer without an address exists in the system")
def step_inactive_customer_without_address(context):
    """Create an inactive customer that has no address."""
    customer = new_customer(address="", active=False)
    context.customer = create_customer(context, customer)


@given("loading a customer will fail")
def step_loading_will_fail(context):
    """Make requests for a single customer fail in the browser."""
    block_requests(context, "*/customers/*")


@when("an admin navigates to the customer details page")
def step_navigate_to_details(context):
    """Go to the details page of the customer."""
    open_page(context, f"#customer/{context.customer['id']}")
    context.driver.refresh()


@when("I select View for that customer")
def step_select_view(context):
    """Use the View control in the customer list."""
    customer_row(context, context.customer).find_element(
        By.CSS_SELECTOR, ".view-btn"
    ).click()


@when("an admin navigates to the details page of a customer that does not exist")
def step_navigate_to_missing_customer(context):
    """Go to the details page of a customer id that is not in use."""
    open_page(context, f"#customer/{MISSING_CUSTOMER_ID}")
    context.driver.refresh()


@then("the customer's details are displayed in the UI")
def step_details_displayed(context):
    """Verify every stored detail of the customer is shown."""
    customer = context.customer
    _wait_visible(context, "view-details")
    assert _text(context, "view-id") == str(customer["id"])
    assert _text(context, "view-name") == f"{customer['first_name']} {customer['last_name']}"
    assert _text(context, "view-email") == customer["email"]
    expected_address = customer["address"] or "Not provided"
    assert _text(context, "view-address") == expected_address
    expected_status = "Active" if customer["active"] else "Inactive"
    assert _text(context, "view-status") == expected_status


@then("the UI indicates that the customer was not found")
def step_not_found(context):
    """Verify the not-found message is shown."""
    error = _wait_visible(context, "view-error")
    assert "not found" in error.text.lower()


@then("the UI indicates that the customer could not be loaded")
def step_could_not_load(context):
    """Verify the load failure message is shown."""
    error = _wait_visible(context, "view-error")
    assert "unable to load" in error.text.lower()


@then("no customer details are displayed")
def step_no_details(context):
    """Verify the details list stays hidden."""
    details = context.driver.find_element(By.ID, "view-details")
    assert not details.is_displayed()
