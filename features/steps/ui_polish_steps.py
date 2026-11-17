"""Step definitions for the list accuracy and navigation fixes (issue #67).

All checks go through the browser. Slow and failing requests are simulated
inside the browser only, so no REST calls or database access are used.
"""

from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from customer_ui import (
    TIMEOUT,
    block_requests,
    create_customer,
    customer_listed,
    customer_row,
    new_customer,
    type_into,
)

SLOW_DELAY_MS = 2000

# Delays every fetch whose URL contains the token, then raises a flag a
# moment after the delayed response arrives so the test knows it was handled.
SLOW_FETCH_SCRIPT = """
const token = arguments[0];
const delay = arguments[1];
const originalFetch = window.fetch;
window.slowFetchDone = false;
window.fetch = (url, options) => {
  if (!String(url).includes(token)) {
    return originalFetch(url, options);
  }
  return new Promise((resolve) => setTimeout(resolve, delay))
    .then(() => originalFetch(url, options))
    .then((response) => {
      setTimeout(() => { window.slowFetchDone = true; }, 500);
      return response;
    });
};
"""


def _search_first_name(context, first_name):
    """Search the list by first name through the search form."""
    type_into(context, "search-value", first_name)
    context.driver.find_element(By.ID, "search-submit").click()


@given("two customers exist with different first names")
def step_two_customers(context):
    """Create two customers through the web UI."""
    context.first = create_customer(context, new_customer(first_name="Early"))
    context.second = create_customer(context, new_customer(first_name="Late"))


@given("searches for the first customer respond slowly")
def step_first_search_slow(context):
    """Delay, inside the browser, every request that searches for the first customer."""
    context.driver.execute_script(
        SLOW_FETCH_SCRIPT, context.first["first_name"], SLOW_DELAY_MS
    )


@when("I search the list for the first customer's first name")
def step_search_first(context):
    """Start the slow search for the first customer."""
    _search_first_name(context, context.first["first_name"])


@when("I search the list for the second customer's first name")
def step_search_second(context):
    """Start a newer search for the second customer."""
    _search_first_name(context, context.second["first_name"])
    customer_row(context, context.second)


@then("only the second customer is listed once both searches finish")
def step_only_second_listed(context):
    """Wait for the slow search to finish, then verify the newer result remains."""
    WebDriverWait(context.driver, TIMEOUT).until(
        lambda driver: driver.execute_script("return window.slowFetchDone === true;")
    )
    assert customer_listed(context, context.second), "the newer search result was replaced"
    assert not customer_listed(context, context.first), (
        "the older, slower search overwrote the newer result"
    )


@given("I have searched the list for that customer's first name")
def step_searched_for_customer(context):
    """Filter the list down to the customer."""
    _search_first_name(context, context.customer["first_name"])
    customer_row(context, context.customer)


@given("loading the full customer list will fail")
def step_full_list_fails(context):
    """Make the unfiltered list request fail in the browser; filtered requests still work."""
    block_requests(context, "*/api/customers")


@then("that customer is still listed")
def step_customer_still_listed(context):
    """Verify the last good result stays on the page."""
    WebDriverWait(context.driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "error"))
    )
    assert customer_listed(context, context.customer), (
        "the failed request removed results that were already on the page"
    )


@then("the UI shows that the customer list could not be loaded")
def step_list_error_shown(context):
    """Verify the load error message."""
    error = context.driver.find_element(By.ID, "error")
    assert error.is_displayed()
    assert "unable to load" in error.text.lower()


@when('I click "Search records" in the sidebar')
def step_click_search_records(context):
    """Click the sidebar link to the customer search."""
    link = WebDriverWait(context.driver, TIMEOUT).until(
        EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Search records"))
    )
    link.click()


@then("the customer search field is ready for input")
def step_search_field_focused(context):
    """Verify the search field is visible and has the keyboard focus."""
    field = context.driver.find_element(By.ID, "search-value")
    assert field.is_displayed()
    WebDriverWait(context.driver, TIMEOUT).until(
        lambda driver: driver.switch_to.active_element == field
    )


@then('the sidebar shows no "Coming soon" links')
def step_no_placeholder_links(context):
    """Verify every sidebar link is a real destination, not a placeholder."""
    links = context.driver.find_elements(By.CSS_SELECTOR, ".sidebar a")
    assert links, "expected the sidebar to have links"
    placeholders = [
        link.text for link in links if link.get_attribute("title") == "Coming soon"
    ]
    assert not placeholders, f"placeholder sidebar links found: {placeholders}"
