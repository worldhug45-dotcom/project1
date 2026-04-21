"""Runtime helpers shared by CLI and use cases."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4


def create_run_id() -> str:
    """Create the default timestamp_uuid run identifier."""

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}_{uuid4().hex[:8]}"

