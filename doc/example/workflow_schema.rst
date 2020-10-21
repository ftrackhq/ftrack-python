..
    :copyright: Copyright (c) 2020 ftrack

.. _example/workflow_schema:

*************************
Creating workflow schemas
*************************

.. currentmodule:: ftrack_api.session

The API exposes `ProjectSchema` that can be used to define what `ObjectType` a
project can have together with `Status` and `Type` that are valid for the
project.

.. note::

    This is an advanced topic, most users will not need it.

.. note::

    ftrack server version 4.5 or higher is required for this example to work.


Below is an example of how to create a complete `ProjectSchema`


Start by querying the data we need to create our project schema::

    status_not_started = session.query('Status where name="{}"'.format('Not started')).one()
    status_in_progress = session.query('Status where name="{}"'.format('In progress')).one()
    status_completed = session.query('Status where name="{}"'.format('Completed')).one()
    status_on_hold = session.query('Status where name="{}"'.format('On Hold')).one()

    all_statuses = [status_not_started, status_in_progress, status_completed, status_on_hold]

    type_generic = session.query('Type where name="{}"'.format('Generic')).one()
    type_modeling = session.query('Type where name="{}"'.format('Modeling')).one()
    type_rigging = session.query('Type where name="{}"'.format('Rigging')).one()
    type_compositing = session.query('Type where name="{}"'.format('Compositing')).one()
    type_deliverable = session.query('Type where name="{}"'.format('Deliverable')).one()
    type_character = session.query('Type where name="{}"'.format('Character')).one()

    all_types = [type_generic, type_modeling, type_rigging, type_compositing, type_deliverable, type_character]

Create a WorkflowSchema defining statuses tasks can have. Each WorkflowSchema is then linked to one or multiple
statuses using a WorkflowSchemaStatus object::

    workflow_schema = session.create('WorkflowSchema')

    for status in all_statuses:
        session.create('WorkflowSchemaStatus', {
            'workflow_schema_id': workflow_schema['id'],
            'status_id': status['id']
        })




Define task types by creating a TaskTypeSchema, linking it to types through TaskTypeSchemaType::

    task_schema = session.create('TaskTypeSchema')

    for typ in all_types:
        session.create('TaskTypeSchemaType', {
            'task_type_schema_id': task_schema['id'],
            'type_id': typ['id']
        })

In a similar manner, define which states a version can have by creating another WorkflowSchema::

    version_schema =  session.create('WorkflowSchema')

    for status in all_statuses:
        session.create('WorkflowSchemaStatus', {
            'workflow_schema_id': version_schema['id'],
            'status_id': status['id']
        })


Then we create the ProjectSchema itself with the ids of the workflows and schemas we already created for Task and
AssetVersion::

    project_schema = session.create('ProjectSchema', {
        'name': 'My custom schema',
        'task_workflow_schema_id': workflow_schema['id'],
        'task_type_schema_id': task_schema['id'],
        'asset_version_workflow_schema_id': version_schema['id'],
    })


Define objects contained in schema, linked with ProjectSchemaObjectType. Also define which statuses and types each
object type can have, linked with Schema and SchemaStatus & SchemaType.

In this example we limit Asset Builds to a reduced set of statuses and types.

Milestone is a built in type which will always be part of a ProjectSchema but it also needs to have statuses and types::

    objecttype_sequence = session.query('ObjectType where name="{}"'.format('Sequence')).one()
    objecttype_shot = session.query('ObjectType where name="{}"'.format('Shot')).one()
    objecttype_folder = session.query('ObjectType where name="{}"'.format('Folder')).one()
    objecttype_assetbuild = session.query('ObjectType where name="{}"'.format('Asset Build')).one()
    objecttype_milestone = session.query('ObjectType where name="{}"'.format('Milestone')).one()

    for (objecttype, statuses, types) in [
            (objecttype_sequence, None, None),
            (objecttype_shot, None, None),
            (objecttype_folder, None, None),
            (objecttype_assetbuild,
                [status_in_progress,status_completed,status_on_hold],
                [type_generic, type_character]),
            (objecttype_milestone, None, None),
        ]:
        session.create('ProjectSchemaObjectType', {
            'project_schema_id': project_schema['id'],
            'object_type_id': objecttype['id']
        })

        object_type_schema = session.create('Schema', {
            'project_schema_id': project_schema['id'],
            'object_type_id': objecttype['id']
        })

        for status in statuses or all_statuses:
            session.create('SchemaStatus', {
                'schema_id': object_type_schema['id'],
                'status_id': status['id']
            })
        for typ in types or all_types:
            session.create('SchemaType', {
                'schema_id': object_type_schema['id'],
                'type_id': typ['id']
            })

A more complex `ProjectSchema` can have overrides for Task where different types of tasks can have different statuses.
For example Animation can have different statuses compared to all other types such as Modelling.

Create a override for Deliverable task type, allowing it to only have two states::

    override_workflow_schema = session.create('WorkflowSchema', {
        'name': 'My schema deliverable override '
    })
    for status in [status_in_progress, status_completed]:
        session.create('WorkflowSchemaStatus', {
            'workflow_schema_id': override_workflow_schema['id'],
            'status_id': status['id']
        })

    session.create('ProjectSchemaOverride', {
        'project_schema_id': project_schema['id'],
        'type_id': type_deliverable['id'],
        'workflow_schema_id': override_workflow_schema['id'],
    })


A task template can be used when creating Asset builds, Shots, etc to also have a predefined set of tasks created.
Create a Modeling template containing two task types::

    task_template = session.create('TaskTemplate', {
        'project_schema_id': project_schema['id'],
        'name': 'Modeling'
    })
    for typ in [type_modeling, type_rigging]:
        session.create('TaskTemplateItem', {
            'template_id': task_template['id'],
            'task_type_id': typ['id']
        })



Finally, commit our new project schema::

    session.commit()


