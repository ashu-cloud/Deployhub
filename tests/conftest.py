"""DeployHub test suite.

Run from the repo root after installing test deps:

    pip install -r requirements-test.txt
    pytest -m unit
    pytest -m health          # docker-compose stack must be up
    pytest -m e2e
    pytest -m security
    pytest -m security_audit  # production-bar checks; expected to fail on known gaps
    pytest -m concurrency    # races, parallel requests, lock contention
    pytest -m load

Set REQUIRE_LIVE=1 to fail (instead of skip) when a service is down.
"""

from __future__ import annotations

import pytest

# Importing tests.helpers.settings generates/loads the shared RS256 test
# keypair and sets JWT_ALGORITHM / JWT_PRIVATE_KEY_PATH / JWT_PUBLIC_KEY_PATH /
# WEBHOOK_SECRET / ENV_VAR_ENCRYPTION_KEY env vars *before* any service module
# gets imported by a test, so in-process services (via service_on_path) and
# tokens minted by tests.helpers.jwt_factory always agree on the same keys.
from tests.helpers import settings as _settings  # noqa: F401


@pytest.fixture(scope="session")
def repo_root():
    from tests.helpers.paths import REPO_ROOT

    return REPO_ROOT


def pytest_configure(config):
    """Default `pytest` skips audit/chaos/slow.

    Explicit ``-m`` or a path other than the suite root opts in so
    ``pytest tests/security/test_foo.py::test_bar`` still runs.
    """
    if (config.option.markexpr or "").strip():
        return
    args = [str(a).replace("\\", "/").rstrip("/") for a in (config.args or [])]
    if args and args not in (["tests"], ["."], []):
        return
    config.option.markexpr = "not security_audit and not chaos and not slow"
