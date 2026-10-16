"""
Models for Customer

All models are stored in this module.
"""

import logging

from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for data validation errors when deserializing."""


class Customer(db.Model):
    """Class that represents a customer."""

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(256), nullable=False)
    address = db.Column(db.String(256), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<Customer {self.email} id=[{self.id}]>"

    def create(self):
        """Creates a customer in the database."""
        logger.info("Creating customer %s", self.email)
        self.id = None  # pylint: disable=invalid-name

        try:
            db.session.add(self)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            logger.error("Error creating customer: %s", self)
            raise DataValidationError(error) from error

    def update(self):
        """Updates a customer in the database."""
        logger.info("Updating customer %s", self.email)

        try:
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            logger.error("Error updating customer: %s", self)
            raise DataValidationError(error) from error

    def delete(self):
        """Removes a customer from the database."""
        logger.info("Deleting customer %s", self.email)

        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            logger.error("Error deleting customer: %s", self)
            raise DataValidationError(error) from error

    def serialize(self):
        """Serializes a customer into a dictionary."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "address": self.address,
            "active": self.active,
        }

    def deserialize(self, data):
        """
        Deserializes a customer from a dictionary.

        Args:
            data (dict): A dictionary containing customer attributes.

        Returns:
            Customer: The deserialized customer.

        Raises:
            DataValidationError: If required fields or values are invalid.
        """
        try:
            self.first_name = data["first_name"]
            self.last_name = data["last_name"]
            self.email = data["email"]

            for field_name in ("first_name", "last_name", "email"):
                value = getattr(self, field_name)

                if not isinstance(value, str) or not value.strip():
                    raise DataValidationError(
                        f"Invalid customer: {field_name} is required"
                    )

            self.address = data.get("address")

            if self.address is not None and not isinstance(self.address, str):
                raise DataValidationError(
                    "Invalid customer: address must be a string or None"
                )
            self.active = data.get("active", True)

            if not isinstance(self.active, bool):
                raise DataValidationError("Invalid customer: active must be a boolean")

        except KeyError as error:
            raise DataValidationError(
                "Invalid customer: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid customer: request body contained bad or no data " + str(error)
            ) from error

        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all customers in the database."""
        logger.info("Processing all customers")
        return cls.query.all()

    @classmethod
    def find(cls, customer_id):
        """Finds a customer by its ID."""
        logger.info("Processing lookup for customer ID %s", customer_id)
        return cls.query.get(customer_id)

    @classmethod
    def find_by_email(cls, email):
        """Returns customers matching the given email address."""
        logger.info("Processing customer query for email %s", email)
        return cls.query.filter(cls.email == email)
