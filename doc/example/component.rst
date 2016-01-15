..
    :copyright: Copyright (c) 2014 ftrack

.. _example/component:

***********************
Working with components
***********************

.. currentmodule:: ftrack_api.session

Components can be created manually or using the provide helper methods on a
:meth:`session <ftrack_api.session.Session.create_component>` or existing
:meth:`asset version
<ftrack_api.entity.asset_version.AssetVersion.create_component>`::

    component = version.create_component('/path/to/file_or_sequence.jpg')
    session.commit()

When a component is created using the helpers it is automatically added to a
location.

.. seealso:: :ref:`Locations tutorial <locations/tutorial>`

.. _example/component/thumbnail

Working with thumbnails
=======================

Components can be used as thumbnails on various entities, including
`Project`, `Task`, `AssetVersion` and `User`. You can use the provided helper
method, :meth:`create_thumbnail <ftrack_api.session.Session.create_thumbnail>`
to reduce the amount of boilerplate needed::

    task = session.get('Task', my_task_id)
    thumbnail_component = session.create_thumbnail(
        '/path/to/image.jpg', entity=task
    )

It is also possible to set an entity thumbnail by setting its `thumbnail`
relation or `thumbnail_id` attribute to a component you would
like to use as a thumbnail. For a component to be usable as a thumbnail,
it should

    1. Be of system type file.
    2. Exist in the *ftrack.server* :term:`location`.
    3. Be of an appropriate resolution and valid file type.

The following example creates a new component in the server location, and
uses that as a thumbnail for a task::

    task = session.get('Task', my_task_id)
    server_location = session.query(
        'Location where name is "ftrack.server"'
    ).one()

    thumbnail_component = session.create_component(
        '/path/to/image.jpg',
        dict(name='thumbnail'),
        location=server_location
    )
    task['thumbnail'] = thumbnail_component
    session.commit()

The next example reuses a versions thumbnail for the asset parent thumbnail::

    asset_version = session.get('AssetVersion', my_asset_version_id)
    asset_parent = asset_version['asset']['parent']
    asset_parent['thumbnail_id'] = asset_version['thumbnail_id']
    session.commit()
