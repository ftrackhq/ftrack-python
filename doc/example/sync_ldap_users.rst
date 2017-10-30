..
    :copyright: Copyright (c) 2014 ftrack

.. _example/sync_with_ldap:

********************
Sync users with LDAP
********************

.. currentmodule:: ftrack_api.session


If ftrack is configured to connect to LDAP you may trigger a
synchronization through the api using the
:meth:`ftrack_api.session.Session.delayed_job`::


    job = session.delayed_job(
        ftrack_api.symbol.JOB_SYNC_USERS_LDAP
    )


You will get a `ftrack_api.entity.job.Job` instance back which can be used
to check the success of the job::

    if job.get('status') == 'failed':
        # the job failed get the error.

        logging.error(
            job.get('data')
        )