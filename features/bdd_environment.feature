Feature: BDD test environment
  As a developer
  I want Behave to discover and run feature scenarios
  So that the BDD testing environment is ready for UI testing

  Scenario: BDD environment initializes successfully
    Given the BDD environment is configured
    Then the BDD environment should be ready