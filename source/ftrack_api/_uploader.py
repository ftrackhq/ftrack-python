# :coding: utf-8
# :copyright: Copyright (c) 2026 ftrack

"""Multi-part upload of file data to the ftrack.server location.

Part sizing and retry back-off follow the ftrack JavaScript API client
(``source/util/get_chunk_size.ts`` and ``source/util/back_off.ts``).
"""

import concurrent.futures
import logging
import os
import random
import threading

import requests

logger = logging.getLogger(__name__)

MEGABYTE = 1024 * 1024
GIGABYTE = 1024 * MEGABYTE

#: Maximum number of parts the server accepts for one upload.
MAX_PARTS = 10000

#: Maximum number of parts uploaded concurrently.
MAX_CONCURRENCY = int(os.getenv("FTRACK_API_UPLOAD_MAX_CONCURRENCY", 0)) or 6

#: Maximum number of attempts per part, including the first one.
MAX_ATTEMPTS = 16

#: Delay before the first retry is twice this value, in seconds.
INITIAL_DELAY = 0.5

#: Maximum delay between attempts, in seconds.
MAX_DELAY = 64

#: Random delay of up to this many seconds added to each retry.
MAX_JITTER = 0.5


def get_chunk_size(file_size):
    """Return part size in bytes for a multi-part upload of *file_size* bytes.

    Raise :exc:`ValueError` if *file_size* exceeds what can be uploaded within
    :data:`MAX_PARTS` parts.
    """
    if file_size > 128 * MEGABYTE * MAX_PARTS:
        raise ValueError("File is larger than the maximum allowed (1,280 GB).")

    if file_size > 64 * GIGABYTE:
        return 128 * MEGABYTE
    if file_size > 8 * GIGABYTE:
        return 64 * MEGABYTE
    if file_size > 1 * GIGABYTE:
        return 32 * MEGABYTE
    if file_size > 128 * MEGABYTE:
        return 16 * MEGABYTE

    return 8 * MEGABYTE


def get_part_count(file_size):
    """Return number of parts to upload *file_size* bytes in.

    Return None when the data should be uploaded with a single PUT request.
    """
    chunk_size = get_chunk_size(file_size)
    part_count = -(-file_size // chunk_size)
    if part_count <= 2:
        return None

    return part_count


def upload_parts(file_object, file_size, urls, timeout):
    """Upload *file_object* to signed part *urls* and return uploaded parts.

    *file_object* must be seekable and hold *file_size* bytes. It is shared by
    all worker threads and must not be used by the caller until this returns.

    *urls* is the list of ``{"part_number": int, "signed_url": str}``
    returned by :meth:`ftrack_api.session.Session.get_upload_metadata`.

    *timeout* is passed to each PUT request.

    Return a list of ``{"part_number": int, "e_tag": str}`` sorted by part
    number, suitable for
    :meth:`ftrack_api.session.Session.complete_multipart_upload`.

    If any part fails after retries, parts not yet started are cancelled and
    the error of that part is raised.
    """
    upload = _MultipartUpload(file_object, get_chunk_size(file_size), timeout)
    return upload.run(urls)


def _is_retryable(error):
    """Return whether a failed part PUT raising *error* should be retried."""
    # Certificate failures are configuration errors that retries cannot fix.
    if isinstance(error, requests.exceptions.SSLError):
        return False

    if isinstance(
        error, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ):
        return True

    if isinstance(error, requests.exceptions.HTTPError):
        response = error.response
        return response is not None and (
            response.status_code == 429 or response.status_code >= 500
        )

    return False


class _MultipartUpload(object):
    """Concurrent upload of parts read from one shared file object."""

    def __init__(self, file_object, chunk_size, timeout):
        """Initialise upload of *file_object* in *chunk_size* parts."""
        self._file = file_object
        self._file_lock = threading.Lock()
        self._chunk_size = chunk_size
        self._timeout = timeout
        self._aborted = threading.Event()
        self._error = None
        self._error_lock = threading.Lock()
        self._local = threading.local()
        self._http_sessions = []
        self._http_sessions_lock = threading.Lock()

    def run(self, urls):
        """Upload all part *urls* and return uploaded parts."""
        executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(MAX_CONCURRENCY, len(urls)),
            thread_name_prefix="ftrack-api-upload",
        )
        futures = []
        try:
            for url in urls:
                futures.append(executor.submit(self._upload_part, url))

            concurrent.futures.wait(
                futures, return_when=concurrent.futures.FIRST_EXCEPTION
            )
        finally:
            # Stops retries and queued parts on failure or interruption; no-op
            # once every part has completed.
            self._aborted.set()
            for future in futures:
                future.cancel()

            executor.shutdown(wait=True)
            for http_session in self._http_sessions:
                http_session.close()

        if self._error is not None:
            raise self._error

        parts = [future.result() for future in futures]
        parts.sort(key=lambda part: part["part_number"])
        return parts

    def _upload_part(self, url):
        """Upload part described by *url*; abort the upload if it fails."""
        try:
            return self._send_part(url)
        except Exception as error:
            # Record before aborting so the first failure is the one raised,
            # not the abort it causes in other parts.
            with self._error_lock:
                if self._error is None:
                    self._error = error
            self._aborted.set()
            raise

    def _send_part(self, url):
        """Upload part described by *url* and return its number and ETag."""
        part_number = url["part_number"]
        if self._aborted.is_set():
            raise RuntimeError("Upload aborted before part {0}.".format(part_number))

        with self._file_lock:
            self._file.seek((part_number - 1) * self._chunk_size)
            data = self._file.read(self._chunk_size)

        http_session = self._get_http_session()
        attempt = 0
        delay = INITIAL_DELAY
        while True:
            try:
                e_tag = self._put(http_session, url["signed_url"], part_number, data)
                return {"part_number": part_number, "e_tag": e_tag}
            except Exception as error:
                attempt += 1
                if attempt >= MAX_ATTEMPTS or not _is_retryable(error):
                    raise

                delay = min(MAX_DELAY, delay * 2)
                wait = delay + random.uniform(0, MAX_JITTER)
                logger.warning(
                    "Failed to upload part %d (%s), retrying in %.1f seconds.",
                    part_number,
                    error,
                    wait,
                )
                if self._aborted.wait(wait):
                    raise

    def _put(self, http_session, signed_url, part_number, data):
        """PUT *data* to *signed_url* and return the ETag without quotes."""
        response = http_session.put(signed_url, data=data, timeout=self._timeout)
        response.raise_for_status()

        e_tag = response.headers.get("ETag")
        if not e_tag:
            raise RuntimeError(
                "Upload of part {0} returned no ETag header.".format(part_number)
            )

        return e_tag.replace('"', "")

    def _get_http_session(self):
        """Return the requests session of the calling worker thread."""
        http_session = getattr(self._local, "http_session", None)
        if http_session is None:
            http_session = requests.Session()
            self._local.http_session = http_session
            with self._http_sessions_lock:
                self._http_sessions.append(http_session)

        return http_session
