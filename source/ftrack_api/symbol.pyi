from _typeshed import Incomplete

class Symbol:
    name: Incomplete
    value: Incomplete
    def __init__(self, name, value: bool = True) -> None: ...
    def __bool__(self) -> bool: ...
    def __copy__(self): ...

NOT_SET: Incomplete
CREATED: Incomplete
MODIFIED: Incomplete
DELETED: Incomplete
COMPONENT_ADDED_TO_LOCATION_TOPIC: str
COMPONENT_REMOVED_FROM_LOCATION_TOPIC: str
ORIGIN_LOCATION_ID: str
UNMANAGED_LOCATION_ID: str
REVIEW_LOCATION_ID: str
CONNECT_LOCATION_ID: str
SERVER_LOCATION_ID: str
CHUNK_SIZE: Incomplete
JOB_SYNC_USERS_LDAP: Incomplete
