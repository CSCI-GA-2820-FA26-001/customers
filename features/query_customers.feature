Feature: Query Customers UI
  As an admin of the Customers service
  I need to search for customers using their attributes through the web UI
  So that I can quickly find customers matching specific criteria

  Scenario Outline: Search by a customer attribute
    Given multiple customers exist with different attributes
    And I am on the Customers admin page
    When I enter that customer's <attribute> in the search field
    And I submit the search
    Then only customers matching the specified criteria are displayed

    Examples: Supported attributes
      | attribute     |
      | first name    |
      | last name     |
      | email address |

  Scenario: Search by account status
    Given multiple customers exist with different attributes
    And I am on the Customers admin page
    When I search for inactive customers
    Then only customers matching the specified criteria are displayed

  Scenario: Search for a value that matches no customers
    Given customers exist in the system
    When I search using an attribute value that matches no customers
    Then no customer records are displayed
    And the UI indicates that no matching customers were found

  Scenario: Clear the search criteria
    Given multiple customers exist with different attributes
    And I have filtered the customer list using a query
    When I clear the search criteria
    Then the full customer list is displayed again

  Scenario: Handle a search that cannot be completed
    Given customers exist in the system
    And searching for customers will fail
    When I enter that customer's last name in the search field
    And I submit the search
    Then the UI reports that the search could not be completed
    And no customer records are displayed
