# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack.entity.factory


class Factory(ftrack.entity.factory.StandardFactory):
    '''Entity class factory.'''

    def create(self, schema, bases=None):
        '''Create and return entity class from *schema*.'''
        # Optionally change bases for class to be generated.
        cls = super(Factory, self).create(schema, bases=bases)

        # Further customise cls before returning.

        return cls


def register(session):
    '''Register plugin with *session*.'''
    factory = Factory()

    def construct_entity_type(event):
        '''Return class to represent entity type specified by *event*.'''
        schema = event['data']['schema']
        return factory.create(schema)

    session.event_hub.subscribe(
        'topic=ftrack.session.construct-entity-type',
        construct_entity_type
    )
