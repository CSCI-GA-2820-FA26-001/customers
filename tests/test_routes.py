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
TestCustomer API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Customer

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestCustomerService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
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

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should call the home page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_customer_unsupported_media_type(self):
        """It should reject requests that are not JSON."""
        response = self.client.post(
            "/customers",
            data="not JSON",
            content_type="text/plain",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )
        self.assertEqual(Customer.query.count(), 0)

    def test_create_customer(self):
        """It should create a customer and return 201 Created."""
        payload = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada.lovelace@example.com",
            "address": "123 Analytical Engine Way",
            "active": True,
        }

        response = self.client.post("/customers", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.get_json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(data["first_name"], payload["first_name"])
        self.assertEqual(data["last_name"], payload["last_name"])
        self.assertEqual(data["email"], payload["email"])
        self.assertEqual(data["address"], payload["address"])
        self.assertEqual(data["active"], payload["active"])

        self.assertIn("Location", response.headers)
        self.assertTrue(
            response.headers["Location"].endswith(f"/customers/{data['id']}")
        )

        # Verify the customer was persisted.
        customer = Customer.find(data["id"])
        self.assertIsNotNone(customer)
        self.assertEqual(customer.email, payload["email"])

    def test_create_customer_with_optional_fields_omitted(self):
        """It should default address to None and active to True."""
        payload = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada.lovelace@example.com",
        }

        response = self.client.post("/customers", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.get_json()
        self.assertIsNotNone(data["id"])
        self.assertIsNone(data["address"])
        self.assertTrue(data["active"])

        # Verify the defaults were persisted.
        customer = Customer.find(data["id"])
        self.assertIsNotNone(customer)
        self.assertIsNone(customer.address)
        self.assertTrue(customer.active)

    def test_create_customer_invalid_data(self):
        """It should reject invalid customer data without persisting it."""
        payload = {
            "first_name": "",
            "last_name": "Lovelace",
            "email": "ada.lovelace@example.com",
        }

        response = self.client.post("/customers", json=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Customer.query.count(), 0)

    def test_read_customer(self):
        """Read a single customer"""
        customer = Customer(
            first_name="Jane",
            last_name="Doe",
            email="janedoe@gmail.com",
            address="123 Main St",
            active=True,
        )
        customer.create()
        response = self.client.get(f"/customers/{customer.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], customer.id)
        self.assertEqual(data["first_name"], customer.first_name)
        self.assertEqual(data["last_name"], customer.last_name)
        self.assertEqual(data["email"], customer.email)
        self.assertEqual(data["address"], customer.address)
        self.assertEqual(data["active"], customer.active)

    def test_read_customer_not_found(self):
        """Return 404 if customer does not exist"""
        response = self.client.get("/customers/99999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
