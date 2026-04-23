from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.infrastructure.local_env import build_runtime_environ
from app.infrastructure.settings import (
    BIZINFO_CERT_KEY_ENV_VAR,
    G2B_API_KEY_ENV_VAR,
    ConfigurationError,
    load_settings,
    resolve_settings_override_path,
    resolve_settings_override_write_path,
    save_settings_override,
)


_ENV_VAR_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_SOURCE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
_SETTINGS_META_FILENAME = "settings.operator.meta.json"
_SUPPORTED_EXTRA_SOURCE_TYPES = {"api", "rss", "html", "file"}
_SUPPORTED_EXTRA_AUTH_TYPES = {"none", "api_key", "bearer", "cookie"}


@dataclass(frozen=True, slots=True)
class OperatorManagedSource:
    key: str
    display_name: str
    enabled: bool
    endpoint: str
    fixture_path: str
    api_key_env_var: str
    api_key_configured: bool
    api_key_masked: str

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "enabled": self.enabled,
            "endpoint": self.endpoint,
            "fixture_path": self.fixture_path,
            "api_key_env_var": self.api_key_env_var,
            "api_key_configured": self.api_key_configured,
            "api_key_masked": self.api_key_masked,
        }


@dataclass(frozen=True, slots=True)
class OperatorExtraSource:
    source_id: str
    display_name: str
    source_type: str
    base_url: str
    auth_type: str
    env_var_name: str
    description: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "display_name": self.display_name,
            "source_type": self.source_type,
            "base_url": self.base_url,
            "auth_type": self.auth_type,
            "env_var_name": self.env_var_name,
            "description": self.description,
            # Legacy aliases keep older dashboard/tests compatible while the
            # registry moves to the new explicit source metadata contract.
            "name": self.display_name,
            "endpoint": self.base_url,
            "api_key_env_var": self.env_var_name,
            "enabled": False,
        }


@dataclass(frozen=True, slots=True)
class OperatorSettingsSaveMeta:
    status: str
    saved_at: str
    target_path: str
    changed_section: str
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "saved_at": self.saved_at,
            "target_path": self.target_path,
            "changed_section": self.changed_section,
            "error_message": self.error_message,
        }


@dataclass(frozen=True, slots=True)
class OperatorSettingsSnapshot:
    status: str
    config_path: str
    override_path: str
    override_exists: bool
    env_local_path: str
    env_local_exists: bool
    current_source_mode: str
    sources: dict[str, OperatorManagedSource]
    extra_sources: tuple[OperatorExtraSource, ...]
    save_meta: OperatorSettingsSaveMeta
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "config_path": self.config_path,
            "override_path": self.override_path,
            "override_exists": self.override_exists,
            "env_local_path": self.env_local_path,
            "env_local_exists": self.env_local_exists,
            "current_source_mode": self.current_source_mode,
            "sources": {key: value.to_dict() for key, value in self.sources.items()},
            "extra_sources": [item.to_dict() for item in self.extra_sources],
            "save_meta": self.save_meta.to_dict(),
            "error_message": self.error_message,
        }


def load_operator_settings_snapshot(
    *,
    config_path: Path,
    environ: Mapping[str, str] | None = None,
) -> OperatorSettingsSnapshot:
    runtime_environ = build_runtime_environ(environ, config_path=config_path)
    settings = load_settings(
        config_path,
        cli_overrides={"action": "export"},
        environ=runtime_environ,
    )
    loaded_override_path = resolve_settings_override_path(config_path, runtime_environ)
    write_override_path = resolve_settings_override_write_path(config_path, runtime_environ)
    env_local_path = _resolve_env_local_path(config_path)

    sources = {
        "bizinfo": OperatorManagedSource(
            key="bizinfo",
            display_name="기업마당",
            enabled=settings.sources.bizinfo.enabled,
            endpoint=settings.sources.bizinfo.endpoint,
            fixture_path=str(settings.sources.bizinfo.fixture_path),
            api_key_env_var=BIZINFO_CERT_KEY_ENV_VAR,
            api_key_configured=bool(runtime_environ.get(BIZINFO_CERT_KEY_ENV_VAR, "").strip()),
            api_key_masked=_mask_secret(runtime_environ.get(BIZINFO_CERT_KEY_ENV_VAR, "")),
        ),
        "g2b": OperatorManagedSource(
            key="g2b",
            display_name="나라장터",
            enabled=settings.sources.g2b.enabled,
            endpoint=settings.sources.g2b.endpoint,
            fixture_path=str(settings.sources.g2b.fixture_path),
            api_key_env_var=G2B_API_KEY_ENV_VAR,
            api_key_configured=bool(runtime_environ.get(G2B_API_KEY_ENV_VAR, "").strip()),
            api_key_masked=_mask_secret(runtime_environ.get(G2B_API_KEY_ENV_VAR, "")),
        ),
    }

    return OperatorSettingsSnapshot(
        status="ready",
        config_path=str(config_path),
        override_path=str(write_override_path),
        override_exists=loaded_override_path is not None and loaded_override_path.exists(),
        env_local_path=str(env_local_path),
        env_local_exists=env_local_path.exists(),
        current_source_mode=settings.runtime.source_mode,
        sources=sources,
        extra_sources=_load_extra_sources(write_override_path),
        save_meta=_load_settings_save_meta(config_path, write_override_path),
    )


