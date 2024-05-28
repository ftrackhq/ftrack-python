# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import math
import os
from typing import IO, Awaitable, Callable, TYPE_CHECKING, List, Optional
import anyio

import anyio.from_thread
import httpx

if TYPE_CHECKING:
    from ftrack_api.session import Session


SIZE_MEGABYTES = 1024**2
SIZE_GIGABYTES = 1024**3
MAX_PARTS = 10000

logger = logging.getLogger(__name__)
ssl_context = httpx.create_ssl_context()


def get_chunk_size(file_size: int) -> int:
    chunk_profiles = [
        (0, 8),
        (0.1, 16),
        (1, 32),
        (8, 64),
        (64, 128),
    ]

    for min_size_in_gb, chunk_size_in_mb in reversed(chunk_profiles):
        if file_size >= min_size_in_gb * SIZE_GIGABYTES:
            return chunk_size_in_mb * SIZE_MEGABYTES

    raise ValueError("Invalid file size.")


async def back_off(func: Callable[..., Awaitable], *args, retries=5, delay=5):
    for i in range(retries):
        try:
            return await func(*args)
        except Exception as e:
            if i == retries - 1:
                raise e

            sleep_time = delay * 2**i
            logger.warn(f"Retrying in {sleep_time}s")
            await anyio.sleep(sleep_time)


class Uploader:
    max_concurrency: int = int(os.environ.get("FTRACK_UPLOAD_MAX_CONCURRENCY", 5))

    def __init__(
        self,
        session: "Session",
        component_id: str,
        file_name: str,
        file_size: int,
        file: "IO",
        checksum: Optional[str],
    ):
        self.session = session
        self.component_id = component_id
        self.file = file
        self.file_name = file_name
        self.file_size = file_size
        self.checksum = checksum

        self.chunk_size = get_chunk_size(self.file_size)
        self.parts_count = math.ceil(self.file_size / self.chunk_size)

        if self.parts_count > MAX_PARTS:
            raise ValueError("File is too big.")

        self.upload_id: Optional[str] = None
        self.upload_urls: List[dict] = []
        self.uploaded_parts: List[dict] = []

    def _single_upload(self, url, headers):
        self.file.seek(0)

        response = httpx.put(
            url,
            verify=ssl_context,
            content=self.file,
            headers=headers,
        )

        response.raise_for_status()

    async def _upload_part_task(self, http: httpx.AsyncClient):
        async def send_data(part_num, url, content):
            resp = await http.put(url=url, content=content)
            resp.raise_for_status()

            return {
                "part_number": part_num,
                "e_tag": resp.headers["ETag"].strip('"'),
            }

        while True:
            url_info = self.upload_urls.pop(0) if self.upload_urls else None
            if not url_info:
                break

            url = url_info["signed_url"]
            part_num = url_info["part_number"]

            startPos = (part_num - 1) * self.chunk_size
            self.file.seek(startPos)
            content = self.file.read(self.chunk_size)

            uploaded_part = await back_off(send_data, part_num, url, content)
            self.uploaded_parts.append(uploaded_part)

    async def _multi_upload(self):
        async with httpx.AsyncClient(verify=ssl_context) as http:
            async with anyio.create_task_group() as tg:
                for _ in range(self.max_concurrency):
                    tg.start_soon(self._upload_part_task, http)

    def start(self):
        metadata = self.session.get_upload_metadata(
            self.component_id,
            self.file_name,
            self.file_size,
            self.checksum,
            self.parts_count if self.parts_count > 1 else None,
        )

        if "urls" in metadata:
            self.upload_id = metadata["upload_id"]
            self.upload_urls = metadata["urls"]

            # start upload in a separate thread, with anyio
            with anyio.from_thread.start_blocking_portal() as portal:
                portal.call(self._multi_upload)

            uploaded = sorted(self.uploaded_parts, key=lambda x: x["part_number"])
            self.session.complete_multipart_upload(
                self.component_id,
                self.upload_id,
                uploaded,
            )
        else:
            self._single_upload(metadata["url"], metadata["headers"])
