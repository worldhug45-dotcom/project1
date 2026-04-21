"""Test helpers for sandbox-friendly temporary directories."""

from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator


TEST_TEMP_ROOT = Path(".test_tmp")


@contextmanager
def temporary_directory() -> Iterator[str]:
    TEST_TEMP_ROOT.mkdir(exist_ok=True)
    path = TEST_TEMP_ROOT / f"tmp_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)