def build_unavailable_settings_snapshot(
    config_path: Path,
    error_message: str,
) -> OperatorSettingsSnapshot:
    override_path = _safe_resolve_override_path(config_path)
    env_local_path = _resolve_env_local_path(config_path)
    return OperatorSettingsSnapshot(
        status="error",
        config_path=str(config_path),
        override_path=str(override_path),
        override_exists=override_path.exists(),
        env_local_path=str(env_local_path),
        env_local_exists=env_local_path.exists(),
        current_source_mode="not_available",
        sources={
            "bizinfo": OperatorManagedSource(
                key="bizinfo",
                display_name="기업마당",
                enabled=False,
                endpoint="not available",
                fixture_path="not available",
                api_key_env_var=BIZINFO_CERT_KEY_ENV_VAR,
                api_key_configured=False,
                api_key_masked="not configured",
            ),
            "g2b": OperatorManagedSource(
                key="g2b",
                display_name="나라장터",
                enabled=False,
                endpoint="not available",
                fixture_path="not available",
                api_key_env_var=G2B_API_KEY_ENV_VAR,
                api_key_configured=False,
                api_key_masked="not configured",
            ),
        },
        extra_sources=(),
        save_meta=_default_settings_save_meta(override_path),
        error_message=error_message,
    )


def save_operator_sources(
    *,
    config_path: Path,
    source_overrides: Mapping[str, Mapping[str, object]],
    source_mode: str | None = None,
    extra_sources: Sequence[Mapping[str, object]] | None = None,
    environ: Mapping[str, str] | None = None,
) -> OperatorSettingsSnapshot:
    runtime_environ = build_runtime_environ(environ, config_path=config_path)
    target_path = resolve_settings_override_write_path(config_path, runtime_environ)

    try:
        normalized_sources = _normalize_source_overrides(source_overrides)
        normalized_source_mode = _normalize_source_mode(source_mode)
        normalized_extra_sources = _normalize_extra_sources(extra_sources or [])
        saved_path = save_settings_override(
            config_path,
            source_overrides=normalized_sources,
            source_mode=normalized_source_mode,
            extra_sources=normalized_extra_sources,
            environ=runtime_environ,
        )
    except ConfigurationError as exc:
        _persist_settings_save_meta(
            config_path,
            target_path=target_path,
            status="failed",
            changed_section="sources",
            error_message=str(exc),
        )
        raise
    except Exception:
        _persist_settings_save_meta(
            config_path,
            target_path=target_path,
            status="failed",
            changed_section="sources",
            error_message="Source settings could not be saved.",
        )
        raise

    _persist_settings_save_meta(
        config_path,
        target_path=saved_path,
        status="success",
        changed_section="sources",
    )
    return load_operator_settings_snapshot(
        config_path=config_path,
        environ=runtime_environ,
    )


