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
    return ftrack_api.structure.standard.StandardStructure(prefix='path')


def container_component():
    '''Return container component.'''
    session = ftrack_api.Session()

    entity = session.create('ContainerComponent', {
        'name': 'container_component'
    })

    return entity


def sequence_component():
    '''Return sequence component.'''
    session = ftrack_api.Session()

    entity = session.create_component(
        '/tmp/foo/%04d.jpg [1-10]', location=None, data={'name': 'baz'}
    )

    return entity


def file_component(name='foo', container=None):
    '''Return file component with *name* and *container*.'''

    plugin_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..','..','fixture', 'plugin')
    )

    if container:
        session = container.session
    else:
        session = ftrack_api.Session(plugin_paths=[plugin_path])

    entity = session.create('FileComponent', {
        'name': name,
        'file_type': '.png',
        'container': container
    })

    return entity


def file_compound_extension_component_event(container=None):

    '''
    Return file component with compound extension through
    **ftrack.api.session.get-file-type-from-string** event.
    '''

    plugin_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..','..','fixture', 'plugin')
    )
    session = ftrack_api.Session(plugin_paths=[plugin_path])

    entity = session.create('FileComponent', {
        'name': '0010',
        'file_type': '.foo.bar',
        'container': container
    })

    return entity


def sequence_compound_extension_component_event(padding=0):

    '''
    Return sequence component with *padding* through
    **ftrack.api.session.get-file-type-from-string** event.
    '''

    plugin_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'fixture', 'plugin')
    )
    session = ftrack_api.Session(plugin_paths=[plugin_path])

    entity = session.create('SequenceComponent', {
        'name': 'sequence_component',
        'file_type': '.foo.bar',
        'padding': padding

    })

    return entity


@pytest.mark.parametrize('entity, context, expected', [
    (
        file_compound_extension_component_event(), {},
        'path/f/6/c/d/40cb-d1c0-469f-a2d5-10369be8a725.foo.bar'
    ),
    (
        file_compound_extension_component_event(container_component()), {},
        'path/0/3/a/b/9967-f86c-4b55-8252-cd187d0c244a/'
        'f6cd40cb-d1c0-469f-a2d5-10369be8a725.foo.bar'
    ),
    (
        file_compound_extension_component_event(
            sequence_compound_extension_component_event()
        ), {},
        'path/f/f/1/7/edad-2129-483b-8b59-d1a654c8497c/file.0010.foo.bar'
    ),
    (
        sequence_compound_extension_component_event(padding=0), {},
        'path/f/f/1/7/edad-2129-483b-8b59-d1a654c8497c/file.%d.foo.bar'
    ),
    (
        sequence_compound_extension_component_event(padding=4), {},
        'path/f/f/1/7/edad-2129-483b-8b59-d1a654c8497c/file.%04d.foo.bar'
    ),

], ids=[
    'file-compound-extension-component',
    'file-component-compound-extension-in-container',
    'file-component-compound-extension-in-sequence',
    'unpadded-sequence-compound-extension-component',
    'padded-sequence-compound-extension-component',
])
def test_get_resource_identifier(structure, entity, context, expected):
    '''Get resource identifier.'''
    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            structure.get_resource_identifier(entity, context)
    else:
        assert structure.get_resource_identifier(entity, context) == expected
