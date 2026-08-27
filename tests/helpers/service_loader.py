"""Load a microservice package named `app` without leaking it across tests."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

from tests.helpers.paths import SERVICES_DIR

_APP_PREFIXES = ("app",)


def _purge_app_modules() -> None:
    stale = [name for name in list(sys.modules) if name == "app" or name.startswith("app.")]
    for name in stale:
        del sys.modules[name]


@contextmanager
def service_on_path(service_name: str):
    service_dir = SERVICES_DIR / service_name
    if not service_dir.is_dir():
        raise FileNotFoundError(f"Unknown service directory: {service_dir}")

    _purge_app_modules()
    inserted = str(service_dir)
    sys.path.insert(0, inserted)
    try:
        yield Path(inserted)
    finally:
        if inserted in sys.path:
            sys.path.remove(inserted)
        _purge_app_modules()
