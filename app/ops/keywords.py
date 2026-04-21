"""Read-only keyword snapshot helpers for operator-facing web endpoints."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.infrastructure.settings import (
    load_settings,
    resolve_keyword_override_path,
    save_core_keyword_override,
    save_exclude_keyword_override,
    save_supporting_keyword_override,
)


@dataclass(frozen=True, slots=True)
class OperatorKeywordsSnapshot:
    """Minimal read-only keyword payload for the operator dashboard."""

    status: str
    config_path: str
    override_path: str
    override_exists: bool
    last_loaded_path: str
    keyword_counts: dict[str, int]
    keywords: dict[str, tuple[str, ...]]
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "config_path": self.config_path,
            "override_path": self.override_path,
            "override_exists": self.override_exists,
            "last_loaded_path": self.last_loaded_path,
            "keyword_counts": dict(self.keyword_counts),
            "keywords": {
                key: list(values)
                for key, values in self.keywords.items()
            },
            "error_message": self.error_message,
        }


def load_operator_keywords_snapshot(
    *,
    config_path: Path,
    environ: dict[str, str] | None = None,
) -> OperatorKeywordsSnapshot:
    runtime_environ = dict(os.environ if environ is None else environ)
    settings = load_settings(
        config_path,
        cli_overrides={"action": "export"},
        environ=runtime_environ,
    )
    override_path = resolve_keyword_override_path(config_path, runtime_environ)
    override_exists = override_path is not None and override_path.exists()
    last_loaded_path = str(override_path if override_exists else config_path)
    keywords = {
        "core": tuple(settings.keywords.core),
        "supporting": tuple(settings.keywords.supporting),
        "exclude": tuple(settings.keywords.exclude),
    }
    keyword_counts = {
        "core": len(keywords["core"]),
        "supporting": len(keywords["supporting"]),
        "exclude": len(keywords["exclude"]),
        "total": len(keywords["core"]) + len(keywords["supporting"]) + len(keywords["exclude"]),
    }

    return OperatorKeywordsSnapshot(
        status="ready",
        config_path=str(config_path),
        override_path=_display_path(override_path),
        override_exists=override_exists,
        last_loaded_path=last_loaded_path,
        keyword_counts=keyword_counts,
        keywords=keywords,
    )


def build_unavailable_keywords_snapshot(
    config_path: Path,
    error_message: str,
) -> OperatorKeywordsSnapshot:
    """Fallback keyword payload when settings or override resolution fails."""

    return OperatorKeywordsSnapshot(
        status="error",
        config_path=str(config_path),
        override_path="not available",
        override_exists=False,
        last_loaded_path=str(config_path),
        keyword_counts={
            "core": 0,
            "supporting": 0,
            "exclude": 0,
            "total": 0,
        },
        keywords={
            "core": (),
            "supporting": (),
            "exclude": (),
        },
        error_message=error_message,
    )


def save_operator_supporting_keywords(
    *,
    config_path: Path,
    supporting_keywords: list[str] | tuple[str, ...],
    environ: dict[str, str] | None = None,
) -> OperatorKeywordsSnapshot:
    """Persist supporting keywords and return the refreshed operator snapshot."""

    save_supporting_keyword_override(
        config_path,
        supporting_keywords,
        environ=environ,
    )
    return load_operator_keywords_snapshot(
        config_path=config_path,
        environ=environ,
    )


def save_operator_core_keywords(
    *,
    config_path: Path,
    core_keywords: list[str] | tuple[str, ...],
    environ: dict[str, str] | None = None,
) -> OperatorKeywordsSnapshot:
    """Persist core keywords and return the refreshed operator snapshot."""

    save_core_keyword_override(
        config_path,
        core_keywords,
        environ=environ,
    )
    return load_operator_keywords_snapshot(
        config_path=config_path,
        environ=environ,
    )


def save_operator_exclude_keywords(
    *,
    config_path: Path,
    exclude_keywords: list[str] | tuple[str, ...],
    environ: dict[str, str] | None = None,
) -> OperatorKeywordsSnapshot:
    """Persist exclude keywords and return the refreshed operator snapshot."""

    save_exclude_keyword_override(
        config_path,
        exclude_keywords,
        environ=environ,
    )
    return load_operator_keywords_snapshot(
        config_path=config_path,
        environ=environ,
    )


def _display_path(path: Path | None) -> str:
    if path is None:
        return "not available"
    return str(path)
