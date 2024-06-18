# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import hashlib
import base64
from typing import BinaryIO

import requests

from .base import Accessor
from ..data import String
import ftrack_api.exception
from ftrack_api.uploader import Uploader
import ftrack_api.symbol


class ServerFile(String):
    """Representation of a server file."""

    def __init__(self, resource_identifier, session, mode="rb"):
        """Initialise file."""
        self.mode = mode
        self.resource_identifier = resource_identifier
        self._session = session
        self._has_read = False
        self._has_uploaded = False

        super(ServerFile, self).__init__()

    def flush(self):
        """Flush all changes."""
        super(ServerFile, self).flush()

        if not self._has_uploaded and self.mode == "wb":
            self._flush_to_server()

    def read(self, limit=None):
        """Read file."""
        if not self._has_read:
            self._read()
            self._has_read = True

        return super(ServerFile, self).read(limit)

    def write(self, content):
        """Write *content* to file."""
        assert self._has_uploaded is False, "Cannot write to file after upload."

        return super().write(content)

    def _read(self):
        """Read all remote content from key into wrapped_file."""
        position = self.tell()
        self.seek(0)

        response = requests.get(
            "{0}/component/get".format(self._session.server_url),
            params={
                "id": self.resource_identifier,
                "username": self._session.api_user,
                "apiKey": self._session.api_key,
            },
            stream=True,
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            raise ftrack_api.exception.AccessorOperationFailedError(
                "Failed to read data: {0}.".format(error)
            )

        for block in response.iter_content(ftrack_api.symbol.CHUNK_SIZE):
            self.wrapped_file.write(block)

        self.seek(position)
        self._has_uploaded = False

    def _flush_to_server(self):
        """Write current data to remote key."""
        position = self.tell()

        self.upload_to_server(self.wrapped_file)

        self.seek(position)

    def upload_to_server(self, source_file: "BinaryIO"):
        """
        Direct upload source to server.
        Use with caution, it will forbid any further write operation until you read the file.
        """
        # Retrieve component from cache to construct a filename.
        component = self._session.get("FileComponent", self.resource_identifier)
        if not component:
            raise ftrack_api.exception.AccessorOperationFailedError(
                "Unable to retrieve component with id: {0}.".format(
                    self.resource_identifier
                )
            )

        # Construct a name from component name and file_type.
        name = component["name"]
        if component["file_type"]:
            name = "{0}.{1}".format(name, component["file_type"].lstrip("."))

        try:
            uploader = Uploader(
                self._session,
                component_id=self.resource_identifier,
                file_name=name,
                file_size=self._get_size(source_file),
                file=source_file,
                checksum=self._compute_checksum(source_file),
            )
            uploader.start()
        except Exception as error:
            raise ftrack_api.exception.AccessorOperationFailedError(
                "Failed to put file to server: {0}.".format(error)
            )

        self._has_uploaded = True

    @staticmethod
    def _get_size(file: "BinaryIO"):
        """Return size of file in bytes."""
        position = file.tell()
        length = file.seek(0, os.SEEK_END)
        file.seek(position)
        return length

    @staticmethod
    def _compute_checksum(fp: "BinaryIO"):
        """Return checksum for file."""
        buf_size = ftrack_api.symbol.CHUNK_SIZE
        hash_obj = hashlib.md5()
        spos = fp.tell()

        s = fp.read(buf_size)
        while s:
            hash_obj.update(s)
            s = fp.read(buf_size)

        base64_digest = base64.encodebytes(hash_obj.digest()).decode("utf-8")
        if base64_digest[-1] == "\n":
            base64_digest = base64_digest[0:-1]

        fp.seek(spos)
        return base64_digest


class _ServerAccessor(Accessor):
    """Provide server location access."""

    def __init__(self, session, **kw):
        """Initialise location accessor."""
        super(_ServerAccessor, self).__init__(**kw)

        self._session = session

    def open(self, resource_identifier, mode="rb"):
        """Return :py:class:`~ftrack_api.Data` for *resource_identifier*."""
        return ServerFile(resource_identifier, session=self._session, mode=mode)

    def remove(self, resourceIdentifier):
        """Remove *resourceIdentifier*."""
        response = requests.get(
            "{0}/component/remove".format(self._session.server_url),
            params={
                "id": resourceIdentifier,
                "username": self._session.api_user,
                "apiKey": self._session.api_key,
            },
        )
        if response.status_code != 200:
            raise ftrack_api.exception.AccessorOperationFailedError(
                "Failed to remove file."
            )

    def get_container(self, resource_identifier):
        """Return resource_identifier of container for *resource_identifier*."""
        return None

    def make_container(self, resource_identifier, recursive=True):
        """Make a container at *resource_identifier*."""

    def list(self, resource_identifier):
        """Return list of entries in *resource_identifier* container."""
        raise NotImplementedError()

    def exists(self, resource_identifier):
        """Return if *resource_identifier* is valid and exists in location."""
        return False

    def is_file(self, resource_identifier):
        """Return whether *resource_identifier* refers to a file."""
        raise NotImplementedError()

    def is_container(self, resource_identifier):
        """Return whether *resource_identifier* refers to a container."""
        raise NotImplementedError()

    def is_sequence(self, resource_identifier):
        """Return whether *resource_identifier* refers to a file sequence."""
        raise NotImplementedError()

    def get_url(self, resource_identifier):
        """Return url for *resource_identifier*."""
        url_string = (
            "{url}/component/get?id={id}&username={username}" "&apiKey={apiKey}"
        )
        return url_string.format(
            url=self._session.server_url,
            id=resource_identifier,
            username=self._session.api_user,
            apiKey=self._session.api_key,
        )

    def get_thumbnail_url(self, resource_identifier, size=None):
        """Return thumbnail url for *resource_identifier*.

        Optionally, specify *size* to constrain the downscaled image to size
        x size pixels.
        """
        url_string = (
            "{url}/component/thumbnail?id={id}&username={username}" "&apiKey={apiKey}"
        )
        url = url_string.format(
            url=self._session.server_url,
            id=resource_identifier,
            username=self._session.api_user,
            apiKey=self._session.api_key,
        )
        if size:
            url += "&size={0}".format(size)

        return url
