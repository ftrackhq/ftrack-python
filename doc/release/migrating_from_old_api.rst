..
    :copyright: Copyright (c) 2015 ftrack

.. _release/migrating_from_old_api:

**********************
Migrating from old API
**********************

Why a new API?
==============

With the introduction of Workflows, ftrack is capable of supporting a greater
diversity of industries. We're enabling teams to closely align the system with
their existing practices and naming conventions, resulting in a tool that feels
more natural and intuitive. The old API was locked to specific workflows, making
it impractical to support this new feature naturally.

We also wanted this new flexibility to extend to developers, so we set about
redesigning the API to fully leverage the power in the system. And while we had
the wrenches out, we figured why not go that extra mile and build in some of the
features that we see developers having to continually implement in-house across
different companies - features such as caching and support for custom pipeline
extensions. In essence, we decided to build the API that, as pipeline
developers, we had always wanted from our production tracking and asset
management systems. We think we succeeded, and we hope you agree.

Installing
==========

Before, you used to download the API package from your ftrack instance. With 
each release of the new API we make it available on :term:`PyPi`, and 
installing is super simple.

    pip install ftrack-python-api

Before installing, it is always good to check the latest
:ref:`release/release_notes`  to see which version of the ftrack server is
required.

.. seealso:: :ref:`installing`

Overview
========

An API needs to be approachable, so we built the ftrack 3.2 API to feel
intuitive and familiar. We bundle all the core functionality into one place – a
session – with consistent methods for interacting with entities in the system::

    import ftrack_api
    session = ftrack_api.Session()

The core methods are straightforward:

Session.create
    create a new entity, like a new version.
Session.query
    fetch entities from the server using a powerful query language.
Session.delete
    delete existing entities.
Session.commit
    commit all changes in one efficient call.

