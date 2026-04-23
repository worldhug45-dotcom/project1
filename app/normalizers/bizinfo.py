"""Bizinfo raw DTO to Notice normalizer."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain import KeywordGroup, Notice, NoticeSource, NoticeStatus, NoticeType
from app.filters import KeywordSet, evaluate_keywords
from app.ops import CollectNoticeDiagnostic
from app.sources import BizinfoNoticeRaw


class BizinfoNoticeNormalizer:
    """NoticeNormalizerPort implementation for Bizinfo DTOs."""

    def __init__(self, keywords: KeywordSet, timezone: str = "Asia/Seoul") -> None:
        self._keywords = keywords
        self._timezone = timezone

    def diagnose(self, raw_notice: object) -> CollectNoticeDiagnostic:
        if not isinstance(raw_notice, BizinfoNoticeRaw):
            raise TypeError("BizinfoNoticeNormalizer expects BizinfoNoticeRaw.")

        match_result = self._evaluate(raw_notice)
        eligible = match_result.eligible and match_result.primary_domain is not None
        return CollectNoticeDiagnostic(
            source=NoticeSource.BIZINFO,
            source_notice_id=raw_notice.source_notice_id,
            title=raw_notice.title,
            organization=raw_notice.organization,
            eligible=eligible,
            matched_core_keywords=_keywords_by_group(
                match_result.match_keywords, KeywordGroup.CORE
            ),
            matched_supporting_keywords=_keywords_by_group(
                match_result.match_keywords,
                KeywordGroup.SUPPORTING,
            ),
            matched_excluded_keywords=match_result.excluded_keywords,
            business_domains=tuple(domain.value for domain in match_result.business_domains),
            primary_domain=(
                match_result.primary_domain.value
                if match_result.primary_domain is not None
                else None
            ),
            skip_reason=(_keyword_skip_reason(match_result) if not eligible else None),
        )

    def normalize(self, raw_notice: object) -> Notice:
        if not isinstance(raw_notice, BizinfoNoticeRaw):
            raise TypeError("BizinfoNoticeNormalizer expects BizinfoNoticeRaw.")

        match_result = self._evaluate(raw_notice)
        if not match_result.eligible or match_result.primary_domain is None:
            raise ValueError("Bizinfo notice is not eligible by keyword rules.")

        return Notice(
            source=NoticeSource.BIZINFO,
            source_notice_id=raw_notice.source_notice_id,
            notice_type=NoticeType.SUPPORT,
            business_domains=match_result.business_domains,
            primary_domain=match_result.primary_domain,
            title=raw_notice.title,
            organization=raw_notice.organization,
            posted_at=_parse_optional_date(raw_notice.posted_at),
            end_at=_parse_optional_date(raw_notice.end_at),
            status=_normalize_status(raw_notice.status),
            url=raw_notice.url,
            match_keywords=match_result.match_keywords,
            collected_at=datetime.now(_resolve_timezone(self._timezone)),
            raw_source_name=raw_notice.raw_source_name,
            summary=raw_notice.summary,
        )

    def _evaluate(self, raw_notice: BizinfoNoticeRaw):
        return evaluate_keywords(
            {
                "title": raw_notice.title,
                "organization": raw_notice.organization,
                "summary": raw_notice.summary,
                "raw_source_name": raw_notice.raw_source_name,
            },
            self._keywords,
        )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    normalized = value.strip().replace(".", "-").replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported Bizinfo date format: {value}")


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return _parse_date(value)
    except ValueError:
        # Bizinfo sometimes returns free-form periods such as "사업별 상이".
        # Dates are optional in the common model, so keep the notice and drop
        # the field instead of failing the whole normalization.
        return None


def _normalize_status(value: str | None) -> NoticeStatus:
    if not value:
        return NoticeStatus.UNKNOWN
    text = value.strip()
    if any(keyword in text for keyword in ("접수중", "진행", "공고중")):
        return NoticeStatus.OPEN
    if any(keyword in text for keyword in ("마감", "종료")):
        return NoticeStatus.CLOSED
    if "예정" in text:
        return NoticeStatus.SCHEDULED
    return NoticeStatus.UNKNOWN


def _resolve_timezone(value: str):
    try:
        return ZoneInfo(value)
    except ZoneInfoNotFoundError:
        if value == "Asia/Seoul":
            return timezone(timedelta(hours=9), name="Asia/Seoul")
        if value == "UTC":
            return UTC
        raise


def _keywords_by_group(values, group: KeywordGroup) -> tuple[str, ...]:
    return tuple(item.keyword for item in values if item.group == group)


def _keyword_skip_reason(match_result) -> str:
    if match_result.excluded_keywords:
        return "excluded_keyword"
    if not match_result.match_keywords:
        return "no_keyword_match"
    if not match_result.business_domains or match_result.primary_domain is None:
        return "no_domain_match"
    return "keyword_ineligible"
