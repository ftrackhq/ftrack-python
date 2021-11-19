..
    :copyright: Copyright (c) 2021 ftrack

.. _example/custom_attribute_links:

*****************************
Using custom attributes links
*****************************

.. currentmodule:: ftrack_api.session

Custom attributes can be queried from entities using the
``custom_attribute_links`` and ``custom_attribute_links_from`` relations.
The "_from" relation represents the reverse direction of a custom attribute link.
Say you have a link between Task and AssetVersion, then custom_attribute_links
represent "Task -> AssetVersion" while custom_attribute_links_from represent
"AssetVersion -> Task". The relations can only be used to query and filter the
result, to read the actual values you need to query CustomAttributeLink objects
directly.

Below are a few examples of how to query and filter using the
custom_attribute_links relation::

    for task in session.query(
        'select name from Task where custom_attribute_links any '
        '(configuration.key is "supervisor" and user.username is "foobar")'
    ):
        print(task['name'])

    for user in session.query(
        'select username from User where custom_attribute_links_from any '
        '(configuration.key is "supervisor" and context.bid > 1)'
    ):
        print(user['username'])

Below is an example of how to read the values of custom attribute links::

    for value in session.query(
        'select user from CustomAttributeLink where '
        'configuration.key = "supervisor" and from_id = "MY_TASK_ID"'
    ):
        print(value['user'])

Relations
=========

The CustomAttributeLink object have relations to the entities that can be used
when filtering a query. In the above examples we are using the "user" and
"context" relations. You can see these relations in the API reference
documentation available on your ftrack workspace if you look for
"CustomAttributeLink" objects that are prefixed such as
"UserCustomAttributeLink" and "ContextCustomAttributeLink".

Creating links
==============

To create a link between two entities you need to create a CustomAttributeLink
entity like this::

    session.create('CustomAttributeLink', {
        'from_id': my_task_id,
        'to_id': my_user_id,
        'configuration_id': my_configuration_id
    })

If you need to create the CustomAttributeLinkConfiguration entity, please
:ref:`read this<example/manage_custom_attribute_configuration/links>`.

Limitations
===========

Projections
-----------

It is currently not possible to use the custom_attribute_links relation as a
projection.
