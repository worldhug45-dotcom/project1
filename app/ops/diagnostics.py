"""Structured diagnostics for collect debugging output."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from app.domain import NoticeSource


@dataclass(frozen=True, slots=True)
class CollectNoticeDiagnostic:
    """Per-notice diagnostic payload for collect debugging."""

    source: NoticeSource
    source_notice_id: str | None
    title: str | None
    organization: str | None
    eligible: bool
    matched_core_keywords: tuple[str, ...] = ()
    matched_supporting_keywords: tuple[str, ...] = ()
    matched_excluded_keywords: tuple[str, ...] = ()
    business_domains: tuple[str, ...] = ()
    primary_domain: str | None = None
    outcome: str = "evaluated"
    skip_reason: str | None = None
    detail_message: str | None = None

    @classmethod
    def from_raw_notice(
        cls,
        *,
        source: NoticeSource,
        raw_notice: object,
        detail_message: str | None = None,
    ) -> "CollectNoticeDiagnostic":
        return cls(
            source=source,
            source_notice_id=_string_or_none(getattr(raw_notice, "source_notice_id", None)),
            title=_string_or_none(getattr(raw_notice, "title", None)),
            organization=_string_or_none(getattr(raw_notice, "organization", None)),
            eligible=False,
            detail_message=detail_message,
        )

    def with_outcome(
        self,
        *,
        outcome: str,
        skip_reason: str | None = None,
        detail_message: str | None = None,
    ) -> "CollectNoticeDiagnostic":
        return replace(
            self,
            outcome=outcome,
            skip_reason=skip_reason,
            detail_message=detail_message if detail_message is not None else self.detail_message,
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "source_notice_id": self.source_notice_id,
            "title": self.title,
            "organization": self.organization,
            "eligible": self.eligible,
            "outcome": self.outcome,
            "skip_reason": self.skip_reason,
            "matched_core_keywords": list(self.matched_core_keywords),
            "matched_supporting_keywords": list(self.matched_supporting_keywords),
            "matched_excluded_keywords": list(self.matched_excluded_keywords),
            "business_domains": list(self.business_domains),
            "primary_domain": self.primary_domain,
            "detail_message": self.detail_message,
        }


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
