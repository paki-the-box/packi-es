from behave import given, when, then, use_step_matcher
from hamcrest import assert_that, equal_to, is_in, not_none

from boxsystem import BoxSystem, Users, User, Shippings, Shipping

use_step_matcher("parse")


@given("box system is running")
def step_impl(context):
    assert isinstance(context.system, BoxSystem)

    assert_that('users', is_in(context.runner.processes))
    assert_that('shippings', is_in(context.runner.processes))

    # Register a user.
    users: Users = context.runner.processes['users']
    assert_that(users, isinstance(users, Users))

    shippings = context.runner.processes['shippings']
    assert isinstance(shippings, Shippings)


@when('a user with name "{user_name}" and email "{email}" is created')
def step_impl(context, user_name, email):
    users: Users = context.runner.processes['users']

    user = users.create_user(user_name, email)

    assert_that(user, not_none())

    user.__save__()

    context.user_id = user.id
    context.name = user_name
    context.email = email


@then("a reverse Index is created")
def step_impl(context):
    users: Users = context.runner.processes['users']
    user_id = context.user_id

    fetched_id = users.get_uuid_for_name(user_name=context.name)

    assert_that(fetched_id, not_none())
    assert_that(user_id, equal_to(fetched_id))


@when('a user "{sender_name}" sends a package to "{receiver_name}"')
def step_impl(context, sender_name, receiver_name):
    users = context.runner.processes['users']

    # Register for work.
    user1 = users.create_user("User 1", "u1@b.de")
    user2 = users.create_user("User 2", "u2@b.de")
    assert isinstance(user1, User)
    assert isinstance(user1, User)
    user1.__save__()
    user2.__save__()
    context.user_id1 = user1.id
    context.user_id2 = user2.id

    # Check the users is registered.
    assert_that(context.user_id1, is_in(users.repository))
    assert_that(context.user_id2, is_in(users.repository))

    sender_id = users.get_uuid_for_name(sender_name)
    assert sender_id is not None

    receiver_id = users.get_uuid_for_name(receiver_name)

    sender = users.repository[sender_id]
    receiver = users.repository[receiver_id]

    assert isinstance(sender, User)
    assert isinstance(receiver, User)

    shipping_id = sender.start_shipping(receiver=receiver.id)
    sender.__save__()

    assert shipping_id is not None

    context.shipping_id = shipping_id


@then('a shipping from "{sender_name}" to "{receiver_name}" is created')
def step_impl(context, sender_name, receiver_name):
    shipping_id = context.shipping_id

    shippings: Shippings = context.runner.processes['shippings']

    assert_that(shipping_id, is_in(shippings.repository))
    shipping: Shipping = shippings.repository[shipping_id]

    # Now we have our shipping
    assert_that(context.user_id1, equal_to(shipping.sender))
    assert_that(context.user_id2, equal_to(shipping.receiver))
