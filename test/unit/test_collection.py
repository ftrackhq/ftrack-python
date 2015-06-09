# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import mock

import ftrack_api.collection
import ftrack_api.symbol


def test_initialisation_does_not_modify_entity_state():
    '''Initialising collection does not modify entity state.'''
    entity = mock.Mock()
    entity.state = ftrack_api.symbol.NOT_SET

    ftrack_api.collection.Collection(
        entity, None, data=[1, 2]
    )

    assert entity.state is ftrack_api.symbol.NOT_SET
