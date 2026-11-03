Feature: Delete Customer UI
  As an admin of the Customers service
  I need to delete customer records through the web UI
  So that I can remove customers who are no longer needed

  Scenario: Delete a customer after confirming
    Given a customer exists in the system
    And I am viewing the customer list
    When I select Delete for that customer
    And I confirm the deletion
    Then the customer is deleted successfully
    And the customer no longer appears in the list
    And the UI confirms that the deletion succeeded

  Scenario: Cancel the deletion
    Given a customer exists in the system
    And I am viewing the customer list
    When I select Delete for that customer
    And I cancel the confirmation
    Then the customer is not deleted
    And the customer remains in the list

  Scenario: Handle a deletion that fails
    Given a customer exists in the system
    And I am viewing the customer list
    And deleting a customer will fail
    When I attempt to delete the customer
    Then the UI displays an appropriate error message
    And does not indicate that the customer was deleted
    And the customer remains in the list
