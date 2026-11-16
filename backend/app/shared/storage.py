from __future__ import annotations

from pathlib import Path


class FileStorage:
    def save(self, storage_key: str, data: bytes) -> str:
        raise NotImplementedError

    def read(self, storage_key: str) -> bytes:
        raise NotImplementedError


class LocalFileStorage(FileStorage):
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, storage_key: str) -> Path:
        safe = storage_key.lstrip("/\\")
        p = (self.base_dir / safe).resolve()
        base = self.base_dir.resolve()
        if base not in p.parents and p != base:
            raise ValueError("invalid_storage_key")
        return p

    def save(self, storage_key: str, data: bytes) -> str:
        path = self._path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return storage_key

    def read(self, storage_key: str) -> bytes:
        path = self._path(storage_key)
        return path.read_bytes()
