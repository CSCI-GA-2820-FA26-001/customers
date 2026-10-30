"""Step definitions for checking the BDD test environment."""

from behave import given, then


@given("the BDD environment is configured")
def step_bdd_environment_configured(context):
    """Check that the environment hook initialized the context."""
    assert hasattr(context, "bdd_environment_ready")


@then("the BDD environment should be ready")
def step_bdd_environment_ready(context):
    """Verify the BDD environment initialization completed."""
    assert context.bdd_environment_ready is True
