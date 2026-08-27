from __future__ import annotations

import pytest

from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit


def test_encrypt_decrypt_roundtrip():
    with service_on_path("project-service"):
        from app.services.encryption import EncryptionService

        svc = EncryptionService()
        plaintext = "super-secret-db-url"
        token = svc.encrypt(plaintext)
        assert token != plaintext
        assert plaintext not in token
        assert svc.decrypt(token) == plaintext


def test_encrypt_uses_unique_nonce():
    with service_on_path("project-service"):
        from app.services.encryption import EncryptionService

        svc = EncryptionService()
        first = svc.encrypt("same-value")
        second = svc.encrypt("same-value")
        assert first != second


def test_decrypt_rejects_tampered_payload():
    with service_on_path("project-service"):
        from app.services.encryption import EncryptionService

        svc = EncryptionService()
        token = svc.encrypt("hello")
        mutated = token[:-4] + ("A" if not token.endswith("A") else "B")
        with pytest.raises(Exception):
            svc.decrypt(mutated)


def test_env_var_response_schema_omits_secret_fields():
    with service_on_path("project-service"):
        from app.schemas.project import EnvVarResponse

        fields = set(EnvVarResponse.model_fields)
        assert "value" not in fields
        assert "encrypted_value" not in fields
        assert {"id", "key", "created_at"} <= fields
