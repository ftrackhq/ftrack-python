..
    :copyright: Copyright (c) 2015 ftrack

.. _release/migration:

***************
Migration notes
***************

Migrate to next
===============

.. _release/migration/next/new_api_name:

New API name
------------

In this release the API has changed name from `ftrack` to `ftrack_api` to
solve issues when using the old API in the same environment.

Any scripts using this API needs to be updated to import `ftrack_api` instead
of ftrack.
