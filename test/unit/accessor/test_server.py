# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import pytest

import ftrack_api
import ftrack_api.exception
import ftrack_api.accessor.server
import ftrack_api.data


def test_read_and_write(new_component, session):
    """Read and write data from server accessor."""
    random_data = uuid.uuid1().hex.encode()

    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_data)
    http_file.close()

    data = accessor.open(new_component["id"], "r")
    assert data.read() == random_data, "Read data is the same as written."
    data.close()


def test_remove_data(new_component, session):
    """Remove data using server accessor."""
    random_data = uuid.uuid1().hex

    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_data)
    http_file.close()

    accessor.remove(new_component["id"])

    data = accessor.open(new_component["id"], "r")
    with pytest.raises(ftrack_api.exception.AccessorOperationFailedError):
        data.read()


def test_read_timeout(new_component, session, monkeypatch):
    """Test that read operations respect timeout settings."""
    random_data = uuid.uuid1().hex.encode()

    # First, write some data so there's something to read
    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_data)
    http_file.close()

    # Set an impossibly short timeout - no server can respond this fast
    monkeypatch.setattr(session, "request_timeout", 0.0001)

    # Open a new file handle (this captures the patched timeout)
    data = accessor.open(new_component["id"], "r")
    with pytest.raises(
        ftrack_api.exception.AccessorOperationFailedError, match="timed out"
    ):
        data.read()


def test_write_timeout(new_component, session, monkeypatch):
    """Test that write operations respect timeout settings."""
    random_data = uuid.uuid1().hex.encode()

    # Set an impossibly short timeout
    monkeypatch.setattr(session, "request_timeout", 0.0001)

    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_data)

    # Timeout is caught and wrapped in AccessorOperationFailedError
    with pytest.raises(
        ftrack_api.exception.AccessorOperationFailedError, match="timed out"
    ):
        http_file.close()  # close() triggers flush() which triggers _write()


def test_remove_timeout(new_component, session, monkeypatch):
    """Test that remove operations respect timeout settings."""
    # Write something first
    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(b"test data")
    http_file.close()

    # Set timeout and create new accessor to pick up the timeout for remove()
    monkeypatch.setattr(session, "request_timeout", 0.0001)
    accessor = ftrack_api.accessor.server._ServerAccessor(session)

    with pytest.raises(
        ftrack_api.exception.AccessorOperationFailedError, match="timed out"
    ):
        accessor.remove(new_component["id"])
