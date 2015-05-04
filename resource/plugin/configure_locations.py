# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack_api
import ftrack_api.entity.location
import ftrack_api.accessor.disk


def configure_locations(event):
    '''Configure locations for session.'''
    session = event['data']['session']

    # Find location(s) and customise instances.
    #
    # location = session.query('Location where name is "my.location"')[0]
    # ftrack_api.mixin(location, ftrack_api.entity.location.UnmanagedLocationMixin)
    # location.accessor = ftrack_api.accessor.disk.DiskAccessor(prefix='')


def register(session):
    '''Register plugin with *session*.'''

    # Validate that session is instance of ftrack_api.Session, if not
    # therefore return early since the register probably is called
    # from old API.
    if not isinstance(session, ftrack_api.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.api.session.configure-location',
        configure_locations
    )
