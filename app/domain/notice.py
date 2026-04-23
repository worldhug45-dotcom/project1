"""Domain model for normalized business opportunity notices."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from re import sub
from urllib.parse import urlsplit, urlunsplit


class NoticeSource(StrEnum):
    """Supported source systems for the first MVP."""

    BIZINFO = "bizinfo"
    G2B = "g2b"


class NoticeType(StrEnum):
    """Normalized notice types."""

    SUPPORT = "support"
    BID = "bid"
    RND = "rnd"
    STARTUP = "startup"


class BusinessDomain(StrEnum):
    """Business domains used for internal classification."""

    AI = "ai"
    DX = "dx"
    SI = "si"
    INFRA = "infra"
    DATA = "data"
    SECURITY = "security"
    MAINTENANCE = "maintenance"


class NoticeStatus(StrEnum):
    """Common lifecycle status for notices."""

    OPEN = "open"
    CLOSED = "closed"
    SCHEDULED = "scheduled"
    UNKNOWN = "unknown"


class KeywordGroup(StrEnum):
    """Keyword group used for matching evidence."""

    CORE = "core"
    SUPPORTING = "supporting"
    EXCLUDE = "exclude"


@dataclass(frozen=True, slots=True)
class MatchedKeyword:
    """Keyword match evidence kept with a normalized notice."""

    keyword: str
    group: KeywordGroup
    domain: BusinessDomain | None = None

    def __post_init__(self) -> None:
        if not self.keyword.strip():
            raise ValueError("MatchedKeyword.keyword is required.")
        if self.group != KeywordGroup.EXCLUDE and self.domain is None:
            raise ValueError("Matched non-exclude keywords require a domain.")


@dataclass(frozen=True, slots=True)
class Notice:
    """Common data model passed between internal layers."""

    source: NoticeSource
    notice_type: NoticeType
    business_domains: tuple[BusinessDomain, ...]
    primary_domain: BusinessDomain
    title: str
    organization: str
    status: NoticeStatus
    url: str
    match_keywords: tuple[MatchedKeyword, ...]
    collected_at: datetime
    source_notice_id: str | None = None
    posted_at: date | None = None
    end_at: date | None = None
    raw_source_name: str | None = None
    summary: str | None = None

    def __post_init__(self) -> None:
        if not self.business_domains:
            raise ValueError("Notice.business_domains must not be empty.")
        if self.primary_domain not in self.business_domains:
            raise ValueError("Notice.primary_domain must be one of business_domains.")
        if not self.title.strip():
            raise ValueError("Notice.title is required.")
        if not self.organization.strip():
            raise ValueError("Notice.organization is required.")
        if not _is_clickable_url(self.url):
            raise ValueError("Notice.url must start with http:// or https://.")
        if not self.match_keywords:
            raise ValueError("Notice.match_keywords must not be empty.")
        if self.collected_at.tzinfo is None or self.collected_at.utcoffset() is None:
            raise ValueError("Notice.collected_at must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class DeduplicationKey:
    """Stable key used to prevent duplicate storage on repeated runs."""

    source: NoticeSource
    key_type: str
    key_value: str

    @classmethod
    def from_notice(cls, notice: Notice) -> "DeduplicationKey":
        if notice.source_notice_id and notice.source_notice_id.strip():
            return cls(
                source=notice.source,
                key_type="source_notice_id",
                key_value=_normalize_text(notice.source_notice_id),
            )

        if _is_clickable_url(notice.url):
            return cls(
                source=notice.source,
                key_type="url",
                key_value=_normalize_url(notice.url),
            )

        fingerprint = "|".join(
            [
                _normalize_text(notice.title),
                _normalize_text(notice.organization),
                notice.posted_at.isoformat() if notice.posted_at else "",
                notice.end_at.isoformat() if notice.end_at else "",
            ]
        )
        return cls(
            source=notice.source,
            key_type="content_fingerprint",
            key_value=fingerprint,
        )

    def __post_init__(self) -> None:
        if self.key_type not in {"source_notice_id", "url", "content_fingerprint"}:
            raise ValueError("Unsupported deduplication key type.")
        if not self.key_value.strip():
            raise ValueError("DeduplicationKey.key_value is required.")


def _is_clickable_url(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def _normalize_text(value: str) -> str:
    return sub(r"\s+", " ", value.strip())


def _normalize_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    path = parsed.path.rstrip("/") or parsed.path
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))
