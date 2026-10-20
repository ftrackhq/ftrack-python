# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import uuid

import pytest
import requests

import ftrack_api
import ftrack_api.exception
import ftrack_api.accessor.server
import ftrack_api.data
import ftrack_api._uploader


@pytest.fixture(scope="module")
def random_binary_data():
    return uuid.uuid1().hex.encode()


@pytest.fixture(scope="module")
def large_binary_data():
    """Return data large enough to be uploaded in three parts."""
    return os.urandom(2 * 8 * ftrack_api._uploader.MEGABYTE + 1)


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


def test_read_and_write_multipart(new_component, large_binary_data, session, mocker):
    """Read and write data uploaded in multiple parts."""
    mocker.patch.object(
        session,
        "complete_multipart_upload",
        wraps=session.complete_multipart_upload,
    )

    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(large_binary_data)
    http_file.close()

    assert session.complete_multipart_upload.call_count == 1

    data = accessor.open(new_component["id"], "r")
    assert data.read() == large_binary_data, "Read data is the same as written."
    data.close()


@pytest.mark.parametrize("server_response", ["error", "single_url"])
def test_write_multipart_unavailable(
    new_component, large_binary_data, session, mocker, server_response
):
    """Fall back to a single PUT when server cannot upload in parts."""
    get_upload_metadata = session.get_upload_metadata

    def without_multipart(
        component_id, file_name, file_size, checksum=None, parts=None
    ):
        if parts is not None:
            if server_response == "error":
                # Raised when multi-part uploads are enabled on the server but
                # its storage is not S3 compatible.
                raise ftrack_api.exception.ServerError(
                    "Multipart upload is not supported."
                )
            # Returned by servers with multi-part uploads disabled.
            return get_upload_metadata(component_id, file_name, file_size)

        return get_upload_metadata(component_id, file_name, file_size, checksum)

    mocker.patch.object(session, "get_upload_metadata", side_effect=without_multipart)
    mocker.patch.object(session, "complete_multipart_upload")

    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(large_binary_data)
    http_file.close()

    assert session.complete_multipart_upload.call_count == 0
    assert session.get_upload_metadata.call_args.kwargs["checksum"]

    data = accessor.open(new_component["id"], "r")
    assert data.read() == large_binary_data, "Read data is the same as written."
    data.close()


def test_write_multipart_part_failure(
    new_component, large_binary_data, session, mocker
):
    """Fail without completing the upload when a part cannot be uploaded."""
    mocker.patch.object(
        ftrack_api._uploader,
        "upload_parts",
        side_effect=requests.exceptions.HTTPError("403 Client Error"),
    )
    mocker.patch.object(session, "complete_multipart_upload")

    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(large_binary_data)

    with pytest.raises(ftrack_api.exception.AccessorOperationFailedError, match="403"):
        http_file.close()

    assert session.complete_multipart_upload.call_count == 0


def test_write_too_large_file(new_component, random_binary_data, session, mocker):
    """Fail before requesting upload metadata when the file has too many parts."""
    # Every non-empty file exceeds the maximum size when no parts are allowed.
    mocker.patch.object(ftrack_api._uploader, "MAX_PARTS", 0)
    mocker.patch.object(session, "get_upload_metadata")

    accessor = ftrack_api.accessor.server._ServerAccessor(session)
    http_file = accessor.open(new_component["id"], mode="wb")
    http_file.write(random_binary_data)

    with pytest.raises(
        ftrack_api.exception.AccessorOperationFailedError,
        match="Failed to put file to server: File is larger than the maximum",
    ):
        http_file.close()

    assert session.get_upload_metadata.call_count == 0
