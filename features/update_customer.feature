Feature: Update Customer UI
  As an admin of the Customers service
  I need to update customer details through the UI
  So that I can maintain customer records

  Scenario: Open a customer for editing
    Given a customer exists
    When I select that customer for editing
    Then the customer's current details are displayed in an editable form

  Scenario: Successfully update customer details
    Given I have opened a customer's edit form
    When I change the customer's details and save the changes
    Then the UI indicates that the update succeeded
    And the updated details are displayed for that customer
    And the saved details remain correct when I reload the page

  Scenario: Cancel editing
    Given I have opened a customer's edit form
    And the customer has previously saved details
    When I change the customer's details and cancel editing
    Then the unsaved changes are discarded
    And the customer's previously saved details remain unchanged

  Scenario: Handle an unsuccessful update
    Given I have opened a customer's edit form
    When I save the changes and the update fails
    Then the UI communicates that the update was unsuccessful
    And the UI does not indicate that the changes were saved successfully

  Scenario: Reject an invalid email address when updating
    Given I have opened a customer's edit form
    When I change the customer's email to an invalid address and save
    Then the UI communicates that the email address is invalid
    And the customer's previously saved details remain unchanged
