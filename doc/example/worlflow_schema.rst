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

    ftrack server version 4.5 or higher is required for this example to work.

Below is an example of how to create a complete `ProjectSchema`::

    # Start by querying the data we need to create our project schema.
    asset_build = session.query(
        'select id from ObjectType where name is "Asset build"'
    ).first()
    milestone = session.query(
        'select id from ObjectType where name is "Milestone"'
    ).first()
    status_1 = session.query(
        'select id from Status where name is "Not started"'
    ).first()
    status_2 = session.query(
        'select id from Status where name is "In progress"'
    ).first()
    type_1 = session.query(
        'select id from Type where name is "Modeling"'
    ).first()
    type_2 = session.query(
        'select id from Type where name is "Animation"'
    ).first()

    # Task and AssetVersion objects use WorkflowSchema to define what statuses they
    # can have. Each WorkflowSchema is then linked to one or multiple statuses using
    # a WorkflowSchemaStatus object.
    task_workflow_schema = session.create('WorkflowSchema')
    version_workflow_schema = session.create('WorkflowSchema')
    session.create('WorkflowSchemaStatus', {
        'workflow_schema_id': task_workflow_schema['id'],
        'status_id': status_1['id']
    })
    session.create('WorkflowSchemaStatus', {
        'workflow_schema_id': version_workflow_schema['id'],
        'status_id': status_1['id']
    })

    # Tasks can also have different types and those are linked to the task using a
    # TaskTypeSchema together with one or multiple TaskTypeSchemaType.
    task_type_schema = session.create('TaskTypeSchema')
    session.create('TaskTypeSchemaType', {
        'task_type_schema_id': task_type_schema['id'],
        'type_id': type_1['id']
    })

    # Then we create the ProjectSchema itself with the ids of the workflows and
    # schemas we already created for Task and AssetVersion.
    project_schema = session.create('ProjectSchema', {
        'name': 'My custom schema',
        'asset_version_workflow_schema_id': version_workflow_schema['id'],
        'task_workflow_schema_id': task_workflow_schema['id'],
        'task_type_schema_id': task_type_schema['id']
    })

    # Then link any additional object types to the ProjectSchema using
    # ProjectSchemaObjectType.
    session.create('ProjectSchemaObjectType', {
        'project_schema_id': project_schema['id'],
        'object_type_id': asset_build['id']
    })

    # Each ObjectType can have statuses and types by creating a Schema and the
    # corresponding SchemaType and SchemaStatus.
    asset_build_schema = session.create('Schema', {
        'project_schema_id': project_schema['id'],
        'object_type_id': asset_build['id']
    })
    session.create('SchemaType', {
        'schema_id': asset_build_schema['id'],
        'type_id': type_1['id']
    })
    session.create('SchemaStatus', {
        'schema_id': asset_build_schema['id'],
        'status_id': status_1['id']
    })

    # Milestone is a built in type which will always be part of a ProjectSchema but
    # it also needs to have statuses and types.
    milestone_schema = session.create('Schema', {
        'project_schema_id': project_schema['id'],
        'object_type_id': milestone['id']
    })
    session.create('SchemaType', {
        'schema_id': milestone_schema['id'],
        'type_id': type_1['id']
    })
    session.create('SchemaStatus', {
        'schema_id': milestone_schema['id'],
        'status_id': status_1['id']
    })

    session.commit()

A more complex `ProjectSchema` can have overrides for Task where different types
of tasks can have different statuses.

Below is an example of how to add an override::

    # Task can have overrides which define different statuses for a type so that
    # Animation can have different statuses compared to all other types such as
    # Modelling.
    task_override_workflow_schema = session.create('WorkflowSchema')
    session.create('WorkflowSchemaStatus', {
        'workflow_schema_id': task_override_workflow_schema['id'],
        'status_id': status_2['id']
    })
    session.create('ProjectSchemaOverride', {
        'id': str(uuid.uuid4()),
        'project_schema_id': project_schema['id'],
        'workflow_schema_id': task_override_workflow_schema['id'],
        'type_id': type_2['id']
    })

    session.commit()
