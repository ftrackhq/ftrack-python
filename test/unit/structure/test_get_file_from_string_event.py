# :coding: utf-8
# :copyright: Copyright (c) 2014-2019 ftrack

import os
import inspect
import pytest

import ftrack_api
import ftrack_api.structure.standard
import ftrack_api.structure.id


@pytest.fixture(scope='session')
def structure():
    '''Return structure.'''
    return ftrack_api.structure.id.IdStructure(prefix='another_path')


def file_compound_extension_no_component_event(component_file=None):

    '''
    Return file component with compound extension through
    **ftrack.api.session.get-file-type-from-string** event.
    '''

    session = ftrack_api.Session()

    entity = session.create_component(
        component_file
    )

    return entity


def file_compound_extension_component_event(component_file=None):

    '''
    Return file component with compound extension through
    **ftrack.api.session.get-file-type-from-string** event.
    '''

    plugin_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..','..','fixture', 'plugin')
    )
    session = ftrack_api.Session(plugin_paths=[plugin_path])

    entity = session.create_component(
        component_file
    )

    return entity


@pytest.mark.parametrize('entity, context, expected', [
    pytest.param(
        file_compound_extension_component_event('mytest.foo.bar'), {},
        '.foo.bar',
        id='file-compound-extension-component-event'
    ),
    pytest.param(
        file_compound_extension_component_event('mytest.%4d.foo.bar'), {},
        '.foo.bar',
        id='file-sequence-compound-extension-component-event'
    ),
    pytest.param(
        file_compound_extension_component_event('mytest'), {},
        '',
        id='no-file-compound-extension-component-event'
    ),
    pytest.param(
        file_compound_extension_no_component_event('mytest.foo.bar'), {},
        '.bar',
        id='file-compound-extension-no-component-event'
    ),
    pytest.param(
        file_compound_extension_no_component_event('mytest.%4d.foo.bar'), {},
        '.bar',
        id='file-sequence-compound-extension-no-component-event'
    ),
    pytest.param(
        file_compound_extension_no_component_event('mytest'), {},
        '',
        id='no-file-compound-extension-no-component-event'
    ),
    pytest.param(
        file_compound_extension_component_event('%04d.bgeo.sc [1-10]'), {},
        '.bgeo.sc',
        id='file-sequence-compound-extension-component-event-valid-clique'
    ),
    pytest.param(
        file_compound_extension_component_event('argh.%04d.bgeo.sc [1-10]'), {},
        '.bgeo.sc',
        id='file-sequence-compound-extension-component-event-valid-clique-with-prefix'
    ),
    pytest.param(
        file_compound_extension_component_event('foobar.%04d.jpg [1-10]'), {},
        '.jpg',
        id='file-sequence-compound-extension-component-event-valid-clique-single-extension'
    ),
])
def test_get_resource_identifier(structure, entity, context, expected):
    '''Get resource identifier.'''
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            structure.get_resource_identifier(entity, context)
    else:
        assert structure.get_resource_identifier(entity, context).endswith(expected)
