..
    :copyright: Copyright (c) 2015 ftrack

.. _release/migration:

***************
Migration notes
***************

.. note::

    Migrating from the old ftrack API? Read the dedicated :ref:`guide
    <release/migrating_from_old_api>`.

Migrate to 1.0.3
================

.. _release/migration/1.0.3/mutating_dictionary:

Mutating custom attribute dictionary
------------------------------------

Custom attributes can no longer be set by mutating entire dictionary::

    # This will result in an error.
    task['custom_attributes'] = dict(foo='baz', bar=2)
    session.commit()

Instead the individual values should be changed::

    # This works better.
    task['custom_attributes']['foo'] = 'baz'
    task['custom_attributes']['bar'] = 2
    session.commit()

Migrate to 1.0.0
================

.. _release/migration/1.0.0/chunked_transfer:

Chunked accessor transfers
--------------------------

Data transfers between accessors is now buffered using smaller chunks instead of
all data at the same time. Included accessor file representations such as
:class:`ftrack_api.data.File` and :class:`ftrack_api.accessor.server.ServerFile`
are built to handle that. If you have written your own accessor and file
representation you may have to update it to support multiple reads using the
limit parameter and multiple writes.

Migrate to 0.2.0
================

.. _release/migration/0.2.0/new_api_name:

New API name
------------

In this release the API has been renamed from `ftrack` to `ftrack_api`. This is
to allow both the old and new API to co-exist in the same environment without
confusion.

As such, any scripts using this new API need to be updated to import
`ftrack_api` instead of `ftrack`. For example:

**Previously**::

    import ftrack
    import ftrack.formatter
    ...

**Now**::

    import ftrack_api
    import ftrack_api.formatter
    ...
