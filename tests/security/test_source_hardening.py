from __future__ import annotations

import re

import pytest

from tests.helpers.paths import FRONTEND_DIR, SERVICES_DIR

pytestmark = [pytest.mark.security, pytest.mark.security_audit]


def test_dev_bypass_tokens_are_not_accepted():
    source = (SERVICES_DIR / "project-service" / "app" / "core" / "security.py").read_text(encoding="utf-8")
    assert "dev-bypass" not in source, (
        "SECURITY FINDING: get_current_user accepts unsigned dev-bypass tokens as a real user"
    )
    assert "dev-token" not in source
    assert "mock-dev-token" not in source


def test_frontend_does_not_ship_a_dev_bypass_control():
    login = (FRONTEND_DIR / "src" / "app" / "login" / "page.tsx").read_text(encoding="utf-8")
    assert "Dev Bypass" not in login, (
        "SECURITY FINDING: login page exposes a client-side Dev Bypass that writes a fake JWT"
    )


def test_git_clone_does_not_interpolate_untrusted_input_into_a_shell():
    source = (SERVICES_DIR / "build-orchestrator" / "app" / "services" / "builder.py").read_text(
        encoding="utf-8"
    )
    assert "create_subprocess_shell" not in source, (
        "SECURITY FINDING: git clone runs via create_subprocess_shell with an interpolated "
        "branch/repo_url string; use create_subprocess_exec with an argument list"
    )


def test_auth_me_enforces_current_user():
    source = (SERVICES_DIR / "auth-service" / "app" / "api" / "auth.py").read_text(encoding="utf-8")
    me_idx = source.find("async def read_users_me")
    assert me_idx != -1
    snippet = source[me_idx : me_idx + 400]
    live_lines = "\n".join(
        line for line in snippet.splitlines() if not line.lstrip().startswith("#")
    )
    assert "get_current_user" in live_lines, (
        "SECURITY FINDING: GET /auth/me is a stub and does not authenticate the caller"
    )


def test_refresh_token_not_duplicated_in_json_body():
    """Architecture: the *access* token is meant to reach the client (held in
    memory, never localStorage) so it can be sent as a Bearer header -- that
    is expected and correct. The actual finding was that the HttpOnly cookie
    duplicated the access token under the same name instead of carrying a
    separate, longer-lived refresh token.
    """
    source = (SERVICES_DIR / "auth-service" / "app" / "api" / "auth.py").read_text(encoding="utf-8")
    assert "create_refresh_token" in source, (
        "SECURITY FINDING: no distinct refresh token is issued; the HttpOnly cookie "
        "just duplicates the access token, which serves no security purpose"
    )
    assert 'key=REFRESH_COOKIE_NAME' in source or 'key="refresh_token"' in source, (
        "SECURITY FINDING: HttpOnly cookie is not carrying the refresh token"
    )


def test_deployment_routes_declare_auth_dependency():
    source = (SERVICES_DIR / "deployment-service" / "app" / "api" / "deployments.py").read_text(
        encoding="utf-8"
    )
    for fn in ("get_deployments", "get_deployment_detail", "rollback_deployment"):
        idx = source.find(f"async def {fn}")
        assert idx != -1, fn
        snippet = source[idx : idx + 350]
        assert "get_current_user" in snippet, (
            f"SECURITY FINDING: {fn} has no authentication dependency"
        )


def test_jwt_algorithm_matches_asymmetric_plan():
    config = (SERVICES_DIR / "auth-service" / "app" / "core" / "config.py").read_text(encoding="utf-8")
    assert 'JWT_ALGORITHM: str = "RS256"' in config or "RS256" in config, (
        "SECURITY FINDING: JWT_ALGORITHM is HS256; architecture specifies RS256"
    )


def test_project_cors_is_not_wildcard():
    source = (SERVICES_DIR / "project-service" / "app" / "main.py").read_text(encoding="utf-8")
    compact = source.replace(" ", "").replace("\n", "")
    assert 'allow_origins=["*"]' not in compact, (
        "SECURITY FINDING: project-service CORS allow_origins is *"
    )


def test_no_eval_or_pickle_in_services():
    # Word-boundary regexes so e.g. `asyncio.create_subprocess_exec(` (a safe,
    # argv-list call) does not false-positive on the substring "exec(".
    banned = (r"(?<!\w)eval\(", r"(?<!\w)exec\(", r"pickle\.loads", r"yaml\.load\(")
    hits = []
    for path in SERVICES_DIR.rglob("*.py"):
        if any(part in {".venv", "venv", "site-packages", "__pycache__"} for part in path.parts):
            continue
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in banned:
            if re.search(pattern, text):
                hits.append(f"{path.relative_to(SERVICES_DIR)}: {pattern}")
    assert hits == [], "SECURITY FINDING: dangerous runtime eval/exec/pickle:\n" + "\n".join(hits)


def test_sqlalchemy_text_is_not_fed_user_strings():
    """Static check: sqlalchemy.text() should only wrap literals, not concatenated request data."""
    skip_parts = {".venv", "venv", "site-packages", "tests", "__pycache__"}
    hits = []
    for path in SERVICES_DIR.rglob("*.py"):
        if skip_parts.intersection(path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r'\btext\(\s*f["\']', text) or re.search(r"\btext\(\s*[^)]*\+\s*request", text):
            hits.append(str(path.relative_to(SERVICES_DIR)))
    assert hits == [], f"SECURITY FINDING: dynamic SQL via sqlalchemy.text: {hits}"
