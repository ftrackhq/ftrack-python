from _typeshed import Incomplete

class Error(Exception):
    default_message: str
    message: Incomplete
    details: Incomplete
    traceback: Incomplete
    def __init__(
        self, message: Incomplete | None = None, details: Incomplete | None = None
    ) -> None: ...

class AuthenticationError(Error):
    default_message: str

class ServerError(Error):
    default_message: str

class ServerCompatibilityError(ServerError):
    default_message: str

class NotFoundError(Error):
    default_message: str

class NotUniqueError(Error):
    default_message: str

class IncorrectResultError(Error):
    default_message: str

class NoResultFoundError(IncorrectResultError):
    default_message: str

class MultipleResultsFoundError(IncorrectResultError):
    default_message: str

class EntityTypeError(Error):
    default_message: str

class UnrecognisedEntityTypeError(EntityTypeError):
    default_message: str
    def __init__(self, entity_type, **kw) -> None: ...

class OperationError(Error):
    default_message: str

class InvalidStateError(Error):
    default_message: str

class InvalidStateTransitionError(InvalidStateError):
    default_message: str
    def __init__(self, current_state, target_state, entity, **kw) -> None: ...

class AttributeError(Error):
    default_message: str

class ImmutableAttributeError(AttributeError):
    default_message: str
    def __init__(self, attribute, **kw) -> None: ...

class CollectionError(Error):
    default_message: str
    def __init__(self, collection, **kw) -> None: ...

class ImmutableCollectionError(CollectionError):
    default_message: str

class DuplicateItemInCollectionError(CollectionError):
    default_message: str
    def __init__(self, item, collection, **kw) -> None: ...

class ParseError(Error):
    default_message: str

class EventHubError(Error):
    default_message: str

class EventHubConnectionError(EventHubError):
    default_message: str

class EventHubPacketError(EventHubError):
    default_message: str

class PermissionDeniedError(Error):
    default_message: str

class LocationError(Error):
    default_message: str

class ComponentNotInAnyLocationError(LocationError):
    default_message: str

class ComponentNotInLocationError(LocationError):
    default_message: str
    def __init__(self, components, location, **kw) -> None: ...

class ComponentInLocationError(LocationError):
    default_message: str
    def __init__(self, components, location, **kw) -> None: ...

class AccessorError(Error):
    default_message: str

class AccessorOperationFailedError(AccessorError):
    default_message: str
    def __init__(
        self,
        operation: str = "",
        resource_identifier: Incomplete | None = None,
        error: Incomplete | None = None,
        **kw
    ) -> None: ...

class AccessorUnsupportedOperationError(AccessorOperationFailedError):
    default_message: str

class AccessorPermissionDeniedError(AccessorOperationFailedError):
    default_message: str

class AccessorResourceIdentifierError(AccessorError):
    default_message: str
    def __init__(self, resource_identifier, **kw) -> None: ...

class AccessorFilesystemPathError(AccessorResourceIdentifierError):
    default_message: str

class AccessorResourceError(AccessorError):
    default_message: str
    def __init__(
        self,
        operation: str = "",
        resource_identifier: Incomplete | None = None,
        error: Incomplete | None = None,
        **kw
    ) -> None: ...

class AccessorResourceNotFoundError(AccessorResourceError):
    default_message: str

class AccessorParentResourceNotFoundError(AccessorResourceError):
    default_message: str

class AccessorResourceInvalidError(AccessorResourceError):
    default_message: str

class AccessorContainerNotEmptyError(AccessorResourceError):
    default_message: str

class StructureError(Error):
    default_message: str

class ConnectionClosedError(Error):
    default_message: str
