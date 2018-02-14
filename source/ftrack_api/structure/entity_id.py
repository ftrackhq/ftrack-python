# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from __future__ import absolute_import
import ftrack_api.structure.base


class EntityIdStructure(ftrack_api.structure.base.Structure):
    '''Entity id pass-through structure.'''

    def get_resource_identifier(self, entity, context=None):
        '''Return a *resourceIdentifier* for supplied *entity*.'''
        return entity['id']
