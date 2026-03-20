# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

"""EventHub singleton registry for connection sharing across sessions."""

from __future__ import absolute_import

import threading
import weakref
import logging


class EventHubRegistry(object):
    """Global registry for shared EventHub instances.

    Manages EventHub instances to ensure that sessions with identical
    credentials can share the same WebSocket connection to the server.

    This prevents connection exhaustion when multiple Session instances
    are created with the same credentials.
    """

    def __init__(self):
        """Initialize the registry."""
        self._hubs = {}  # (server_url, api_user, api_key, plugin_paths_key) -> EventHub
        self._hub_sessions = {}  # hub_key -> WeakSet of session weakrefs
        self._hub_connect_locks = {}  # hub_key -> Lock (for first connection)
        self._hub_plugins_discovered = {}  # hub_key -> bool (plugins discovered?)
        self._lock = threading.RLock()
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__)

    def get_or_create(
        self,
        server_url,
        api_user,
        api_key,
        plugin_paths=None,
        headers=None,
        cookies=None,
        auto_connect=False,
    ):
        """Get existing EventHub or create new one for credentials.

        Args:
            server_url (str): The ftrack server URL.
            api_user (str): The API user to authenticate as.
            api_key (str): The API key to authenticate with.
            plugin_paths (list): Optional list of plugin paths (affects hub key).
            headers (dict): Optional custom headers.
            cookies (dict): Optional custom cookies.
            auto_connect (bool): Whether to automatically connect the hub.

        Returns:
            tuple: (EventHub, hub_key) - Shared EventHub instance and its key.

        Note:
            Headers and cookies are only used when creating a new hub.
            If a hub already exists for these credentials, the provided
            headers/cookies are ignored (the existing hub is returned).
            
            Plugin paths are included in the hub key to ensure sessions with
            different plugin configurations use separate hubs, preventing
            duplicate plugin subscriptions.
        """
        # Create key from credentials and plugin paths
        # Include plugin_paths to avoid plugin subscription conflicts
        plugin_paths_key = tuple(sorted(plugin_paths)) if plugin_paths else ()
        key = (server_url, api_user, api_key, plugin_paths_key)

        with self._lock:
            if key not in self._hubs:
                # Import here to avoid circular dependency
                import ftrack_api.event.hub

                # Create new hub
                hub = ftrack_api.event.hub.EventHub(
                    server_url, api_user, api_key, headers=headers, cookies=cookies
                )

                self._hubs[key] = hub
                self._hub_sessions[key] = weakref.WeakSet()
                self._hub_connect_locks[key] = threading.Lock()
                self._hub_plugins_discovered[key] = False

                self.logger.debug(
                    'Created new shared EventHub for {0}@{1}'.format(
                        api_user, server_url
                    )
                )

                # Connect if requested
                if auto_connect:
                    self._ensure_connected(key, hub)
            else:
                existing_hub = self._hubs[key]
                self.logger.debug(
                    'Reusing existing EventHub for {0}@{1} ({2} active sessions)'.format(
                        api_user, server_url, len(self._hub_sessions[key])
                    )
                )

                # If auto_connect requested and hub not connected, connect it
                if auto_connect and not existing_hub.connected:
                    self._ensure_connected(key, existing_hub)

                hub = existing_hub

            return hub, key

    def _ensure_connected(self, hub_key, hub):
        """Ensure the hub is connected (thread-safe).

        Args:
            hub_key: The hub registry key.
            hub: The EventHub instance to connect.
        """
        # Use per-hub lock to ensure only one thread initiates connection
        with self._hub_connect_locks[hub_key]:
            if not hub.connected and not hub._connection_initialised:
                hub.init_connection()
                # Connect in background thread
                connect_thread = threading.Thread(target=hub.connect)
                connect_thread.daemon = True
                connect_thread.start()

    def register_session(self, hub_key, session):
        """Register a session as using this hub.

        Args:
            hub_key: The hub registry key (server_url, api_user, api_key).
            session: The session object (WeakSet will create weak ref automatically).
        """
        with self._lock:
            if hub_key in self._hub_sessions:
                self._hub_sessions[hub_key].add(session)

    def on_session_deleted(self, hub_key):
        """Callback when a session is garbage collected.

        Args:
            hub_key: The hub registry key.
        """
        with self._lock:
            if hub_key not in self._hub_sessions:
                return

            # WeakSet automatically removes dead references
            active_sessions = len(self._hub_sessions[hub_key])

            if active_sessions == 0:
                # No more sessions using this hub - disconnect and clean up
                hub = self._hubs.pop(hub_key, None)
                self._hub_sessions.pop(hub_key, None)
                self._hub_connect_locks.pop(hub_key, None)
                self._hub_plugins_discovered.pop(hub_key, None)

                if hub:
                    try:
                        if hub.connected:
                            # Disconnect without unsubscribing - subscribers already cleaned up
                            hub.disconnect(unsubscribe=False)
                            self.logger.debug(
                                'Disconnected unused shared EventHub for {0}@{1}'.format(
                                    hub_key[1], hub_key[0]
                                )
                            )
                    except Exception as error:
                        self.logger.debug(
                            'Error disconnecting unused EventHub: {0}'.format(
                                error)
                        )

    def get_session_count(self, hub_key):
        """Get the number of active sessions for a hub.

        Args:
            hub_key: The hub registry key.

        Returns:
            int: Number of active sessions using this hub.
        """
        with self._lock:
            if hub_key in self._hub_sessions:
                return len(self._hub_sessions[hub_key])
            return 0

    def mark_plugins_discovered(self, hub_key):
        """Mark that plugins have been discovered for this hub.

        Args:
            hub_key: The hub registry key.
        """
        with self._lock:
            if hub_key in self._hub_plugins_discovered:
                self._hub_plugins_discovered[hub_key] = True

    def plugins_discovered(self, hub_key):
        """Check if plugins have been discovered for this hub.

        Args:
            hub_key: The hub registry key.

        Returns:
            bool: True if plugins already discovered for this hub.
        """
        with self._lock:
            return self._hub_plugins_discovered.get(hub_key, False)


# Global singleton instance
_GLOBAL_EVENT_HUB_REGISTRY = EventHubRegistry()


def get_event_hub_registry():
    """Get the global EventHub registry instance.

    Returns:
        EventHubRegistry: The global registry instance.
    """
    return _GLOBAL_EVENT_HUB_REGISTRY
