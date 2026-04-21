import ftrack_api.structure.base
from _typeshed import Incomplete

class StandardStructure(ftrack_api.structure.base.Structure):
    project_versions_prefix: Incomplete
    illegal_character_substitute: Incomplete
    def __init__(
        self,
        project_versions_prefix: Incomplete | None = None,
        illegal_character_substitute: str = "_",
    ) -> None: ...
    def sanitise_for_filesystem(self, value): ...
    def get_resource_identifier(self, entity, context: Incomplete | None = None): ...