def save_operator_api_keys(
    *,
    config_path: Path,
    bizinfo_api_key: str | None = None,
    g2b_api_key: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> OperatorSettingsSnapshot:
    runtime_environ = build_runtime_environ(environ, config_path=config_path)
    env_local_path = _resolve_env_local_path(config_path)

    try:
        env_payload = _read_env_payload(env_local_path)
        updates: dict[str, str] = {}
        for key_name, raw_value in (
            (BIZINFO_CERT_KEY_ENV_VAR, bizinfo_api_key),
            (G2B_API_KEY_ENV_VAR, g2b_api_key),
        ):
            normalized = str(raw_value or "").strip()
            if not normalized:
                continue
            if any(character in normalized for character in ("\n", "\r")):
                raise ConfigurationError(f"{key_name} must be provided as a single-line value.")
            updates[key_name] = normalized

        if not updates:
            raise ConfigurationError("At least one API key value must be provided.")

        env_payload.update(updates)
        _write_env_payload(env_local_path, env_payload)
    except ConfigurationError as exc:
        _persist_settings_save_meta(
            config_path,
            target_path=env_local_path,
            status="failed",
            changed_section="api_keys",
            error_message=str(exc),
        )
        raise
    except Exception:
        _persist_settings_save_meta(
            config_path,
            target_path=env_local_path,
            status="failed",
            changed_section="api_keys",
            error_message="API key settings could not be saved.",
        )
        raise

    _persist_settings_save_meta(
        config_path,
        target_path=env_local_path,
        status="success",
        changed_section="api_keys",
    )
    return load_operator_settings_snapshot(
        config_path=config_path,
        environ=runtime_environ,
    )


def _normalize_source_overrides(
    source_overrides: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    normalized: dict[str, dict[str, object]] = {}
    for source_key in ("bizinfo", "g2b"):
        raw = source_overrides.get(source_key, {})
        if not isinstance(raw, Mapping):
            raise ConfigurationError(f"sources.{source_key} must be an object.")
        normalized[source_key] = {"enabled": _as_bool(raw.get("enabled", False))}

    if not any(item["enabled"] for item in normalized.values()):
        raise ConfigurationError("At least one built-in source must remain enabled.")
    if sum(1 for item in normalized.values() if item["enabled"]) > 1:
        raise ConfigurationError(
            "Collect currently supports one enabled source at a time. Enable either Bizinfo or G2B."
        )
    return normalized


def _normalize_source_mode(source_mode: str | None) -> str | None:
    if source_mode is None:
        return None
    normalized = str(source_mode).strip().lower()
    if normalized not in {"api", "fixture"}:
        raise ConfigurationError("runtime.source_mode must be one of: api, fixture.")
    return normalized


def _normalize_extra_sources(
    extra_sources: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    for index, item in enumerate(extra_sources):
        if not isinstance(item, Mapping):
            raise ConfigurationError(f"extra_sources[{index}] must be an object.")

        display_name = str(item.get("display_name") or item.get("name") or "").strip()
        source_id = str(item.get("source_id") or _slugify_source_id(display_name)).strip().lower()
        source_type = str(item.get("source_type") or "api").strip().lower()
        base_url = str(item.get("base_url") or item.get("endpoint") or "").strip()
        auth_type = str(item.get("auth_type") or "api_key").strip().lower()
        env_var_name = (
            str(item.get("env_var_name") or item.get("api_key_env_var") or "").strip().upper()
        )
        description = str(item.get("description") or item.get("notes") or "").strip()

        if not source_id:
            raise ConfigurationError(f"extra_sources[{index}].source_id is required.")
        if source_id in {"bizinfo", "g2b"}:
            raise ConfigurationError(
                f"extra_sources[{index}].source_id must not use a built-in source id."
            )
        if not _SOURCE_ID_PATTERN.match(source_id):
            raise ConfigurationError(
                f"extra_sources[{index}].source_id must use lowercase letters, numbers, '-' or '_'."
            )
        if not display_name:
            raise ConfigurationError(f"extra_sources[{index}].display_name is required.")
        if source_type not in _SUPPORTED_EXTRA_SOURCE_TYPES:
            raise ConfigurationError(
                f"extra_sources[{index}].source_type must be one of: api, rss, html, file."
            )
        if not base_url:
            raise ConfigurationError(f"extra_sources[{index}].base_url is required.")
        if auth_type not in _SUPPORTED_EXTRA_AUTH_TYPES:
            raise ConfigurationError(
                f"extra_sources[{index}].auth_type must be one of: none, api_key, bearer, cookie."
            )
        if env_var_name and not _ENV_VAR_PATTERN.match(env_var_name):
            raise ConfigurationError(
                f"extra_sources[{index}].env_var_name must look like an environment variable name."
            )

        dedup_key = source_id.casefold()
        if dedup_key in seen_ids:
            raise ConfigurationError(f"extra source_id '{source_id}' is duplicated.")
        seen_ids.add(dedup_key)

        normalized.append(
            {
                "source_id": source_id,
                "display_name": display_name,
                "source_type": source_type,
                "base_url": base_url,
                "auth_type": auth_type,
                "env_var_name": env_var_name,
                "description": description,
            }
        )

    return normalized


def _load_extra_sources(path: Path) -> tuple[OperatorExtraSource, ...]:
    if not path.exists():
        return ()
    try:
        with path.open("rb") as file:
            raw = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        return ()

    extra_sources = raw.get("extra_sources", [])
    if not isinstance(extra_sources, list):
        return ()

    loaded: list[OperatorExtraSource] = []
    for item in extra_sources:
        if not isinstance(item, dict):
            continue
        display_name = str(item.get("display_name") or item.get("name") or "").strip()
        loaded.append(
            OperatorExtraSource(
                source_id=str(item.get("source_id") or _slugify_source_id(display_name)).strip(),
                display_name=display_name,
                source_type=str(item.get("source_type") or "api").strip(),
                base_url=str(item.get("base_url") or item.get("endpoint") or "").strip(),
                auth_type=str(item.get("auth_type") or "api_key").strip(),
                env_var_name=str(
                    item.get("env_var_name") or item.get("api_key_env_var") or ""
                ).strip(),
                description=str(item.get("description", "")).strip(),
            )
        )
    return tuple(loaded)


def _resolve_env_local_path(config_path: Path) -> Path:
    if config_path.parent:
        return config_path.parent / ".env.local"
    return Path(".env.local")


def _read_env_payload(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        payload[key] = _strip_env_quotes(value.strip())
    return payload


def _write_env_payload(path: Path, payload: Mapping[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Operator-managed local environment values.",
        "# Sensitive values are stored here so runtime loading can reuse config/.env.local.",
    ]
    for key in sorted(payload):
        value = str(payload[key]).strip()
        if not value:
            continue
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _strip_env_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _mask_secret(value: str) -> str:
    secret = str(value or "").strip()
    if not secret:
        return "not configured"
    if len(secret) <= 4:
        return "*" * len(secret)
    if len(secret) <= 8:
        return f"{secret[:2]}{'*' * (len(secret) - 4)}{secret[-2:]}"
    return f"{secret[:3]}{'*' * (len(secret) - 5)}{secret[-2:]}"


def _load_settings_save_meta(
    config_path: Path,
    override_path: Path,
) -> OperatorSettingsSaveMeta:
    meta_path = _settings_save_meta_path(config_path)
    if not meta_path.exists():
        return _default_settings_save_meta(override_path)

    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return OperatorSettingsSaveMeta(
            status="error",
            saved_at="not available",
            target_path=str(override_path),
            changed_section="not_available",
            error_message="Settings save metadata could not be loaded.",
        )

    if not isinstance(payload, dict):
        return _default_settings_save_meta(override_path)

    return OperatorSettingsSaveMeta(
        status=str(payload.get("status") or "not_available"),
        saved_at=str(payload.get("saved_at") or "not available"),
        target_path=str(payload.get("target_path") or override_path),
        changed_section=str(payload.get("changed_section") or "not_available"),
        error_message=(str(payload["error_message"]) if payload.get("error_message") else None),
    )


def _persist_settings_save_meta(
    config_path: Path,
    *,
    target_path: Path,
    status: str,
    changed_section: str,
    error_message: str | None = None,
) -> None:
    meta = OperatorSettingsSaveMeta(
        status=status,
        saved_at=_now_isoformat(),
        target_path=str(target_path),
        changed_section=changed_section,
        error_message=error_message,
    )
    meta_path = _settings_save_meta_path(config_path)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(meta.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _default_settings_save_meta(target_path: Path) -> OperatorSettingsSaveMeta:
    return OperatorSettingsSaveMeta(
        status="not_available",
        saved_at="not available",
        target_path=str(target_path),
        changed_section="not_available",
    )


def _settings_save_meta_path(config_path: Path) -> Path:
    return config_path.with_name(_SETTINGS_META_FILENAME)


def _safe_resolve_override_path(config_path: Path) -> Path:
    try:
        return resolve_settings_override_write_path(config_path)
    except ConfigurationError:
        return config_path.with_name("settings.override.toml")


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _slugify_source_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_-]+", "_", value.strip().lower())
    normalized = normalized.strip("_-")
    if normalized and normalized[0].isdigit():
        return f"source_{normalized}"
    return normalized


def _now_isoformat() -> str:
    return datetime.now(timezone.utc).isoformat()
