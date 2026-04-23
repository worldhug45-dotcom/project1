"""Helpers for collecting and rendering repeated bizinfo observation records."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


COMMON_SKIP_REASONS = (
    "no_keyword_match",
    "excluded_keyword",
    "normalization_value_error",
)


@dataclass(frozen=True, slots=True)
class NoticeObservationExample:
    """Representative saved or skipped notice example for observation logs."""

    title: str | None
    organization: str | None
    primary_domain: str | None
    skip_reason: str | None
    matched_core_keywords: tuple[str, ...] = ()
    matched_supporting_keywords: tuple[str, ...] = ()
    matched_excluded_keywords: tuple[str, ...] = ()
    detail_message: str | None = None

    @classmethod
    def from_metadata(cls, metadata: dict[str, Any]) -> "NoticeObservationExample":
        return cls(
            title=_string_or_none(metadata.get("title")),
            organization=_string_or_none(metadata.get("organization")),
            primary_domain=_string_or_none(metadata.get("primary_domain")),
            skip_reason=_string_or_none(metadata.get("skip_reason")),
            matched_core_keywords=_tuple_of_strings(metadata.get("matched_core_keywords")),
            matched_supporting_keywords=_tuple_of_strings(
                metadata.get("matched_supporting_keywords")
            ),
            matched_excluded_keywords=_tuple_of_strings(metadata.get("matched_excluded_keywords")),
            detail_message=_string_or_none(metadata.get("detail_message")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "organization": self.organization,
            "primary_domain": self.primary_domain,
            "skip_reason": self.skip_reason,
            "matched_core_keywords": list(self.matched_core_keywords),
            "matched_supporting_keywords": list(self.matched_supporting_keywords),
            "matched_excluded_keywords": list(self.matched_excluded_keywords),
            "detail_message": self.detail_message,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "NoticeObservationExample":
        return cls.from_metadata(raw)


@dataclass(frozen=True, slots=True)
class CollectObservationRecord:
    """Aggregated collect observation result for one API execution."""

    observed_on: str
    run_id: str
    status: str
    fetched_count: int
    saved_count: int
    skipped_count: int
    error_count: int
    skip_reason_counts: tuple[tuple[str, int], ...]
    saved_examples: tuple[NoticeObservationExample, ...]
    skipped_examples: tuple[NoticeObservationExample, ...]

    def skip_reason_count(self, reason: str) -> int:
        for key, value in self.skip_reason_counts:
            if key == reason:
                return value
        return 0

    def other_skip_reason_count(self) -> int:
        known_total = sum(self.skip_reason_count(reason) for reason in COMMON_SKIP_REASONS)
        return max(self.skipped_count - known_total, 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed_on": self.observed_on,
            "run_id": self.run_id,
            "status": self.status,
            "fetched_count": self.fetched_count,
            "saved_count": self.saved_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "skip_reason_counts": dict(self.skip_reason_counts),
            "saved_examples": [example.to_dict() for example in self.saved_examples],
            "skipped_examples": [example.to_dict() for example in self.skipped_examples],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CollectObservationRecord":
        raw_skip_reason_counts = raw.get("skip_reason_counts", {})
        if isinstance(raw_skip_reason_counts, dict):
            skip_reason_counts = tuple(
                sorted(
                    ((str(reason), int(count)) for reason, count in raw_skip_reason_counts.items()),
                    key=lambda item: item[0],
                )
            )
        else:
            skip_reason_counts = tuple(
                (str(reason), int(count)) for reason, count in raw_skip_reason_counts
            )
        return cls(
            observed_on=str(raw["observed_on"]),
            run_id=str(raw["run_id"]),
            status=str(raw["status"]),
            fetched_count=int(raw["fetched_count"]),
            saved_count=int(raw["saved_count"]),
            skipped_count=int(raw["skipped_count"]),
            error_count=int(raw["error_count"]),
            skip_reason_counts=skip_reason_counts,
            saved_examples=tuple(
                NoticeObservationExample.from_dict(example)
                for example in raw.get("saved_examples", [])
            ),
            skipped_examples=tuple(
                NoticeObservationExample.from_dict(example)
                for example in raw.get("skipped_examples", [])
            ),
        )


def parse_collect_observation_lines(
    lines: list[str],
    *,
    saved_example_limit: int = 20,
    skipped_example_limit: int = 20,
) -> CollectObservationRecord:
    """Parse CLI collect output lines into one aggregated observation record."""

    events = [json.loads(line) for line in lines if line.strip()]
    summary = next(
        (
            event
            for event in events
            if event.get("summary_type") == "run_summary" and event.get("action") == "collect"
        ),
        None,
    )
    if summary is None:
        raise ValueError("Collect observation lines do not contain a run_summary payload.")

    run_started = next(
        (
            event
            for event in events
            if event.get("event_type") == "run_started" and event.get("action") == "collect"
        ),
        None,
    )
    observed_on = _observation_date(run_started, summary)

    skip_reason_counter: Counter[str] = Counter()
    saved_examples: list[NoticeObservationExample] = []
    skipped_examples: list[NoticeObservationExample] = []

    for event in events:
        if event.get("event_type") != "collect_diagnostic":
            continue
        metadata = event.get("metadata") or {}
        outcome = metadata.get("outcome")
        if outcome == "saved":
            if len(saved_examples) < saved_example_limit:
                saved_examples.append(NoticeObservationExample.from_metadata(metadata))
            continue
        if outcome != "skipped":
            continue
        skip_reason = _string_or_none(metadata.get("skip_reason"))
        if skip_reason is not None:
            skip_reason_counter[skip_reason] += 1
        if len(skipped_examples) < skipped_example_limit:
            skipped_examples.append(NoticeObservationExample.from_metadata(metadata))

    return CollectObservationRecord(
        observed_on=observed_on,
        run_id=str(summary["run_id"]),
        status=str(summary["status"]),
        fetched_count=int(summary["collected_count"]),
        saved_count=int(summary["saved_count"]),
        skipped_count=int(summary["skipped_count"]),
        error_count=int(summary["error_count"]),
        skip_reason_counts=tuple(sorted(skip_reason_counter.items(), key=lambda item: item[0])),
        saved_examples=tuple(saved_examples),
        skipped_examples=tuple(skipped_examples),
    )


def load_observation_history(path: Path) -> tuple[CollectObservationRecord, ...]:
    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(CollectObservationRecord.from_dict(item) for item in raw)


def save_observation_history(
    path: Path,
    records: tuple[CollectObservationRecord, ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [record.to_dict() for record in records]
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def upsert_observation_record(
    records: tuple[CollectObservationRecord, ...],
    record: CollectObservationRecord,
) -> tuple[CollectObservationRecord, ...]:
    deduped = [item for item in records if item.run_id != record.run_id]
    deduped.append(record)
    return tuple(sorted(deduped, key=lambda item: (item.observed_on, item.run_id)))


def render_observation_log(
    records: tuple[CollectObservationRecord, ...],
    *,
    config_path: str,
    source_mode: str,
    next_round_candidates: tuple[str, ...] = (),
) -> str:
    """Render a Markdown observation log that can be appended over multiple days."""

    lines = [
        "# 기업마당 collect 관찰 기록",
        "",
        "이 문서는 `source_mode=api` 기준 기업마당 실제 collect 결과를 2~3일간 같은 조건으로 비교하기 위한 운영 기록이다.",
        "",
        "## 관찰 조건",
        "",
        f"- config: `{config_path}`",
        "- action: `collect`",
        f"- source_mode: `{source_mode}`",
        "- diagnostics: `on`",
        "- g2b: `disabled`",
        "- storage: 관찰용 snapshot DB를 실행마다 새로 사용",
        "",
        "## 비교 표",
        "",
        "| date | run_id | status | fetched | saved | skipped | error | no_keyword_match | excluded_keyword | normalization_value_error | other |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in records:
        lines.append(
            "| "
            f"{record.observed_on} | "
            f"`{record.run_id}` | "
            f"{record.status} | "
            f"{record.fetched_count} | "
            f"{record.saved_count} | "
            f"{record.skipped_count} | "
            f"{record.error_count} | "
            f"{record.skip_reason_count('no_keyword_match')} | "
            f"{record.skip_reason_count('excluded_keyword')} | "
            f"{record.skip_reason_count('normalization_value_error')} | "
            f"{record.other_skip_reason_count()} |"
        )
    if not records:
        lines.append("| pending | pending | pending | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |")

    lines.extend(
        [
            "",
            "## 누적 요약",
            "",
        ]
    )
    if records:
        lines.extend(_render_aggregate_summary(records))
    else:
        lines.append("- 아직 누적 관찰 기록이 없다.")

    lines.extend(
        [
            "",
            "## 실행 명령",
            "",
            "```powershell",
            '$env:PROJECT1_BIZINFO_CERT_KEY = "발급받은_인증키"',
            f"python scripts/observe_bizinfo_collect.py --config {config_path}",
            "```",
            "",
        ]
    )

    for index, record in enumerate(records, start=1):
        lines.extend(_render_record_detail(index, record))

    lines.extend(
        [
            "",
            "## 다음 라운드 검토 후보",
            "",
        ]
    )
    if next_round_candidates:
        lines.extend(f"- {candidate}" for candidate in next_round_candidates)
    else:
        lines.append("- 관찰 2~3일차 누적 후 후보를 확정한다.")
    lines.extend(
        [
            "",
            "## 메모",
            "",
            "- 이번 라운드에서는 제외 키워드 규칙을 직접 수정하지 않고 근거만 누적한다.",
            "- 동일 조건 비교를 위해 config, source_mode, page_size, retry 설정은 관찰 기간 동안 고정한다.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_record_detail(index: int, record: CollectObservationRecord) -> list[str]:
    lines = [
        f"## 관찰 {index}: {record.observed_on}",
        "",
        f"- run_id: `{record.run_id}`",
        f"- status: `{record.status}`",
        f"- fetched_count: `{record.fetched_count}`",
        f"- saved_count: `{record.saved_count}`",
        f"- skipped_count: `{record.skipped_count}`",
        f"- error_count: `{record.error_count}`",
        "- skip_reason 분포:",
    ]
    if record.skip_reason_counts:
        for reason, count in record.skip_reason_counts:
            lines.append(f"  - `{reason}`: `{count}`")
    else:
        lines.append("  - 진단 출력이 없거나 skipped 진단이 없어 분포를 집계하지 못했다.")

    lines.append("- 저장 대표 사례:")
    if record.saved_examples:
        for example in record.saved_examples:
            lines.append(f"  - {_format_example(example)}")
    else:
        lines.append("  - 저장 사례 없음")

    lines.append("- 제외 대표 사례:")
    if record.skipped_examples:
        for example in record.skipped_examples:
            lines.append(f"  - {_format_example(example)}")
    else:
        lines.append("  - 제외 사례 없음")
    lines.append("")
    return lines


def _render_aggregate_summary(records: tuple[CollectObservationRecord, ...]) -> list[str]:
    total_fetched = sum(record.fetched_count for record in records)
    total_saved = sum(record.saved_count for record in records)
    total_skipped = sum(record.skipped_count for record in records)
    total_errors = sum(record.error_count for record in records)
    no_keyword_titles = _aggregate_titles(records, "no_keyword_match")
    excluded_titles = _aggregate_titles(records, "excluded_keyword")
    excluded_keywords = _aggregate_excluded_keywords(records)
    saved_titles = _aggregate_saved_titles(records)

    lines = [
        f"- 누적 관찰 일수: `{len(records)}`일",
        f"- 누적 fetched_count: `{total_fetched}`",
        f"- 누적 saved_count: `{total_saved}`",
        f"- 누적 skipped_count: `{total_skipped}`",
        f"- 누적 error_count: `{total_errors}`",
    ]
    if len(records) < 3:
        lines.append(
            f"- 3일 누적 관찰은 아직 진행 중이며, 남은 관찰 필요 일수는 `{3 - len(records)}`일"
        )
    else:
        lines.append("- 3일 누적 관찰이 완료되었다.")
    lines.extend(
        [
            "- no_keyword_match 상위 skipped 제목:",
        ]
    )
    if no_keyword_titles:
        for title, count in no_keyword_titles:
            lines.append(f"  - `{title}`: `{count}`회")
    else:
        lines.append("  - 없음")

    lines.append("- excluded_keyword 상위 제외 사례:")
    if excluded_titles:
        for title, count in excluded_titles:
            lines.append(f"  - `{title}`: `{count}`회")
    else:
        lines.append("  - 없음")

    lines.append("- excluded_keyword 재검토 후보:")
    if excluded_keywords:
        for keyword, count in excluded_keywords:
            lines.append(f"  - `{keyword}`: `{count}`회")
    else:
        lines.append("  - 없음")

    lines.append("- 저장 대표 사례 누적:")
    if saved_titles:
        for title, count in saved_titles:
            lines.append(f"  - `{title}`: `{count}`회")
    else:
        lines.append("  - 없음")
    return lines


def _format_example(example: NoticeObservationExample) -> str:
    parts: list[str] = []
    title = example.title or "제목 없음"
    parts.append(title)
    if example.organization:
        parts.append(f"기관={example.organization}")
    if example.primary_domain:
        parts.append(f"primary_domain={example.primary_domain}")
    if example.skip_reason:
        parts.append(f"skip_reason={example.skip_reason}")

    keyword_parts: list[str] = []
    if example.matched_core_keywords:
        keyword_parts.append(f"core={list(example.matched_core_keywords)}")
    if example.matched_supporting_keywords:
        keyword_parts.append(f"supporting={list(example.matched_supporting_keywords)}")
    if example.matched_excluded_keywords:
        keyword_parts.append(f"exclude={list(example.matched_excluded_keywords)}")
    if keyword_parts:
        parts.append("keywords=" + ", ".join(keyword_parts))
    if example.detail_message:
        parts.append(f"detail={example.detail_message}")
    return " | ".join(parts)


def _aggregate_titles(
    records: tuple[CollectObservationRecord, ...],
    skip_reason: str,
    *,
    limit: int = 8,
) -> tuple[tuple[str, int], ...]:
    counter: Counter[str] = Counter()
    for record in records:
        for example in record.skipped_examples:
            if example.skip_reason != skip_reason:
                continue
            if not _is_usable_text(example.title):
                continue
            counter[str(example.title)] += 1
    return tuple(counter.most_common(limit))


def _aggregate_excluded_keywords(
    records: tuple[CollectObservationRecord, ...],
    *,
    limit: int = 8,
) -> tuple[tuple[str, int], ...]:
    counter: Counter[str] = Counter()
    for record in records:
        for example in record.skipped_examples:
            if example.skip_reason != "excluded_keyword":
                continue
            for keyword in example.matched_excluded_keywords:
                if not _is_usable_text(keyword):
                    continue
                counter[keyword] += 1
    return tuple(counter.most_common(limit))


def _aggregate_saved_titles(
    records: tuple[CollectObservationRecord, ...],
    *,
    limit: int = 8,
) -> tuple[tuple[str, int], ...]:
    counter: Counter[str] = Counter()
    for record in records:
        for example in record.saved_examples:
            if not _is_usable_text(example.title):
                continue
            counter[str(example.title)] += 1
    return tuple(counter.most_common(limit))


def _observation_date(run_started: dict[str, Any] | None, summary: dict[str, Any]) -> str:
    if run_started is not None:
        timestamp = _string_or_none(run_started.get("timestamp"))
        if timestamp is not None and len(timestamp) >= 10:
            return timestamp[:10]
    run_id = str(summary.get("run_id", ""))
    if len(run_id) >= 8 and run_id[:8].isdigit():
        return f"{run_id[:4]}-{run_id[4:6]}-{run_id[6:8]}"
    return "unknown"


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if _string_or_none(item) is not None)


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_usable_text(value: str | None) -> bool:
    if value is None:
        return False
    return "�" not in value