In addition all entities in the API now act like simple Python dictionaries,
with some additional helper methods where appropriate. If you know a little
Python (or even if you don't) getting up to speed should be a breeze::

    >>> print user.keys()
    ['first_name', 'last_name', 'email', ...]
    >>> print user['email']
    'old@example.com'
    >>> user['email'] = 'new@example.com'

And of course, relationships between entities are reflected in a natural way as
well::

    new_timelog = session.create('Timelog', {...})
    task['timelogs'].append(new_timelog)

Open source and standard code style
===================================

The new API is open source software and developed in the public at 
`bitbucket <https://bitbucket.org/ftrack/ftrack-python-api>`_. We welcome you 
to join us in the development and create pull requests and raise issues there.

In the new API, we also follow the standard code style for Python, PEP-8. This
means that you will now find that methods and variables are written on 
``snake_case`` instead of ``camelCase``, amongst other things. We suggest you
do the same in your scripts.

Package name
============

The new module is named :mod:`ftrack_api`, by using a new module name, 
you can continue to use the old API side-by-side with the new.

Old API::

    import ftrack

New API::

    import ftrack_api


Specifying your credentials
===========================

The old API used three environment variables to authenticate with your ftrack
instance: :envvar:`FTRACK_SERVER`, :envvar:`FTRACK_APIKEY` and :envvar:`LOGNAME`.

In the new API, you have the option to either specify the credentials using
the new names :envvar:`FTRACK_SERVER`, :envvar:`FTRACK_API_USER` and 
:envvar:`FTRACK_API_KEY`, or by specifying them when initializing the session::

    >>> import ftrack_api
    >>> session = ftrack_api.Session(
    ...     server_url='http://mycompany.ftrackapp.com',
    ...     api_key='7545384e-a653-11e1-a82c-f22c11dd25eq',
    ...     api_user='martin'
    ... )

In the examples below, will assume that you have imported the module and 

.. seealso:: :ref:`tutorial`


Querying objects
================

The old API relied on predefined methods for querying objects and constructors
which enabled you to get an entity by it's id or name.

Old API::

    project = ftrack.getProject('dev_tutorial')
    task = ftrack.Task('8923b7b3-4bf0-11e5-8811-3c0754289fd3')
    user = ftrack.User('jane')

New API::

    project = ftrack_api.query('Project where name is "dev_tutorial"').one()
    task = ftrack_api.get('Task', '8923b7b3-4bf0-11e5-8811-3c0754289fd3')
    user = ftrack_api.query('User where username is "jane"').one()

While the new API can be a bit more verbose for simple queries, it is much more
powerful and allows you filter on any field and preload related data::

    tasks = session.query(
        'select name, parent.name from Task '
        'where project.full_name is "My Project" '
        'and status.type.name is "DONE" '
        'and not timelogs any ()'
    ).all()

The above fetches all tasks for “My Project” that are done but have no timelogs.
It also pre-fetches related information about the tasks parent – all in one
efficient query.


.. seealso:: :ref:`querying`


Caching
=======

In this new API we chose to tackle some of the common issues that developers
face using an API in larger productions. Our first significant contribution is a
built-in caching system to optimise retrieval of frequently used data within a
session. The cache is present by default so everyone benefits from the default
setup, but if you want to take it further rest assured that we have you covered.
For example, configuring a per-site, selective persistent cache is just a few
lines of code away.

.. seealso:: :ref:`caching`


Creating objects
================

In the old API, you create objects using specialized methods, such as 
:meth:`ftrack.createProject`, :meth:`Project.createSequence` and
:meth:`Task.createShot`.

In the new API, you can create any object using :meth:`session.create`. In 
addition, there are a few helper methods to reduce the amount of boilerplate
necessary to create certain objects. Don't forget to call :meth:`session.commit`
once you have issued your create statements to commit your changes.

As an example, let's look at creating a few entities on a project.

Old API::

    project = ftrack.getProject('migration_test')

    # Get default task type and status from project schema
    taskType = project.getTaskTypes()[0]
    taskStatus = project.getTaskStatuses(taskType)[0]

    sequence = ftrack.createSequence('001')

    # Create five shots with one task each
    for shot_number in xrange(10, 60, 10):
        shot = sequence.createShot(
            '{0:03d}'.format(shot_number)
        )
        shot.createTask(
            'Task name',
            taskType,
            taskStatus
        )


New API::

    project = session.query('Project where name is "migration_test"').one()

    # Get default task type and status from project schema
    project_schema = project['project_schema']
    default_task_type = project_schema.get_types('Task').first()
    default_task_status = project_schema.get_statuses(
        'Task', default_task_type['id']
    ).first()

    # Create sequence
    sequence = session.create('Sequence', {
        'name': '001'
        'parent': project
    })

    # Create five shots with one task each
    for shot_number in xrange(10, 60, 10):
        shot = session.create('Shot', {
            'name': '{0:03d}'.format(shot_number)
            'parent': sequence,
            'status': default_shot_status
        })
        session.create('Task', {
            'name': 'Task name'
            'parent': shot,
            'status': default_task_status,
            'type': default_task_type
        })

    # Commit all changes to the server.
    session.commit()

If you test the example above, one thing you might notice is that the new API
is much more efficient. Thanks to the transaction-based architecture in the new
API only a single call to the server is required to create all the objects.

.. seealso:: :ref:`working_with_entities/creating`

Updating objects
================

Updating objects in the new API works in a similar way to the old API. Instead
of using the :meth:`set` method on objects, you simply set the key of the 
entity to the new value, and call :meth:`session.commit` to persist the 
changes to the database.

The following example adjusts the duration and comment of a timelog for a
user using the old and new API, respectively.

Old API::

    import datetime
    import ftrack

    user = ftrack.User('john')

    today = datetime.date.today()
    timelog = user.getTimelogs(start=today, end=today)[0]
    timelog.set('comment', 'Migrating to the new ftrack API')
    timelog.set('duration', 8*60*60)

New API::

    import arrow
    import ftrack_api
    session = ftrack_api.Session()

    user = session.query('User where username is "john"').one()
    timelog = session.query(
        'Timelog where user is {0} and start >= "{1}"'.format(
            user, arrow.now().floor('day')
        )
    )
    timelog['comment'] = 'Migrating to the new ftrack API'
    timelog['duration'] = 8 * 60 * 60
    session.commit()

.. seealso:: :ref:`working_with_entities/updating`


Using both APIs side-by-side
============================

With so many powerful new features and the necessary support for more flexible
workflows, we chose early on to not limit the new API design by necessitating
backwards compatibility. However, we also didn't want to force teams using the
existing API to make a costly all-or-nothing switchover. As such, we have made
the new API capable of coexisting in the same process as the old API::

    import ftrack
    import ftrack_api

In addition, the old API will continue to be supported for some time, but do
note that it will not support the new Workflows and will not have new features
back ported to it.

In the following example, we obtain a task reference using the old API and
then use the new API to assign a user to it::

    import os

    import ftrack
    import ftrack_api

    # Create session using envvars used by old API.
    session = ftrack_api.Session(
        server_url=os.environ['FTRACK_SERVER'],
        api_key=os.environ['FTRACK_APIKEY'],
        api_user=os.environ['LOGNAME']
    )

    # Obtain task id using old API
    task = ftrack.getTask(['migration_test', '001', '010', 'Task name'])
    task_id = task.getId()

    user = session.query(
        'User where username is "{0}"'.format(session.api_user)
    )
    session.create('Appointment', {
        'resource': user,
        'context_id': task_id,
        'type': 'assignment'
    })


Workarounds for missing convenience methods
===========================================

Query object by path
--------------------

In the old API, there existed a convenience methods to get an object by 
referencing the path (i.e object and parent names).

Old API::

    shot = ftrack.getShot(['dev_tutorial', '001', '010'])

New API::

    project = session.query(
        'Project where name is "{0}"'.format('dev_tutorial')
    )
    sequence = session.query(
        'Sequence where parent is "{0}" and name is "{1}"'.format(project, '001')
    )
    shot = session.query(
        'Shot where parent is "{0}" and name is "{1}"'.format(sequence, '010')
    )


Retrieving an object's parents
------------------------------

To retrieve a list of an object's parents, you could call the method
:meth:`getParents` in the old API. Currently, it is not possible to fetch this
in a single call using the new API, so you will have to traverse the ancestors 
one-by-one and fetch each object's parent.

Old API::

    parents = task.getParents()

New API::

    item = task
    parents = []

    while True:
        item = item['parent']
        if not item:
            break
        parents.append(item)


Limitations in the current version of the API
=============================================

The new API is still quite young and in active development and there are a few
things which is currently not present.

Missing schemas
---------------

The following entities are as of the time of writing not currently available
in the new API. Let us know if you depend on any of them.

    * Attachment
    * Booking
    * Calendar and Calendar Type
    * Dependency
    * Disk
    * List
    * Manager and Manager Type
    * Phase
    * Role
    * Socal Event and Social Feed
    * Task template
    * Temp data
    * Version link

Custom attributes
-----------------
Custom attributes in the new API are not yet available, but will be added
shortly.

Attachments and Thumbnails
--------------------------
Uploading attachments and thumbnails using the new API is not yet possible. The
functionality is planned for the near future.

Publish components for review
-----------------------------
It is currently possible to create web reviewable versions using the new API. 
The functionality is planned for the near future.

Action base class
-----------------
There is currently no helper class for creating actions using the new API. We
will add one in the near future.

In the meantime, it is still possible to create actions without the base class
by listening and responding to the 
:ref:`ftrack:developing/events/list/ftrack.action.discover` and 
:ref:`ftrack:developing/events/list/ftrack.action.launch` events.

Legacy location
---------------

The ftrack legacy disk locations utilizing the 
:class:`InternalResourceIdentifierTransformer` has been deprecated.
