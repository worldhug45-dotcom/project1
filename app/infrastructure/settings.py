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


BIZINFO_CERT_KEY_ENV_VAR = "PROJECT1_BIZINFO_CERT_KEY"
G2B_API_KEY_ENV_VAR = "PROJECT1_G2B_API_KEY"
KEYWORDS_OVERRIDE_PATH_ENV_VAR = "PROJECT1_KEYWORDS_OVERRIDE_PATH"
DEFAULT_KEYWORDS_OVERRIDE_FILENAME = "keywords.override.toml"


@dataclass(frozen=True, slots=True)
class AppSettings:
    name: str = "project1"
    env: str = "local"
    timezone: str = "Asia/Seoul"


@dataclass(frozen=True, slots=True)
class SourceSettings:
    enabled: bool = True
    endpoint: str = ""
    fixture_path: Path = Path("")
    cert_key: str = field(default="", repr=False)
    timeout_seconds: int = 10
    retry_count: int = 3
    retry_backoff_seconds: int = 2
    page_size: int = 20
    inquiry_division: str = "1"
    inquiry_window_days: int = 7


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
    source_mode: str = "api"
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

    environment = environ or os.environ
    settings = Settings()
    if config_path and config_path.exists():
        settings = _merge_dict(settings, _read_toml(config_path))
    elif config_path and not config_path.exists():
        raise ConfigurationError(f"Config file does not exist: {config_path}")

    keyword_override_path = resolve_keyword_override_path(config_path, environment)
    if keyword_override_path is not None:
        settings = _apply_keyword_override_file(settings, keyword_override_path)

    settings = _apply_env(settings, environment)
    settings = _apply_cli(settings, cli_overrides or {})
    validate_settings(settings)
    return settings


def resolve_keyword_override_path(
    config_path: Path | None = None,
    environ: dict[str, str] | None = None,
) -> Path | None:
    """Return the user keyword override file when it exists."""

    environment = environ or os.environ
    if KEYWORDS_OVERRIDE_PATH_ENV_VAR in environment:
        override_path = Path(environment[KEYWORDS_OVERRIDE_PATH_ENV_VAR])
        if not override_path.exists():
            raise ConfigurationError(
                f"Keyword override file does not exist: {override_path}"
            )
        return override_path

    if config_path is not None:
        candidate = config_path.with_name(DEFAULT_KEYWORDS_OVERRIDE_FILENAME)
        if candidate.exists():
            return candidate

    default_candidate = Path("config") / DEFAULT_KEYWORDS_OVERRIDE_FILENAME
    if default_candidate.exists():
        return default_candidate
    return None


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

    if settings.runtime.action in {"collect", "all"} and settings.runtime.source_mode == "api":
        for label, source in enabled_sources:
            if source.enabled and not source.endpoint.strip():
                errors.append(f"{label}.endpoint is required when the source is enabled.")
        if settings.sources.bizinfo.enabled and not settings.sources.bizinfo.cert_key.strip():
            errors.append(
                f"sources.bizinfo.cert_key must be provided via {BIZINFO_CERT_KEY_ENV_VAR} in api source mode."
            )
        if settings.sources.g2b.enabled and not settings.sources.g2b.cert_key.strip():
            errors.append(
                f"sources.g2b.cert_key must be provided via {G2B_API_KEY_ENV_VAR} in api source mode."
            )
    if settings.runtime.action in {"collect", "all"} and settings.runtime.source_mode == "fixture":
        for label, source in enabled_sources:
            if not source.enabled:
                continue
            if not str(source.fixture_path).strip():
                errors.append(f"{label}.fixture_path is required in fixture source mode.")
            elif not source.fixture_path.exists():
                errors.append(f"{label}.fixture_path does not exist: {source.fixture_path}")

    for label, source in enabled_sources:
        if source.timeout_seconds < 1:
            errors.append(f"{label}.timeout_seconds must be greater than 0.")
        if source.retry_count < 0:
            errors.append(f"{label}.retry_count must be 0 or greater.")
        if source.page_size < 1:
            errors.append(f"{label}.page_size must be greater than 0.")
        if source.inquiry_window_days < 0:
            errors.append(f"{label}.inquiry_window_days must be 0 or greater.")

    if settings.sources.g2b.enabled and settings.sources.g2b.inquiry_division not in {"1", "3"}:
        errors.append("sources.g2b.inquiry_division currently supports only '1' or '3'.")

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
    if settings.runtime.source_mode not in {"api", "fixture"}:
        errors.append("runtime.source_mode must be one of: api, fixture.")
    if settings.logging.format not in {"jsonl", "text"}:
        errors.append("logging.format must be one of: jsonl, text.")

    if errors:
        raise ConfigurationError("\n".join(errors))


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def _apply_keyword_override_file(settings: Settings, path: Path) -> Settings:
    raw = _read_toml(path)
    override_raw = raw.get("keywords_override", {})
    if not isinstance(override_raw, dict):
        raise ConfigurationError("keywords_override must be a TOML table.")

    return replace(
        settings,
        keywords=_merge_keywords_override(settings.keywords, override_raw),
    )


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
        fixture_path=Path(raw.get("fixture_path", current.fixture_path)),
        timeout_seconds=int(raw.get("timeout_seconds", current.timeout_seconds)),
        retry_count=int(raw.get("retry_count", current.retry_count)),
        retry_backoff_seconds=int(
            raw.get("retry_backoff_seconds", current.retry_backoff_seconds)
        ),
        page_size=int(raw.get("page_size", current.page_size)),
        inquiry_division=str(raw.get("inquiry_division", current.inquiry_division)),
        inquiry_window_days=int(
            raw.get("inquiry_window_days", current.inquiry_window_days)
        ),
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


