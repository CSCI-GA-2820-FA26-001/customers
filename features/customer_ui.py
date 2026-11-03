"""Browser helpers shared by the Customers admin UI step definitions."""

import uuid

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

TIMEOUT = 10


def unique(prefix):
    """Return a value that cannot collide with existing customers."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def new_customer(first_name="Ada", last_name="Lovelace", address="1 Analytical Way",
                 active=True):
    """Build the details of a customer whose name and email are unique."""
    first_name = unique(first_name)
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": f"{first_name.lower()}@example.com",
        "address": address,
        "active": active,
    }


def open_page(context, fragment=""):
    """Open the Customers admin page and wait for the customer form."""
    context.driver.get(f"{context.base_url.rstrip('/')}/{fragment}")
    WebDriverWait(context.driver, TIMEOUT).until(
        EC.presence_of_element_located((By.ID, "customer-form"))
    )


def type_into(context, element_id, value):
    """Replace the text of a form field."""
    element = context.driver.find_element(By.ID, element_id)
    element.clear()
    element.send_keys(value)


def wait_for_row(context, text):
    """Wait for and return the table row that contains the given text."""

    def _ready(driver):
        try:
            for row in driver.find_elements(By.CSS_SELECTOR, "#customers tbody tr"):
                if text in row.text:
                    return row
        except StaleElementReferenceException:
            return False
        return False

    return WebDriverWait(context.driver, TIMEOUT).until(_ready)


def create_customer(context, customer):
    """Create a customer through the form and return it with its assigned id."""
    open_page(context)
    type_into(context, "field-first-name", customer["first_name"])
    type_into(context, "field-last-name", customer["last_name"])
    type_into(context, "field-email", customer["email"])
    type_into(context, "field-address", customer.get("address") or "")
    Select(context.driver.find_element(By.ID, "field-active")).select_by_visible_text(
        "Active" if customer.get("active", True) else "Inactive"
    )
    context.driver.find_element(By.ID, "save-customer").click()
    row = wait_for_row(context, customer["first_name"])
    created = dict(customer)
    created["id"] = row.get_attribute("data-customer-id")
    return created


def customer_row(context, customer):
    """Wait for and return the table row of a customer, found by its id."""
    return WebDriverWait(context.driver, TIMEOUT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, f"#customers tbody tr[data-customer-id='{customer['id']}']")
        )
    )


def block_requests(context, url_pattern):
    """Make the browser fail every request that matches the URL pattern."""
    context.driver.execute_cdp_cmd("Network.enable", {})
    context.driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": [url_pattern]})
