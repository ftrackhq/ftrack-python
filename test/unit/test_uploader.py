# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

import io
import threading

import pytest
import requests

import ftrack_api._uploader as uploader

MB = uploader.MEGABYTE
GB = uploader.GIGABYTE


@pytest.mark.parametrize(
    "file_size, expected",
    [
        (128 * MB, 8 * MB),
        (128 * MB + 1, 16 * MB),
        (1 * GB + 1, 32 * MB),
        (8 * GB + 1, 64 * MB),
        (64 * GB + 1, 128 * MB),
        (128 * MB * uploader.MAX_PARTS, 128 * MB),
    ],
)
def test_chunk_size_boundaries(file_size, expected):
    """Part size steps up just above each threshold."""
    assert uploader.get_chunk_size(file_size) == expected


def test_chunk_size_rejects_too_large_file():
    with pytest.raises(ValueError):
        uploader.get_chunk_size(128 * MB * uploader.MAX_PARTS + 1)


@pytest.mark.parametrize(
    "file_size, expected",
    [(0, None), (16 * MB, None), (16 * MB + 1, 3), (128 * MB, 16)],
)
def test_part_count_single_put_up_to_two_parts(file_size, expected):
    """Up to two parts is uploaded with a single PUT."""
    assert uploader.get_part_count(file_size) == expected


class _Response(object):
    def __init__(self, status_code=200, e_tag=None):
        self.status_code = status_code
        self.headers = {} if e_tag is None else {"ETag": e_tag}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(
                "{0} Error".format(self.status_code), response=self
            )


@pytest.fixture()
def fake_put(monkeypatch):
    """Route part PUTs to a handler; return the recorded calls."""
    monkeypatch.setattr(uploader, "INITIAL_DELAY", 0)
    monkeypatch.setattr(uploader, "MAX_JITTER", 0)

    state = {"handler": None, "calls": [], "lock": threading.Lock()}

    def put(session, url, data=None, timeout=None):
        with state["lock"]:
            state["calls"].append((url, data, timeout))
            attempt = sum(1 for call in state["calls"] if call[0] == url)
        return state["handler"](url, data, attempt)

    monkeypatch.setattr(requests.Session, "put", put)
    return state


def _urls(count, reverse=False):
    numbers = range(count, 0, -1) if reverse else range(1, count + 1)
    return [
        {"part_number": number, "signed_url": "part-{0}".format(number)}
        for number in numbers
    ]


def _upload(data, urls, chunk_size):
    upload = uploader._MultipartUpload(io.BytesIO(data), chunk_size, timeout=7)
    return upload.run(urls)


def test_upload_reads_part_offsets_and_sorts_by_part_number(fake_put):
    """Each part gets its own slice; result is ordered with ETags unquoted."""
    data = bytes(bytearray(range(10)))
    fake_put["handler"] = lambda url, body, attempt: _Response(
        e_tag='"etag-{0}"'.format(url)
    )

    parts = _upload(data, _urls(4, reverse=True), chunk_size=3)

    assert parts == [
        {"part_number": number, "e_tag": "etag-part-{0}".format(number)}
        for number in range(1, 5)
    ]
    bodies = {url: body for url, body, _ in fake_put["calls"]}
    assert bodies == {
        "part-1": data[0:3],
        "part-2": data[3:6],
        "part-3": data[6:9],
        "part-4": data[9:10],
    }
    assert {timeout for _, _, timeout in fake_put["calls"]} == {7}


@pytest.mark.parametrize(
    "failure",
    [
        lambda: _Response(503),
        lambda: _Response(429),
        lambda: (_ for _ in ()).throw(requests.exceptions.ConnectionError("down")),
        lambda: (_ for _ in ()).throw(requests.exceptions.ReadTimeout("slow")),
    ],
    ids=["5xx", "429", "connection-error", "timeout"],
)
def test_transient_failure_is_retried(fake_put, failure):
    def handler(url, body, attempt):
        if url == "part-2" and attempt < 3:
            return failure()
        return _Response(e_tag="e")

    fake_put["handler"] = handler

    parts = _upload(b"x" * 9, _urls(3), chunk_size=3)

    assert [part["part_number"] for part in parts] == [1, 2, 3]
    assert sum(1 for url, _, _ in fake_put["calls"] if url == "part-2") == 3


def test_client_error_is_not_retried(fake_put):
    def handler(url, body, attempt):
        if url == "part-2":
            return _Response(403)
        return _Response(e_tag="e")

    fake_put["handler"] = handler

    with pytest.raises(requests.exceptions.HTTPError, match="403"):
        _upload(b"x" * 9, _urls(3), chunk_size=3)

    assert sum(1 for url, _, _ in fake_put["calls"] if url == "part-2") == 1


def test_certificate_error_is_not_retried(fake_put):
    """SSLError subclasses ConnectionError but retrying cannot fix it."""

    def handler(url, body, attempt):
        if url == "part-2":
            raise requests.exceptions.SSLError("certificate verify failed")
        return _Response(e_tag="e")

    fake_put["handler"] = handler

    with pytest.raises(requests.exceptions.SSLError):
        _upload(b"x" * 9, _urls(3), chunk_size=3)

    assert sum(1 for url, _, _ in fake_put["calls"] if url == "part-2") == 1


def test_retries_stop_after_max_attempts(fake_put, monkeypatch):
    monkeypatch.setattr(uploader, "MAX_ATTEMPTS", 4)
    fake_put["handler"] = lambda url, body, attempt: _Response(500)

    with pytest.raises(requests.exceptions.HTTPError, match="500"):
        _upload(b"x" * 3, _urls(1), chunk_size=3)

    assert len(fake_put["calls"]) == 4


def test_missing_etag_fails_upload(fake_put):
    fake_put["handler"] = lambda url, body, attempt: _Response(e_tag=None)

    with pytest.raises(RuntimeError, match="ETag"):
        _upload(b"x" * 3, _urls(1), chunk_size=3)


def test_failed_part_cancels_parts_not_started(fake_put, monkeypatch):
    """With one worker, parts queued behind a failed part are never sent."""
    monkeypatch.setattr(uploader, "MAX_CONCURRENCY", 1)

    def handler(url, body, attempt):
        if url == "part-2":
            return _Response(400)
        return _Response(e_tag="e")

    fake_put["handler"] = handler

    with pytest.raises(requests.exceptions.HTTPError, match="400"):
        _upload(b"x" * 30, _urls(10), chunk_size=3)

    assert [url for url, _, _ in fake_put["calls"]] == ["part-1", "part-2"]


def test_failed_part_stops_retries_of_other_parts(fake_put, monkeypatch):
    """A part waiting to retry gives up once another part has failed."""
    # Long enough that the retry only ends early through the abort.
    monkeypatch.setattr(uploader, "INITIAL_DELAY", 30)
    started = threading.Event()
    failed = threading.Event()

    def handler(url, body, attempt):
        if url == "part-1":
            started.wait(5)
            failed.set()
            return _Response(400)
        started.set()
        failed.wait(5)
        return _Response(503)

    fake_put["handler"] = handler

    with pytest.raises(requests.exceptions.HTTPError, match="400"):
        _upload(b"x" * 6, _urls(2), chunk_size=3)

    assert sum(1 for url, _, _ in fake_put["calls"] if url == "part-2") == 1
