"""Artifact identity and integrity checks."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_artifact(path: str | Path, expected: dict[str, Any]) -> dict[str, Any]:
    """Verify file identity using a full SHA-256 and an optional byte count."""

    if not isinstance(expected, dict):
        raise ValueError("The manifest entry must be an object with a full SHA-256.")
    expected_sha = expected.get("sha256")
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha):
        raise ValueError("The manifest entry must contain a full 64-digit hexadecimal SHA-256.")
    expected_size = expected.get("size_bytes")
    if expected_size is not None and (
        type(expected_size) is not int or expected_size < 0
    ):
        raise ValueError("size_bytes must be a non-negative integer.")
    artifact = Path(path)
    if not artifact.is_file():
        raise FileNotFoundError(artifact)
    size = artifact.stat().st_size
    if expected_size is not None and size != expected_size:
        raise ValueError(f"Size mismatch: expected {expected_size}, found {size} bytes.")
    digest = sha256_file(artifact)
    if digest != expected_sha.lower():
        raise ValueError("SHA-256 mismatch.")
    return {"path": str(artifact), "size_bytes": size, "sha256": digest, "valid": True}
