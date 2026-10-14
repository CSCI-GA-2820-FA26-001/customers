"""Tests for the application's shared error handlers."""

# The import must happen inside the application context because the handlers
# use Flask's current_app when registering their decorators.
# pylint: disable=import-outside-toplevel,redefined-outer-name

import pytest
from flask import Flask

from service.common import status
from service.models import DataValidationError


@pytest.fixture
def handlers():
    """Import error handlers inside an active Flask application context."""
    test_app = Flask(__name__)

    with test_app.app_context():
        from service.common import error_handlers

        yield error_handlers


def assert_error_response(result, expected_status, expected_error, error):
    """Verify the status code and JSON response returned by a handler."""
    response, actual_status = result

    assert actual_status == expected_status
    assert response.get_json() == {
        "status": expected_status,
        "error": expected_error,
        "message": str(error),
    }


def test_request_validation_error(handlers):
    """Return a 400 response for invalid customer data."""
    error = DataValidationError("Invalid customer data")

    result = handlers.request_validation_error(error)

    assert_error_response(result, status.HTTP_400_BAD_REQUEST, "Bad Request", error)


def test_bad_request(handlers):
    """Return a 400 response for a bad request."""
    error = ValueError("Invalid request")

    result = handlers.bad_request(error)

    assert_error_response(result, status.HTTP_400_BAD_REQUEST, "Bad Request", error)


def test_not_found(handlers):
    """Return a 404 response when a resource is not found."""
    error = ValueError("Customer not found")

    result = handlers.not_found(error)

    assert_error_response(result, status.HTTP_404_NOT_FOUND, "Not Found", error)


def test_method_not_supported(handlers):
    """Return a 405 response for an unsupported HTTP method."""
    error = ValueError("Method not allowed")

    result = handlers.method_not_supported(error)

    assert_error_response(
        result,
        status.HTTP_405_METHOD_NOT_ALLOWED,
        "Method not Allowed",
        error,
    )


def test_mediatype_not_supported(handlers):
    """Return a 415 response for an unsupported media type."""
    error = ValueError("Unsupported content type")

    result = handlers.mediatype_not_supported(error)

    assert_error_response(
        result,
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "Unsupported media type",
        error,
    )


def test_internal_server_error(handlers):
    """Return a 500 response for an unexpected server error."""
    error = RuntimeError("Unexpected server failure")

    result = handlers.internal_server_error(error)

    assert_error_response(
        result,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Internal Server Error",
        error,
    )
