# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import hashlib
import base64
import json

import requests

from .base import Accessor
from ..data import String
import ftrack_api.exception


class ServerFile(String):
    '''HTTP Buffered File.'''
    def __init__(self, resource_identifier, session, mode='rb', **kwargs):
        '''Initialise file.'''
        self.resource_identifier = resource_identifier
        self.mode = mode
        self._hasRead = False
        self._session = session
        super(ServerFile, self).__init__(**kwargs)

    def flush(self):
        '''Flush all changes.'''
        super(ServerFile, self).flush()

        # TODO: Handle other modes.
        if self.mode == 'wb':
            self._write()

    def read(self):
        '''Read remote content from resource_identifier.'''
        if not self._hasRead:
            position = self.tell()
            self.wrapped_file.seek(0)

            response = requests.get(
                '{0}/component/get'.format(self._session.server_url),
                params={
                    'id': self.resource_identifier,
                    'username': self._session.api_user,
                    'apiKey': self._session.api_key
                }
            )

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as error:
                raise ftrack_api.exception.AccessorOperationFailedError(
                    'Failed to read data: {0}.'.format(error)
                )

            self.wrapped_file.write(response.content)
            self.seek(position)

            self._hasRead = True

        return self.wrapped_file.read()

    def _write(self):
        '''Write current data to remote *resource_identifier*.'''
        position = self.tell()
        self.seek(0)

        url = '{0}/component/getPutMetadata'.format(
            self._session.server_url
        )

        # Retrieve component from cache to construct a filename.
        component = self._session.get('FileComponent', self.resource_identifier)
        if not component:
            raise ftrack_api.exception.AccessorOperationFailedError(
                'Unable to retrieve component with id: {0}.'.format(
                    self.resource_identifier
                )
            )

        # Construct a name from component name and file_type.
        name = component['name']
        if component['file_type']:
            name = u'{0}.{1}'.format(
                name,
                component['file_type'].lstrip('.')
            )

        # Get put metadata.
        response = requests.get(
            url,
            params={
                'id': self.resource_identifier,
                'username': self._session.api_user,
                'apiKey': self._session.api_key,
                'checksum': self._compute_checksum(),
                'fileSize': self._get_size(),
                'fileName': name
            }
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            raise ftrack_api.exception.AccessorOperationFailedError(
                'Failed to get put metadata: {0}.'.format(error)
            )

        try:
            metadata = json.loads(response.text)
        except ValueError as error:
            raise ftrack_api.exception.AccessorOperationFailedError(
                'Failed to decode put metadata response: {0}.'.format(error)
            )

        # Ensure at beginning of file before put.
        self.seek(0)

        # Put the file based on the metadata.
        response = requests.put(
            metadata['url'],
            data=self.wrapped_file,
            headers=metadata['headers']
        )

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            raise ftrack_api.exception.AccessorOperationFailedError(
                'Failed to put file to server: {0}.'.format(error)
            )

        self.seek(position)

    def _get_size(self):
        '''Return size of file in bytes.'''
        position = self.tell()
        self.seek(0, os.SEEK_END)
        length = self.tell()
        self.seek(position)
        return length

    def _compute_checksum(self):
        '''Return checksum for file.'''
        fp = self.wrapped_file
        buf_size = 8192
        hash_obj = hashlib.md5()
        spos = fp.tell()

        s = fp.read(buf_size)
        while s:
            hash_obj.update(s)
            s = fp.read(buf_size)

        base64_digest = base64.encodestring(hash_obj.digest())
        if base64_digest[-1] == '\n':
            base64_digest = base64_digest[0:-1]

        fp.seek(spos)
        return base64_digest


class _ServerAccessor(Accessor):
    '''Provide server location access.'''

    def __init__(self, session, **kw):
        '''Initialise location accessor.'''
        super(_ServerAccessor, self).__init__(**kw)

        self._session = session

    def open(self, resource_identifier, mode='rb'):
        '''Return :py:class:`~ftrack_api.Data` for *resource_identifier*.'''
        return ServerFile(resource_identifier, session=self._session, mode=mode)

    def remove(self, resourceIdentifier):
        '''Remove *resourceIdentifier*.'''
        response = requests.get(
            '{0}/component/remove'.format(self._session.server_url),
            params={
                'id': resourceIdentifier,
                'username': self._session.api_user,
                'apiKey': self._session.api_key
            }
        )
        if response.status_code != 200:
            raise ftrack_api.exception.AccessorOperationFailedError(
                'Failed to remove file.'
            )

    def get_container(self, resource_identifier):
        '''Return resource_identifier of container for *resource_identifier*.'''
        return None

    def make_container(self, resource_identifier, recursive=True):
        '''Make a container at *resource_identifier*.'''

    def list(self, resource_identifier):
        '''Return list of entries in *resource_identifier* container.'''
        raise NotImplementedError()

    def exists(self, resource_identifier):
        '''Return if *resource_identifier* is valid and exists in location.'''
        return False

    def is_file(self, resource_identifier):
        '''Return whether *resource_identifier* refers to a file.'''
        raise NotImplementedError()

    def is_container(self, resource_identifier):
        '''Return whether *resource_identifier* refers to a container.'''
        raise NotImplementedError()

    def is_sequence(self, resource_identifier):
        '''Return whether *resource_identifier* refers to a file sequence.'''
        raise NotImplementedError()

    def get_url(self, resource_identifier):
        '''Return url for *resource_identifier*.'''
        url_string = (
            u'{url}/component/get?id={id}&username={username}'
            u'&apiKey={apiKey}'
        )
        return url_string.format(
            url=self._session.server_url,
            id=resource_identifier,
            username=self._session.api_user,
            apiKey=self._session.api_key
        )
