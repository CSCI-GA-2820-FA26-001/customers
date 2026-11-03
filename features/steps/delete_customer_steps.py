"""Step definitions for the Delete Customer UI (story #31)."""

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from customer_ui import (
    TIMEOUT,
    block_requests,
    customer_listed,
    customer_row,
    open_page,
)


def _select_delete(context):
    """Click Delete for the customer and wait for the confirmation dialog."""
    customer_row(context, context.customer).find_element(
        By.CSS_SELECTOR, ".delete-btn"
    ).click()
    alert = WebDriverWait(context.driver, TIMEOUT).until(EC.alert_is_present())
    context.confirmation = alert.text
    return alert


def _list_status(context):
    """Wait for the list status message and return its text."""
    return WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "list-status"))
    ).text.lower()


@given("deleting a customer will fail")
def step_deleting_will_fail(context):
    """Make requests for a single customer fail in the browser."""
    block_requests(context, "*/customers/*")


@when("I select Delete for that customer")
def step_select_delete(context):
    """Ask to delete the customer."""
    _select_delete(context)


@when("I confirm the deletion")
def step_confirm_deletion(context):
    """Accept the confirmation dialog."""
    context.driver.switch_to.alert.accept()


@when("I cancel the confirmation")
def step_cancel_confirmation(context):
    """Dismiss the confirmation dialog."""
    context.driver.switch_to.alert.dismiss()


@when("I attempt to delete the customer")
def step_attempt_delete(context):
    """Ask to delete the customer and confirm."""
    _select_delete(context).accept()


@then("the customer is deleted successfully")
def step_deleted(context):
    """Verify the confirmation named the customer and the deletion persisted."""
    assert context.customer["first_name"] in context.confirmation
    context.status_text = _list_status(context)
    open_page(context)
    assert not customer_listed(context, context.customer)


@then("the customer no longer appears in the list")
def step_not_listed(context):
    """Verify the customer's row is gone."""
    assert not customer_listed(context, context.customer)


@then("the UI confirms that the deletion succeeded")
def step_confirms_deletion(context):
    """Verify the success message that was shown after the deletion."""
    assert "customer deleted" in context.status_text


@then("the customer is not deleted")
def step_not_deleted(context):
    """Verify the customer is still stored after the page is reloaded."""
    open_page(context)
    assert customer_listed(context, context.customer)


@then("the customer remains in the list")
def step_remains_listed(context):
    """Verify the customer's row is still shown."""
    assert customer_listed(context, context.customer)


@then("the UI displays an appropriate error message")
def step_error_message(context):
    """Verify the failure message is shown."""
    assert "unable to delete" in _list_status(context)


@then("does not indicate that the customer was deleted")
def step_no_deleted_message(context):
    """Verify the deletion is not reported as successful."""
    assert "customer deleted" not in _list_status(context)
