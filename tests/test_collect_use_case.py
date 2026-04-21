from pathlib import Path
from unittest import TestCase

from app.application import DefaultCollectNoticesUseCase
from app.domain import BusinessDomain, DeduplicationKey, Notice, NoticeSource
from app.filters import KeywordSet
from app.normalizers import BizinfoNoticeNormalizer, G2BNoticeNormalizer
from app.ops import ErrorType, RunStatus, StorageWriteError
from app.persistence import InMemoryNoticeRepository
from app.sources import BizinfoFixtureSourceAdapter, G2BFixtureSourceAdapter


FIXTURE_PATH = Path("tests/fixtures/bizinfo/support_notices.json")
G2B_FIXTURE_PATH = Path("tests/fixtures/g2b/bid_notices.json")
KEYWORDS = KeywordSet(
    core=("AI", "인공지능", "디지털전환", "DX", "디지털트윈", "시스템 통합", "SI", "정보화"),
    supporting=("데이터", "빅데이터", "클라우드", "인프라", "서버", "네트워크", "보안", "IT서비스", "유지보수"),
    exclude=("채용", "행사", "교육", "경진대회", "복지", "문화", "비관련 제조 일반"),
)


class CollectUseCaseTests(TestCase):
    def test_collect_emits_diagnostics_for_saved_and_skipped_notices(self) -> None:
        repository = InMemoryNoticeRepository()
        diagnostics = []
        use_case = DefaultCollectNoticesUseCase(
            source=BizinfoFixtureSourceAdapter(FIXTURE_PATH),
            normalizer=BizinfoNoticeNormalizer(KEYWORDS),
            repository=repository,
            diagnostic_reporter=diagnostics.append,
        )

        summary = use_case.execute(run_id="run-1")

        self.assertEqual(summary.saved_count, 1)
        self.assertEqual(summary.skipped_count, 1)
        self.assertEqual(len(diagnostics), 2)
        self.assertEqual(diagnostics[0].outcome, "saved")
        self.assertTrue(diagnostics[0].eligible)
        self.assertTrue(diagnostics[0].matched_core_keywords)
        self.assertEqual(diagnostics[1].outcome, "skipped")
        self.assertFalse(diagnostics[1].eligible)
        self.assertIsNotNone(diagnostics[1].skip_reason)

    def test_collect_saves_eligible_and_skips_ineligible_bizinfo_notices(self) -> None:
        repository = InMemoryNoticeRepository()
        use_case = DefaultCollectNoticesUseCase(
            source=BizinfoFixtureSourceAdapter(FIXTURE_PATH),
            normalizer=BizinfoNoticeNormalizer(KEYWORDS),
            repository=repository,
        )

        summary = use_case.execute(run_id="run-1")
        saved_notices = repository.list_all()

        self.assertEqual(summary.run_id, "run-1")
        self.assertEqual(summary.action, "collect")
        self.assertEqual(summary.status, RunStatus.SUCCESS)
        self.assertEqual(summary.collected_count, 2)
        self.assertEqual(summary.saved_count, 1)
        self.assertEqual(summary.skipped_count, 1)
        self.assertEqual(summary.error_count, 0)
        self.assertEqual(summary.source_results[0].source, NoticeSource.BIZINFO)
        self.assertEqual(repository.count(), 1)
        self.assertEqual(saved_notices[0].primary_domain, BusinessDomain.AI)
        self.assertEqual(repository.all(), saved_notices)

    def test_collect_saves_eligible_and_skips_ineligible_g2b_notices(self) -> None:
        repository = InMemoryNoticeRepository()
        use_case = DefaultCollectNoticesUseCase(
            source=G2BFixtureSourceAdapter(G2B_FIXTURE_PATH),
            normalizer=G2BNoticeNormalizer(KEYWORDS),
            repository=repository,
        )

        summary = use_case.execute(run_id="run-g2b-1")
        saved_notices = repository.list_all()

        self.assertEqual(summary.run_id, "run-g2b-1")
        self.assertEqual(summary.action, "collect")
        self.assertEqual(summary.status, RunStatus.SUCCESS)
        self.assertEqual(summary.collected_count, 2)
        self.assertEqual(summary.saved_count, 1)
        self.assertEqual(summary.skipped_count, 1)
        self.assertEqual(summary.error_count, 0)
        self.assertEqual(summary.source_results[0].source, NoticeSource.G2B)
        self.assertEqual(repository.count(), 1)
        self.assertEqual(saved_notices[0].notice_type.value, "bid")
        self.assertEqual(saved_notices[0].primary_domain, BusinessDomain.AI)

    def test_collect_skips_duplicate_notices_on_repeated_run(self) -> None:
        repository = InMemoryNoticeRepository()
        use_case = DefaultCollectNoticesUseCase(
            source=BizinfoFixtureSourceAdapter(FIXTURE_PATH),
            normalizer=BizinfoNoticeNormalizer(KEYWORDS),
            repository=repository,
        )

        first_summary = use_case.execute(run_id="run-1")
        second_summary = use_case.execute(run_id="run-2")

        self.assertEqual(first_summary.saved_count, 1)
        self.assertEqual(second_summary.collected_count, 2)
        self.assertEqual(second_summary.saved_count, 0)
        self.assertEqual(second_summary.skipped_count, 2)
        self.assertEqual(repository.count(), 1)

    def test_collect_treats_repository_save_failure_as_fatal(self) -> None:
        use_case = DefaultCollectNoticesUseCase(
            source=BizinfoFixtureSourceAdapter(FIXTURE_PATH),
            normalizer=BizinfoNoticeNormalizer(KEYWORDS),
            repository=_FailingSaveRepository(),
        )

        summary = use_case.execute(run_id="run-1")

        self.assertEqual(summary.status, RunStatus.FAILED)
        self.assertEqual(summary.collected_count, 2)
        self.assertEqual(summary.saved_count, 0)
        self.assertEqual(summary.skipped_count, 0)
        self.assertEqual(summary.error_count, 1)
        self.assertEqual(summary.source_results[0].error_count, 1)
        self.assertEqual(summary.errors[0].error_type, ErrorType.FATAL)
        self.assertEqual(summary.errors[0].source, NoticeSource.BIZINFO.value)

    def test_collect_treats_source_fetch_failure_as_failed_summary(self) -> None:
        use_case = DefaultCollectNoticesUseCase(
            source=_FailingSource(),
            normalizer=BizinfoNoticeNormalizer(KEYWORDS),
            repository=InMemoryNoticeRepository(),
        )

        summary = use_case.execute(run_id="run-1")

        self.assertEqual(summary.status, RunStatus.FAILED)
        self.assertEqual(summary.collected_count, 0)
        self.assertEqual(summary.saved_count, 0)
        self.assertEqual(summary.skipped_count, 0)
        self.assertEqual(summary.error_count, 1)
        self.assertEqual(summary.source_results[0].source, NoticeSource.BIZINFO)
        self.assertEqual(summary.source_results[0].error_count, 1)
        self.assertEqual(summary.errors[0].error_type, ErrorType.FATAL)
        self.assertEqual(summary.errors[0].source, NoticeSource.BIZINFO.value)


class _FailingSaveRepository:
    def exists(self, key: DeduplicationKey) -> bool:
        return False

    def save(self, notice: Notice, key: DeduplicationKey) -> None:
        raise StorageWriteError("sqlite write failed")


class _FailingSource:
    source = NoticeSource.BIZINFO

    def fetch(self) -> tuple[object, ...]:
        raise RuntimeError("network down")
