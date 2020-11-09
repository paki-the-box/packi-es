from unittest import TestCase

from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.system.runner import SingleThreadedRunner

from boxsystem import BoxSystem, User, Negotiations


class BoxSystemTests(TestCase):

    def test_negotiation(self):
        system = BoxSystem(
            infrastructure_class=SQLAlchemyApplication,
            setup_tables=True,
        )

        runner = SingleThreadedRunner(system)

        runner.start()

        negotiations: Negotiations = runner.processes['negotiations']

        negotiation = negotiations.create_negotiation("a", "b", "c")
        negotiation.__save__()

        negotiation.create_offer()
        negotiation.__save__()

        self.assertEqual("created", negotiation.status)

        copy = negotiations.get_negotiation(negotiation.id)

        self.assertEqual("created", copy.status)

        runner.close()

    def test_theSystem(self):
        system = BoxSystem(
            infrastructure_class=SQLAlchemyApplication,
            setup_tables=True,
        )

        runner = SingleThreadedRunner(system)

        runner.start()

        users = runner.processes['users']
        shippings = runner.processes['shippings']

        julian: User = users.create_user("Julian", "a@b.c")
        niklas: User = users.create_user("Niklas", "b@c.d")

        julian.__save__()
        niklas.__save__()

        julian.start_shipping(niklas.id)

        julian.__save__()

        self.assertGreater(len(julian.shippings), 0)
        self.assertGreater(len(users.get_user(niklas.id).shippings), 0)

        shipping_id = julian.shippings[0]

        shipping = shippings.repository[shipping_id]
        self.assertEqual(julian.id, shipping.sender)
        self.assertEqual(niklas.id, shipping.receiver)

        runner.close()
