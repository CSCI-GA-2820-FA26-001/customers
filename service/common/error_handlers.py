######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Module: error_handlers

Every error is returned as JSON, both for the REST API and for the other
routes, using the same status/error/message structure.
"""

from flask import current_app as app  # Import Flask application
from sqlalchemy.exc import DataError
from werkzeug.exceptions import HTTPException
from service.routes import api
from service.models import db, DataValidationError
from service.common import status


######################################################################
# Helpers
######################################################################
def error_body(code, error, message):
    """Builds the JSON body shared by every error response"""
    return {"status": code, "error": error, "message": message}


######################################################################
# Error Handlers
######################################################################
@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """Handles Value Errors from bad data"""
    message = str(error)
    app.logger.warning(message)
    return (
        error_body(status.HTTP_400_BAD_REQUEST, "Bad Request", message),
        status.HTTP_400_BAD_REQUEST,
    )


@api.errorhandler(DataError)
def data_error(error):
    """Handles values the database cannot store or compare as bad requests"""
    app.logger.warning(str(error))
    db.session.rollback()
    return (
        error_body(
            status.HTTP_400_BAD_REQUEST,
            "Bad Request",
            "A value in the request is not valid",
        ),
        status.HTTP_400_BAD_REQUEST,
    )


@api.errorhandler(HTTPException)
@app.errorhandler(HTTPException)
def http_error(error):
    """Handles every HTTP error (400, 404, 405, 415, ...) with a JSON body"""
    code = error.code or status.HTTP_500_INTERNAL_SERVER_ERROR
    message = error.description
    app.logger.warning("%s %s: %s", code, error.name, message)
    body = error_body(code, error.name, message)

    # Flask-RESTX replaces the handler's body with the exception's own data
    if hasattr(error, "data"):
        errors = error.data.get("errors")
        if errors:
            body["errors"] = errors
        error.data = body
    return body, code


@api.errorhandler(Exception)
def internal_server_error(error):
    """Handles unexpected errors without exposing their details"""
    app.logger.error(str(error), exc_info=error)
    return (
        error_body(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "The server encountered an internal error",
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
