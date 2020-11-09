from uuid import UUID, uuid4

from eventsourcing.application.process import ProcessApplication
from eventsourcing.domain.model.aggregate import AggregateRoot
from eventsourcing.system.definition import System


class User(AggregateRoot):

    def __init__(self, name, **kwargs):
        super(User, self).__init__(**kwargs)
        self.name = name
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

    def track_shipping_received(self, shipping_id, sender):
        self.__trigger_event__(
            self.ShippingOffered,
            shipping_id=shipping_id,
            sender=sender,
            receiver=self.id
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


class Users(ProcessApplication):
    persist_event_type = User.Event

    @staticmethod
    def create_user(name):
        return User.__create__(name=name)

    def get_user(self, user_id):
        user = self.repository[user_id]
        assert isinstance(user, User)
        return user

    @staticmethod
    def policy(repository, event):
        if isinstance(event, User.ShippingStarted):
            receiver = repository[event.receiver]
            assert isinstance(receiver, User)
            receiver.track_shipping_received(
                shipping_id=event.shipping_id,
                sender=event.sender,
            )


class Shippings(ProcessApplication):
    persist_event_type = Shipping.Event

    @staticmethod
    def policy(repository, event):
        if isinstance(event, User.ShippingStarted):
            shipping = Shipping.__create__(originator_id=event.shipping_id, sender=event.sender, receiver=event.receiver)
            return shipping


class BoxSystem(System):
    def __init__(self, **kwargs):
        super(BoxSystem, self).__init__(
            Users | Shippings | Users | Users,
            **kwargs
        )
