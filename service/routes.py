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

Paths:
------
GET /health - Returns the health status of the service
GET /apidocs/ - Swagger documentation for the REST API
GET /api/customers - Returns a list of Customers, optionally filtered
POST /api/customers - Creates a new Customer
GET /api/customers/{id} - Returns the Customer with the given id
PUT /api/customers/{id} - Updates the Customer with the given id
DELETE /api/customers/{id} - Deletes the Customer with the given id
PUT /api/customers/{id}/activate - Activates the Customer
PUT /api/customers/{id}/deactivate - Deactivates the Customer
"""

from flask import abort, current_app as app, jsonify, request
from flask_restx import Api, Resource, fields, inputs, reqparse

from service.common import status
from service.models import Customer


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Returns useful information about the Customers service."""
    return jsonify({"name": "Customers Service"}), status.HTTP_200_OK


######################################################################
# HEALTH CHECK
######################################################################
@app.route("/health", methods=["GET"])
def health():
    """Returns the health status of the service."""
    return jsonify({"status": "OK"}), status.HTTP_200_OK


######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(
    app,
    version="1.0.0",
    title="Customers REST API Service",
    description="REST API for managing customers.",
    default="customers",
    default_label="Customer operations",
    doc="/apidocs/",
    prefix="/api",
)

# Define the models so that the docs reflect what can be sent
create_model = api.model(
    "Customer",
    {
        "first_name": fields.String(
            required=True, description="The first name of the customer"
        ),
        "last_name": fields.String(
            required=True, description="The last name of the customer"
        ),
        "email": fields.String(
            required=True, description="The email address of the customer"
        ),
        "address": fields.String(
            required=False, description="The postal address of the customer"
        ),
        "active": fields.Boolean(
            required=False,
            default=True,
            description="Is the customer active?",
        ),
    },
)

customer_model = api.inherit(
    "CustomerModel",
    create_model,
    {
        "id": fields.Integer(
            readOnly=True,
            description="The unique id assigned internally by the service",
        ),
    },
)

# Query string arguments accepted by the list endpoint
customer_args = reqparse.RequestParser()
customer_args.add_argument(
    "first_name",
    type=str,
    location="args",
    required=False,
    help="List customers by first name",
)
customer_args.add_argument(
    "last_name",
    type=str,
    location="args",
    required=False,
    help="List customers by last name",
)
customer_args.add_argument(
    "email",
    type=str,
    location="args",
    required=False,
    help="List customers by email address",
)
customer_args.add_argument(
    "active",
    type=inputs.boolean,
    location="args",
    required=False,
    help="List customers by active status",
)


