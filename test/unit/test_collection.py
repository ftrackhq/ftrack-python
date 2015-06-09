# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.collection
import ftrack_api.symbol


def test_initialisation_does_not_modify_entity_state(new_user):
    '''Initialising collection does not modify entity state.'''
    ftrack_api.collection.Collection(
        new_user, None, data=[1, 2]
    )

    assert new_user.state is ftrack_api.symbol.NOT_SET
