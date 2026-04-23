"""Command line entry point for the first MVP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.application import (
    DefaultCollectNoticesUseCase,
    DefaultExportNoticesUseCase,
    RunSummary,
)
from app.exporters import XlsxExcelExporter
from app.filters import KeywordSet
from app.infrastructure.settings import ConfigurationError, Settings, load_settings
from app.normalizers import BizinfoNoticeNormalizer, G2BNoticeNormalizer
from app.ops import (
    ConfigurationAppError,
    ConsoleLogSink,
    LogEvent,
    LogEventType,
    RunStatus,
    classify_exception,
    create_run_id,
)
from app.persistence import SQLiteNoticeRepository
from app.sources import (
    BizinfoApiHttpClient,
    BizinfoFixtureSourceAdapter,
    BizinfoSourceAdapter,
    G2BApiHttpClient,
    G2BFixtureSourceAdapter,
    G2BSourceAdapter,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project1",
        description="AI, infrastructure, SI opportunity notice collector MVP.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to a TOML settings file. Defaults are used when omitted.",
    )
    parser.add_argument(
        "--env",
        choices=["local", "dev", "prod"],
        default=None,
        help="Runtime environment override.",
    )
    parser.add_argument(
        "--action",
        choices=["collect", "export", "all"],
        default=None,
        help="Runtime action override.",
    )
    parser.add_argument(
        "--mode",
        choices=["normal", "dry_run"],
        default=None,
        help="Runtime mode override.",
    )
    parser.add_argument(
        "--source-mode",
        choices=["api", "fixture"],
        default=None,
        help="Notice source mode override. Fixture mode uses local sample responses.",
    )
    parser.add_argument(
        "--collect-diagnostics",
        action="store_true",
        help="Emit per-notice collect diagnostics for keyword eligibility and skipped reasons.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_id = create_run_id()
    sink = ConsoleLogSink()

    overrides = {
        key: value
        for key, value in {
            "action": args.action,
            "mode": args.mode,
            "source_mode": args.source_mode,
            "env": args.env,
        }.items()
        if value is not None
    }
    requested_action = args.action or "all"

    sink.emit(
        LogEvent(
            run_id=run_id,
            event_type=LogEventType.RUN_STARTED,
            action=requested_action,
            status=RunStatus.RUNNING,
        )
    )

    try:
        settings = load_settings(args.config, cli_overrides=overrides)
    except ConfigurationError as exc:
        error = ConfigurationAppError(str(exc)).to_error_info()
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.ERROR,
                action=requested_action,
                status=RunStatus.FAILED,
                error=error,
            )
        )
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.RUN_FINISHED,
                action=requested_action,
                status=RunStatus.FAILED,
                error=error,
            )
        )
        parser.exit(status=2, message=f"Configuration error:\n{exc}\n")
    except Exception as exc:
        error = classify_exception(exc)
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.ERROR,
                action=requested_action,
                status=RunStatus.FAILED,
                error=error,
            )
        )
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.RUN_FINISHED,
                action=requested_action,
                status=RunStatus.FAILED,
                error=error,
            )
        )
        raise

    action = settings.runtime.action
    status = RunStatus.SUCCESS
    try:
        if action == "collect":
            summary = _run_collect(
                settings,
                run_id,
                sink,
                emit_collect_diagnostics=args.collect_diagnostics,
            )
            status = summary.status
            print(_run_summary_json(summary))
        elif action == "export":
            summary = _run_export(settings, run_id, sink)
            status = summary.status
            print(_run_summary_json(summary))
        else:
            print(f"project1 action={action} env={settings.app.env} mode={settings.runtime.mode}")
            print("CLI skeleton is ready; source, storage, export, and logging work follow.")
    except Exception as exc:
        error = classify_exception(exc)
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.ERROR,
                action=action,
                status=RunStatus.FAILED,
                error=error,
            )
        )
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.RUN_FINISHED,
                action=action,
                status=RunStatus.FAILED,
                error=error,
            )
        )
        return 1

    sink.emit(
        LogEvent(
            run_id=run_id,
            event_type=LogEventType.RUN_FINISHED,
            action=action,
            status=status,
        )
    )
    return 1 if status == RunStatus.FAILED else 0


def _run_collect(
    settings: Settings,
    run_id: str,
    sink: ConsoleLogSink,
    *,
    emit_collect_diagnostics: bool = False,
) -> RunSummary:
    keywords = KeywordSet(
        core=settings.keywords.core,
        supporting=settings.keywords.supporting,
        exclude=settings.keywords.exclude,
    )
    source, normalizer = _build_collect_stack(settings, keywords)
    diagnostic_reporter = (
        _build_collect_diagnostic_reporter(run_id, sink) if emit_collect_diagnostics else None
    )
    with SQLiteNoticeRepository(settings.storage.database_path) as repository:
        use_case = DefaultCollectNoticesUseCase(
            source=source,
            normalizer=normalizer,
            repository=repository,
            diagnostic_reporter=diagnostic_reporter,
        )
        summary = use_case.execute(run_id=run_id)

    for source_result in summary.source_results:
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.SOURCE_FINISHED,
                action=summary.action,
                status=summary.status,
                source=source_result.source,
                fetched_count=source_result.collected_count,
                saved_count=source_result.saved_count,
                excluded_count=source_result.skipped_count,
            )
        )
    for error in summary.errors:
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.ERROR,
                action=summary.action,
                status=summary.status,
                error=error,
            )
        )
    return summary


def _build_collect_diagnostic_reporter(run_id: str, sink: ConsoleLogSink):
    def _report(diagnostic) -> None:
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.COLLECT_DIAGNOSTIC,
                action="collect",
                status=RunStatus.RUNNING,
                source=diagnostic.source,
                metadata=diagnostic.to_metadata(),
            )
        )

    return _report


def _build_bizinfo_collect_source(settings: Settings):
    if settings.runtime.source_mode == "fixture":
        return BizinfoFixtureSourceAdapter(settings.sources.bizinfo.fixture_path)
    if settings.runtime.source_mode == "api":
        return BizinfoSourceAdapter(
            BizinfoApiHttpClient(
                endpoint=settings.sources.bizinfo.endpoint,
                cert_key=settings.sources.bizinfo.cert_key,
                timeout_seconds=settings.sources.bizinfo.timeout_seconds,
                retry_count=settings.sources.bizinfo.retry_count,
                retry_backoff_seconds=settings.sources.bizinfo.retry_backoff_seconds,
                page_size=settings.sources.bizinfo.page_size,
            )
        )
    raise ConfigurationAppError(f"Unsupported collect source_mode: {settings.runtime.source_mode}")


def _build_g2b_collect_source(settings: Settings):
    if settings.runtime.source_mode == "fixture":
        return G2BFixtureSourceAdapter(settings.sources.g2b.fixture_path)
    if settings.runtime.source_mode == "api":
        return G2BSourceAdapter(
            G2BApiHttpClient(
                endpoint=settings.sources.g2b.endpoint,
                api_key=settings.sources.g2b.cert_key,
                timeout_seconds=settings.sources.g2b.timeout_seconds,
                retry_count=settings.sources.g2b.retry_count,
                retry_backoff_seconds=settings.sources.g2b.retry_backoff_seconds,
                page_size=settings.sources.g2b.page_size,
                inquiry_division=settings.sources.g2b.inquiry_division,
                inquiry_window_days=settings.sources.g2b.inquiry_window_days,
                timezone_name=settings.app.timezone,
            )
        )
    raise ConfigurationAppError(f"Unsupported collect source_mode: {settings.runtime.source_mode}")


def _build_collect_stack(settings: Settings, keywords: KeywordSet):
    collect_stacks: list[tuple[object, object]] = []
    if settings.sources.bizinfo.enabled:
        collect_stacks.append(
            (
                _build_bizinfo_collect_source(settings),
                BizinfoNoticeNormalizer(keywords, timezone=settings.app.timezone),
            )
        )
    if settings.sources.g2b.enabled:
        collect_stacks.append(
            (
                _build_g2b_collect_source(settings),
                G2BNoticeNormalizer(keywords, timezone=settings.app.timezone),
            )
        )
    if not collect_stacks:
        raise ConfigurationAppError("No collect source is enabled.")
    if len(collect_stacks) > 1:
        raise ConfigurationAppError(
            "Collect currently supports one enabled source at a time. Disable either sources.bizinfo or sources.g2b."
        )
    return collect_stacks[0]


def _run_export(settings: Settings, run_id: str, sink: ConsoleLogSink) -> RunSummary:
    with SQLiteNoticeRepository(settings.storage.database_path) as repository:
        use_case = DefaultExportNoticesUseCase(
            repository=repository,
            exporter=XlsxExcelExporter(
                output_dir=settings.export.output_dir,
                filename_pattern=settings.export.filename_pattern,
            ),
            support_sheet_name=settings.export.support_sheet_name,
            bid_sheet_name=settings.export.bid_sheet_name,
        )
        summary = use_case.execute(run_id=run_id)

    for exported_file in summary.exported_files:
        sink.emit(
            LogEvent(
                run_id=run_id,
                event_type=LogEventType.EXPORT_FINISHED,
                action=summary.action,
                status=summary.status,
                output_file_path=exported_file,
            )
        )
    return summary


def _run_summary_json(summary: RunSummary) -> str:
    payload = {
        "summary_type": "run_summary",
        "run_id": summary.run_id,
        "action": summary.action,
        "status": summary.status.value,
        "collected_count": summary.collected_count,
        "saved_count": summary.saved_count,
        "skipped_count": summary.skipped_count,
        "error_count": summary.error_count,
        "exported_files": [str(path) for path in summary.exported_files],
        "source_results": [
            {
                "source": source.source.value,
                "collected_count": source.collected_count,
                "saved_count": source.saved_count,
                "skipped_count": source.skipped_count,
                "error_count": source.error_count,
            }
            for source in summary.source_results
        ],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())
