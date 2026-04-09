import ftrack_api.entity.base
from _typeshed import Incomplete

class Job(ftrack_api.entity.base.Entity):
    def __init__(self, session, data: Incomplete | None = None, reconstructing: bool = False) -> None: ...
