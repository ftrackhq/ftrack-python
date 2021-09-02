..
    :copyright: Copyright (c) 2016 ftrack

.. currentmodule:: ftrack_api.session

.. _example/web_review:

*************************
Publishing for web review
*************************

Follow the :ref:`example/encode_media` example if you want to
upload and encode media using ftrack.

If you already have a file encoded in the correct format and want to bypass
the built-in encoding in ftrack, you can create the component manually
and add it to the `ftrack.server` location::

    # Retrieve or create version.
    version = session.query('AssetVersion', 'SOME-ID')

    server_location = session.query('Location where name is "ftrack.server"').one()
    filepath = '/path/to/local/file.mp4'

    component = version.create_component(
        path=filepath,
        data={
            'name': 'ftrackreview-mp4'
        },
        location=server_location
    )

    # Meta data needs to contain *frameIn*, *frameOut*, *frameRate*, *height*
    # and *width*.
    component['metadata']['ftr_meta'] = json.dumps({
        'frameIn': 0,
        'frameOut': 150,
        'frameRate': 25,
        'height': 720,
        'width': 1280
    })

    component.session.commit()

.. note::

    It is possible to add multiple components with different resolutions
    (supported in ftrack 4.5+). If you add multiple components, they need to be
    named correctly. The lowest resolution should keep the name ftrackreview-mp4
    but the higher resolutions should be named ftrackreview-mp4-1080,
    ftrackreview-mp4-1440, ftrackreview-mp4-2160.

To publish an image for review the steps are similar::

    # Retrieve or create version.
    version = session.query('AssetVersion', 'SOME-ID')

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
        'format': 'image',
        'height': 3840,
        'width': 3840
    })

    component.session.commit()

.. note::

    It is possible to add multiple components with different resolutions
    (supported in ftrack 4.5+). If you add multiple components, they need to be
    named correctly. The lowest resolution should keep the name
    ftrackreview-image and a higher resolution image should be named
    ftrackreview-image-high.

To make a pdf reviewable (client reviews in ftrack 4.2+ and experimental/new web
player in ftrack 4.5+), add format to the original pdf component. Also generate a
reviewable image from it as in the previous step and use that as the thumbnail of
the AssetVersion::

    component['metadata']['ftr_meta'] = json.dumps({
        'format': 'pdf'
    })

Here is a list of components names and how they should be used:

========================  =====================================
Component name            Use
========================  =====================================
ftrackreview-image        Images reviewable in the browser
ftrackreview-image-high   High resolution image
ftrackreview-mp4          H.264/mp4 video reviewable in browser
ftrackreview-mp4-1080     1080p resolution H.264/mp4 video
ftrackreview-mp4-1440     1440p resolution H.264/mp4 video
ftrackreview-mp4-2160     2160p resolution H.264/mp4 video
========================  =====================================

.. note::

    Make sure to use the pre-defined component names and set the `ftr_meta` on
    the components. PDF components should not use any of the pre-defined
    component names.
