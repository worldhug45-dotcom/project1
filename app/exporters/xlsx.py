"""Minimal XLSX exporter implementation for the first MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile

from app.application.models import ExportSheetInput, ExportWorkbookInput
from app.exporters.formatting import (
    DEFAULT_FILENAME_PATTERN,
    EXPORT_COLUMN_ORDER,
    build_export_filename,
    format_sheet_rows,
)


SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RELATIONSHIP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_RELATIONSHIP_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ElementTree.register_namespace("", SPREADSHEET_NS)
ElementTree.register_namespace("r", RELATIONSHIP_NS)


@dataclass(slots=True)
class XlsxExcelExporter:
    """ExcelExporterPort implementation that writes a real .xlsx workbook."""

    output_dir: Path = Path("output")
    filename_pattern: str = DEFAULT_FILENAME_PATTERN
    run_date: date | None = None

    def export(self, workbook: ExportWorkbookInput, run_id: str) -> tuple[Path, ...]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = build_export_filename(
            pattern=self.filename_pattern,
            run_date=self.run_date or date.today(),
            run_id=run_id,
        )
        output_path = self.output_dir / filename
        _write_xlsx(output_path, workbook)
        return (output_path,)


def _write_xlsx(output_path: Path, workbook: ExportWorkbookInput) -> None:
    sheets = workbook.sheets
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml(len(sheets)))
        archive.writestr("_rels/.rels", _package_relationships_xml())
        archive.writestr("xl/workbook.xml", _workbook_xml(sheets))
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_relationships_xml(sheets))

        for index, sheet in enumerate(sheets, start=1):
            sheet_xml, relationships_xml = _worksheet_xml(sheet)
            archive.writestr(f"xl/worksheets/sheet{index}.xml", sheet_xml)
            if relationships_xml is not None:
                archive.writestr(
                    f"xl/worksheets/_rels/sheet{index}.xml.rels",
                    relationships_xml,
                )


def _content_types_xml(sheet_count: int) -> bytes:
    root = ElementTree.Element(_qualified(CONTENT_TYPES_NS, "Types"))
    ElementTree.SubElement(
        root,
        _qualified(CONTENT_TYPES_NS, "Default"),
        {
            "Extension": "rels",
            "ContentType": "application/vnd.openxmlformats-package.relationships+xml",
        },
    )
    ElementTree.SubElement(
        root,
        _qualified(CONTENT_TYPES_NS, "Default"),
        {"Extension": "xml", "ContentType": "application/xml"},
    )
    ElementTree.SubElement(
        root,
        _qualified(CONTENT_TYPES_NS, "Override"),
        {
            "PartName": "/xl/workbook.xml",
            "ContentType": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
            ),
        },
    )
    for index in range(1, sheet_count + 1):
        ElementTree.SubElement(
            root,
            _qualified(CONTENT_TYPES_NS, "Override"),
            {
                "PartName": f"/xl/worksheets/sheet{index}.xml",
                "ContentType": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"
                ),
            },
        )
    return _xml_bytes(root)


def _package_relationships_xml() -> bytes:
    return _relationships_xml(
        (
            {
                "Id": "rId1",
                "Type": f"{RELATIONSHIP_NS}/officeDocument",
                "Target": "xl/workbook.xml",
            },
        )
    )


def _workbook_xml(sheets: tuple[ExportSheetInput, ...]) -> bytes:
    root = ElementTree.Element(_qualified(SPREADSHEET_NS, "workbook"))
    sheets_element = ElementTree.SubElement(root, _qualified(SPREADSHEET_NS, "sheets"))
    for index, sheet in enumerate(sheets, start=1):
        _validate_sheet_name(sheet.sheet_name)
        ElementTree.SubElement(
            sheets_element,
            _qualified(SPREADSHEET_NS, "sheet"),
            {
                "name": sheet.sheet_name,
                "sheetId": str(index),
                _qualified(RELATIONSHIP_NS, "id"): f"rId{index}",
            },
        )
    return _xml_bytes(root)


def _workbook_relationships_xml(sheets: tuple[ExportSheetInput, ...]) -> bytes:
    relationships = tuple(
        {
            "Id": f"rId{index}",
            "Type": f"{RELATIONSHIP_NS}/worksheet",
            "Target": f"worksheets/sheet{index}.xml",
        }
        for index, _sheet in enumerate(sheets, start=1)
    )
    return _relationships_xml(relationships)


def _worksheet_xml(sheet: ExportSheetInput) -> tuple[bytes, bytes | None]:
    root = ElementTree.Element(_qualified(SPREADSHEET_NS, "worksheet"))
    sheet_data = ElementTree.SubElement(root, _qualified(SPREADSHEET_NS, "sheetData"))
    _append_row(sheet_data, row_index=1, values=EXPORT_COLUMN_ORDER)

    hyperlink_targets: list[tuple[str, str]] = []
    rows = format_sheet_rows(sheet.notices)
    for row_offset, row in enumerate(rows, start=2):
        values = tuple(row[column] for column in EXPORT_COLUMN_ORDER)
        _append_row(sheet_data, row_index=row_offset, values=values)
        url = row["url"]
        if url:
            hyperlink_targets.append((_cell_ref(_url_column_index(), row_offset), url))

    if hyperlink_targets:
        hyperlinks = ElementTree.SubElement(root, _qualified(SPREADSHEET_NS, "hyperlinks"))
        for relationship_index, (cell_ref, _url) in enumerate(hyperlink_targets, start=1):
            ElementTree.SubElement(
                hyperlinks,
                _qualified(SPREADSHEET_NS, "hyperlink"),
                {"ref": cell_ref, _qualified(RELATIONSHIP_NS, "id"): f"rId{relationship_index}"},
            )

    relationships_xml = None
    if hyperlink_targets:
        relationships_xml = _relationships_xml(
            tuple(
                {
                    "Id": f"rId{index}",
                    "Type": f"{RELATIONSHIP_NS}/hyperlink",
                    "Target": url,
                    "TargetMode": "External",
                }
                for index, (_cell_ref_value, url) in enumerate(hyperlink_targets, start=1)
            )
        )

    return _xml_bytes(root), relationships_xml


def _append_row(parent: ElementTree.Element, *, row_index: int, values: tuple[str, ...]) -> None:
    row_element = ElementTree.SubElement(
        parent,
        _qualified(SPREADSHEET_NS, "row"),
        {"r": str(row_index)},
    )
    for column_index, value in enumerate(values, start=1):
        cell = ElementTree.SubElement(
            row_element,
            _qualified(SPREADSHEET_NS, "c"),
            {"r": _cell_ref(column_index, row_index), "t": "inlineStr"},
        )
        inline_string = ElementTree.SubElement(cell, _qualified(SPREADSHEET_NS, "is"))
        text = ElementTree.SubElement(inline_string, _qualified(SPREADSHEET_NS, "t"))
        if value != value.strip():
            text.set(_qualified(XML_NS, "space"), "preserve")
        text.text = value


def _relationships_xml(relationships: tuple[dict[str, str], ...]) -> bytes:
    root = ElementTree.Element(_qualified(PACKAGE_RELATIONSHIP_NS, "Relationships"))
    for relationship in relationships:
        ElementTree.SubElement(
            root,
            _qualified(PACKAGE_RELATIONSHIP_NS, "Relationship"),
            relationship,
        )
    return _xml_bytes(root)


def _validate_sheet_name(value: str) -> None:
    if not value.strip():
        raise ValueError("Excel sheet name is required.")
    if len(value) > 31:
        raise ValueError("Excel sheet name must be 31 characters or fewer.")
    if any(character in value for character in "[]:*?/\\"):
        raise ValueError("Excel sheet name contains an unsupported character.")


def _url_column_index() -> int:
    return EXPORT_COLUMN_ORDER.index("url") + 1


def _cell_ref(column_index: int, row_index: int) -> str:
    return f"{_column_name(column_index)}{row_index}"


def _column_name(column_index: int) -> str:
    if column_index < 1:
        raise ValueError("column_index must be greater than 0.")
    result = ""
    current = column_index
    while current:
        current, remainder = divmod(current - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _qualified(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def _xml_bytes(root: ElementTree.Element) -> bytes:
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
