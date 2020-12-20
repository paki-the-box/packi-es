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

#  Scenario: Rider takes a ride
#    Given taxi system is running
#
#    When a rider requests a ride from "home" to "work"
#    Then a car is booked from "home" to "work"
#    And the car heads to pickup at "home" and dropoff at "work"
#
#    When the car has arrived at the pickup position
#    Then the office knows the car arrived at the pickup position
#    And the rider knows the car arrived at the pickup position
#
#    When the car has arrived at the dropoff position
#    Then the office knows the car arrived at the dropoff position
#    And the rider knows the car arrived at the dropoff position