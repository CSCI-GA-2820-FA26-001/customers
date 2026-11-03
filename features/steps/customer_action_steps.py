"""Step definitions for the Perform Customer Action UI (story #33).

The supported action is the activate/deactivate action of Story #23: it
switches a customer between the Active and Inactive account states.
"""

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


def _state(context):
    """Return the displayed account status and action label of the customer."""
    row = customer_row(context, context.customer)
    return (
        row.find_element(By.CSS_SELECTOR, ".pill").text,
        row.find_element(By.CSS_SELECTOR, ".action-btn").text,
    )


def _list_status(context):
    """Wait for the list status message and return its text."""
    return WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "list-status"))
    ).text.lower()


def _click_action(context):
    """Select the action control of the customer."""
    context.state_before = _state(context)
    customer_row(context, context.customer).find_element(
        By.CSS_SELECTOR, ".action-btn"
    ).click()


@given("an inactive customer exists in the system")
def step_inactive_customer_exists(context):
    """Create an inactive customer through the web UI."""
    context.customer = create_customer(context, new_customer(active=False))


@given("I am viewing that customer's information")
def step_viewing_customer(context):
    """Open the admin page, where the customer's row is shown."""
    open_page(context)
    customer_row(context, context.customer)


@given("the customer action will fail")
def step_action_will_fail(context):
    """Make requests for a single customer fail in the browser."""
    block_requests(context, "*/customers/*")


@when("I select the supported customer action")
def step_select_action(context):
    """Use the Activate or Deactivate control."""
    _click_action(context)


@when("I attempt to perform the customer action")
def step_attempt_action(context):
    """Use the Activate or Deactivate control while the request fails."""
    _click_action(context)


@then("the action is performed successfully")
def step_action_performed(context):
    """Verify the state changed on screen and was saved on the server."""
    context.status_text = _list_status(context)
    WebDriverWait(context.driver, TIMEOUT).until(
        lambda _: _state(context) != context.state_before
    )
    context.state_after = _state(context)
    expected = "Inactive" if context.state_before[0] == "Active" else "Active"
    open_page(context)
    assert _state(context)[0] == expected


@then("the customer's updated state is displayed")
def step_updated_state(context):
    """Verify the status and the offered action both changed on screen."""
    if context.state_before[0] == "Active":
        assert context.state_after == ("Inactive", "Activate")
    else:
        assert context.state_after == ("Active", "Deactivate")


@then("the UI confirms that the action succeeded")
def step_action_confirmed(context):
    """Verify the success message shown after the action."""
    verb = "deactivated" if context.state_before[0] == "Active" else "activated"
    assert f"customer {verb}" in context.status_text


@then("the UI reports that the customer action failed")
def step_action_failed(context):
    """Verify the failure message is shown."""
    assert "unable to" in _list_status(context)


@then("does not indicate that the action succeeded")
def step_no_success(context):
    """Verify no success message is shown."""
    status = _list_status(context)
    assert "customer activated" not in status
    assert "customer deactivated" not in status


@then("the customer's state is unchanged")
def step_state_unchanged(context):
    """Verify the displayed state did not change."""
    assert _state(context) == context.state_before
