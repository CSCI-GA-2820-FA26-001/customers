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
Customer Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Customer.
"""

from flask import abort, current_app as app, jsonify, request

from service.common import status
from service.models import Customer


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################
@app.route("/customers", methods=["POST"])
def create_customer():
    """Creates a customer and returns the newly created resource."""
    app.logger.info("Request to create a customer")

    customer = Customer()
    customer.deserialize(request.get_json())
    customer.create()

    message = customer.serialize()
    location_url = f"{request.host_url.rstrip('/')}/customers/{customer.id}"

    return (
        jsonify(message),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# LIST ALL CUSTOMERS
######################################################################
@app.route("/customers", methods=["GET"])
def list_customers():
    """Returns a list of all Customers"""
    app.logger.info("Request to list all Customers")
    customers = Customer.all()
    results = [customer.serialize() for customer in customers]
    app.logger.info("Returning %d customers", len(results))
    return jsonify(results), status.HTTP_200_OK


@app.route("/customers/<int:customer_id>", methods=["GET"])
def read_customer(customer_id):
    """Retrieve a customer by ID"""
    app.logger.info("Request to read customer with ID %s", customer_id)
    customer = Customer.find(customer_id)
    if customer is None:
        return jsonify({"error": "Customer not found"}), status.HTTP_404_NOT_FOUND

    return jsonify(customer.serialize()), status.HTTP_200_OK


@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    """Updates an existing customer and returns the updated resource."""
    app.logger.info("Request to update customer with id: %s", customer_id)

    data = request.get_json()

    customer = Customer.find(customer_id)
    if not customer:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Customer with id '{customer_id}' was not found.",
        )

    customer.deserialize(data)
    customer.update()

    app.logger.info("Customer with id [%s] updated.", customer.id)
    return jsonify(customer.serialize()), status.HTTP_200_OK
