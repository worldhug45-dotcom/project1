"""Read-only keyword snapshot helpers for operator-facing web endpoints."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.infrastructure.local_env import build_runtime_environ
from app.infrastructure.settings import (
    ConfigurationError,
    load_settings,
    resolve_keyword_override_path,
    resolve_keyword_override_write_path,
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
    save_meta: OperatorKeywordSaveMeta
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "config_path": self.config_path,
            "override_path": self.override_path,
            "override_exists": self.override_exists,
            "last_loaded_path": self.last_loaded_path,
            "keyword_counts": dict(self.keyword_counts),
            "keywords": {key: list(values) for key, values in self.keywords.items()},
            "save_meta": self.save_meta.to_dict(),
            "error_message": self.error_message,
        }


@dataclass(frozen=True, slots=True)
class OperatorKeywordSaveMeta:
    """Persisted keyword-save metadata shown in the operator dashboard."""

    status: str
    saved_at: str
    target_path: str
    changed_group: str
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "saved_at": self.saved_at,
            "target_path": self.target_path,
            "changed_group": self.changed_group,
            "error_message": self.error_message,
        }


def load_operator_keywords_snapshot(
    *,
    config_path: Path,
    environ: dict[str, str] | None = None,
) -> OperatorKeywordsSnapshot:
    runtime_environ = build_runtime_environ(environ, config_path=config_path)
    settings = load_settings(
        config_path,
        cli_overrides={"action": "export"},
        environ=runtime_environ,
    )
    override_path = resolve_keyword_override_path(config_path, runtime_environ)
    override_write_path = resolve_keyword_override_write_path(
        config_path,
        runtime_environ,
    )
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
        save_meta=_load_keyword_save_meta(override_write_path),
    )


def build_unavailable_keywords_snapshot(
    config_path: Path,
    error_message: str,
) -> OperatorKeywordsSnapshot:
    """Fallback keyword payload when settings or override resolution fails."""

    fallback_target_path = _safe_resolve_keyword_override_write_path(config_path)

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
        save_meta=_default_keyword_save_meta(fallback_target_path),
        error_message=error_message,
    )


def save_operator_supporting_keywords(
    *,
    config_path: Path,
    supporting_keywords: list[str] | tuple[str, ...],
    environ: dict[str, str] | None = None,
) -> OperatorKeywordsSnapshot:
    """Persist supporting keywords and return the refreshed operator snapshot."""
    return _save_operator_keywords(
        changed_group="supporting",
        config_path=config_path,
        keywords=supporting_keywords,
        save_func=save_supporting_keyword_override,
        environ=environ,
    )


def save_operator_core_keywords(
    *,
    config_path: Path,
    core_keywords: list[str] | tuple[str, ...],
    environ: dict[str, str] | None = None,
) -> OperatorKeywordsSnapshot:
    """Persist core keywords and return the refreshed operator snapshot."""
    return _save_operator_keywords(
        changed_group="core",
        config_path=config_path,
        keywords=core_keywords,
        save_func=save_core_keyword_override,
        environ=environ,
    )


def save_operator_exclude_keywords(
    *,
    config_path: Path,
    exclude_keywords: list[str] | tuple[str, ...],
    environ: dict[str, str] | None = None,
) -> OperatorKeywordsSnapshot:
    """Persist exclude keywords and return the refreshed operator snapshot."""
    return _save_operator_keywords(
        changed_group="exclude",
        config_path=config_path,
        keywords=exclude_keywords,
        save_func=save_exclude_keyword_override,
        environ=environ,
    )


def _display_path(path: Path | None) -> str:
    if path is None:
        return "not available"
    return str(path)


def _save_operator_keywords(
    *,
    changed_group: str,
    config_path: Path,
    keywords: list[str] | tuple[str, ...],
    save_func: Callable[..., Path],
    environ: dict[str, str] | None = None,
) -> OperatorKeywordsSnapshot:
    runtime_environ = build_runtime_environ(environ, config_path=config_path)
    target_path = _safe_resolve_keyword_override_write_path(
        config_path,
        runtime_environ,
    )

    try:
        saved_path = save_func(
            config_path,
            keywords,
            environ=runtime_environ,
        )
    except ConfigurationError as exc:
        if target_path is not None:
            _persist_keyword_save_meta(
                target_path,
                status="failed",
                changed_group=changed_group,
                error_message=str(exc),
            )
        raise
    except Exception:
        if target_path is not None:
            _persist_keyword_save_meta(
                target_path,
                status="failed",
                changed_group=changed_group,
                error_message="Keyword save failed.",
            )
        raise

    _persist_keyword_save_meta(
        saved_path,
        status="success",
        changed_group=changed_group,
    )
    return load_operator_keywords_snapshot(
        config_path=config_path,
        environ=runtime_environ,
    )


def _load_keyword_save_meta(override_path: Path) -> OperatorKeywordSaveMeta:
    meta_path = _keyword_save_meta_path(override_path)
    if not meta_path.exists():
        return _default_keyword_save_meta(override_path)

    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return OperatorKeywordSaveMeta(
            status="error",
            saved_at="not available",
            target_path=str(override_path),
            changed_group="not available",
            error_message="Keyword save metadata could not be loaded.",
        )

    if not isinstance(payload, dict):
        return OperatorKeywordSaveMeta(
            status="error",
            saved_at="not available",
            target_path=str(override_path),
            changed_group="not available",
            error_message="Keyword save metadata could not be loaded.",
        )

    return OperatorKeywordSaveMeta(
        status=str(payload.get("status") or "not_available"),
        saved_at=str(payload.get("saved_at") or "not available"),
        target_path=str(payload.get("target_path") or override_path),
        changed_group=str(payload.get("changed_group") or "not available"),
        error_message=(str(payload["error_message"]) if payload.get("error_message") else None),
    )


def _persist_keyword_save_meta(
    override_path: Path,
    *,
    status: str,
    changed_group: str,
    error_message: str | None = None,
) -> None:
    meta = OperatorKeywordSaveMeta(
        status=status,
        saved_at=_now_isoformat(),
        target_path=str(override_path),
        changed_group=changed_group,
        error_message=error_message,
    )
    meta_path = _keyword_save_meta_path(override_path)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(meta.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _default_keyword_save_meta(override_path: Path | None) -> OperatorKeywordSaveMeta:
    return OperatorKeywordSaveMeta(
        status="not_available",
        saved_at="not available",
        target_path=_display_path(override_path),
        changed_group="not available",
    )


def _keyword_save_meta_path(override_path: Path) -> Path:
    return override_path.with_suffix(".meta.json")


def _safe_resolve_keyword_override_write_path(
    config_path: Path,
    environ: dict[str, str] | None = None,
) -> Path | None:
    try:
        return resolve_keyword_override_write_path(
            config_path,
            environ,
        )
    except ConfigurationError:
        return None


def _now_isoformat() -> str:
    return datetime.now(timezone.utc).isoformat()
