# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack
import ftrack.entity.location
import ftrack.accessor.disk


def configure_locations(event):
    '''Configure locations for session.'''
    session = event['data']['session']

    # Find location(s) and customise instances.
    #
    # location = session.query('Location where name is "my.location"')[0]
    # ftrack.mixin(location, ftrack.entity.location.UnmanagedLocationMixin)
    # location.accessor = ftrack.accessor.disk.DiskAccessor(prefix='')


def register(session):
    '''Register plugin with *session*.'''
    session.event_hub.subscribe(
        'topic=ftrack.session.configure-location',
        configure_locations
    )
