from datetime import UTC, date, datetime
from unittest import TestCase

from app.domain import (
    BusinessDomain,
    KeywordGroup,
    MatchedKeyword,
    Notice,
    NoticeSource,
    NoticeStatus,
    NoticeType,
)
from app.exporters import (
    DEFAULT_FILENAME_PATTERN,
    EXPORT_COLUMN_ORDER,
    build_export_filename,
    format_match_keywords,
    format_notice_row,
    format_sheet_rows,
)


class ExcelExportFormatTests(TestCase):
    def test_notice_row_uses_fixed_column_order_and_display_values(self) -> None:
        notice = _make_notice()

        row = format_notice_row(notice)

        self.assertEqual(tuple(row.keys()), EXPORT_COLUMN_ORDER)
        self.assertEqual(row["source"], "bizinfo")
        self.assertEqual(row["notice_type"], "support")
        self.assertEqual(row["primary_domain"], "ai")
        self.assertNotIn("business_domains", row)
        self.assertEqual(row["posted_at"], "2026-04-01")
        self.assertEqual(row["end_at"], "2026-04-30")
        self.assertEqual(row["collected_at"], "2026-04-17")
        self.assertEqual(row["url"], "https://example.com/notices/BIZ-1")
        self.assertEqual(row["match_keywords"], "AI, 데이터")

    def test_optional_dates_are_rendered_as_empty_strings(self) -> None:
        notice = _make_notice(posted_at=None, end_at=None)

        row = format_notice_row(notice)

        self.assertEqual(row["posted_at"], "")
        self.assertEqual(row["end_at"], "")

    def test_match_keywords_are_deduplicated_in_stored_order(self) -> None:
        keywords = (
            MatchedKeyword(
                keyword="AI",
                group=KeywordGroup.CORE,
                domain=BusinessDomain.AI,
            ),
            MatchedKeyword(
                keyword="데이터",
                group=KeywordGroup.SUPPORTING,
                domain=BusinessDomain.DATA,
            ),
            MatchedKeyword(
                keyword="AI",
                group=KeywordGroup.CORE,
                domain=BusinessDomain.AI,
            ),
        )

        self.assertEqual(format_match_keywords(keywords), "AI, 데이터")

    def test_empty_sheet_rows_are_allowed(self) -> None:
        self.assertEqual(format_sheet_rows(()), ())

    def test_export_filename_uses_yyyymmdd_run_date_and_run_id(self) -> None:
        filename = build_export_filename(
            pattern=DEFAULT_FILENAME_PATTERN,
            run_date=date(2026, 4, 17),
            run_id="run-1",
        )

        self.assertEqual(str(filename), "notices_20260417_run-1.xlsx")

    def test_export_filename_requires_placeholder_and_xlsx_extension(self) -> None:
        with self.assertRaises(ValueError):
            build_export_filename(
                pattern="notices.xlsx",
                run_date=date(2026, 4, 17),
                run_id="run-1",
            )

        with self.assertRaises(ValueError):
            build_export_filename(
                pattern="notices_{run_id}.csv",
                run_date=date(2026, 4, 17),
                run_id="run-1",
            )


def _make_notice(
    *,
    posted_at: date | None = date(2026, 4, 1),
    end_at: date | None = date(2026, 4, 30),
) -> Notice:
    return Notice(
        source=NoticeSource.BIZINFO,
        notice_type=NoticeType.SUPPORT,
        business_domains=(BusinessDomain.AI, BusinessDomain.DATA),
        primary_domain=BusinessDomain.AI,
        title="AI 기반 업무 자동화 지원사업",
        organization="중소벤처기업부",
        posted_at=posted_at,
        end_at=end_at,
        status=NoticeStatus.OPEN,
        url="https://example.com/notices/BIZ-1",
        match_keywords=(
            MatchedKeyword(
                keyword="AI",
                group=KeywordGroup.CORE,
                domain=BusinessDomain.AI,
            ),
            MatchedKeyword(
                keyword="데이터",
                group=KeywordGroup.SUPPORTING,
                domain=BusinessDomain.DATA,
            ),
        ),
        collected_at=datetime(2026, 4, 17, 9, 30, tzinfo=UTC),
        source_notice_id="BIZ-1",
    )
