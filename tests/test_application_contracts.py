from pathlib import Path
from unittest import TestCase

from app.application import ExportSheetInput, ExportWorkbookInput, RunSummary, SourceRunSummary
from app.application.ports import ExcelExporterPort, NoticeRepositoryPort, NoticeSourcePort
from app.domain import (
    BusinessDomain,
    DeduplicationKey,
    KeywordGroup,
    MatchedKeyword,
    Notice,
    NoticeSource,
    NoticeStatus,
    NoticeType,
)
from app.ops import ErrorInfo, ErrorType, RunStatus


class ApplicationContractTests(TestCase):
    def test_run_summary_aggregates_source_results(self) -> None:
        summary = RunSummary.from_sources(
            run_id="run-1",
            action="all",
            status=RunStatus.SUCCESS,
            source_results=(
                SourceRunSummary(
                    source=NoticeSource.BIZINFO,
                    collected_count=20,
                    saved_count=5,
                    skipped_count=15,
                    error_count=0,
                ),
                SourceRunSummary(
                    source=NoticeSource.G2B,
                    collected_count=20,
                    saved_count=4,
                    skipped_count=16,
                    error_count=1,
                ),
            ),
            exported_files=(Path("output/notices.xlsx"),),
        )

        self.assertEqual(summary.collected_count, 40)
        self.assertEqual(summary.saved_count, 9)
        self.assertEqual(summary.skipped_count, 31)
        self.assertEqual(summary.error_count, 1)
        self.assertEqual(summary.exported_files, (Path("output/notices.xlsx"),))

    def test_run_summary_rejects_unknown_action(self) -> None:
        with self.assertRaises(ValueError):
            RunSummary(run_id="run-1", action="unknown", status=RunStatus.SUCCESS)

    def test_run_summary_does_not_double_count_error_details(self) -> None:
        summary = RunSummary.from_sources(
            run_id="run-1",
            action="collect",
            status=RunStatus.PARTIAL_SUCCESS,
            source_results=(
                SourceRunSummary(
                    source=NoticeSource.BIZINFO,
                    collected_count=1,
                    skipped_count=1,
                    error_count=1,
                ),
            ),
            errors=(
                ErrorInfo(
                    error_type=ErrorType.NON_FATAL,
                    message="invalid raw notice",
                    source=NoticeSource.BIZINFO.value,
                ),
            ),
        )

        self.assertEqual(summary.error_count, 1)
        self.assertEqual(len(summary.errors), 1)

    def test_ports_can_be_satisfied_by_infrastructure_like_adapters(self) -> None:
        notice = _make_notice()
        key = DeduplicationKey.from_notice(notice)
        source: NoticeSourcePort = _FakeSource()
        repository: NoticeRepositoryPort = _FakeRepository()
        exporter: ExcelExporterPort = _FakeExporter()

        self.assertEqual(source.fetch(), ("raw-notice",))
        self.assertFalse(repository.exists(key))
        repository.save(notice, key)
        self.assertTrue(repository.exists(key))
        self.assertEqual(repository.list_all(), (notice,))
        workbook = ExportWorkbookInput(
            support_sheet=ExportSheetInput(
                sheet_name="support_notices",
                notices=(notice,),
            ),
            bid_sheet=ExportSheetInput(
                sheet_name="bid_notices",
                notices=(),
            ),
        )
        self.assertEqual(exporter.export(workbook, "run-1"), (Path("output/run-1.xlsx"),))


class _FakeSource:
    source = NoticeSource.BIZINFO

    def fetch(self) -> tuple[object, ...]:
        return ("raw-notice",)


class _FakeRepository:
    def __init__(self) -> None:
        self._keys: set[DeduplicationKey] = set()
        self._notices: list[Notice] = []

    def exists(self, key: DeduplicationKey) -> bool:
        return key in self._keys

    def save(self, notice: Notice, key: DeduplicationKey) -> None:
        self._keys.add(key)
        self._notices.append(notice)

    def list_all(self) -> tuple[Notice, ...]:
        return tuple(self._notices)


class _FakeExporter:
    def export(self, workbook: ExportWorkbookInput, run_id: str) -> tuple[Path, ...]:
        return (Path(f"output/{run_id}.xlsx"),)


def _make_notice() -> Notice:
    from datetime import UTC, datetime

    return Notice(
        source=NoticeSource.BIZINFO,
        notice_type=NoticeType.SUPPORT,
        business_domains=(BusinessDomain.AI,),
        primary_domain=BusinessDomain.AI,
        title="AI 기반 업무 자동화 지원사업",
        organization="중소벤처기업부",
        status=NoticeStatus.OPEN,
        url="https://example.com/notices/1",
        match_keywords=(
            MatchedKeyword(
                keyword="AI",
                group=KeywordGroup.CORE,
                domain=BusinessDomain.AI,
            ),
        ),
        collected_at=datetime.now(UTC),
        source_notice_id="BIZ-1",
    )
