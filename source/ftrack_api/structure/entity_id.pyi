import ftrack_api.structure.base
from _typeshed import Incomplete

class EntityIdStructure(ftrack_api.structure.base.Structure):
    def get_resource_identifier(self, entity, context: Incomplete | None = None): ...
