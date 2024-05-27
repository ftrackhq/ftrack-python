# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import io
import pytest
from ftrack_api.uploader import Uploader, get_chunk_size, SIZE_GIGABYTES, SIZE_MEGABYTES


@pytest.mark.parametrize(
    "file_size, expected_chunk_size",
    [
        (0, 8),
        (3 * SIZE_MEGABYTES, 8),
        (255 * SIZE_MEGABYTES, 16),
        (2 * SIZE_GIGABYTES, 32),
        (70 * SIZE_GIGABYTES, 128),
    ],
)
def test_get_chunk_size(file_size, expected_chunk_size):
    chunk_size_in_mb = get_chunk_size(file_size) // SIZE_MEGABYTES
    assert chunk_size_in_mb == expected_chunk_size


@pytest.fixture()
def make_dummy_file():
    chunk = b"DEADBEEF"
    files = []

    def _make_dummy_file(size):
        chunk_count = size // len(chunk)
        f = io.BytesIO(chunk * chunk_count)
        files.append(f)
        return f

    yield _make_dummy_file

    for f in files:
        f.close()

@pytest.mark.parametrize("size", [1 * SIZE_MEGABYTES, 10 * SIZE_MEGABYTES])
def test_uploader(session, make_dummy_file, size):
    file = make_dummy_file(size)
    uploader = Uploader(
        session, "17db4ccc-dd37-49c9-8be5-9afc4abf7c2c", "test.jpg", size, file, None
    )
    uploader.start()
