# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest


def test_create_job_using_faulty_type(session, user):
    '''Fail to create job with faulty type.'''

    with pytest.raises(ValueError):
        session.create('Job', {
            'user': user,
            'type': 'not-allowed-type'
        })