######################################################################
#  PATH: /customers/{id}
######################################################################
@api.route("/customers/<int:customer_id>")
@api.param("customer_id", "The customer identifier")
class CustomerResource(Resource):
    """
    CustomerResource class

    Allows the manipulation of a single Customer
    GET /customers/{id} - Returns a Customer with the id
    PUT /customers/{id} - Updates a Customer with the id
    DELETE /customers/{id} - Deletes a Customer with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE A CUSTOMER
    # ------------------------------------------------------------------
    @api.doc("read_customer")
    @api.response(200, "Success", customer_model)
    @api.response(404, "Customer not found")
    def get(self, customer_id):
        """Retrieve a single Customer"""
        app.logger.info("Request to read customer with ID %s", customer_id)
        customer = Customer.find(customer_id)
        if customer is None:
            return {"error": "Customer not found"}, status.HTTP_404_NOT_FOUND

        return customer.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE AN EXISTING CUSTOMER
    # ------------------------------------------------------------------
    @api.doc("update_customer")
    @api.response(404, "Customer not found")
    @api.response(400, "The posted Customer data was not valid")
    @api.response(415, "The request content type must be application/json")
    @api.expect(create_model)
    @api.marshal_with(customer_model)
    def put(self, customer_id):
        """Update a Customer"""
        app.logger.info("Request to update customer with id: %s", customer_id)

        data = get_json_body()

        customer = Customer.find(customer_id)
        if not customer:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Customer with id '{customer_id}' was not found.",
            )

        customer.deserialize(data)
        customer.update()

        app.logger.info("Customer with id [%s] updated.", customer.id)
        return customer.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE A CUSTOMER
    # ------------------------------------------------------------------
    @api.doc("delete_customer")
    @api.response(204, "Customer deleted")
    def delete(self, customer_id):
        """Delete a Customer

        Deleting a customer that does not exist is not an error.
        """
        app.logger.info("Request to delete customer with id: %s", customer_id)

        customer = Customer.find(customer_id)
        if customer is not None:
            customer.delete()
            app.logger.info("Customer with id [%s] deleted.", customer_id)

        return "", status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /customers
######################################################################
@api.route("/customers")
class CustomerCollection(Resource):
    """Handles all interactions with collections of Customers"""

    # ------------------------------------------------------------------
    # LIST ALL CUSTOMERS
    # ------------------------------------------------------------------
    @api.doc("list_customers")
    @api.expect(customer_args)
    @api.marshal_list_with(customer_model)
    def get(self):
        """Returns all of the Customers, optionally filtered by one attribute"""
        app.logger.info("Request to list all Customers")
        args = customer_args.parse_args()

        if args["first_name"] is not None:
            customers = Customer.find_by_first_name(args["first_name"])
        elif args["last_name"] is not None:
            customers = Customer.find_by_last_name(args["last_name"])
        elif args["email"] is not None:
            customers = Customer.find_by_email(args["email"])
        elif args["active"] is not None:
            customers = Customer.find_by_active(args["active"])
        else:
            customers = Customer.all()

        results = [customer.serialize() for customer in customers]
        app.logger.info("Returning %d customers", len(results))
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # CREATE A NEW CUSTOMER
    # ------------------------------------------------------------------
    @api.doc("create_customer")
    @api.response(400, "The posted data was not valid")
    @api.response(415, "The request content type must be application/json")
    @api.expect(create_model)
    @api.marshal_with(customer_model, code=status.HTTP_201_CREATED)
    def post(self):
        """Creates a Customer"""
        app.logger.info("Request to create a customer")

        customer = Customer()
        customer.deserialize(get_json_body())
        customer.create()

        location_url = api.url_for(
            CustomerResource, customer_id=customer.id, _external=True
        )
        return (
            customer.serialize(),
            status.HTTP_201_CREATED,
            {"Location": location_url},
        )


######################################################################
#  PATH: /customers/{id}/activate
######################################################################
@api.route("/customers/<int:customer_id>/activate")
@api.param("customer_id", "The customer identifier")
class ActivateResource(Resource):
    """Activate action on a Customer"""

    @api.doc("activate_customer")
    @api.response(404, "Customer not found")
    @api.marshal_with(customer_model)
    def put(self, customer_id):
        """Activates a Customer (sets active to True)"""
        app.logger.info("Request to activate customer with id: %s", customer_id)
        return set_active(customer_id, True)


######################################################################
#  PATH: /customers/{id}/deactivate
######################################################################
@api.route("/customers/<int:customer_id>/deactivate")
@api.param("customer_id", "The customer identifier")
class DeactivateResource(Resource):
    """Deactivate action on a Customer"""

    @api.doc("deactivate_customer")
    @api.response(404, "Customer not found")
    @api.marshal_with(customer_model)
    def put(self, customer_id):
        """Deactivates a Customer (sets active to False)"""
        app.logger.info("Request to deactivate customer with id: %s", customer_id)
        return set_active(customer_id, False)


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def get_json_body():
    """Returns the JSON request body, rejecting bodies nested too deeply to parse"""
    try:
        return request.get_json()
    except RecursionError:
        abort(status.HTTP_400_BAD_REQUEST, "Request body is nested too deeply")


def set_active(customer_id, active):
    """Sets the active flag of an existing customer"""
    customer = Customer.find(customer_id)
    if not customer:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Customer with id '{customer_id}' was not found.",
        )

    customer.active = active
    customer.update()

    app.logger.info("Customer with id [%s] active set to %s.", customer_id, active)
    return customer.serialize(), status.HTTP_200_OK
