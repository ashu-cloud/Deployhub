import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings


class EncryptionService:
    """AES-256-GCM encryption for sensitive values stored in the database.

    The key is a 32-byte value supplied as a 64-char hex string via the
    OAUTH_TOKEN_ENCRYPTION_KEY environment variable.  Generate it once with:

        python -c "import secrets; print(secrets.token_hex(32))"

    and store the result in your secrets manager / .env file.
    """

    def __init__(self):
        if not settings.OAUTH_TOKEN_ENCRYPTION_KEY:
            raise RuntimeError(
                "OAUTH_TOKEN_ENCRYPTION_KEY is not set. "
                "Run `python scripts/generate_secrets.py` and supply it via "
                "the environment — refusing to start without an encryption key."
            )
        raw = bytes.fromhex(settings.OAUTH_TOKEN_ENCRYPTION_KEY)
        if len(raw) != 32:
            raise RuntimeError(
                f"OAUTH_TOKEN_ENCRYPTION_KEY must be 32 bytes (64 hex chars) "
                f"for AES-256, got {len(raw)} bytes."
            )
        self._aesgcm = AESGCM(raw)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string and return a base64-encoded ciphertext."""
        nonce = os.urandom(12)          # 96-bit random nonce — standard for GCM
        ct = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ct).decode("utf-8")

    def decrypt(self, encrypted_b64: str) -> str:
        """Decrypt a base64-encoded ciphertext and return the plaintext."""
        data = base64.b64decode(encrypted_b64.encode("utf-8"))
        nonce, ct = data[:12], data[12:]
        return self._aesgcm.decrypt(nonce, ct, None).decode("utf-8")


encryption_service = EncryptionService()
