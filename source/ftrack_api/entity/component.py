# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.entity.base


class Component(ftrack_api.entity.base.Entity):
    '''Represent a component.'''

    def get_availability(self, locations=None):
        '''Return availability in *locations*.

        If *locations* is None, all known locations will be checked.

        Return a dictionary of {location_id:percentage_availability}

        '''
        return self.session.get_component_availability(
            self, locations=locations
        )
