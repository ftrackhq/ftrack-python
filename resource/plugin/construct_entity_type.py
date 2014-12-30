# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack.entity.factory


def default_task_status(entity):
    '''Return default task status entity for *entity*.'''
    return entity.session.query('TaskStatus')[0]


def default_task_type(entity):
    '''Return default task type entity for *entity*.'''
    return entity.session.query('TaskType')[0]


def default_task_priority(entity):
    '''Return default task priority entity for *entity*.'''
    return entity.session.query('PriorityType')[0]


class Factory(ftrack.entity.factory.Factory):
    '''Entity class factory.'''

    def create(self, schema, bases=None):
        '''Create and return entity class from *schema*.'''
        cls = super(Factory, self).create(schema, bases=bases)

        if schema['id'] in ('Episode', 'Sequence'):
            # Add dynamic default values to appropriate attributes so that end
            # users don't need to specify them each time.
            cls.attributes.get('status').default_value = default_task_status
            cls.attributes.get('type').default_value = default_task_type
            cls.attributes.get('priority').default_value = default_task_priority

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
