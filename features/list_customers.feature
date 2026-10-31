Feature: List Customers UI
  As an admin of the Customers service
  I need to view all customers through the web UI
  So that I can browse and manage customer records

  Scenario: Display all existing customers
    Given multiple customers exist in the system
    When an admin opens the Customers page
    Then all existing customers are displayed in the UI
    And their information is shown correctly

  Scenario: Display an empty customer list
    Given no customers exist in the system
    When an admin opens the Customers page
    Then the UI displays an empty customer list
    And indicates that no customers are available

  Scenario: Handle an unavailable Customers API
    Given the Customers API is unavailable
    When an admin attempts to view the customer list
    Then the UI displays an appropriate error message
