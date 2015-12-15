# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import pytest

import ftrack_api
import ftrack_api.structure.standard


def file_component(name='foo', container=None):
    '''Return file component with *name* and *container*.'''
    if container:
        session = container.session
    else:
        session = ftrack_api.Session()

    entity = session.create('FileComponent', {
        'name': name,
        'file_type': '.png',
        'container': container
    })

    return entity


def sequence_component(padding=0):
    '''Return sequence component with *padding*.'''
    session = ftrack_api.Session()

    entity = session.create_component(
        '/tmp/foo/%04d.jpg [1-10]', location=None, data={'name': 'baz'}
    )

    return entity


def container_component():
    '''Return container component.'''
    session = ftrack_api.Session()

    entity = session.create('ContainerComponent', {
        'name': 'container_component'
    })

    return entity


@pytest.mark.parametrize(
    'component, hierarchy, expected, structure, asset_name',
    [
        (
            file_component(),
            [],
            '{project_name}/my_new_asset/v001/foo.png',
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            file_component(),
            [],
            '{project_name}/foobar/my_new_asset/v001/foo.png',
            ftrack_api.structure.standard.StandardStructure(
                project_versions_prefix='foobar'
            ),
            'my_new_asset'
        ),
        (
            file_component(),
            ['baz', 'bar'],
            '{project_name}/baz/bar/my_new_asset/v001/foo.png',
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            sequence_component(),
            ['baz', 'bar'],
            '{project_name}/baz/bar/my_new_asset/v001/baz.%04d.jpg',
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            sequence_component()['members'][3],
            ['baz', 'bar'],
            '{project_name}/baz/bar/my_new_asset/v001/baz.0004.jpg',
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            container_component(),
            ['baz', 'bar'],
            '{project_name}/baz/bar/my_new_asset/v001/container_component',
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            file_component(container=container_component()),
            ['baz', 'bar'],
            (
                '{project_name}/baz/bar/my_new_asset/v001/container_component/'
                'foo.png'
            ),
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            file_component(),
            [u'björn'],
            '{project_name}/bjorn/my_new_asset/v001/foo.png',
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            file_component(),
            [u'björn!'],
            '{project_name}/bjorn_/my_new_asset/v001/foo.png',
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            file_component(name=u'fää'),
            [],
            '{project_name}/my_new_asset/v001/faa.png',
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            file_component(name=u'fo/o'),
            [],
            '{project_name}/my_new_asset/v001/fo_o.png',
            ftrack_api.structure.standard.StandardStructure(),
            'my_new_asset'
        ),
        (
            file_component(),
            [],
            '{project_name}/aao/v001/foo.png',
            ftrack_api.structure.standard.StandardStructure(),
            u'åäö'
        ),
        (
            file_component(),
            [],
            '{project_name}/my_ne____w_asset/v001/foo.png',
            ftrack_api.structure.standard.StandardStructure(),
            u'my_ne!!!!w_asset'
        ),
        (
            file_component(),
            [u'björn'],
            u'{project_name}/björn/my_new_asset/v001/foo.png',
            ftrack_api.structure.standard.StandardStructure(
                replace_illegal_characters=None
            ),
            'my_new_asset'
        ),
        (
            file_component(),
            [u'bj!rn'],
            '{project_name}/bj^rn/my_new_asset/v001/foo.png',
            ftrack_api.structure.standard.StandardStructure(
                replace_illegal_characters='^'
            ),
            'my_new_asset'
        )
    ], ids=[
        'file_component_on_project',
        'file_component_on_project_with_prefix',
        'file_component_with_hierarchy',
        'sequence_component',
        'sequence_component_member',
        'container_component',
        'container_component_member',
        'slugify_non_ascii_hierarchy',
        'slugify_illegal_hierarchy',
        'slugify_non_ascii_component_name',
        'slugify_illegal_component_name',
        'slugify_non_ascii_asset_name',
        'slugify_illegal_asset_name',
        'slutify_none',
        'slugify_other_character'
    ]
)
def test_get_resource_identifier(
    component, hierarchy, expected, structure, asset_name, new_project
):
    '''Get resource identifier.'''
    session = component.session

    # Create structure, asset and version.
    context_id = new_project['id']
    for name in hierarchy:
        context_id = session.create('Folder', {
            'name': name,
            'project_id': new_project['id'],
            'parent_id': context_id
        })['id']

    asset = session.create(
        'Asset', {'name': asset_name, 'context_id': context_id}
    )
    version = session.create('AssetVersion', {'asset': asset})

    # Update component with version.
    if component['container']:
        component['container']['version'] = version
    else:
        component['version'] = version

    session.commit()

    assert structure.get_resource_identifier(component) == expected.format(
        project_name=new_project['name']
    )


def test_unsupported_entity(user):
    '''Fail to get resource identifer for unsupported entity.'''
    structure = ftrack_api.structure.standard.StandardStructure()
    with pytest.raises(NotImplementedError):
            structure.get_resource_identifier(user)
