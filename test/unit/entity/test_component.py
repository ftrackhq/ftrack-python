# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from __future__ import unicode_literals


def test_get_availability(new_component):
    '''Retrieve availability in locations.'''
    session = new_component.session
    availability = new_component.get_availability()

    # Note: Currently the origin location is also 0.0 as the link is not
    # persisted to the server. This may change in future and this test would
    # need updating as a result.
    assert set(availability.values()) == set([0.0])

    # Add to a location.
    source_location = session.query(
        'Location where name is "ftrack.origin"'
    ).one()

    target_location = session.query(
        'Location where name is "ftrack.unmanaged"'
    ).one()

    target_location.add_component(new_component, source_location)

    # Recalculate availability.

    # Currently have to manually expire the related attribute. This should be
    # solved in future by bi-directional relationship updating.
    del new_component['component_locations']

    availability = new_component.get_availability()
    target_availability = availability.pop(target_location['id'])
    assert target_availability == 100.0

    # All other locations should still be 0.
    assert set(availability.values()) == set([0.0])
