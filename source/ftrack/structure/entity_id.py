# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack.structure.base


class EntityIdStructure(ftrack.structure.base.Structure):
    '''Entity id pass-through structure.'''

    def get_resource_identifier(self, entity, context=None):
        '''Return a *resourceIdentifier* for supplied *entity*.'''
        return entity['id']
