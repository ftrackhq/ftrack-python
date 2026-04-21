import threading
from _typeshed import Incomplete
from typing import NamedTuple

class SocketIoSession(NamedTuple):
    id: Incomplete
    heartbeatTimeout: Incomplete
    supportedTransports: Incomplete

class ServerDetails(NamedTuple):
    scheme: Incomplete
    hostname: Incomplete
    port: Incomplete

class EventHub:
    logger: Incomplete
    id: Incomplete
    server: Incomplete
    def __init__(
        self,
        server_url,
        api_user,
        api_key,
        headers: Incomplete | None = None,
        cookies: Incomplete | None = None,
    ) -> None: ...
    def get_server_url(self): ...
    def get_network_location(self): ...
    @property
    def secure(self): ...
    def init_connection(self) -> None: ...
    def connect(self) -> None: ...
    @property
    def connected(self): ...
    def disconnect(self, unsubscribe: bool = True, reconnect: bool = False) -> None: ...
    def reconnect(self, attempts: int = 10, delay: int = 5) -> None: ...
    def wait(self, duration: Incomplete | None = None) -> None: ...
    def get_subscriber_by_identifier(self, identifier): ...
    def subscribe(
        self,
        subscription,
        callback,
        subscriber: Incomplete | None = None,
        priority: int = 100,
    ): ...
    def unsubscribe(self, subscriber_identifier) -> None: ...
    def publish(
        self,
        event,
        synchronous: bool = False,
        on_reply: Incomplete | None = None,
        on_error: str = "raise",
    ): ...
    def publish_reply(
        self, source_event, data, source: Incomplete | None = None
    ) -> None: ...
    def subscription(
        self,
        subscription,
        callback,
        subscriber: Incomplete | None = None,
        priority: int = 100,
    ): ...

class _SubscriptionContext:
    def __init__(self, hub, subscription, callback, subscriber, priority) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None: ...

class _ProcessorThread(threading.Thread):
    daemon: bool
    logger: Incomplete
    client: Incomplete
    done: Incomplete
    def __init__(self, client) -> None: ...
    def run(self) -> None: ...
    def cancel(self) -> None: ...
