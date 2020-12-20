Feature: Request Box
  Request and get a taxi.

  Scenario: User is created
    Given box system is running

    When a user with name "User" and email "user@user.de" is created
    Then a reverse Index is created

  Scenario: Shipping is created
    Given box system is running

    When a user "User 1" sends a package to "User 2"
    Then a shipping from "User 1" to "User 2" is created
    And associated to both users

  Scenario: Duplicate Users impossible
    Given box system is running

    When a user with name "Username" is created
    Then another user with name "Username" throws UserAlreadyExistsException exception

    When a user with email "Email" is created
    Then another user with email "Email" throws EmailAlreadyExistsException exception
