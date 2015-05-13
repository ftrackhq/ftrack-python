# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.entity.base


class ProjectSchema(ftrack_api.entity.base.Entity):
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
                        'select task_status from SchemaStatus '
                        'where schema_id is {0}'.format(_schema['id'])
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
                        'select task_type from SchemaType '
                        'where schema_id is {0}'.format(_schema['id'])
                    )
                    return [schema_type['task_type'] for schema_type in result]

        raise ValueError('Schema {0} does not have types.'.format(schema))
