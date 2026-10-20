from _typeshed import Incomplete

logger: Incomplete
MEGABYTE: int
GIGABYTE: int
MAX_PARTS: int
MAX_CONCURRENCY: int
MAX_ATTEMPTS: int
INITIAL_DELAY: float
MAX_DELAY: int
MAX_JITTER: float

def get_chunk_size(file_size: int) -> int: ...
def get_part_count(file_size: int) -> int | None: ...
def upload_parts(
    file_object, file_size: int, urls, timeout
) -> list[dict[str, Incomplete]]: ...

class _MultipartUpload:
    def __init__(self, file_object, chunk_size: int, timeout) -> None: ...
    def run(self, urls) -> list[dict[str, Incomplete]]: ...
