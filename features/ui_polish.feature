Feature: Accurate customer list and navigation
  As an administrator
  I need the customer admin UI to show accurate results and working navigation
  So that I can trust what the page displays

  Scenario: A slower earlier search does not replace a newer one
    Given two customers exist with different first names
    And searches for the first customer respond slowly
    When I search the list for the first customer's first name
    And I search the list for the second customer's first name
    Then only the second customer is listed once both searches finish

  Scenario: A slower earlier search that fails does not affect a newer one
    Given two customers exist with different first names
    And searches for the first customer fail slowly
    When I search the list for the first customer's first name
    And I search the list for the second customer's first name
    Then only the second customer is listed once both searches finish
    And the UI does not show a load error

  Scenario: A failed follow-up request keeps the last good results
    Given a customer exists in the system
    And I have searched the list for that customer's first name
    And loading the full customer list will fail
    When I refresh the customer list
    Then that customer is still listed
    And the UI shows that the customer list could not be loaded

  Scenario: A failed refresh keeps the unfiltered list
    Given a customer exists in the system
    And loading the full customer list will fail
    When I refresh the customer list
    Then that customer is still listed
    And the UI shows that the customer list could not be loaded

  Scenario: A failed full-list request keeps a new search result
    Given a customer exists in the system
    And loading the full customer list will fail
    When I search the list for that customer's first name
    Then that customer is still listed
    And the UI shows that the customer list could not be loaded

  Scenario: A failed reload after a delete does not keep the deleted customer
    Given a customer exists in the system
    And loading the full customer list will fail
    When I attempt to delete the customer
    Then the UI shows that the customer list could not be loaded
    And the customer no longer appears in the list

  Scenario: The sidebar has no placeholder links
    Given I am viewing the customer list
    Then the sidebar shows no "Coming soon" links

  Scenario: The sidebar search link opens the customer search
    Given I am viewing the customer list
    When I click "Search records" in the sidebar
    Then the customer search field is ready for input
