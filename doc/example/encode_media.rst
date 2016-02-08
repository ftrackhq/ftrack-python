..
    :copyright: Copyright (c) 2016 ftrack

.. currentmodule:: ftrack_api.session

.. _example/encode_media:

**************
Encoding media
**************

Media such as images and video can be encoded by the ftrack server to allow
playing it in the ftrack web interface. Media can be encoded using
:meth:`ftrack_api.session.Session.encode_media` which accepts a path to a file
or an existing component in the ftrack.server location.

Here is an example of how to encode a video and add to an existing asset
version::

    job = session.encode_media('/PATH/TO/MEDIA')
    job_data = json.loads(job['data'])

    for output in job_data['output']:
        component = session.get('FileComponent', output['component_id'])
        
        # Add component to version.
        component['version_id'] = version['id']

        # Add thumbnail to the version.
        if output['format'] == 'image/jpeg':
            version['thumbnail_id'] = output['component_id']

It is also possible to get the URL to an encoded component once the job has
finished::

    job = session.encode_media('/PATH/TO/MEDIA')

    # Wait for job to finish.

    location = session.query('Location where name is ftrack.server').one()
    for component in job['job_components']:
        print location.get_url(component)

Media can also be an existing component in another location. Before encoding it,
the component needs to be added to the ftrack.server location::

    location = session.query('Location where name is ftrack.server').one()
    location.add_component(component)
    session.commit()

    job = session.encode_media(component)
