from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from unittest import TestCase
from xml.etree import ElementTree
from zipfile import ZipFile

from app.application import DefaultExportNoticesUseCase
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
from app.exporters import EXPORT_COLUMN_ORDER, XlsxExcelExporter, format_notice_row
from app.exporters.xlsx import PACKAGE_RELATIONSHIP_NS, SPREADSHEET_NS
from app.ops import RunStatus
from app.persistence import InMemoryNoticeRepository
from tests.temp_utils import temporary_directory


SPREADSHEET_NAMESPACES = {"s": SPREADSHEET_NS}
RELATIONSHIP_NAMESPACES = {"r": PACKAGE_RELATIONSHIP_NS}


class XlsxExcelExporterTests(TestCase):
    def test_export_creates_xlsx_with_fixed_sheets_headers_and_formatted_row(self) -> None:
        with temporary_directory() as directory:
            output_dir = Path(directory)
            notice = _make_notice()
            exporter = XlsxExcelExporter(
                output_dir=output_dir,
                run_date=date(2026, 4, 17),
            )

            paths = exporter.export(
                _workbook_with_support_notice(notice),
                run_id="run-1",
            )

            output_path = output_dir / "notices_20260417_run-1.xlsx"
            self.assertEqual(paths, (output_path,))
            self.assertTrue(output_path.exists())

            with ZipFile(output_path) as workbook:
                names = set(workbook.namelist())
                self.assertIn("xl/workbook.xml", names)
                self.assertIn("xl/worksheets/sheet1.xml", names)
                self.assertIn("xl/worksheets/sheet2.xml", names)
                self.assertIn("xl/worksheets/_rels/sheet1.xml.rels", names)
                self.assertNotIn("xl/worksheets/_rels/sheet2.xml.rels", names)

                workbook_sheet_names = _sheet_names(workbook.read("xl/workbook.xml"))
                self.assertEqual(workbook_sheet_names, ("support_notices", "bid_notices"))

                support_rows = _sheet_rows(workbook.read("xl/worksheets/sheet1.xml"))
                self.assertEqual(support_rows[0], EXPORT_COLUMN_ORDER)
                self.assertEqual(support_rows[1], tuple(format_notice_row(notice).values()))
                self.assertNotIn("business_domains", support_rows[0])

                bid_rows = _sheet_rows(workbook.read("xl/worksheets/sheet2.xml"))
                self.assertEqual(bid_rows, (EXPORT_COLUMN_ORDER,))

                hyperlink_targets = _relationship_targets(
                    workbook.read("xl/worksheets/_rels/sheet1.xml.rels")
                )
                self.assertEqual(hyperlink_targets, (notice.url,))

    def test_export_use_case_can_use_real_xlsx_exporter(self) -> None:
        with temporary_directory() as directory:
            repository = InMemoryNoticeRepository()
            notice = _make_notice()
            repository.save(notice, DeduplicationKey.from_notice(notice))
            exporter = XlsxExcelExporter(
                output_dir=Path(directory),
                run_date=date(2026, 4, 17),
            )
            use_case = DefaultExportNoticesUseCase(
                repository=repository,
                exporter=exporter,
            )

            summary = use_case.execute(run_id="export-1")

            self.assertEqual(summary.status, RunStatus.SUCCESS)
            self.assertEqual(len(summary.exported_files), 1)
            self.assertEqual(summary.exported_files[0].name, "notices_20260417_export-1.xlsx")
            self.assertTrue(summary.exported_files[0].exists())

    def test_invalid_sheet_name_fails_before_file_is_created(self) -> None:
        with temporary_directory() as directory:
            exporter = XlsxExcelExporter(output_dir=Path(directory))

            with self.assertRaises(ValueError):
                exporter.export(
                    _workbook_with_support_notice(
                        _make_notice(),
                        support_sheet_name="invalid/name",
                    ),
                    run_id="run-1",
                )


def _workbook_with_support_notice(
    notice: Notice,
    *,
    support_sheet_name: str = "support_notices",
):
    from app.application import ExportSheetInput, ExportWorkbookInput

    return ExportWorkbookInput(
        support_sheet=ExportSheetInput(
            sheet_name=support_sheet_name,
            notices=(notice,),
        ),
        bid_sheet=ExportSheetInput(sheet_name="bid_notices", notices=()),
    )


def _sheet_names(xml_bytes: bytes) -> tuple[str, ...]:
    root = ElementTree.fromstring(xml_bytes)
    return tuple(
        element.attrib["name"]
        for element in root.findall("s:sheets/s:sheet", SPREADSHEET_NAMESPACES)
    )


def _sheet_rows(xml_bytes: bytes) -> tuple[tuple[str, ...], ...]:
    root = ElementTree.fromstring(xml_bytes)
    rows: list[tuple[str, ...]] = []
    for row in root.findall("s:sheetData/s:row", SPREADSHEET_NAMESPACES):
        rows.append(
            tuple(
                cell.findtext("s:is/s:t", default="", namespaces=SPREADSHEET_NAMESPACES)
                for cell in row.findall("s:c", SPREADSHEET_NAMESPACES)
            )
        )
    return tuple(rows)


def _relationship_targets(xml_bytes: bytes) -> tuple[str, ...]:
    root = ElementTree.fromstring(xml_bytes)
    return tuple(
        element.attrib["Target"]
        for element in root.findall("r:Relationship", RELATIONSHIP_NAMESPACES)
    )


def _make_notice() -> Notice:
    return Notice(
        source=NoticeSource.BIZINFO,
        notice_type=NoticeType.SUPPORT,
        business_domains=(BusinessDomain.AI, BusinessDomain.DATA),
        primary_domain=BusinessDomain.AI,
        title="AI automation support",
        organization="MSS",
        posted_at=date(2026, 4, 1),
        end_at=date(2026, 4, 30),
        status=NoticeStatus.OPEN,
        url="https://example.com/notices/BIZ-1",
        match_keywords=(
            MatchedKeyword(
                keyword="AI",
                group=KeywordGroup.CORE,
                domain=BusinessDomain.AI,
            ),
            MatchedKeyword(
                keyword="data",
                group=KeywordGroup.SUPPORTING,
                domain=BusinessDomain.DATA,
            ),
        ),
        collected_at=datetime(2026, 4, 17, 9, 30, tzinfo=UTC),
        source_notice_id="BIZ-1",
    )
