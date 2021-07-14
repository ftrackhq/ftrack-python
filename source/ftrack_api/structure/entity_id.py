# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack_api.structure.base


class EntityIdStructure(ftrack_api.structure.base.Structure):
    '''Entity id pass-through structure.'''

    def get_resource_identifiers(self, entitities, context=None):
        '''Return a *resourceIdentifier* for supplied *entity*.'''
        result = []
        for entity in entitities:
            result.append(entity['id'])
        return result
