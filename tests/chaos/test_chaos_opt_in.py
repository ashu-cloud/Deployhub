from __future__ import annotations

import os

import pytest

from tests.helpers.paths import REPO_ROOT

pytestmark = [pytest.mark.chaos, pytest.mark.slow]


def test_chaos_monkey_recovers_when_opted_in():
    if os.getenv("RUN_CHAOS") != "1":
        pytest.skip("destructive test; set RUN_CHAOS=1 to enable")

    import importlib.util

    path = REPO_ROOT / "tests" / "chaos" / "chaos_monkey.py"
    spec = importlib.util.spec_from_file_location("chaos_monkey", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.run_chaos(duration_seconds=20, interval_seconds=8)
