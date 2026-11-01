Feature: Create Customer UI
  As an admin of the Customers service
  I need to create a customer through the web UI
  So that I can add customers using a browser

  Scenario: Successfully create a customer
    Given I am on the Customers admin page
    When I enter the customer's first name, last name, and email
    And I optionally enter an address
    And I set the customer's active status
    And I submit the form
    Then the customer is created successfully
    And the new customer appears in the UI
    And the customer's saved details are displayed correctly
    And the UI confirms that the customer was created successfully

  Scenario: Create a customer using the default optional values
    Given I am on the Customers admin page
    And the active status is enabled by default
    When I enter the customer's first name, last name, and email
    And I leave the address blank
    And I leave the active status unchanged
    And I submit the form
    Then the customer is created successfully
    And the customer's address is empty
    And the customer's active status is True
    And the new customer appears in the UI

  Scenario: Create an inactive customer
    Given I am on the Customers admin page
    When I enter the customer's first name, last name, and email
    And I set the active status to inactive
    And I submit the form
    Then the customer is created successfully
    And the new customer appears in the UI
    And the customer's active status is False

  Scenario: Reject missing required customer details
    Given I am on the Customers admin page
    When I submit the form with a missing or empty first name, last name, or email
    Then the customer is not created
    And the UI identifies the required information that must be provided

  Scenario: Handle an unsuccessful creation
    Given I am on the Customers admin page
    And the creation request will fail
    When I enter valid customer details and submit the form
    Then the UI communicates that the customer could not be created
    And the UI does not indicate that the customer was created successfully
