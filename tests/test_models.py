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
Test cases for Customer Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from unittest.mock import patch

from wsgi import app
from service.models import Customer, DataValidationError, db
from .factories import CustomerFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  Customer   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestCustomer(TestCase):
    """Test Cases for Customer Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Customer).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_repr_customer(self):
        """It should return a useful customer representation."""
        customer = Customer(
            id=10,
            email="ada@example.com",
        )

        self.assertEqual(
            repr(customer),
            "<Customer ada@example.com id=[10]>",
        )

    def test_deserialize_customer(self):
        """It should deserialize all customer attributes."""
        customer = Customer()
        data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "address": "123 Example Street",
            "active": True,
        }

        customer.deserialize(data)

        self.assertEqual(customer.first_name, "Ada")
        self.assertEqual(customer.last_name, "Lovelace")
        self.assertEqual(customer.email, "ada@example.com")
        self.assertEqual(customer.address, "123 Example Street")
        self.assertTrue(customer.active)

    def test_deserialize_rejects_non_string_address(self):
        """It should reject an address that is not a string."""
        customer = Customer()
        data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "address": 123,
        }

        with self.assertRaises(DataValidationError):
            customer.deserialize(data)

    def test_deserialize_missing_email(self):
        """It should reject a customer without an email."""
        customer = Customer()
        data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
        }

        with self.assertRaises(DataValidationError):
            customer.deserialize(data)

    def test_deserialize_empty_email(self):
        """It should reject an empty email."""
        customer = Customer()
        data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "",
        }

        with self.assertRaises(DataValidationError):
            customer.deserialize(data)

    def test_deserialize_missing_first_name(self):
        """It should reject a customer without a first name."""
        customer = Customer()
        data = {
            "last_name": "Lovelace",
            "email": "ada@example.com",
        }

        with self.assertRaises(DataValidationError):
            customer.deserialize(data)

    def test_deserialize_missing_last_name(self):
        """It should reject a customer without a last name."""
        customer = Customer()
        data = {
            "first_name": "Ada",
            "email": "ada@example.com",
        }

        with self.assertRaises(DataValidationError):
            customer.deserialize(data)

    def test_deserialize_defaults_active_to_true(self):
        """It should default active to True when omitted."""
        customer = Customer()
        data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
        }

        customer.deserialize(data)

        self.assertIs(customer.active, True)

    def test_deserialize_preserves_inactive_customer(self):
        """It should preserve an explicitly supplied False value."""
        customer = Customer()
        data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "active": False,
        }

        customer.deserialize(data)

        self.assertIs(customer.active, False)

    def test_deserialize_rejects_non_boolean_active(self):
        """It should reject a non-boolean active value."""
        customer = Customer()
        data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "active": "false",
        }

        with self.assertRaises(DataValidationError):
            customer.deserialize(data)

    def test_deserialize_invalid_data(self):
        """It should reject a missing request body."""
        customer = Customer()

        with self.assertRaises(DataValidationError):
            customer.deserialize(None)

    def test_serialize_customer(self):
        """It should serialize all customer attributes."""
        customer = CustomerFactory()
        customer.id = 10

        data = customer.serialize()

        self.assertEqual(data["id"], 10)
        self.assertEqual(data["first_name"], customer.first_name)
        self.assertEqual(data["last_name"], customer.last_name)
        self.assertEqual(data["email"], customer.email)
        self.assertEqual(data["address"], customer.address)
        self.assertEqual(data["active"], customer.active)

    def test_delete_customer(self):
        """It should remove a customer from the database."""
        customer = CustomerFactory()
        customer.create()
        customer_id = customer.id

        customer.delete()

        self.assertIsNone(Customer.find(customer_id))

    def test_update_customer(self):
        """It should persist changes to an existing customer."""
        customer = CustomerFactory()
        customer.create()
        customer.first_name = "Grace"

        customer.update()

        found = Customer.find(customer.id)
        self.assertEqual(found.first_name, "Grace")

    def test_all_customers(self):
        """It should return all customers in the database."""
        CustomerFactory().create()
        CustomerFactory().create()

        customers = Customer.all()

        self.assertEqual(len(customers), 2)

    def test_create_customer(self):
        """It should persist a customer and assign an ID."""
        customer = CustomerFactory()

        customer.create()

        self.assertIsNotNone(customer.id)

        found = Customer.find(customer.id)

        self.assertIsNotNone(found)
        self.assertEqual(found.email, customer.email)
        self.assertEqual(found.first_name, customer.first_name)
        self.assertEqual(found.last_name, customer.last_name)
        self.assertEqual(found.address, customer.address)
        self.assertEqual(found.active, customer.active)

    def test_create_customer_database_error(self):
        """It should roll back and raise an error if creation fails."""
        customer = CustomerFactory()

        with (
            patch(
                "service.models.db.session.commit",
                side_effect=Exception("database failure"),
            ),
            patch("service.models.db.session.rollback") as mock_rollback,
        ):
            with self.assertRaises(DataValidationError):
                customer.create()

        mock_rollback.assert_called_once()

    def test_update_customer_database_error(self):
        """It should roll back and raise an error if updating fails."""
        customer = CustomerFactory()

        with (
            patch(
                "service.models.db.session.commit",
                side_effect=Exception("database failure"),
            ),
            patch("service.models.db.session.rollback") as mock_rollback,
        ):
            with self.assertRaises(DataValidationError):
                customer.update()

        mock_rollback.assert_called_once()

    def test_create_customer_missing_email(self):
        """It should reject a customer without an email."""
        customer = Customer(first_name="Ada", last_name="Lovelace")

        with self.assertRaises(DataValidationError):
            customer.create()

        self.assertEqual(Customer.all(), [])

    def test_delete_customer_database_error(self):
        """It should roll back and raise an error if deletion fails."""
        customer = CustomerFactory()
        customer.create()

        with (
            patch(
                "service.models.db.session.commit",
                side_effect=Exception("database failure"),
            ),
            patch("service.models.db.session.rollback") as mock_rollback,
        ):
            with self.assertRaises(DataValidationError):
                customer.delete()

        mock_rollback.assert_called_once()
