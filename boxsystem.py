from typing import Any, Optional
from uuid import UUID, uuid4

from eventsourcing.application.decorators import applicationpolicy
from eventsourcing.application.process import ProcessApplication
from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.infrastructure.sqlalchemy.records import Base
from eventsourcing.system.definition import System
from sqlalchemy import Column, Text
from sqlalchemy.orm import Session
from sqlalchemy_utils import UUIDType


class User(AggregateRoot):

    def __init__(self, name, email, **kwargs):
        super(User, self).__init__(**kwargs)
        self.name = name
        self.email = email
        self.shippings = []

    class Event(AggregateRoot.Event):
        pass

    class Created(Event, AggregateRoot.Created):
        pass

    class ShippingStarted(Event):

        @property
        def shipping_id(self):
            return self.__dict__['shipping_id']

        @property
        def sender(self):
            return self.__dict__['sender']

        @property
        def receiver(self):
            return self.__dict__['receiver']

        def mutate(self, obj):
            obj.shippings.append(self.shipping_id)

    def start_shipping(self, receiver: UUID) -> UUID:
        shipping_id = uuid4()
        self.__trigger_event__(
            event_class=self.ShippingStarted,
            shipping_id=shipping_id,
            sender=self.id,
            receiver=receiver
        )
        return shipping_id

    class ShippingOffered(Event):
        @property
        def shipping_id(self):
            return self.__dict__['shipping_id']

        @property
        def sender(self):
            return self.__dict__['sender']

        @property
        def receiver(self):
            return self.__dict__['receiver']

        def mutate(self, obj):
            obj.shippings.append(self.shipping_id)

    def track_shipping(self, shipping_id, sender, receiver):
        if not self.shippings.__contains__(shipping_id):
            self.__trigger_event__(
                self.ShippingOffered,
                shipping_id=shipping_id,
                sender=sender,
                receiver=receiver
            )

    def __str__(self):
        return f'{self.name} - {self.shippings}'


class Shipping(AggregateRoot):

    def __init__(self, sender, receiver, **kwargs):
        super(Shipping, self).__init__(**kwargs)
        self.sender = sender
        self.receiver = receiver

    class Event(AggregateRoot.Event):
        pass

    class Created(Event, AggregateRoot.Created):
        pass

    def __str__(self):
        return f'{self.sender} -> {self.receiver}'


class Negotiation(AggregateRoot):

    def __init__(self, author, box, date, **kwargs):
        super(Negotiation, self).__init__(**kwargs)
        self.author = author
        self.box = box
        self.date = date
        self.status = ""

    class Event(AggregateRoot.Event):
        pass

    class Created(Event, AggregateRoot.Created):
        pass

    class OfferCreated(Event):

        def mutate(self, obj):
            obj.status = "created"

    class OfferAccepted(Event):
        pass

    class OfferRejected(Event):
        pass

    def create_offer(self):
        self.__trigger_event__(
            Negotiation.OfferCreated
        )

    def accept_offer(self):
        self.__trigger_event__(
            Negotiation.OfferAccepted
        )

    def reject_offer(self):
        self.__trigger_event__(
            Negotiation.OfferRejected
        )

    def __str__(self):
        return f'{self.author} -> {self.box} ({self.status}, {self.id})'


class UserIndex(Base):
    __tablename__ = "user_index"

    user_name = Column(Text(), primary_key=True)
    email = Column(Text())
    user_id = Column(UUIDType())


class UserAlreadyExistsException(Exception):
    pass


class EmailAlreadyExistsException(Exception):
    pass


class Users(SQLAlchemyApplication, ProcessApplication):
    """
    Reverse Index for the Users ProcessApplication
    Roughly following the example from
    https://eventsourcing.readthedocs.io/en/stable/topics/projections.html?highlight=index#reliable-projections
    """
    persist_event_type = User.Event

    def create_user(self, name, email):
        if self.get_uuid_for_name(name) is not None:
            raise UserAlreadyExistsException
        if self.get_uuid_for_email(email) is not None:
            raise EmailAlreadyExistsException
        return User.__create__(name=name, email=email)

    def __init__(self, uri: Optional[str] = None, session: Optional[Any] = None, tracking_record_class: Any = None,
                 **kwargs: Any):
        super().__init__(uri, session, tracking_record_class, **kwargs)
        self.datastore.setup_table(UserIndex)

    def get_user(self, user_id):
        user = self.repository[user_id]
        assert isinstance(user, User)
        return user

    @staticmethod
    def policy(repository, event):
        if isinstance(event, User.ShippingStarted):
            receiver = repository[event.receiver]
            assert isinstance(receiver, User)
            receiver.track_shipping(
                shipping_id=event.shipping_id,
                sender=event.sender,
                receiver=event.receiver
            )
        elif isinstance(event, Shipping.Created):
            sender: User = repository[event.sender]
            receiver: User = repository[event.receiver]
            receiver.track_shipping(shipping_id=event.originator_id,
                                    sender=sender.id, receiver=receiver.id)
            sender.track_shipping(shipping_id=event.originator_id,
                                  sender=sender.id, receiver=receiver.id)

    @applicationpolicy
    def policy(self, repository, event):
        """Do nothing by default."""

    @policy.register(User.Created)
    def _(self, repository, event: User.Created):
        session: Session = self.datastore.session
        if session.query(UserIndex).filter(UserIndex.user_name == event.name).count() > 0:
            print("Warning, updating Index!")
            record = session.query(UserIndex).filter(UserIndex.user_name == event.name).one()
            record.user_id = event.originator_id
        else:
            record = UserIndex(user_name=event.name, email=event.email, user_id=event.originator_id)
        repository.save_orm_obj(record)

    def get_uuid_for_name(self, user_name):
        session: Session = self.datastore.session

        return session.query(UserIndex.user_id).filter(UserIndex.user_name == user_name).scalar()

    def get_uuid_for_email(self, email):
        session: Session = self.datastore.session

        return session.query(UserIndex.user_id).filter(UserIndex.email == email).scalar()


class Shippings(ProcessApplication):
    persist_event_type = Shipping.Event

    @staticmethod
    def policy(repository, event):
        if isinstance(event, User.ShippingStarted):
            shipping = Shipping.__create__(originator_id=event.shipping_id, sender=event.sender,
                                           receiver=event.receiver)
            return shipping


class Negotiations(ProcessApplication):
    persist_event_type = Negotiation.Event

    @staticmethod
    def create_negotiation(author, box, date):
        return Negotiation.__create__(author=author, box=box, date=date)

    def get_negotiation(self, negotiation_id):
        negotiation = self.repository[negotiation_id]
        assert isinstance(negotiation, Negotiation)
        return negotiation


class BoxSystem(System):
    def __init__(self, **kwargs):
        super(BoxSystem, self).__init__(
            Users | Shippings | Users | Users | Negotiations,
            **kwargs
        )
