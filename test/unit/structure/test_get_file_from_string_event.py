# :coding: utf-8
# :copyright: Copyright (c) 2014-2019 ftrack

import os
import inspect
import pytest

import ftrack_api
import ftrack_api.structure.standard


@pytest.fixture(scope='session')
def structure():
    '''Return structure.'''
    return ftrack_api.structure.id.IdStructure(prefix='another_path')


def file_compound_extension_component_event(container=None):

    '''
    Return file component with compound extension through
    **ftrack.api.session.get-file-type-from-string** event.
    '''

    plugin_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..','..','fixture', 'plugin')
    )
    session = ftrack_api.Session(plugin_paths=[plugin_path])


    entity = session.create_component(
        'mytest.foo.bar'
    )

    return entity



@pytest.mark.parametrize('entity, context, expected', [
    (
        file_compound_extension_component_event(), {},
        'foo.bar'
    )

], ids=[
    'file-compound-extension-component',
])
def test_get_resource_identifier(structure, entity, context, expected):
    '''Get resource identifier.'''
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            structure.get_resource_identifier(entity, context)
    else:
        assert structure.get_resource_identifier(entity, context).endswith(expected)
