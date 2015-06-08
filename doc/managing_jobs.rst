..
    :copyright: Copyright (c) 2014 ftrack

.. _managing_jobs:

*************
Managing jobs
*************

Jobs can be used to display feedback to users in the ftrack web interface
when performing long running tasks in the API.

When a job is created it will appear in the :guilabel:`jobs` menu in the
top bar.

To create a job use the :meth:`Session.create`.

.. code-block:: python
    
    user = # Get a user from ftrack.

    job = session.create('Job', {
        'user': user,
        'status': 'running'
    })

The created job will appear as running in the :guilabel:`jobs` menu for the
specified user. To set a description on the job, add a dictionary containing
description as the `data` key:

.. note::

    In the current version of the API the dictionary needs to be JSON
    serialised.

.. code-block:: python
    
    import json

    job = session.create('Job', {
        'user': user,
        'status': 'running',
        'data': json.dumps({
            'description': 'My custom job description.'
        })
    })

When the long running task has finished simply set the job as completed and
continue with the next task.

.. code-block:: python

    job['status'] = 'done'
    job.session.commit()
