# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import uuid
import hashlib
import base64
import json

import requests

from .base import Accessor
from ..data import String
from ftrack_api.exception import AccessorOperationFailedError


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
            self.wrapped_file.write(response.content)
            self.seek(position)

            self._hasRead = True

        return self.wrapped_file.read()

    def _write(self):
        '''Write current data to remote *resource_identifier*.'''
        position = self.tell()
        self.seek(0)

        size = self._get_size()
        response = requests.post(
            '{0}/component/put'.format(self._session.server_url),
            data={
                'id': self.resource_identifier,
                'username': self._session.api_user,
                'apiKey': self._session.api_key,
                'resumableChunkNumber': 1,
                'resumableChunkSize': size,
                'resumableCurrentChunkSize': size,
                'resumableTotalSize': size,
                'resumableIdentifier': uuid.uuid1().hex,
                'checksum': self._compute_checksum()
            },
            files={'file': self.wrapped_file},
            allow_redirects=False
        )

        if response.status_code == 200:
            try:
                data = json.loads(response.text)
            except ValueError:
                pass
            else:
                if 'url' in data and 'headers' in data:
                    # The response contains a url and headers that should be
                    # used to put the file.
                    self.seek(0)

                    response = requests.put(
                        data['url'],
                        data=self.wrapped_file,
                        headers=data['headers']
                    )
                    if response.status_code != 200:
                        raise AccessorOperationFailedError(
                            'Failed to write file.'
                        )
        else:
            raise AccessorOperationFailedError(
                'Failed to write file.'
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
            raise AccessorOperationFailedError(
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
