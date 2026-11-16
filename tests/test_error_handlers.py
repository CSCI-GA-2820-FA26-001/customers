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
Error handling and Swagger documentation tests for the Customers API
"""

# pylint: disable=duplicate-code
import os
import json
import logging
from unittest import TestCase
from unittest.mock import patch

from wsgi import app
from service.common import status
from service.models import db, Customer

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres@localhost:5432/testdb"
)
BASE_URL = "/api/customers"
HUGE_ID = 99999999999999999999


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestErrorHandlers(TestCase):
    """Every error must be reported as JSON and never as a server error"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Customer).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    def assert_error(self, response, expected_status, expected_error):
        """Verify the status code and the JSON structure of an error"""
        self.assertEqual(response.status_code, expected_status)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data["status"], expected_status)
        self.assertEqual(data["error"], expected_error)
        self.assertTrue(data["message"])
        return data

    ######################################################################
    #  H T T P   E R R O R S
    ######################################################################

    def test_unknown_url(self):
        """It should return a JSON 404 for a URL that does not exist"""
        response = self.client.get("/nothing-here")
        self.assert_error(response, status.HTTP_404_NOT_FOUND, "Not Found")

    def test_unprefixed_customers_url(self):
        """It should not serve the REST API without the /api prefix"""
        response = self.client.get("/customers")
        self.assert_error(response, status.HTTP_404_NOT_FOUND, "Not Found")

    def test_method_not_allowed_on_api(self):
        """It should return a JSON 405 for an unsupported API method"""
        response = self.client.delete(BASE_URL)
        self.assert_error(
            response, status.HTTP_405_METHOD_NOT_ALLOWED, "Method Not Allowed"
        )

    def test_method_not_allowed_outside_api(self):
        """It should return a JSON 405 for an unsupported method elsewhere"""
        response = self.client.post("/health")
        self.assert_error(
            response, status.HTTP_405_METHOD_NOT_ALLOWED, "Method Not Allowed"
        )

    def test_unsupported_media_type(self):
        """It should return a JSON 415 when the body is not JSON"""
        response = self.client.post(
            BASE_URL, data="not JSON", content_type="text/plain"
        )
        self.assert_error(
            response, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported Media Type"
        )

    def test_malformed_json(self):
        """It should return a JSON 400 when the JSON cannot be parsed"""
        response = self.client.post(
            BASE_URL, data='{"first_name":', content_type="application/json"
        )
        self.assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")
        self.assertEqual(Customer.query.count(), 0)

    def test_missing_customer_message(self):
        """It should explain which customer was not found without extra hints"""
        response = self.client.put(f"{BASE_URL}/9999", json={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.get_json()["message"],
            "Customer with id '9999' was not found.",
        )

    ######################################################################
    #  I N V A L I D   D A T A
    ######################################################################

    def test_validation_error(self):
        """It should return a JSON 400 for a body that is not a customer"""
        for body in ('["a list"]', '"a string"', "null", '{"first_name": "Ada"}'):
            response = self.client.post(
                BASE_URL, data=body, content_type="application/json"
            )
            self.assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")
        self.assertEqual(Customer.query.count(), 0)

    def test_invalid_active_filter(self):
        """It should return a JSON 400 for an active filter that is not a boolean"""
        response = self.client.get(f"{BASE_URL}?active=banana")
        data = self.assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")
        self.assertIn("active", data["errors"])

    def test_customer_id_out_of_range(self):
        """It should return a JSON 400 for an id the database cannot represent"""
        urls = (
            ("get", f"{BASE_URL}/{HUGE_ID}"),
            ("delete", f"{BASE_URL}/{HUGE_ID}"),
            ("put", f"{BASE_URL}/{HUGE_ID}/activate"),
            ("put", f"{BASE_URL}/{HUGE_ID}/deactivate"),
        )
        for method, url in urls:
            response = getattr(self.client, method)(url)
            self.assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")

    def test_update_customer_id_out_of_range(self):
        """It should return a JSON 400 when updating an id that is out of range"""
        payload = {"first_name": "Ada", "last_name": "Lovelace", "email": "a@b.c"}
        response = self.client.put(f"{BASE_URL}/{HUGE_ID}", json=payload)
        self.assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")

    def test_query_with_null_character(self):
        """It should return a JSON 400 for a query value the database rejects"""
        for field in ("first_name", "last_name", "email"):
            response = self.client.get(f"{BASE_URL}?{field}=%00")
            self.assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")

    def test_non_numeric_customer_id(self):
        """It should return a JSON 404 when the id is not a number"""
        response = self.client.get(f"{BASE_URL}/abc")
        self.assert_error(response, status.HTTP_404_NOT_FOUND, "Not Found")

    ######################################################################
    #  U N E X P E C T E D   E R R O R S
    ######################################################################

    def test_unexpected_error(self):
        """It should hide the details of an unexpected error in a JSON 500"""
        with patch.object(Customer, "all", side_effect=RuntimeError("secret")):
            response = self.client.get(BASE_URL)
        data = self.assert_error(
            response,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error",
        )
        self.assertNotIn("secret", data["message"])

    ######################################################################
    #  R E G R E S S I O N   T E S T S
    ######################################################################

    def test_deeply_nested_json(self):
        """It should return a JSON 400 for a body nested too deeply to parse"""
        customer = Customer(first_name="Ada", last_name="Lovelace", email="a@b.c")
        customer.create()
        body = "[" * 100000
        for method, url in (
            ("post", BASE_URL),
            ("put", f"{BASE_URL}/{customer.id}"),
        ):
            response = getattr(self.client, method)(
                url, data=body, content_type="application/json"
            )
            data = self.assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")
            self.assertIn("nested", data["message"])

    def test_database_errors_hide_details(self):
        """It should not expose SQL or driver details when the database rejects data"""
        customer = Customer(first_name="Ada", last_name="Lovelace", email="a@b.c")
        customer.create()
        rejected = (
            "a\u0000b",  # a NUL character cannot be stored in a text column
            "x" * 100,  # longer than the first_name column
        )
        for first_name in rejected:
            payload = json.dumps(
                {"first_name": first_name, "last_name": "L", "email": "a@b.c"}
            )
            for method, url in (
                ("post", BASE_URL),
                ("put", f"{BASE_URL}/{customer.id}"),
            ):
                response = getattr(self.client, method)(
                    url, data=payload, content_type="application/json"
                )
                data = self.assert_error(
                    response, status.HTTP_400_BAD_REQUEST, "Bad Request"
                )
                for detail in ("SQL", "psycopg", "INSERT", "UPDATE", "VARCHAR"):
                    self.assertNotIn(detail, data["message"])
        stored = Customer.find(customer.id)
        self.assertEqual(stored.first_name, "Ada")

    def test_database_error_on_delete_hides_details(self):
        """It should report a failed delete without database details"""
        customer = Customer(first_name="Ada", last_name="Lovelace", email="a@b.c")
        customer.create()
        with patch.object(
            db.session, "commit", side_effect=RuntimeError("SQL: DELETE FROM customer")
        ):
            response = self.client.delete(f"{BASE_URL}/{customer.id}")
        data = self.assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")
        self.assertNotIn("DELETE", data["message"])


class TestSwaggerDocumentation(TestCase):
    """The REST API must be documented with Swagger"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.logger.setLevel(logging.CRITICAL)

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()

    def test_apidocs(self):
        """It should serve the Swagger UI at /apidocs/"""
        response = self.client.get("/apidocs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/html", response.content_type)
        self.assertIn("swagger", response.get_data(as_text=True).lower())

    def test_swagger_paths(self):
        """It should document every customer path under the /api prefix"""
        response = self.client.get("/api/swagger.json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        spec = response.get_json()
        self.assertEqual(spec["basePath"], "/api")
        self.assertEqual(
            set(spec["paths"]),
            {
                "/customers",
                "/customers/{customer_id}",
                "/customers/{customer_id}/activate",
                "/customers/{customer_id}/deactivate",
            },
        )

    def test_swagger_data_models(self):
        """It should document the customer payloads as data models"""
        spec = self.client.get("/api/swagger.json").get_json()
        models = spec["definitions"]
        self.assertEqual(
            set(models["Customer"]["properties"]),
            {"first_name", "last_name", "email", "address", "active"},
        )
        self.assertEqual(
            set(models["Customer"]["required"]),
            {"first_name", "last_name", "email"},
        )
        parts = models["CustomerModel"]["allOf"]
        self.assertIn({"$ref": "#/definitions/Customer"}, parts)
        self.assertIn("id", [part for part in parts if "properties" in part][0]["properties"])
