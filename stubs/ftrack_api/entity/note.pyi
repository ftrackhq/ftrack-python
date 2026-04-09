import ftrack_api.entity.base
from _typeshed import Incomplete

class Note(ftrack_api.entity.base.Entity):
    def create_reply(self, content, author): ...

class CreateNoteMixin:
    def create_note(self, content, author, recipients: Incomplete | None = None, category: Incomplete | None = None, labels: Incomplete | None = None): ...
