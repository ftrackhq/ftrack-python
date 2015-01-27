..
    :copyright: Copyright (c) 2014 ftrack

.. currentmodule:: ftrack.session

.. _tutorial:

********
Tutorial
********

First make sure the ftrack Python API is :ref:`installed <installing>`.

Then start a Python session and import the ftrack API::

    >>> import ftrack

Before continuing, execute the following code to create a helper function for
printing entities in a more human readable format.::

    >>> import ftrack.formatter
    >>>
    >>> def print_entity(entity):
    ...     '''Pretty print *entity* without fetching unset attribute values.'''
    ...     with session.auto_populating(False):
    ...         print ftrack.formatter.format(entity)


The API uses :ref:`sessions <using_sessions>` to manage communication with an
ftrack server. Create a session that connects to your ftrack server (changing
the passed values as appropriate)::

    >>> session = ftrack.Session(
    ...     server_url='http://mycompany.ftrackapp.com',
    ...     api_key='7545384e-a653-11e1-a82c-f22c11dd25eq',
    ...     api_user='martin'
    ... )

.. note::

    A session can use :ref:`environment variables
    <using_sessions/configuring_with_environment_variables>` to configure
    itself.

Now print a list of the available entity types retrieved from the server::

    >>> print session.types.keys()
    [u'AbstractTask', u'ObjectType', u'PriorityType', u'Project', u'Sequence',
     u'Shot', u'Task', u'TaskStatus', u'TaskType', u'Timelog', u'User']

Now the list of possible entity types is known, query the server to retrieve
entities of a particular type by using the :meth:`Session.query` method::

    >>> projects = session.query('Project')

Each project retrieved will be an :ref:`entity <working_with_entities>` instance
that behaves much like a standard Python dictionary. For example, to find out
the available keys for an entity, call the :meth:`~ftrack.entity.Entity.keys`
method::

    >>> print projects[0].keys()
    [u'status', u'is_global', u'name', u'end_date', u'context_type',
     u'id', u'full_name', u'root', u'start_date']

Now, iterate over the retrieved entities and print each ones name::

    >>> for project in projects:
    ...     print project['name']
    test
    client_review
    tdb
    man_test
    ftrack
    bunny

.. note::

    Many attributes for retrieved entities are loaded on demand when the
    attribute is first accessed. Doing this lots of times in a script can be
    inefficient, so there is also an easy way to :ref:`optimise queries
    <querying/optimising_queries>`.

To narrow a search, add :ref:`criteria <querying/using_criteria>` to the query::

    >>> active_projects = session.query('Project where status is active')

Combine criteria for more powerful queries::

    >>> import arrow
    >>>
    >>> active_projects_ending_before_next_week = session.query(
    ...     'Project where status is active and end_date before "{0}"'
    ...     .format(arrow.now().replace(weeks=+1))
    ... )

Some attributes on an entity will refer to another entity or collection of
entities, such as *children* on a *Project* being a collection of *Context*
entities that have the project as their parent::

    >>> project = session.query('Project')[0]
    >>> print project['children']
    <ftrack.collection.Collection object at 0x00000000045B1438>

And on each *Context* there is a corresponding *parent* attribute which is a
link back to the parent::

    >>> child = project['children'][0]
    >>> print child['parent'] is project
    True

These relationships can also be used in the criteria for a query::

    >>> results = session.query(
    ...     'Context where parent.name like "te%"'
    ... )

To create new entities in the system use :meth:`Session.create`::

    >>> new_sequence = session.create('Sequence', {
    ...     'name': 'Starlord Reveal'
    ... })

The created entity is not yet persisted to the server, but it is still possible
to modify it.

    >>> new_sequence['description'] = 'First hero character reveal.'

The sequence also needs a parent. This can be done in one of two ways:

* Set the parent attribute on the sequence::

    >>> new_sequence['parent'] = project

* Add the sequence to a parent's children attribute::

    >>> project['children'].append(new_sequence)

When ready, persist to the server using :meth:`Session.commit`::

    >>> session.commit()

Creating a project
==================

A project with sequences, shots and tasks can be created in one single
transaction. Tasks need to have a type and status set on creation based on the
project schema:

    >>> name = 'projectname_{0}'.format(uuid.uuid1().hex)
    ... project_schema = self.session.query('ProjectSchema')[0]
    ... default_shot_status = project_schema.get_statuses('Shot')[0]
    ... default_task_type = project_schema.get_types('Task')[0]
    ... default_task_status = project_schema.get_statuses(
    ...     'Task', default_task_type['id']
    ... )[0]
    ... 
    ... project = self.session.create('Project', {
    ...     'name': name,
    ...     'full_name': name + '_full',
    ...     'project_schema': project_schema
    ... })
    ... 
    ... for sequence_number in range(1, 5):
    ...     sequence = self.session.create('Sequence', {
    ...         'name': 'seq_{0}'.format(sequence_number),
    ...         'parent': project
    ...     })
    ... 
    ...     for shot_number in range(1, 5):
    ...         shot = self.session.create('Shot', {
    ...             'name': '{0}0'.format(shot_number).zfill(3),
    ...             'parent': sequence,
    ...             'status': default_shot_status
    ...         })
    ... 
    ...         for task_number in range(1, 5):
    ...             self.session.create('Task', {
    ...                 'name': 'task_{0}'.format(task_number),
    ...                 'parent': shot,
    ...                 'status': default_task_status,
    ...                 'type': default_task_type
    ...             })
    ... 
    ... self.session.commit()

Components
==========

Components can currently only be created and added to a location manually.

    >>> sequence_component = session.create('SequenceComponent', {
    ...     'name': 'my sequence component',
    ...     'version': version
    ... })
    ...
    ... for i in range(1, 100):
    ...     component = session.create('FileComponent', {
    ...         'name': 'file_{0}'.format(i),
    ...         'container': sequence_component
    ...     })
    ...
    ... session.create('ComponentLocation', {
    ...     'component': component,
    ...     'location': location,
    ...     'resource_identifier': 'path_to_file'
    ... })
    ...
    ... session.commit()

Metadata
========

Key/value metadata can be written to entities using the metadata property and
also used to query entities.

The matadata property has a similar interface as a dictionary and keys can be
printed using the keys method::

    >>> print new_sequence['metadata'].keys()
    ['frame_padding', 'focal_length']

or items::

    >>> print new_sequence['metadata'].items()
    [('frame_padding': '4'), ('focal_length': '70')]

Read existing metadata::

    >>> print new_sequence['metadata']['frame_padding']
    '4'

Setting metadata can be done in a few ways where that later one will replace
any existing metadata::

    >>> new_sequence['metadata']['frame_padding'] = '5'
    ... new_sequence['metadata']['frame_padding'] = {
    ...     'frame_padding': '4'
    ... }

Entities can also be queried using metadata::

    >>> session.query(
    ...     'Sequence where metadata.key is "frame_padding" and metadata.value is "4"'
    ... )
