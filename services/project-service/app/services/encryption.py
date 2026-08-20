import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings

class EncryptionService:
    def __init__(self):
        # We need a 32-byte key for AES-256. 
        # Convert hex string from settings to bytes.
        self.key = bytes.fromhex(settings.ENV_VAR_ENCRYPTION_KEY)
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, value: str) -> str:
        nonce = os.urandom(12) # 12 bytes is standard for GCM
        ciphertext = self.aesgcm.encrypt(nonce, value.encode('utf-8'), None)
        # Store as base64(nonce + ciphertext)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def decrypt(self, encrypted_value_b64: str) -> str:
        data = base64.b64decode(encrypted_value_b64.encode('utf-8'))
        nonce = data[:12]
        ciphertext = data[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')

encryption_service = EncryptionService()
