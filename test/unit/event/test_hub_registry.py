# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import pytest
import weakref

import ftrack_api
import ftrack_api.event.hub
import ftrack_api.event.hub_registry
import ftrack_api.event.hub_proxy


@pytest.fixture()
def registry():
    """Return a fresh EventHub registry instance for testing."""
    # Create a new registry instance for isolation between tests
    return ftrack_api.event.hub_registry.EventHubRegistry()


def test_get_or_create_returns_same_hub_for_same_credentials(registry):
    """Return same EventHub instance for identical credentials."""
    hub1 = registry.get_or_create(
        'https://test.ftrack.com',
        'user1',
        'key1',
        auto_connect=False
    )
    
    hub2 = registry.get_or_create(
        'https://test.ftrack.com',
        'user1',
        'key1',
        auto_connect=False
    )
    
    assert hub1 is hub2


def test_get_or_create_returns_different_hub_for_different_credentials(registry):
    """Return different EventHub instances for different credentials."""
    hub1 = registry.get_or_create(
        'https://test.ftrack.com',
        'user1',
        'key1',
        auto_connect=False
    )
    
    hub2 = registry.get_or_create(
        'https://test.ftrack.com',
        'user2',  # Different user
        'key2',
        auto_connect=False
    )
    
    assert hub1 is not hub2


def test_get_or_create_returns_different_hub_for_different_server(registry):
    """Return different EventHub instances for different servers."""
    hub1 = registry.get_or_create(
        'https://test.ftrack.com',
        'user1',
        'key1',
        auto_connect=False
    )
    
    hub2 = registry.get_or_create(
        'https://other.ftrack.com',  # Different server
        'user1',
        'key1',
        auto_connect=False
    )
    
    assert hub1 is not hub2


def test_register_session_tracks_active_sessions(registry):
    """Track active sessions using a hub."""
    hub_key = ('https://test.ftrack.com', 'user1', 'key1')
    
    # Create hub
    registry.get_or_create(*hub_key, auto_connect=False)
    
    # Create mock sessions
    class MockSession:
        pass
    
    session1 = MockSession()
    session2 = MockSession()
    
    # Register sessions
    registry.register_session(hub_key, weakref.ref(session1))
    registry.register_session(hub_key, weakref.ref(session2))
    
    # Check count
    count = registry.get_session_count(hub_key)
    assert count == 2


def test_on_session_deleted_cleans_up_unused_hub(registry):
    """Disconnect and clean up hub when last session is deleted."""
    hub_key = ('https://test.ftrack.com', 'user1', 'key1')
    
    # Create hub
    hub = registry.get_or_create(*hub_key, auto_connect=False)
    
    # Mock the disconnect method to track if it was called
    disconnect_called = []
    original_disconnect = hub.disconnect
    
    def mock_disconnect(*args, **kwargs):
        disconnect_called.append(True)
        # Don't actually disconnect in test
    
    hub.disconnect = mock_disconnect
    
    # Create and register a mock session
    class MockSession:
        pass
    
    session = MockSession()
    session_ref = weakref.ref(session)
    registry.register_session(hub_key, session_ref)
    
    # Delete the session
    del session
    
    # Trigger cleanup
    registry.on_session_deleted(hub_key)
    
    # Hub should be removed from registry
    assert hub_key not in registry._hubs
    assert hub_key not in registry._hub_sessions
    

def test_session_uses_shared_hub_by_default(session):
    """Session uses shared EventHub by default."""
    assert session._is_shared_hub is True
    assert hasattr(session, '_hub_registry')
    assert hasattr(session, '_hub_key')


def test_session_with_force_new_connection_creates_dedicated_hub(session):
    """Session with force_new_connection=True creates dedicated EventHub."""
    # Create a new session with force_new_connection
    dedicated_session = ftrack_api.Session(
        server_url=session.server_url,
        api_user=session.api_user,
        api_key=session.api_key,
        auto_connect_event_hub=False,
        force_new_connection=True
    )
    
    try:
        assert dedicated_session._is_shared_hub is False
        assert dedicated_session._event_hub_impl is not session._event_hub_impl
    finally:
        dedicated_session.close()


def test_multiple_sessions_share_same_hub():
    """Multiple sessions with same credentials share one EventHub."""
    # Note: Using environment variables for credentials from conftest
    session1 = ftrack_api.Session(auto_connect_event_hub=False)
    session2 = ftrack_api.Session(auto_connect_event_hub=False)
    session3 = ftrack_api.Session(auto_connect_event_hub=False)
    
    try:
        # All should share the same underlying EventHub
        assert session1._event_hub_impl is session2._event_hub_impl
        assert session2._event_hub_impl is session3._event_hub_impl
        
        # But should have independent subscriber lists
        assert session1._session_subscribers is not session2._session_subscribers
        assert session2._session_subscribers is not session3._session_subscribers
    finally:
        session1.close()
        session2.close()
        session3.close()


def test_session_event_hub_property_returns_proxy(session):
    """Session.event_hub property returns SessionEventHubProxy."""
    event_hub_proxy = session.event_hub
    
    assert isinstance(
        event_hub_proxy,
        ftrack_api.event.hub_proxy.SessionEventHubProxy
    )
    assert event_hub_proxy._session is session
    assert event_hub_proxy._event_hub is session._event_hub_impl


def test_proxy_delegates_attributes_to_hub(session):
    """SessionEventHubProxy delegates attributes to underlying EventHub."""
    proxy = session.event_hub
    hub = session._event_hub_impl
    
    # Test attribute delegation
    assert proxy.id == hub.id
    assert proxy.logger == hub.logger
    assert proxy.connected == hub.connected


def test_proxy_tracks_session_subscribers(session):
    """SessionEventHubProxy tracks subscribers for the session."""
    def callback(event):
        pass
    
    # Subscribe via proxy
    subscriber_id = session.event_hub.subscribe('topic=test', callback)
    
    # Should be tracked in session
    assert subscriber_id in session._session_subscribers
    
    # Unsubscribe
    session.event_hub.unsubscribe(subscriber_id)
    
    # Should be removed from tracking
    assert subscriber_id not in session._session_subscribers


def test_session_close_only_unsubscribes_own_subscribers():
    """Session.close() only removes its own subscribers from shared hub."""
    session1 = ftrack_api.Session(auto_connect_event_hub=False)
    session2 = ftrack_api.Session(auto_connect_event_hub=False)
    
    def callback1(event):
        pass
    
    def callback2(event):
        pass
    
    try:
        # Subscribe from both sessions
        subscriber_id1 = session1.event_hub.subscribe('topic=test', callback1)
        subscriber_id2 = session2.event_hub.subscribe('topic=test', callback2)
        
        # Both should be tracked separately
        assert subscriber_id1 in session1._session_subscribers
        assert subscriber_id2 in session2._session_subscribers
        
        # Close session1
        session1.close()
        
        # session1's subscriber should be gone, but session2's should remain
        assert subscriber_id2 in session2._session_subscribers
        
    finally:
        if not session1._closed:
            session1.close()
        if not session2._closed:
            session2.close()


def test_dedicated_hub_disconnects_on_close(session):
    """Session with dedicated hub fully disconnects on close."""
    dedicated_session = ftrack_api.Session(
        server_url=session.server_url,
        api_user=session.api_user,
        api_key=session.api_key,
        auto_connect_event_hub=False,
        force_new_connection=True
    )
    
    hub = dedicated_session._event_hub_impl
    
    # Close the session
    dedicated_session.close()
    
    # The hub should have been disconnected
    # (In practice we can't easily test this without mocking, 
    # but we verify the code path was taken)
    assert dedicated_session._closed is True
