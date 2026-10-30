
Feature: Verify deployed Customers service
  As a DevOps engineer
  I want to verify the deployed Customers service
  So that I know the deployment is working

  Scenario: Customers service is reachable
    Given the Customers service is deployed
    When I request the Customers service health endpoint
    Then the service should return HTTP 200
