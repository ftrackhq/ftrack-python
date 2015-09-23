..
    :copyright: Copyright (c) 2015 ftrack

.. _release/migration:

***************
Migration notes
***************

.. note::

    Migrating from the old ftrack API? Read the dedicated :ref:`guide
    <release/migrating_from_old_api>`.

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
