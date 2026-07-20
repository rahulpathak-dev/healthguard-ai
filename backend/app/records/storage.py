import hashlib
import hmac
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.config import get_settings


@dataclass(frozen=True)
class StoredObject:
    storage_path: str
    sha256: str


class LocalPrivateStorage:
    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or get_settings().record_storage_root).resolve()

    def _resolve(self, storage_path: str) -> Path:
        target = (self.root / storage_path).resolve()
        if self.root not in target.parents and target != self.root:
            raise ValueError("Storage path escapes configured root")
        return target

    async def put_quarantine(
        self, *, record_id: uuid.UUID, extension: str, data: bytes
    ) -> StoredObject:
        digest = hashlib.sha256(data).hexdigest()
        storage_path = f"quarantine/{record_id}/{digest}{extension}"
        target = self._resolve(storage_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return StoredObject(storage_path=storage_path, sha256=digest)

    async def delete(self, storage_path: str) -> None:
        target = self._resolve(storage_path)
        if target.exists():
            target.unlink()

    def signed_url(self, storage_path: str, *, expires_minutes: int = 5) -> str:
        expires_at = int((datetime.now(UTC) + timedelta(minutes=expires_minutes)).timestamp())
        secret = get_settings().token_secret.get_secret_value().encode("utf-8")
        payload = f"{storage_path}:{expires_at}".encode()
        signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return (
            f"/api/v1/records/files?path={storage_path}&expires={expires_at}&signature={signature}"
        )

    def validate_signature(self, storage_path: str, expires: int, signature: str) -> bool:
        if expires < int(datetime.now(UTC).timestamp()):
            return False
        secret = get_settings().token_secret.get_secret_value().encode("utf-8")
        payload = f"{storage_path}:{expires}".encode()
        expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


def storage() -> LocalPrivateStorage:
    os.makedirs(get_settings().record_storage_root, exist_ok=True)
    return LocalPrivateStorage()
