import ftrack_api.entity.base
from _typeshed import Incomplete

class Component(ftrack_api.entity.base.Entity):
    def get_availability(self, locations: Incomplete | None = None): ...

class CreateThumbnailMixin:
    def create_thumbnail(self, path, data: Incomplete | None = None): ...
