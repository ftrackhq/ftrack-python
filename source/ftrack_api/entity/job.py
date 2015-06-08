# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.entity.base


class Job(ftrack_api.entity.base.Entity):
    '''Represent job.'''

    def __init__(self, session, data=None, reconstructing=False):
        '''Initialise entity.

        *session* is an instance of :class:`ftrack_api.session.Session` that
        this entity instance is bound to.

        *data* is a mapping of key, value pairs to apply as initial attribute
        values.

        To set a job `description` visible in the web interface, *data* can
        contain a key called `data` which should be a JSON serialised
        dictionary containing description::

            data = {
                'status': 'running',
                'data': json.dumps(dict(description='My job description.')),
                ...
            }

        *reconstructing* indicates whether this entity is being reconstructed,
        such as from a query, and therefore should not have any special creation
        logic applied, such as initialising defaults for missing data.

        '''

        # If creating a new Job force the `type` to be `api_job`. Other values
        # than this will cause issues in the web interface.
        if not reconstructing:
            data['type'] = 'api_job'

        super(Job, self).__init__(
            session, data=data, reconstructing=reconstructing
        )
