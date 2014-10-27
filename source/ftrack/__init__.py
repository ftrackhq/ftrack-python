# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import getpass

from ._version import __version__
from .session import Session as _Session


def Session(server_url=None, api_key=None, api_user=None):
    '''Create and return an isolated session for interaction with ftrack.'''
    if server_url is None:
        server_url = os.environ.get('FTRACK_SERVER')

    if not server_url:
        raise ValueError(
            'Required "server_url" not specified. Pass as argument or set in '
            'environment variable FTRACK_SERVER.'
        )

    if api_key is None:
        api_key = os.environ.get(
            'FTRACK_API_KEY',
            # Backwards compatibility
            os.environ.get('FTRACK_APIKEY')
        )

    if not api_key:
        raise ValueError(
            'Required "api_key" not specified. Pass as argument or set in '
            'environment variable FTRACK_API_KEY.'
        )

    if api_user is None:
        api_user = os.environ.get('FTRACK_API_USER')
        if not api_user:
            try:
                api_user = getpass.getuser()
            except Exception:
                pass

    if not api_user:
        raise ValueError(
            'Required "api_user" not specified. Pass as argument, set in '
            'environment variable FTRACK_API_USER or one of the standard '
            'environment variables used by Python\'s getpass module.'
        )

    return _Session(server_url=server_url, api_key=api_key, api_user=api_user)
