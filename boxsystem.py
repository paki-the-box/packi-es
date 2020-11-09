from typing import Optional
from uuid import UUID, uuid4

from eventsourcing.application.process import ProcessApplication
from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.domain.model.entity import TEntityWithHashchain
from eventsourcing.system.definition import System


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

    def start_shipping(self, receiver: UUID) -> UUID:
        shipping_id = uuid4()
        self.__trigger_event__(
            self.ShippingStarted,
            shipping_id=shipping_id,
            sender=self.id,
            receiver=receiver
        )
        return shipping_id

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


class Users(ProcessApplication):
    persist_event_type = User.Event

    @staticmethod
    def create_user(name, email):
        return User.__create__(name=name, email=email)

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
            print(receiver)


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
