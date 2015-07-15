# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest

import ftrack_api.entity.factory
import ftrack_api.inspection


@pytest.mark.parametrize('default', [
    ftrack_api.entity.factory.default_task_status,
    ftrack_api.entity.factory.default_task_type,
    ftrack_api.entity.factory.default_task_priority
], ids=[
    'default_task_status',
    'default_task_type',
    'default_task_priority'
])
def test_optimised_defaults(default, mocker, task, user):
    '''Optimised defaults should only be called once per session.'''
    # Check result is same across session regardless of entity.
    session = ftrack_api.Session()
    entity = session.get(*ftrack_api.inspection.identity(task))
    first_result = default(entity)

    other_entity = session.get(*ftrack_api.inspection.identity(user))
    mocker.patch.object(entity.session, '_call')
    second_result = default(other_entity)
    assert first_result is second_result
    assert not entity.session._call.called

    # Check result is not the same for a different session.
    other_session = ftrack_api.Session()
    entity_from_other_session = other_session.get(
        *ftrack_api.inspection.identity(task)
    )

    mocker.patch.object(other_session, '_call', wraps=other_session._call)
    third_result = default(entity_from_other_session)

    assert third_result is not first_result
    assert other_session._call.called
