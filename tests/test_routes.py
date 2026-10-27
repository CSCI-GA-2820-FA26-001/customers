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
from .factories import CustomerFactory

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
        """It should return useful JSON identifying the Customers service."""
        response = self.client.get("/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.is_json)
        self.assertEqual(
            response.get_json(),
            {"name": "Customers Service"},
        )
        self.assertNotIn(
            "Reminder",
            response.get_data(as_text=True),
        )

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

    def test_list_customers_empty(self):
        """It should return an empty list when no customers exist."""
        response = self.client.get("/customers")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_list_customers(self):
        """It should return all persisted customers."""
        # Create five customers in the database.
        customers = []
        for _ in range(5):
            customer = CustomerFactory()
            customer.create()
            customers.append(customer)

        response = self.client.get("/customers")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)

        expected = sorted(
            (customer.serialize() for customer in customers),
            key=lambda customer: customer["email"],
        )
        returned = sorted(data, key=lambda customer: customer["email"])

        self.assertEqual(returned, expected)

    def test_query_customers_by_first_name(self):
        """It should return customers matching a first name."""
        CustomerFactory(first_name="Ada").create()
        CustomerFactory(first_name="Grace").create()

        response = self.client.get("/customers?first_name=Ada")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["first_name"], "Ada")

    def test_query_customers_by_last_name(self):
        """It should return customers matching a last name."""
        CustomerFactory(last_name="Smith").create()
        CustomerFactory(last_name="Jones").create()

        response = self.client.get("/customers?last_name=Smith")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["last_name"], "Smith")

    def test_query_customers_by_email(self):
        """It should return customers matching an email."""
        CustomerFactory(email="ada@example.com").create()
        CustomerFactory(email="grace@example.com").create()

        response = self.client.get("/customers?email=ada@example.com")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["email"], "ada@example.com")

    def test_query_customers_by_active(self):
        """It should return customers matching their active status."""
        CustomerFactory(active=True).create()
        CustomerFactory(active=False).create()

        response = self.client.get("/customers?active=false")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertFalse(data[0]["active"])

    def test_query_customers_no_match(self):
        """It should return an empty list when no customers match."""
        CustomerFactory(first_name="Ada").create()

        response = self.client.get("/customers?first_name=Nobody")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_read_customer(self):
        """Read a single customer."""
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
        """Return 404 if customer does not exist."""
        response = self.client.get("/customers/99999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.get_json(), {"error": "Customer not found"})

    def test_update_customer(self):
        """It should update an existing customer."""
        customer = CustomerFactory()
        customer.create()
        customer_id = customer.id

        updated = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test.user@example.com",
            "address": "1 Test St",
            "active": False,
        }

        response = self.client.put(f"/customers/{customer_id}", json=updated)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], customer_id)
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "User")
        self.assertEqual(data["email"], "test.user@example.com")
        self.assertEqual(data["address"], "1 Test St")
        self.assertFalse(data["active"])

        # Verify the changes were persisted.
        persisted = Customer.find(customer_id)
        self.assertEqual(persisted.first_name, "Test")
        self.assertEqual(persisted.email, "test.user@example.com")

    def test_update_customer_not_found(self):
        """It should return 404 when updating a customer that does not exist."""
        response = self.client.put(
            "/customers/9999",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "test.user@example.com",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_customer_invalid_data(self):
        """It should reject invalid updates without modifying the customer."""
        customer = CustomerFactory()
        customer.create()
        customer_id = customer.id
        original_email = customer.email

        response = self.client.put(
            f"/customers/{customer_id}",
            json={
                "first_name": "",
                "last_name": "User",
                "email": "new@example.com",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # The failed update must not change the persisted record.
        db.session.rollback()
        persisted = Customer.find(customer_id)
        self.assertEqual(persisted.email, original_email)

    def test_delete_customer(self):
        """It should delete a customer without changing other customers."""
        customer = CustomerFactory()
        customer.create()
        customer_id = customer.id

        other = CustomerFactory()
        other.create()
        other_id = other.id
        original_other = other.serialize()

        response = self.client.delete(f"/customers/{customer_id}")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        # Verify the customer was actually deleted.
        response = self.client.get(f"/customers/{customer_id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIsNone(Customer.find(customer_id))

        # Verify the other customer was not modified.
        response = self.client.get(f"/customers/{other_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), original_other)
        self.assertEqual(Customer.query.count(), 1)

    def test_delete_customer_not_found(self):
        """It should return 204 when the customer does not exist."""
        customer = CustomerFactory()
        customer.create()
        original = customer.serialize()
        missing_id = customer.id + 1

        response = self.client.delete(f"/customers/{missing_id}")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")
        self.assertEqual(Customer.query.count(), 1)
        self.assertEqual(Customer.find(customer.id).serialize(), original)

    def test_delete_customer_twice(self):
        """It should return 204 when deleting the same customer twice."""
        customer = CustomerFactory()
        customer.create()
        customer_id = customer.id

        response = self.client.delete(f"/customers/{customer_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")

        response = self.client.delete(f"/customers/{customer_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")
        self.assertEqual(Customer.query.count(), 0)

    def test_activate_customer(self):
        """It should activate an inactive customer."""
        customer = CustomerFactory(active=False)
        customer.create()
        customer_id = customer.id
        self.assertFalse(customer.active)

        response = self.client.put(f"/customers/{customer_id}/activate")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], customer_id)
        self.assertTrue(data["active"])

        # Verify the change was persisted.
        persisted = Customer.find(customer_id)
        self.assertTrue(persisted.active)

    def test_deactivate_customer(self):
        """It should deactivate an active customer."""
        customer = CustomerFactory(active=True)
        customer.create()
        customer_id = customer.id
        self.assertTrue(customer.active)

        response = self.client.put(f"/customers/{customer_id}/deactivate")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["id"], customer_id)
        self.assertFalse(data["active"])

        # Verify the change was persisted.
        persisted = Customer.find(customer_id)
        self.assertFalse(persisted.active)

    def test_activate_customer_not_found(self):
        """It should return 404 when activating a customer that does not exist."""
        response = self.client.put("/customers/9999/activate")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deactivate_customer_not_found(self):
        """It should return 404 when deactivating a customer that does not exist."""
        response = self.client.put("/customers/9999/deactivate")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
