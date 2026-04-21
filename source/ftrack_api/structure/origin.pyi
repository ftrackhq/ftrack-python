from .base import Structure as Structure
from _typeshed import Incomplete

class OriginStructure(Structure):
    def get_resource_identifier(self, entity, context: Incomplete | None = None): ...
