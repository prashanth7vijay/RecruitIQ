import hashlib
import hmac
import os
import time

from app.storage.base_storage import BaseStorage


class LocalStorage(BaseStorage):
    def __init__(self, base_path: str, secret_key: str):
        self.base_path = base_path
        self.secret_key = secret_key
        os.makedirs(self.base_path, exist_ok=True)

    def save(self, file_obj, key: str) -> str:
        full_path = self._full_path(key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file_obj.save(full_path)
        return key

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        expires_at = int(time.time()) + expires_in
        signature = self._sign(key, expires_at)
        return f"/api/v1/files/{key}?expires={expires_at}&signature={signature}"

    def delete(self, key: str) -> None:
        full_path = self._full_path(key)
        if os.path.exists(full_path):
            os.remove(full_path)

    def exists(self, key: str) -> bool:
        return os.path.exists(self._full_path(key))

    def verify_signature(self, key: str, expires: int, signature: str) -> bool:
        if int(time.time()) > expires:
            return False
        expected = self._sign(key, expires)
        return hmac.compare_digest(expected, signature)

    def read_bytes(self, key: str) -> bytes:
        with open(self._full_path(key), "rb") as f:
            return f.read()

    # --- internal -----------------------------------------------------

    def _full_path(self, key: str) -> str:
        # Reject any key that could escape base_path via path traversal.
        normalized = os.path.normpath(key)
        if normalized.startswith("..") or os.path.isabs(normalized):
            raise ValueError(f"Invalid storage key: {key}")
        return os.path.join(self.base_path, normalized)

    def _sign(self, key: str, expires_at: int) -> str:
        message = f"{key}:{expires_at}".encode("utf-8")
        return hmac.new(self.secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()
