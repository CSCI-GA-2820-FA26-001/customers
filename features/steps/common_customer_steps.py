"""Steps shared by the Customers admin UI features."""

from behave import given

from customer_ui import create_customer, new_customer, open_page


@given("a customer exists in the system")
def step_customer_exists(context):
    """Create a customer through the web UI."""
    context.customer = create_customer(context, new_customer())


@given("I am viewing the customer list")
def step_viewing_customer_list(context):
    """Open the Customers admin page."""
    open_page(context)
