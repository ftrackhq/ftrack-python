# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack.inspection


def test_identity(user):
    '''Retrieve identity of *user*.'''
    identity = ftrack.inspection.identity(user)
    assert identity[0] == 'User'
    assert identity[1] == ['d07ae5d0-66e1-11e1-b5e9-f23c91df25eb']


def test_primary_key(user):
    '''Retrieve primary key of *user*.'''
    primary_key = ftrack.inspection.primary_key(user)
    assert primary_key == {
        'id': 'd07ae5d0-66e1-11e1-b5e9-f23c91df25eb'
    }
