"""Collect notices use case orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.models import RunSummary, SourceRunSummary
from app.application.ports import (
    NoticeNormalizerPort,
    NoticeRepositoryPort,
    NoticeSourcePort,
)
from app.domain import DeduplicationKey
from app.ops import (
    CollectNoticeDiagnostic,
    ErrorInfo,
    ErrorType,
    Project1Error,
    RunStatus,
    StorageWriteError,
)


@dataclass(slots=True)
class DefaultCollectNoticesUseCase:
    """Fixture/test-ready collect orchestration over source, normalizer, repository."""

    source: NoticeSourcePort
    normalizer: NoticeNormalizerPort
    repository: NoticeRepositoryPort
    diagnostic_reporter: Callable[[CollectNoticeDiagnostic], None] | None = None

    def execute(self, *, run_id: str) -> RunSummary:
        started_at = datetime.now(UTC)
        try:
            raw_notices = self.source.fetch()
        except Exception as exc:
            error = _source_error_info(exc, self.source.source.value)
            return _build_summary(
                run_id=run_id,
                source=self.source,
                status=RunStatus.FAILED,
                started_at=started_at,
                collected_count=0,
                saved_count=0,
                skipped_count=0,
                error_count=1,
                errors=(error,),
            )
        saved_count = 0
        skipped_count = 0
        error_count = 0
        errors: list[ErrorInfo] = []

        for raw_notice in raw_notices:
            diagnostic = (
                _build_diagnostic(self.source, self.normalizer, raw_notice)
                if self.diagnostic_reporter is not None
                else None
            )
            try:
                notice = self.normalizer.normalize(raw_notice)
            except ValueError as exc:
                skipped_count += 1
                _emit_diagnostic(
                    self.diagnostic_reporter,
                    _with_diagnostic_outcome(
                        diagnostic,
                        outcome="skipped",
                        skip_reason=(
                            diagnostic.skip_reason
                            if diagnostic is not None and diagnostic.skip_reason is not None
                            else "normalization_value_error"
                        ),
                        detail_message=str(exc),
                    ),
                )
                continue
            except TypeError as exc:
                # Type mismatches and unexpected normalization failures are non-fatal
                # at this orchestration boundary; the source run can continue.
                skipped_count += 1
                error_count += 1
                _emit_diagnostic(
                    self.diagnostic_reporter,
                    _with_diagnostic_outcome(
                        diagnostic,
                        outcome="skipped",
                        skip_reason="normalization_type_error",
                        detail_message=str(exc),
                    ),
                )
                errors.append(
                    ErrorInfo(
                        error_type=ErrorType.NON_FATAL,
                        message=str(exc),
                        source=self.source.source.value,
                    )
                )
                continue

            try:
                key = DeduplicationKey.from_notice(notice)
                if self.repository.exists(key):
                    skipped_count += 1
                    _emit_diagnostic(
                        self.diagnostic_reporter,
                        _with_diagnostic_outcome(
                            diagnostic,
                            outcome="skipped",
                            skip_reason="duplicate_notice",
                        ),
                    )
                    continue

                self.repository.save(notice, key)
            except Exception as exc:
                error = _storage_error_info(exc, self.source.source.value)
                return _build_summary(
                    run_id=run_id,
                    source=self.source,
                    status=RunStatus.FAILED,
                    started_at=started_at,
                    collected_count=len(raw_notices),
                    saved_count=saved_count,
                    skipped_count=skipped_count,
                    error_count=error_count + 1,
                    errors=tuple([*errors, error]),
                )
            saved_count += 1
            _emit_diagnostic(
                self.diagnostic_reporter,
                _with_diagnostic_outcome(
                    diagnostic,
                    outcome="saved",
                    skip_reason=None,
                ),
            )

        status = RunStatus.SUCCESS if error_count == 0 else RunStatus.PARTIAL_SUCCESS
        return _build_summary(
            run_id=run_id,
            source=self.source,
            status=status,
            started_at=started_at,
            collected_count=len(raw_notices),
            saved_count=saved_count,
            skipped_count=skipped_count,
            error_count=error_count,
            errors=tuple(errors),
        )


def _storage_error_info(exc: Exception, source: str) -> ErrorInfo:
    if isinstance(exc, Project1Error):
        error = exc.to_error_info()
        return ErrorInfo(
            error_type=error.error_type,
            message=error.message,
            source=error.source or source,
        )
    return StorageWriteError(f"Notice storage failed: {exc}", source=source).to_error_info()


def _source_error_info(exc: Exception, source: str) -> ErrorInfo:
    if isinstance(exc, Project1Error):
        error = exc.to_error_info()
        return ErrorInfo(
            error_type=error.error_type,
            message=error.message,
            source=error.source or source,
        )
    return Project1Error(f"Notice source fetch failed: {exc}", source=source).to_error_info()


def _build_summary(
    *,
    run_id: str,
    source: NoticeSourcePort,
    status: RunStatus,
    started_at: datetime,
    collected_count: int,
    saved_count: int,
    skipped_count: int,
    error_count: int,
    errors: tuple[ErrorInfo, ...],
) -> RunSummary:
    finished_at = datetime.now(UTC)
    source_summary = SourceRunSummary(
        source=source.source,
        collected_count=collected_count,
        saved_count=saved_count,
        skipped_count=skipped_count,
        error_count=error_count,
    )
    return RunSummary.from_sources(
        run_id=run_id,
        action="collect",
        status=status,
        source_results=(source_summary,),
        started_at=started_at,
        finished_at=finished_at,
        errors=errors,
    )


def _build_diagnostic(
    source: NoticeSourcePort,
    normalizer: NoticeNormalizerPort,
    raw_notice: object,
) -> CollectNoticeDiagnostic:
    diagnose = getattr(normalizer, "diagnose", None)
    if callable(diagnose):
        try:
            diagnostic = diagnose(raw_notice)
            if isinstance(diagnostic, CollectNoticeDiagnostic):
                return diagnostic
        except Exception as exc:
            return CollectNoticeDiagnostic.from_raw_notice(
                source=source.source,
                raw_notice=raw_notice,
                detail_message=f"diagnostic unavailable: {exc}",
            )
    return CollectNoticeDiagnostic.from_raw_notice(
        source=source.source,
        raw_notice=raw_notice,
    )


def _emit_diagnostic(
    reporter: Callable[[CollectNoticeDiagnostic], None] | None,
    diagnostic: CollectNoticeDiagnostic | None,
) -> None:
    if reporter is None or diagnostic is None:
        return
    reporter(diagnostic)


def _with_diagnostic_outcome(
    diagnostic: CollectNoticeDiagnostic | None,
    *,
    outcome: str,
    skip_reason: str | None = None,
    detail_message: str | None = None,
) -> CollectNoticeDiagnostic | None:
    if diagnostic is None:
        return None
    return diagnostic.with_outcome(
        outcome=outcome,
        skip_reason=skip_reason,
        detail_message=detail_message,
    )