def _merge_keywords_override(
    current: KeywordsSettings,
    raw: dict[str, Any],
) -> KeywordsSettings:
    add_core = _keyword_list(raw.get("add_core", []))
    add_supporting = _keyword_list(raw.get("add_supporting", []))
    add_exclude = _keyword_list(raw.get("add_exclude", []))
    remove_core = _keyword_list(raw.get("remove_core", []))
    remove_supporting = _keyword_list(raw.get("remove_supporting", []))
    remove_exclude = _keyword_list(raw.get("remove_exclude", []))

    return replace(
        current,
        core=_remove_keywords(_append_keywords(current.core, add_core), remove_core),
        supporting=_remove_keywords(
            _append_keywords(current.supporting, add_supporting),
            remove_supporting,
        ),
        exclude=_remove_keywords(_append_keywords(current.exclude, add_exclude), remove_exclude),
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
        source_mode=str(raw.get("source_mode", current.source_mode)),
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
    _set_if_present(raw, ("sources", "bizinfo", "fixture_path"), environ, "PROJECT1_SOURCES_BIZINFO_FIXTURE_PATH")
    _set_if_present(raw, ("sources", "g2b", "enabled"), environ, "PROJECT1_SOURCES_G2B_ENABLED")
    _set_if_present(raw, ("sources", "g2b", "endpoint"), environ, "PROJECT1_SOURCES_G2B_ENDPOINT")
    _set_if_present(raw, ("sources", "g2b", "fixture_path"), environ, "PROJECT1_SOURCES_G2B_FIXTURE_PATH")
    _set_if_present(raw, ("sources", "g2b", "inquiry_division"), environ, "PROJECT1_SOURCES_G2B_INQUIRY_DIVISION")
    _set_if_present(raw, ("sources", "g2b", "inquiry_window_days"), environ, "PROJECT1_SOURCES_G2B_INQUIRY_WINDOW_DAYS")
    _set_if_present(raw, ("storage", "database_path"), environ, "PROJECT1_STORAGE_DATABASE_PATH")
    _set_if_present(raw, ("export", "output_dir"), environ, "PROJECT1_EXPORT_OUTPUT_DIR")
    _set_if_present(raw, ("logging", "level"), environ, "PROJECT1_LOGGING_LEVEL")
    _set_if_present(raw, ("runtime", "action"), environ, "PROJECT1_RUNTIME_ACTION")
    _set_if_present(raw, ("runtime", "source_mode"), environ, "PROJECT1_RUNTIME_SOURCE_MODE")
    settings = _merge_dict(settings, raw)
    if BIZINFO_CERT_KEY_ENV_VAR in environ:
        settings = replace(
            settings,
            sources=replace(
                settings.sources,
                bizinfo=replace(
                    settings.sources.bizinfo,
                    cert_key=environ[BIZINFO_CERT_KEY_ENV_VAR],
                ),
            ),
        )
    if G2B_API_KEY_ENV_VAR in environ:
        settings = replace(
            settings,
            sources=replace(
                settings.sources,
                g2b=replace(
                    settings.sources.g2b,
                    cert_key=environ[G2B_API_KEY_ENV_VAR],
                ),
            ),
        )
    return settings


def _apply_cli(settings: Settings, overrides: dict[str, str]) -> Settings:
    raw: dict[str, Any] = {}
    if action := overrides.get("action"):
        _assign_nested(raw, ("runtime", "action"), action)
    if mode := overrides.get("mode"):
        _assign_nested(raw, ("runtime", "mode"), mode)
    if source_mode := overrides.get("source_mode"):
        _assign_nested(raw, ("runtime", "source_mode"), source_mode)
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


def _keyword_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ConfigurationError("Keyword override values must be arrays of strings.")
    return tuple(_normalize_keyword(item) for item in value if _normalize_keyword(item))


def _append_keywords(base: tuple[str, ...], additions: tuple[str, ...]) -> tuple[str, ...]:
    values = list(base)
    existing = {item.casefold() for item in base}
    for keyword in additions:
        key = keyword.casefold()
        if key in existing:
            continue
        values.append(keyword)
        existing.add(key)
    return tuple(values)


def _remove_keywords(base: tuple[str, ...], removals: tuple[str, ...]) -> tuple[str, ...]:
    removal_keys = {keyword.casefold() for keyword in removals}
    if not removal_keys:
        return base
    return tuple(keyword for keyword in base if keyword.casefold() not in removal_keys)


def _normalize_keyword(value: Any) -> str:
    return str(value).strip()
