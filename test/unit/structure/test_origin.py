# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import inspect

import pytest
import mock

import ftrack_api.structure.origin


@pytest.fixture(scope='session')
def structure():
    '''Return structure.'''
    return ftrack_api.structure.origin.OriginStructure()


@pytest.mark.parametrize('entity, context, expected', [
    pytest.param(mock.Mock(), {'source_resource_identifier': 'identifier'}, 'identifier', id='valid-context'),
    pytest.param(mock.Mock(), {}, ValueError, id='invalid-context'),
    pytest.param(mock.Mock(), None, ValueError, id='unspecified-context')
])
def test_get_resource_identifier(structure, entity, context, expected):
    '''Get resource identifier.'''
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            structure.get_resource_identifier(entity, context)
    else:
        assert structure.get_resource_identifier(entity, context) == expected
