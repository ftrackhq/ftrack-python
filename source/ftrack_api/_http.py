# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import httpx
import os
from pathlib import Path


def _get_ssl_context():
    ssl_context = httpx.create_ssl_context()

    requests_ca_env = os.environ.get("REQUESTS_CA_BUNDLE")
    if not requests_ca_env:
        return

    ca_path = Path(requests_ca_env)

    if ca_path.is_file():
        ssl_context.load_verify_locations(cafile=str(ca_path))
    elif ca_path.is_dir():
        ssl_context.load_verify_locations(capath=str(ca_path))

    return ssl_context


ssl_context = _get_ssl_context()
