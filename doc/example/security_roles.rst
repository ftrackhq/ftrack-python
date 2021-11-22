..
    :copyright: Copyright (c) 2017 ftrack

.. _example/security_roles:

*********************************
Working with user security roles
*********************************

.. currentmodule:: ftrack_api.session

The API exposes ``SecurityRole`` and ``UserSecurityRole`` that can be used to
specify who should have access to certain data on different projects.

List all available security roles like this:

.. code-block:: python

    security_roles = session.query(
        'select name from SecurityRole where type is "PROJECT"'
    )

.. note::

    We only query for project roles since those are the ones we can add to a
    user for certain projects. Other types include API and ASSIGNED. Type API
    can only be added to global API keys, which is currently not supported via
    the api and type ASSIGNED only applies to assigned tasks.

To get all security roles from a user we can either use relations like this:

.. code-block:: python

    for user_security_role in user['user_security_roles']:
        if user_security_role['is_all_projects']:
            result_string = 'all projects'
        else:
            result_string = ', '.join(
                [project['full_name'] for project in user_security_role['projects']]
            )

        print('User has security role "{0}" which is valid on {1}.'.format(
            user_security_role['security_role']['name'],
            result_string
        ))

or query them directly like this:

.. code-block:: python

    user_security_roles = session.query(
        'UserSecurityRole where user.username is "{0}"'.format(session.api_user)
    ).all()

User security roles can also be added to a user:

.. code-block:: python

    project_manager_role = session.query(
        'SecurityRole where name is "Project Manager"'
    ).one()

    session.call(
        [
            {
                "action": "add_user_security_role",
                "user_id": user["id"],
                "role_id": project_manager_role["id"]
            }
        ]
    )

Or revoked:

.. code-block:: python

    session.call(
        [
            {
                "action": "revoke_user_security_role",
                "user_id": user["id"],
                "role_id": project_manager_role["id"]
            }
        ]
    )

Removing a specific role and adding another can be done in one request
by using the ``update_user_security_role`` action:

.. code-block:: python

    user_role = session.query('SecurityRole where name is "User"').one()
    session.call(
        [
            {
                "action": "update_user_security_role",
                "user_id": user["id"],
                "role_id": project_manager_role["id"],
                "new_role_id": user_role["id"],
            }
        ]
    )


You may also grant access to a specific project for a user:

.. code-block:: python

    projects = session.query(
        'Project where full_name is "project1" or full_name is "project2"'
    )

    session.call(
        [
            {
                "action": "grant_user_security_role_project",
                "user_id": user["id"],
                "role_id": project_manager_role["id"],
                "project_id": projects[0]["id"]
            }
        ]
    )

Or revoke the access:

.. code-block:: python

    session.call(
        [
            {
                "action": "revoke_user_security_role_project",
                "user_id": user["id"],
                "role_id": project_manager_role["id"],
                "project_id": projects[0]["id"]
            }
        ]
    )

