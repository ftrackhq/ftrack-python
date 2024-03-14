import typing
import collections

from ftrack_api.symbol import NOT_SET

if typing.TYPE_CHECKING:
    from ftrack_api.entity.base import Entity

ENTITY_STORAGE_KEY = "ftrack_attribute_storage"

LOCAL_ENTITY_STORAGE_KEY = "local"
REMOTE_ENTITY_STORAGE_KEY = "remote"


class EntityStorage(collections.defaultdict):
    """Storage for entity attributes"""

    def get(self, key: str) -> typing.Any:
        local, remote = self.get_local_remote_pair(key)

        return local if local is not NOT_SET else remote

    def get_local(self, key: str) -> typing.Any:
        return self[key][LOCAL_ENTITY_STORAGE_KEY]

    def get_remote(self, key: str) -> typing.Any:
        return self[key][REMOTE_ENTITY_STORAGE_KEY]

    def get_local_remote_pair(self, key: str) -> typing.Tuple[typing.Any, typing.Any]:
        """Return local and remote values for *key*."""
        return self[key][LOCAL_ENTITY_STORAGE_KEY], self[key][REMOTE_ENTITY_STORAGE_KEY]

    def set_local(self, key: str, value: typing.Any) -> None:
        self[key][LOCAL_ENTITY_STORAGE_KEY] = value

    def set_remote(self, key: str, value: typing.Any) -> None:
        self[key][REMOTE_ENTITY_STORAGE_KEY] = value


def get_entity_storage(entity: "Entity") -> EntityStorage:
    """Return attribute storage on *entity* creating if missing."""

    storage = getattr(entity, ENTITY_STORAGE_KEY, None)
    if storage is None:
        storage = EntityStorage(
            lambda: {
                LOCAL_ENTITY_STORAGE_KEY: NOT_SET,
                REMOTE_ENTITY_STORAGE_KEY: NOT_SET,
            }
        )
        setattr(entity, ENTITY_STORAGE_KEY, storage)

    return storage
