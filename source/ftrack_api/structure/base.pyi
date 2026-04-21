from _typeshed import Incomplete
from abc import ABCMeta, abstractmethod

class Structure(metaclass=ABCMeta):
    prefix: Incomplete
    path_separator: str
    def __init__(self, prefix: str = "") -> None: ...
    @abstractmethod
    def get_resource_identifier(self, entity, context: Incomplete | None = None): ...
