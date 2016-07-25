..
    :copyright: Copyright (c) 2016 ftrack

.. currentmodule:: ftrack_api.session

.. _example/web_review:

*************************
Publishing for web review
*************************

Follow the :ref:` encode media <example/encode_media>` example if you want to
upload and encode media using ftrack.

If you already have a file encoded in the correct format and want to bypass
the built-in encoding in ftrack, you can create the component manually
and add it to the `ftrack.server` location::

    version = # Retrieve or create version.
    server_location = session.query('Location where name is "ftrack.server"').one()
    filepath = '/path/to/local/file.mp4'

    component = version.create_component(
        path=filepath,
        data={
            'name': 'ftrackreview-mp4'
        },
        location=server_location
    )

    # Meta data needs to contain *frameIn*, *frameOut* and *frameRate*.
    component['metadata']['ftr_meta'] = json.dumps({
        'frameIn': 0,
        'frameOut': 150,
        'frameRate': 25
    })

    component.session.commit()

To publish an image for review the steps are similar::

    version = # Retrieve or create a version you want to use
    server_location = session.query('Location where name is "ftrack.server"').one()
    filepath = '/path/to/image.jpg'

    component = version.create_component(
        path=filepath,
        data={
            'name': 'ftrackreview-image'
        },
        location=server_location
    )

    # Meta data needs to contain *format*.
    component['metadata']['ftr_meta'] = json.dumps({
        'format': 'image'
    })

    component.session.commit()

.. note::

    Make sure to use the pre-defined component names `ftrackreview-mp4`,
    `ftrackreview-webm` and `ftrackreview-image`. They are used to identify
    playable components in ftrack. You also need to set the `ftr_meta` on the
    components.
