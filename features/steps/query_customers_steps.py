"""Step definitions for the Query Customers UI (story #32)."""

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from customer_ui import (
    TIMEOUT,
    block_requests,
    create_customer,
    new_customer,
    open_page,
    type_into,
    unique,
)

ATTRIBUTES = {
    "first name": ("First name", "first_name"),
    "last name": ("Last name", "last_name"),
    "email address": ("Email address", "email"),
}


def _create_customers(context, statuses):
    """Create one customer per active status through the web UI."""
    context.customers = [
        create_customer(
            context, new_customer(last_name=unique("Surname"), active=active)
        )
        for active in statuses
    ]
    context.target = context.customers[0]


def _wait_for_results(context):
    """Wait until the customer list has finished loading."""
    WebDriverWait(context.driver, TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#customers[data-state='ready']"))
    )


def _rows(context):
    """Return the displayed customer rows once the list has loaded."""
    _wait_for_results(context)
    return context.driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr")


def _listed_ids(context):
    """Return the ids of the displayed customers."""
    return {row.get_attribute("data-customer-id") for row in _rows(context)}


def _search_by(context, label):
    """Choose the attribute to search by."""
    Select(context.driver.find_element(By.ID, "search-attribute")).select_by_visible_text(
        label
    )


def _submit_search(context):
    """Submit the search form."""
    context.driver.find_element(By.ID, "search-submit").click()


@given("multiple customers exist with different attributes")
def step_multiple_customers(context):
    """Create active and inactive customers through the web UI."""
    _create_customers(context, [True, False, True])


@given("customers exist in the system")
def step_customers_exist(context):
    """Create a couple of customers through the web UI."""
    _create_customers(context, [True, True])


@given("I have filtered the customer list using a query")
def step_filtered_list(context):
    """Search by the last name of one customer."""
    open_page(context)
    _search_by(context, "Last name")
    type_into(context, "search-value", context.target["last_name"])
    _submit_search(context)
    assert _listed_ids(context) == {context.target["id"]}


@given("searching for customers will fail")
def step_search_will_fail(context):
    """Make filtered list requests fail in the browser."""
    open_page(context)
    block_requests(context, "*/customers?*")


@when("I enter that customer's {attribute} in the search field")
def step_enter_attribute(context, attribute):
    """Search by one attribute of the target customer."""
    label, key = ATTRIBUTES[attribute]
    value = context.target[key]
    _search_by(context, label)
    type_into(context, "search-value", value)
    context.matches = lambda text: value in text


@when("I submit the search")
def step_submit_search(context):
    """Submit the search form."""
    _submit_search(context)


@when("I search for inactive customers")
def step_search_inactive(context):
    """Search by account status."""
    context.target = next(c for c in context.customers if not c["active"])
    _search_by(context, "Account status")
    Select(context.driver.find_element(By.ID, "search-status")).select_by_visible_text(
        "Inactive"
    )
    context.matches = lambda text: "Inactive" in text
    _submit_search(context)


@when("I search using an attribute value that matches no customers")
def step_search_no_match(context):
    """Search for a last name that no customer has."""
    open_page(context)
    _search_by(context, "Last name")
    type_into(context, "search-value", unique("NoSuchSurname"))
    _submit_search(context)


@when("I clear the search criteria")
def step_clear_search(context):
    """Clear the search."""
    context.driver.find_element(By.ID, "search-clear").click()


@then("only customers matching the specified criteria are displayed")
def step_only_matching(context):
    """Verify the target is listed and every displayed customer matches."""
    rows = _rows(context)
    assert rows, "expected at least one matching customer"
    for row in rows:
        assert context.matches(row.text), f"unexpected customer displayed: {row.text}"
    listed = _listed_ids(context)
    assert context.target["id"] in listed
    for customer in context.customers:
        if not context.matches(f"{customer['first_name']} {customer['last_name']} "
                               f"{customer['email']} "
                               f"{'Active' if customer['active'] else 'Inactive'}"):
            assert customer["id"] not in listed


@then("no customer records are displayed")
def step_no_records(context):
    """Verify the list is empty."""
    assert not _rows(context)


@then("the UI indicates that no matching customers were found")
def step_no_matches_message(context):
    """Verify the no-match message is shown instead of the empty-directory text."""
    message = WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "no-matches"))
    )
    assert "no matching customers" in message.text.lower()
    assert not context.driver.find_element(By.ID, "empty").is_displayed()


@then("the full customer list is displayed again")
def step_full_list(context):
    """Verify every customer is listed again and the search is cleared."""
    _wait_for_results(context)
    WebDriverWait(context.driver, TIMEOUT).until(
        lambda _: {c["id"] for c in context.customers} <= _listed_ids(context)
    )
    assert context.driver.find_element(By.ID, "search-value").get_attribute("value") == ""


@then("the UI reports that the search could not be completed")
def step_search_failed(context):
    """Verify the load error is shown."""
    error = WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "error"))
    )
    assert "unable to load" in error.text.lower()
