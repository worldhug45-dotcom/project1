from pathlib import Path
from unittest import TestCase

from app.application import DefaultCollectNoticesUseCase
from app.domain import BusinessDomain
from app.filters import KeywordSet
from app.normalizers import BizinfoNoticeNormalizer
from app.persistence import SQLiteNoticeRepository
from app.sources import BizinfoFixtureSourceAdapter
from tests.temp_utils import temporary_directory


FIXTURE_PATH = Path("tests/fixtures/bizinfo/support_notices.json")
KEYWORDS = KeywordSet(
    core=("AI", "인공지능", "디지털전환", "DX", "디지털트윈", "시스템 통합", "SI", "정보화"),
    supporting=("데이터", "빅데이터", "클라우드", "인프라", "서버", "네트워크", "보안", "IT서비스", "유지보수"),
    exclude=("채용", "행사", "교육", "경진대회", "복지", "문화", "비관련 제조 일반"),
)


class SQLiteNoticeRepositoryTests(TestCase):
    def test_collect_fixture_saves_eligible_notice_to_sqlite(self) -> None:
        with temporary_directory() as directory:
            database_path = Path(directory) / "notices.sqlite3"
            with SQLiteNoticeRepository(database_path) as repository:
                use_case = _make_collect_use_case(repository)

                summary = use_case.execute(run_id="run-1")
                saved_notices = repository.list_all()

                self.assertEqual(summary.collected_count, 2)
                self.assertEqual(summary.saved_count, 1)
                self.assertEqual(summary.skipped_count, 1)
                self.assertEqual(summary.error_count, 0)
                self.assertEqual(repository.count(), 1)
                self.assertEqual(saved_notices[0].primary_domain, BusinessDomain.AI)
                self.assertEqual(saved_notices[0].title, "AI 기반 업무 자동화 지원사업")
                self.assertEqual(repository.all(), saved_notices)

    def test_collect_fixture_does_not_duplicate_sqlite_rows_on_rerun(self) -> None:
        with temporary_directory() as directory:
            database_path = Path(directory) / "notices.sqlite3"
            with SQLiteNoticeRepository(database_path) as repository:
                use_case = _make_collect_use_case(repository)

                first_summary = use_case.execute(run_id="run-1")
                second_summary = use_case.execute(run_id="run-2")

                self.assertEqual(first_summary.saved_count, 1)
                self.assertEqual(second_summary.collected_count, 2)
                self.assertEqual(second_summary.saved_count, 0)
                self.assertEqual(second_summary.skipped_count, 2)
                self.assertEqual(repository.count(), 1)


def _make_collect_use_case(
    repository: SQLiteNoticeRepository,
) -> DefaultCollectNoticesUseCase:
    return DefaultCollectNoticesUseCase(
        source=BizinfoFixtureSourceAdapter(FIXTURE_PATH),
        normalizer=BizinfoNoticeNormalizer(KEYWORDS),
        repository=repository,
    )
