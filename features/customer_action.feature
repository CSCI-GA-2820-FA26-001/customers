Feature: Perform Customer Action UI
  As an admin of the Customers service
  I need to perform a supported action on a customer through the web UI
  So that I can manage customer states without manually calling the REST API

  Scenario: Deactivate an active customer
    Given a customer exists in the system
    And I am viewing that customer's information
    When I select the supported customer action
    Then the action is performed successfully
    And the customer's updated state is displayed
    And the UI confirms that the action succeeded

  Scenario: Activate an inactive customer
    Given an inactive customer exists in the system
    And I am viewing that customer's information
    When I select the supported customer action
    Then the action is performed successfully
    And the customer's updated state is displayed
    And the UI confirms that the action succeeded

  Scenario: Handle an action that fails
    Given a customer exists in the system
    And I am viewing that customer's information
    And the customer action will fail
    When I attempt to perform the customer action
    Then the UI reports that the customer action failed
    And does not indicate that the action succeeded
    And the customer's state is unchanged
