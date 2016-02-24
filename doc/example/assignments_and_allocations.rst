..
    :copyright: Copyright (c) 2015 ftrack

.. _example/assignments_and_allocations:

****************************************
Working with assignments and allocations
****************************************

.. currentmodule:: ftrack_api.session

The API exposes `assignments` and `allocations` relationships on objects in
the project hierarchy. You can use these to retrieve the allocated or assigned
resources, which can be either groups or users. Allocations can be used to
allocate users or groups to a project team, while assignments are more explicit
and is typically used to assign users to tasks.

The following example prints all groups and users assigned to a `Folder`
object::

    # Retrieve a `Folder` object
    folder = session.query('Folder').first()

    # Print a header
    print folder['name']
    print 80*'='

    # List all assigned groups and users
    for assignment in folder['assignments']:

        # Resource may be either a group or a user
        resource = assignment['resource']

        if resource.entity_type == 'Group':
            print resource['name']

            # Print group members
            for membership in resource['memberships']:
                user = membership['user']
                print u'   |- {0} {1}'.format(
                    user['first_name'], user['last_name']
                )
        else:
            print u'{0} {1}'.format(
                resource['first_name'], resource['last_name']
            )
