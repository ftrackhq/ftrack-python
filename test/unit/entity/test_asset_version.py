# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from __future__ import unicode_literals


def test_create_component(new_asset_version, temporary_file):
    '''Create component on asset version.'''
    session = new_asset_version.session
    component = new_asset_version.create_component(
        temporary_file, location=None
    )
    assert component['version'] is new_asset_version

    # Have to delete component before can delete asset version.
    session.delete(component)


def test_create_component_specifying_different_version(
    new_asset_version, temporary_file
):
    '''Create component on asset version ignoring specified version.'''
    session = new_asset_version.session
    component = new_asset_version.create_component(
        temporary_file, location=None,
        data=dict(
            version_id='this-value-should-be-ignored',
            version='this-value-should-be-overridden'
        )
    )
    assert component['version'] is new_asset_version

    # Have to delete component before can delete asset version.
    session.delete(component)
