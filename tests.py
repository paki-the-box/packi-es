from unittest import TestCase

from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.system.runner import SingleThreadedRunner

from boxsystem import BoxSystem, User


class BoxSystemTests(TestCase):

    def test_theSystem(self):
        system = BoxSystem(
            infrastructure_class=SQLAlchemyApplication,
            setup_tables=True,
        )

        runner = SingleThreadedRunner(system)

        runner.start()

        users = runner.processes['users']
        shippings = runner.processes['shippings']

        julian: User = users.create_user("Julian")
        niklas: User = users.create_user("Niklas")

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
