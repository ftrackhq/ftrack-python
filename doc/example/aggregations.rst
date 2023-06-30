..
    :copyright: Copyright (c) 2015 ftrack

.. _example/aggregations:

******************
Using aggregations
******************

The following aggregation methods are available for summarizing data in a grouped results
set:

:sum():

    Adds together all the values in a particular column.

:avg():

    Calculates the average of a group of selected values.

:min():

    Determines the minimum numeric values in each group.

:max():

    Determines the maximum numeric values in each group.

:count():

    Returns the total number of rows in each group.

To use these methods you must configure API's “strict api” mode when
generating the session object. Do this by setting :func:`strict_api=True` when
configuring the session: ::

    session = ftrack_api.Session(
        server_url='https://YOUR-SITE-URL',
        api_key='YOUR-API-KEY',
        api_user='YOUR-API-USER',
        strict_api=True
    )

Aggregation functions also require “group by” clause that specifies
the attributes that will be used to distinguish how the aggregate results are
grouped, such as::

    select count(id) from Task group by status_id

.. note::

  Queries that include aggregations have to use the operations syntax (see:
  https://help.ftrack.com/en/articles/1040498-operations) and be passed to the
  :func:`session.call()` method versus the :func:`session.query()` method.


Summarize task totals
=====================

Select the total number of Tasks grouped by Status and Project::

    status_lookup = {}
    for i in session.query('select id, name from Status'):
        status_lookup[i['id']] = i['name']

    project_lookup = {}
    for i in session.query('select id, name from Project'):
        project_lookup[i['id']] = i['name']

    res = session.call(
        [
            {
                'action': 'query',
                'expression': 'select count(id) from Task group by project_id, status_id'
            }
        ]
    )
    status_count = res[0]['data']

    for count in status_count:
        print('{} Tasks are "{}" in project {}'.format(
            count['count_id'],
            status_lookup[count['status_id']],
            project_lookup[count['project_id']]
          )
        )

Sample output::

    2 Tasks are "Not started" in project sync
    4 Tasks are "In progress" in project sync
    16 Tasks are "Approved" in project sync
    2 Tasks are "Not started" in project napo
    3 Tasks are "In progress" in project napo
    13 Tasks are "Approved" in project napo
    4 Tasks are "Client approved" in project napo

