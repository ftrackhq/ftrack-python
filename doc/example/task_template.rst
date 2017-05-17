..
    :copyright: Copyright (c) 2015 ftrack

.. _example/task_template:


***************************
Working with Task Templates
***************************

Task templates can help you organize your workflows by building a collection
of tasks to be applied for specific contexts. They can be applied to all `Context`
objects for example Project, Sequences, Shots, etc.. Normally you would create your
Task Templates from the Schema settings page.

Creating task templates
=======================

Below we create two new task templates. For the example to work the project
schema must contain `Shot` and `Asset Build` object types and task types
"Modeling", "Lookdev", "Compositing" and "Lighting"::


    # Naively pick the first project.
    project = session.query('Project').first()
    project_schema = project.get('project_schema')

    task_templates = {
        'Asset Build': [
            'Modeling',
            'Lookdev',
        ],

        'Shot': [
            'Compositing',
            'Lighting'
        ]
    }

    # fist we create our task templates
    for task_template_name, task_types in task_templates.items():
        task_template = session.create(
            'TaskTemplate', {
                'name': task_template_name,
                'project_schema': project_schema
            }
        )

        schema_task_types = project_schema.get(
            '_task_type_schema'
        )

        # iterate over the project schema task types
        # and add the ones matching our names
        for task_type in schema_task_types.get('types'):
            if task_type.get('name') in task_types:

                session.create(
                    'TaskTemplateItem', {
                        'template': task_template,
                        'task_type': task_type
                    }
                )

    session.commit()


Query task templates
====================

Using our newly created task templates we create tasks for all shots and
asset builds in the project::


    # fetch all `Asset Build`s and `Shot`s for the project
    contexts = session.query(
        'TypedContext where object_type.name  in ("Asset Build", "Shot") and project_id = "{0}"'.format(
            project.get('id')
        )
    )

    for context in contexts:
        #fetch a matching task template for the context
        task_template = session.query(
            'select items.task_type.name from TaskTemplate where name="{0}"'.format(
                context.get('object_type').get('name')
            )
        ).first()

        # create a task for each task type in the task template
        for task_type in [t.get('task_type') for t in task_template.get('items')]:

            session.create(
                'Task', {
                    'name': task_type.get('name'),
                    'parent': context
                }
            )

    session.commit()

