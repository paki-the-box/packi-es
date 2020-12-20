from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.system.runner import SingleThreadedRunner

from boxsystem import BoxSystem


def before_all(context):
    context.system = BoxSystem(
        infrastructure_class=SQLAlchemyApplication,
        setup_tables=True,
    )
    context.runner = SingleThreadedRunner(context.system)
    context.runner.start()


def after_all(context):
    context.runner.close()
