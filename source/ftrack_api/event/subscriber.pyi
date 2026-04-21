from _typeshed import Incomplete

class Subscriber:
    subscription: Incomplete
    callback: Incomplete
    metadata: Incomplete
    priority: Incomplete
    def __init__(self, subscription, callback, metadata, priority) -> None: ...
    def interested_in(self, event): ...
