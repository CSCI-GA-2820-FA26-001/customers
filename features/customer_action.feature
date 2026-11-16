Feature: Perform Customer Action UI
  As an admin of the Customers service
  I need to activate or deactivate customers through the web UI
  So that I can manage customer states without manually calling the REST API

  Scenario: Successfully deactivate an active customer
    Given an active customer exists for the action test
    And I am viewing that customer in the admin UI
    When I click the Deactivate button
    Then the customer should be displayed as inactive
    And the UI should confirm that the action succeeded

  Scenario: Successfully activate an inactive customer
    Given an inactive customer exists for the action test
    And I am viewing that customer in the admin UI
    When I click the Activate button
    Then the customer should be displayed as active
    And the UI should confirm that the action succeeded

  Scenario: Handle an unsuccessful customer action
    Given an active customer exists for the action test
    And I am viewing that customer in the admin UI
    And the customer action request will fail
    When I click the Deactivate button
    Then the UI should display an action error
    And the customer should still be displayed as active
