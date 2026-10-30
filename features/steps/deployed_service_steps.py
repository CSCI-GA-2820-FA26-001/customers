"""BDD steps for verifying the deployed Customers service."""

from urllib.request import urlopen
from behave import given, when, then


@given("the Customers service is deployed")
def step_service_deployed(context):
    """Verify that a deployment URL has been configured."""
    assert context.base_url, "BASE_URL must be configured"


@when("I request the Customers service health endpoint")
def step_request_health(context):
    """Request the deployed service health endpoint."""
    url = f"{context.base_url.rstrip('/')}/health"

    with urlopen(url, timeout=10) as response:
        context.response_status = response.status


@then("the service should return HTTP 200")
def step_check_status(context):
    """Verify that the deployed service responds successfully."""
    assert context.response_status == 200
