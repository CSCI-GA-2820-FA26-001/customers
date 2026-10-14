"""
Test Factory to make fake objects for testing.
"""

import factory

from service.models import Customer


class CustomerFactory(factory.Factory):
    """Creates fake customers for testing."""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps the factory to the data model."""

        model = Customer

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    address = factory.Faker("address")
    active = True
