# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import uuid

import pytest

import ftrack_api
import ftrack_api.exception
import ftrack_api.accessor.server
import ftrack_api.data


@pytest.fixture(scope="module")
def random_binary_data():
    return uuid.uuid1().hex.encode()


def test_read_and_write(new_component, random_binary_data, session):
    """Read and write data from server accessor."""
    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_binary_data)
    http_file.close()

    data = accessor.open(new_component["id"], "r")
    assert data.read() == random_binary_data, "Read data is the same as written."
    data.close()


def test_remove_data(new_component, random_binary_data, session):
    """Remove data using server accessor."""
    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_binary_data)
    http_file.close()

    accessor.remove(new_component["id"])

    data = accessor.open(new_component["id"], "r")
    with pytest.raises(ftrack_api.exception.AccessorOperationFailedError):
        data.read()


def test_read_timeout(new_component, random_binary_data, session, monkeypatch):
    """Test that read operations respect timeout settings."""
    # First, write some data so there's something to read
    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_binary_data)
    http_file.close()

    # Set an impossibly short timeout - no server can respond this fast
    monkeypatch.setattr(session, "request_timeout", 0.0001)

    # Open a new file handle (this captures the patched timeout)
    data = accessor.open(new_component["id"], "r")
    with pytest.raises(
        ftrack_api.exception.AccessorOperationFailedError, match="timed out"
    ):
        data.read()


def test_write_timeout(new_component, random_binary_data, session, monkeypatch):
    """Test that write operations respect timeout settings."""
    # Set an impossibly short timeout
    monkeypatch.setattr(session, "request_timeout", 0.0001)

    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_binary_data)

    # Timeout is caught and wrapped in AccessorOperationFailedError
    with pytest.raises(
        ftrack_api.exception.AccessorOperationFailedError, match="timed out"
    ):
        http_file.close()  # close() triggers flush() which triggers _write()


def test_remove_timeout(new_component, random_binary_data, session, monkeypatch):
    """Test that remove operations respect timeout settings."""
    # Write something first
    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_binary_data)
    http_file.close()

    # Set timeout and create new accessor to pick up the timeout for remove()
    monkeypatch.setattr(session, "request_timeout", 0.0001)
    accessor = ftrack_api.accessor.server._ServerAccessor(session)

    with pytest.raises(
        ftrack_api.exception.AccessorOperationFailedError, match="timed out"
    ):
        accessor.remove(new_component["id"])
