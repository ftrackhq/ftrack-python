# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack.entity.factory
import ftrack.entity.base


def default_task_status(entity):
    '''Return default task status entity for *entity*.'''
    return entity.session.query('TaskStatus')[0]


def default_task_type(entity):
    '''Return default task type entity for *entity*.'''
    return entity.session.query('TaskType')[0]


def default_task_priority(entity):
    '''Return default task priority entity for *entity*.'''
    return entity.session.query('PriorityType')[0]


class ProjectSchema(ftrack.entity.base.Entity):
    '''Class representing ProjectSchema.'''

    def get_statuses(self, schema, type_id=None):
        '''Return statuses for *schema* and optional *type_id*.

        *type_id* is the id of the TaskType for a Task and can be used to get
        statuses where the workflow has been overridden.

        '''
        # TODO: Refactor this once arbitrary context is supported on server.
        if schema == 'Task':
            if type_id is not None:
                overrides = self['_overrides']
                for override in overrides:
                    if override['type_id'] == type_id:
                        return override['workflow_schema']['statuses'][:]

            return self['_task_workflow']['statuses'][:]

        elif schema == 'Shot':
            return self['_shot_workflow']['statuses'][:]

        elif schema == 'AssetVersion':
            return self['_version_workflow']['statuses'][:]

        elif schema == 'AssetBuild':
            for _schema in self['_schemas']:
                if _schema['type_id'] == '4be63b64-5010-42fb-bf1f-428af9d638f0':
                    result = self.session.query(
                        'select task_status from SchemaStatus'
                        ' where schema_id is {0}'.format(_schema['id'])
                    )
                    return [
                        schema_type['task_status'] for schema_type in result
                    ]

        raise ValueError('Schema {0} does not have statuses.'.format(schema))

    def get_types(self, schema):
        '''Return statuses for *schema*.'''
        # TODO: Refactor this once arbitrary context is supported on server.
        if schema == 'Task':
            return self['_task_type_schema']['types'][:]

        elif schema == 'AssetBuild':
            for _schema in self['_schemas']:
                if _schema['type_id'] == '4be63b64-5010-42fb-bf1f-428af9d638f0':
                    result = self.session.query(
                        'select task_type from SchemaType'
                        ' where schema_id is {0}'.format(_schema['id'])
                    )
                    return [schema_type['task_type'] for schema_type in result]

        raise ValueError('Schema {0} does not have types.'.format(schema))


class Factory(ftrack.entity.factory.StandardFactory):
    '''Entity class factory.'''

    def create(self, schema, bases=None):
        '''Create and return entity class from *schema*.'''
        if schema['id'] == 'ProjectSchema':
            cls = super(Factory, self).create(schema, bases=[ProjectSchema])
        else:
            cls = super(Factory, self).create(schema, bases=bases)

        # Add dynamic default values to appropriate attributes so that end
        # users don't need to specify them each time.
        if schema['id'] in ('Episode', 'Sequence'):
            cls.attributes.get('status').default_value = default_task_status

        if schema['id'] in ('Episode', 'Sequence', 'Shot', 'AssetBuild', 'Task'):
            cls.attributes.get('priority').default_value = default_task_priority

        if schema['id'] in ('Episode', 'Sequence', 'Shot'):
            cls.attributes.get('type').default_value = default_task_type

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
