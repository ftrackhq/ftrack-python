# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack.entity


def construct_entity_type(event):
    '''Return class to represent entity type specified by *event*.'''
    return ftrack.entity.class_factory(event['data']['schema'])


def register(session):
    '''Register plugin with *session*.'''
    session.event_hub.subscribe(
        'topic=ftrack.session.construct-entity-type',
        construct_entity_type
    )
