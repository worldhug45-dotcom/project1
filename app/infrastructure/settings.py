"""Settings loading and validation for the MVP runtime."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ConfigurationError(ValueError):
    """Raised when settings cannot be loaded or validated."""


@dataclass(frozen=True, slots=True)
class AppSettings:
    name: str = "project1"
    env: str = "local"
    timezone: str = "Asia/Seoul"


@dataclass(frozen=True, slots=True)
class SourceSettings:
    enabled: bool = True
    endpoint: str = ""
    timeout_seconds: int = 10
    retry_count: int = 3
    retry_backoff_seconds: int = 2
    page_size: int = 20


@dataclass(frozen=True, slots=True)
class SourcesSettings:
    bizinfo: SourceSettings = field(default_factory=SourceSettings)
    g2b: SourceSettings = field(default_factory=SourceSettings)


@dataclass(frozen=True, slots=True)
class KeywordsSettings:
    core: tuple[str, ...] = ()
    supporting: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StorageSettings:
    type: str = "sqlite"
    database_path: Path = Path("data/notices.sqlite3")


@dataclass(frozen=True, slots=True)
class ExportSettings:
    output_dir: Path = Path("output")
    filename_pattern: str = "notices_{run_date}_{run_id}.xlsx"
    support_sheet_name: str = "support_notices"
    bid_sheet_name: str = "bid_notices"
    date_format: str = "%Y-%m-%d"


@dataclass(frozen=True, slots=True)
class LoggingSettings:
    level: str = "INFO"
    log_dir: Path = Path("logs")
    format: str = "jsonl"
    filename_pattern: str = "run_{run_date}.jsonl"


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    action: str = "all"
    mode: str = "normal"
    run_id_strategy: str = "timestamp_uuid"


@dataclass(frozen=True, slots=True)
class ValidationSettings:
    fail_fast: bool = True
    allow_unknown_keys: bool = False
    require_at_least_one_source: bool = True


@dataclass(frozen=True, slots=True)
class Settings:
    app: AppSettings = field(default_factory=AppSettings)
    sources: SourcesSettings = field(default_factory=SourcesSettings)
    keywords: KeywordsSettings = field(default_factory=KeywordsSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    runtime: RuntimeSettings = field(default_factory=RuntimeSettings)
    validation: ValidationSettings = field(default_factory=ValidationSettings)


def load_settings(
    config_path: Path | None = None,
    *,
    cli_overrides: dict[str, str] | None = None,
    environ: dict[str, str] | None = None,
) -> Settings:
    """Load settings using CLI > env > file > defaults precedence."""

    settings = Settings()
    if config_path and config_path.exists():
        settings = _merge_dict(settings, _read_toml(config_path))
    elif config_path and not config_path.exists():
        raise ConfigurationError(f"Config file does not exist: {config_path}")

    settings = _apply_env(settings, environ or os.environ)
    settings = _apply_cli(settings, cli_overrides or {})
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    errors: list[str] = []

    if settings.app.env not in {"local", "dev", "prod"}:
        errors.append("app.env must be one of: local, dev, prod.")
    if not _is_supported_timezone(settings.app.timezone):
        errors.append("app.timezone must be a valid timezone name.")

    enabled_sources = [
        ("sources.bizinfo", settings.sources.bizinfo),
        ("sources.g2b", settings.sources.g2b),
    ]
    if settings.validation.require_at_least_one_source and not any(
        source.enabled for _, source in enabled_sources
    ):
        errors.append("At least one source must be enabled.")

    if settings.runtime.action in {"collect", "all"}:
        for label, source in enabled_sources:
            if source.enabled and not source.endpoint.strip():
                errors.append(f"{label}.endpoint is required when the source is enabled.")

    for label, source in enabled_sources:
        if source.timeout_seconds < 1:
            errors.append(f"{label}.timeout_seconds must be greater than 0.")
        if source.retry_count < 0:
            errors.append(f"{label}.retry_count must be 0 or greater.")
        if source.page_size < 1:
            errors.append(f"{label}.page_size must be greater than 0.")

    if not settings.keywords.core:
        errors.append("keywords.core must not be empty.")
    if not settings.keywords.supporting:
        errors.append("keywords.supporting must not be empty.")
    if not settings.keywords.exclude:
        errors.append("keywords.exclude must not be empty.")
    if settings.storage.type != "sqlite":
        errors.append("storage.type currently supports only sqlite.")
    if not str(settings.storage.database_path).strip():
        errors.append("storage.database_path is required.")
    if not str(settings.export.output_dir).strip():
        errors.append("export.output_dir is required.")
    if settings.runtime.action not in {"collect", "export", "all"}:
        errors.append("runtime.action must be one of: collect, export, all.")
    if settings.runtime.mode not in {"normal", "dry_run"}:
        errors.append("runtime.mode must be one of: normal, dry_run.")
    if settings.logging.format not in {"jsonl", "text"}:
        errors.append("logging.format must be one of: jsonl, text.")

    if errors:
        raise ConfigurationError("\n".join(errors))


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def _is_supported_timezone(value: str) -> bool:
    try:
        ZoneInfo(value)
        return True
    except ZoneInfoNotFoundError:
        # Windows environments may not include the IANA timezone database.
        return value in {"Asia/Seoul", "UTC"}


def _merge_dict(settings: Settings, raw: dict[str, Any]) -> Settings:
    return replace(
        settings,
        app=_merge_app(settings.app, raw.get("app", {})),
        sources=_merge_sources(settings.sources, raw.get("sources", {})),
        keywords=_merge_keywords(settings.keywords, raw.get("keywords", {})),
        storage=_merge_storage(settings.storage, raw.get("storage", {})),
        export=_merge_export(settings.export, raw.get("export", {})),
        logging=_merge_logging(settings.logging, raw.get("logging", {})),
        runtime=_merge_runtime(settings.runtime, raw.get("runtime", {})),
        validation=_merge_validation(settings.validation, raw.get("validation", {})),
    )


def _merge_app(current: AppSettings, raw: dict[str, Any]) -> AppSettings:
    return replace(
        current,
        name=str(raw.get("name", current.name)),
        env=str(raw.get("env", current.env)),
        timezone=str(raw.get("timezone", current.timezone)),
    )


def _merge_source(current: SourceSettings, raw: dict[str, Any]) -> SourceSettings:
    return replace(
        current,
        enabled=_as_bool(raw.get("enabled", current.enabled)),
        endpoint=str(raw.get("endpoint", current.endpoint)),
        timeout_seconds=int(raw.get("timeout_seconds", current.timeout_seconds)),
        retry_count=int(raw.get("retry_count", current.retry_count)),
        retry_backoff_seconds=int(
            raw.get("retry_backoff_seconds", current.retry_backoff_seconds)
        ),
        page_size=int(raw.get("page_size", current.page_size)),
    )


def _merge_sources(current: SourcesSettings, raw: dict[str, Any]) -> SourcesSettings:
    return replace(
        current,
        bizinfo=_merge_source(current.bizinfo, raw.get("bizinfo", {})),
        g2b=_merge_source(current.g2b, raw.get("g2b", {})),
    )


def _merge_keywords(current: KeywordsSettings, raw: dict[str, Any]) -> KeywordsSettings:
    return replace(
        current,
        core=tuple(raw.get("core", current.core)),
        supporting=tuple(raw.get("supporting", current.supporting)),
        exclude=tuple(raw.get("exclude", current.exclude)),
    )


def _merge_storage(current: StorageSettings, raw: dict[str, Any]) -> StorageSettings:
    return replace(
        current,
        type=str(raw.get("type", current.type)),
        database_path=Path(raw.get("database_path", current.database_path)),
    )


def _merge_export(current: ExportSettings, raw: dict[str, Any]) -> ExportSettings:
    return replace(
        current,
        output_dir=Path(raw.get("output_dir", current.output_dir)),
        filename_pattern=str(raw.get("filename_pattern", current.filename_pattern)),
        support_sheet_name=str(raw.get("support_sheet_name", current.support_sheet_name)),
        bid_sheet_name=str(raw.get("bid_sheet_name", current.bid_sheet_name)),
        date_format=str(raw.get("date_format", current.date_format)),
    )


def _merge_logging(current: LoggingSettings, raw: dict[str, Any]) -> LoggingSettings:
    return replace(
        current,
        level=str(raw.get("level", current.level)),
        log_dir=Path(raw.get("log_dir", current.log_dir)),
        format=str(raw.get("format", current.format)),
        filename_pattern=str(raw.get("filename_pattern", current.filename_pattern)),
    )


def _merge_runtime(current: RuntimeSettings, raw: dict[str, Any]) -> RuntimeSettings:
    return replace(
        current,
        action=str(raw.get("action", current.action)),
        mode=str(raw.get("mode", current.mode)),
        run_id_strategy=str(raw.get("run_id_strategy", current.run_id_strategy)),
    )


def _merge_validation(
    current: ValidationSettings, raw: dict[str, Any]
) -> ValidationSettings:
    return replace(
        current,
        fail_fast=_as_bool(raw.get("fail_fast", current.fail_fast)),
        allow_unknown_keys=_as_bool(raw.get("allow_unknown_keys", current.allow_unknown_keys)),
        require_at_least_one_source=_as_bool(
            raw.get("require_at_least_one_source", current.require_at_least_one_source)
        ),
    )


def _apply_env(settings: Settings, environ: dict[str, str]) -> Settings:
    raw: dict[str, Any] = {}
    _set_if_present(raw, ("app", "env"), environ, "PROJECT1_APP_ENV")
    _set_if_present(raw, ("sources", "bizinfo", "enabled"), environ, "PROJECT1_SOURCES_BIZINFO_ENABLED")
    _set_if_present(raw, ("sources", "bizinfo", "endpoint"), environ, "PROJECT1_SOURCES_BIZINFO_ENDPOINT")
    _set_if_present(raw, ("sources", "g2b", "enabled"), environ, "PROJECT1_SOURCES_G2B_ENABLED")
    _set_if_present(raw, ("sources", "g2b", "endpoint"), environ, "PROJECT1_SOURCES_G2B_ENDPOINT")
    _set_if_present(raw, ("storage", "database_path"), environ, "PROJECT1_STORAGE_DATABASE_PATH")
    _set_if_present(raw, ("export", "output_dir"), environ, "PROJECT1_EXPORT_OUTPUT_DIR")
    _set_if_present(raw, ("logging", "level"), environ, "PROJECT1_LOGGING_LEVEL")
    _set_if_present(raw, ("runtime", "action"), environ, "PROJECT1_RUNTIME_ACTION")
    return _merge_dict(settings, raw)


def _apply_cli(settings: Settings, overrides: dict[str, str]) -> Settings:
    raw: dict[str, Any] = {}
    if action := overrides.get("action"):
        _assign_nested(raw, ("runtime", "action"), action)
    if mode := overrides.get("mode"):
        _assign_nested(raw, ("runtime", "mode"), mode)
    if env := overrides.get("env"):
        _assign_nested(raw, ("app", "env"), env)
    return _merge_dict(settings, raw)


def _set_if_present(
    raw: dict[str, Any],
    path: tuple[str, ...],
    environ: dict[str, str],
    key: str,
) -> None:
    if key in environ:
        _assign_nested(raw, path, environ[key])


def _assign_nested(raw: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    cursor = raw
    for part in path[:-1]:
        cursor = cursor.setdefault(part, {})
    cursor[path[-1]] = value


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)
