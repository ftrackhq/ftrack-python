..
    :copyright: Copyright (c) 2015 ftrack

.. _example/link_attribute:

*********************
Using link attributes
*********************

The `link` attribute can be used to retreive the ids and names of the parents of
an object. It is particularly useful in cases where the path of an object must
be presented in a UI, but can also be used to speedup certain query patterns.

You can use the `link` attribute on any entity inheriting from a
`TypedContext`::

    task = session.query(
        'select link from Task where name is "myTask"'
    ).first()
    print task['link']

The `link` attribute is an ordered list of dictionaries containting data
of the parents. Each dictionary contains the following entries:

    * id - the id of the object and can be used to do a :meth:`Session.get`.
    * name - the name of the object.
    * type - the schema id of the object.

A more advanced use-case is to get the parent names and ids of all timelogs for
a user::

    for timelog in session.query(
        'select context.link, start, duration from Timelog '
        'where user.username is "john.doe"'
    ):
        print timelog['context']['link'], timelog['start'], timelog['duration']

The attribute is also availabe from the `AssetVersion` asset relation::

    for asset_version in session.query(
        'select asset.parent.link from AssetVersion '
        'where user.username is "john.doe"'
    ):
        print asset_version['asset']['parent']['link']
