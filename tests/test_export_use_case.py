from pathlib import Path
from unittest import TestCase

from app.application import DefaultCollectNoticesUseCase, DefaultExportNoticesUseCase
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
from app.exporters import FakeExcelExporter
from app.filters import KeywordSet
from app.normalizers import BizinfoNoticeNormalizer
from app.ops import RunStatus
from app.persistence import InMemoryNoticeRepository, SQLiteNoticeRepository
from app.sources import BizinfoFixtureSourceAdapter
from tests.temp_utils import temporary_directory


FIXTURE_PATH = Path("tests/fixtures/bizinfo/support_notices.json")
KEYWORDS = KeywordSet(
    core=("AI", "인공지능", "디지털전환", "DX", "디지털트윈", "시스템 통합", "SI", "정보화"),
    supporting=(
        "데이터",
        "빅데이터",
        "클라우드",
        "인프라",
        "서버",
        "네트워크",
        "보안",
        "IT서비스",
        "유지보수",
    ),
    exclude=("채용", "행사", "교육", "경진대회", "복지", "문화", "비관련 제조 일반"),
)


class ExportUseCaseTests(TestCase):
    def test_export_reads_in_memory_repository_and_splits_sheet_inputs(self) -> None:
        repository = InMemoryNoticeRepository()
        support_notice = _make_notice("BIZ-1", NoticeSource.BIZINFO, NoticeType.SUPPORT)
        bid_notice = _make_notice("G2B-1", NoticeSource.G2B, NoticeType.BID)
        repository.save(support_notice, DeduplicationKey.from_notice(support_notice))
        repository.save(bid_notice, DeduplicationKey.from_notice(bid_notice))
        exporter = FakeExcelExporter(output_paths=(Path("output/run-1.xlsx"),))
        use_case = DefaultExportNoticesUseCase(repository=repository, exporter=exporter)

        summary = use_case.execute(run_id="run-1")

        self.assertEqual(summary.action, "export")
        self.assertEqual(summary.status, RunStatus.SUCCESS)
        self.assertEqual(summary.exported_files, (Path("output/run-1.xlsx"),))
        self.assertEqual(len(exporter.calls), 1)
        workbook = exporter.last_workbook
        self.assertIsNotNone(workbook)
        assert workbook is not None
        self.assertEqual(workbook.support_sheet.sheet_name, "support_notices")
        self.assertEqual(workbook.bid_sheet.sheet_name, "bid_notices")
        self.assertEqual(workbook.support_sheet.notices, (support_notice,))
        self.assertEqual(workbook.bid_sheet.notices, (bid_notice,))

    def test_export_reads_sqlite_repository_with_same_flow(self) -> None:
        with temporary_directory() as directory:
            database_path = Path(directory) / "notices.sqlite3"
            with SQLiteNoticeRepository(database_path) as repository:
                support_notice = _make_notice(
                    "BIZ-1",
                    NoticeSource.BIZINFO,
                    NoticeType.SUPPORT,
                )
                bid_notice = _make_notice("G2B-1", NoticeSource.G2B, NoticeType.BID)
                repository.save(support_notice, DeduplicationKey.from_notice(support_notice))
                repository.save(bid_notice, DeduplicationKey.from_notice(bid_notice))
                exporter = FakeExcelExporter(output_paths=(Path("output/run-1.xlsx"),))
                use_case = DefaultExportNoticesUseCase(
                    repository=repository,
                    exporter=exporter,
                )

                summary = use_case.execute(run_id="run-1")

                workbook = exporter.last_workbook
                self.assertIsNotNone(workbook)
                assert workbook is not None
                self.assertEqual(summary.status, RunStatus.SUCCESS)
                self.assertEqual(summary.exported_files, (Path("output/run-1.xlsx"),))
                self.assertEqual(len(workbook.support_sheet.notices), 1)
                self.assertEqual(len(workbook.bid_sheet.notices), 1)
                self.assertEqual(
                    workbook.support_sheet.notices[0].notice_type,
                    NoticeType.SUPPORT,
                )
                self.assertEqual(workbook.bid_sheet.notices[0].notice_type, NoticeType.BID)

    def test_collect_to_sqlite_then_export_with_fake_exporter(self) -> None:
        with temporary_directory() as directory:
            database_path = Path(directory) / "notices.sqlite3"
            with SQLiteNoticeRepository(database_path) as repository:
                collect_use_case = DefaultCollectNoticesUseCase(
                    source=BizinfoFixtureSourceAdapter(FIXTURE_PATH),
                    normalizer=BizinfoNoticeNormalizer(KEYWORDS),
                    repository=repository,
                )
                collect_summary = collect_use_case.execute(run_id="collect-1")
                exporter = FakeExcelExporter(output_paths=(Path("output/export-1.xlsx"),))
                export_use_case = DefaultExportNoticesUseCase(
                    repository=repository,
                    exporter=exporter,
                )

                export_summary = export_use_case.execute(run_id="export-1")

                workbook = exporter.last_workbook
                self.assertIsNotNone(workbook)
                assert workbook is not None
                self.assertEqual(collect_summary.saved_count, 1)
                self.assertEqual(export_summary.status, RunStatus.SUCCESS)
                self.assertEqual(export_summary.exported_files, (Path("output/export-1.xlsx"),))
                self.assertEqual(len(workbook.support_sheet.notices), 1)
                self.assertEqual(len(workbook.bid_sheet.notices), 0)
                self.assertEqual(
                    workbook.support_sheet.notices[0].title,
                    "AI 기반 업무 자동화 지원사업",
                )


def _make_notice(
    source_notice_id: str,
    source: NoticeSource,
    notice_type: NoticeType,
) -> Notice:
    from datetime import UTC, datetime

    return Notice(
        source=source,
        notice_type=notice_type,
        business_domains=(BusinessDomain.AI,),
        primary_domain=BusinessDomain.AI,
        title=f"{source_notice_id} AI 기반 사업",
        organization="테스트 기관",
        status=NoticeStatus.OPEN,
        url=f"https://example.com/notices/{source_notice_id}",
        match_keywords=(
            MatchedKeyword(
                keyword="AI",
                group=KeywordGroup.CORE,
                domain=BusinessDomain.AI,
            ),
        ),
        collected_at=datetime.now(UTC),
        source_notice_id=source_notice_id,
    )
