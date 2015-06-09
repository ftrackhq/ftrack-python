..
    :copyright: Copyright (c) 2015 ftrack

.. currentmodule:: ftrack_api.session

.. _using_notes:

***********
Using notes
***********

Notes can be written on almost all levels in ftrack. To retrieve notes on an
entity you can either query them or use the relation called `notes`::

    # Retrieve notes using notes property.
    notes_on_task = task_entity['notes']

    # Or query them.
    notes_on_task = session.query('Note where parent_id is "{}"'.format(
        task_entity['id']
    ))

.. note::

    It's currently not possible to use the `parent` property when querying
    notes or to use the `parent` property on notes::

        # This won't work in the current version of the API.
        session.query('Note where parent.id is "{}"'.format(
            task_entity['id']
        ))

        # Neither will this.
        parent_of_note = note['parent']

To create new notes you can either use the helper method called `create_note`
on any entity that can have notes or use the :meth:`Session.create` to create
them manually::
    
    # Create note using the helper method.
    note = task.create_note('My new note', user)

    # Manually create a note
    note = session.create('Note', {
        'text': 'My new note',
        'user': user,
        'parent_id': task['id'],
        'parent_id': entity.entity_type
    })

Replying on an existing note can also be done with a helper method or by
using :meth:`Session.create`::
    
    # Create using helper method.
    first_note_on_task = task_entity['notes'][0]
    first_note_on_task.create_reply('My new reply on note', user)

    # Create manually
    reply = session.create('Note', {
        'text': 'My new note',
        'user': user,
        'note_parent_id': first_note_on_task['id'],
        'parent_id': first_note_on_task['parent_id'],
        'parent_type': first_note_on_task['parent_type']
    })
