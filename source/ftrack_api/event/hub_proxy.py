# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""Session-scoped EventHub proxy for tracking subscriptions."""

from __future__ import absolute_import

from builtins import object


class SessionEventHubProxy(object):
    """Proxy for EventHub that tracks subscriptions per session.

    This wrapper intercepts subscribe() and unsubscribe() calls to maintain
    a session-local list of subscriber IDs. When the session is closed, only
    the subscribers created by that session are unsubscribed, leaving other
    sessions' subscribers intact on the shared EventHub.
    """

    def __init__(self, event_hub, session):
        """Initialize the proxy.

        Args:
            event_hub: The underlying EventHub instance (may be shared).
            session: The Session instance that owns this proxy.
        """
        self._event_hub = event_hub
        self._session = session

    def subscribe(self, subscription, callback, subscriber=None, priority=100):
        """Subscribe to events and track the subscriber ID for this session.

        All arguments are passed through to the underlying EventHub.subscribe().
        The returned subscriber ID is tracked for cleanup when this session closes.

        Args:
            subscription (str): The subscription expression.
            callback (callable): The callback to invoke when matching events occur.
            subscriber (dict): Optional subscriber metadata.
            priority (int): Optional priority (lower = earlier execution).

        Returns:
            str: The subscriber identifier.
        """
        subscriber_id = self._event_hub.subscribe(
            subscription, callback, subscriber=subscriber, priority=priority
        )

        # Track this subscriber for session cleanup
        if not hasattr(self._session, '_session_subscribers'):
            self._session._session_subscribers = []
        self._session._session_subscribers.append(subscriber_id)

        return subscriber_id

    def unsubscribe(self, subscriber_identifier):
        """Unsubscribe and remove from session tracking.

        Args:
            subscriber_identifier (str): The subscriber identifier to unsubscribe.
        """
        self._event_hub.unsubscribe(subscriber_identifier)

        # Remove from session tracking
        if hasattr(self._session, '_session_subscribers'):
            if subscriber_identifier in self._session._session_subscribers:
                self._session._session_subscribers.remove(
                    subscriber_identifier)

    def __getattr__(self, name):
        """Delegate all other method/attribute access to the underlying EventHub.

        This allows the proxy to be used transparently as if it were the
        actual EventHub instance.

        Args:
            name (str): The attribute name to access.

        Returns:
            The attribute from the underlying EventHub.
        """
        return getattr(self._event_hub, name)

    def __repr__(self):
        """Return string representation."""
        return '<SessionEventHubProxy for {0}>'.format(self._event_hub)
