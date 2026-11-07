Feature: Read Customer UI
  As an admin of the Customers service
  I need to view customer details in the UI
  So that I can inspect a customer

  Scenario: View the details of an existing customer
    Given a customer exists in the system
    When an admin navigates to the customer details page
    Then the customer's details are displayed in the UI

  Scenario: Open the details from the customer list
    Given a customer exists in the system
    And I am viewing the customer list
    When I select View for that customer
    Then the customer's details are displayed in the UI

  Scenario: View a customer who has no address and is inactive
    Given an inactive customer without an address exists in the system
    When an admin navigates to the customer details page
    Then the customer's details are displayed in the UI

  Scenario: Navigate to a customer that does not exist
    When an admin navigates to the details page of a customer that does not exist
    Then the UI indicates that the customer was not found
    And no customer details are displayed

  Scenario: Handle a customer that cannot be loaded
    Given a customer exists in the system
    And loading a customer will fail
    When an admin navigates to the customer details page
    Then the UI indicates that the customer could not be loaded
    And no customer details are displayed
