"""Keyword matching domain service used by source normalizers."""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass

from app.domain import BusinessDomain, KeywordGroup, MatchedKeyword


KEYWORD_DOMAIN_MAP: dict[str, BusinessDomain] = {
    "ai": BusinessDomain.AI,
    "인공지능": BusinessDomain.AI,
    "디지털전환": BusinessDomain.DX,
    "dx": BusinessDomain.DX,
    "디지털트윈": BusinessDomain.DX,
    "시스템 통합": BusinessDomain.SI,
    "si": BusinessDomain.SI,
    "정보화": BusinessDomain.SI,
    "데이터": BusinessDomain.DATA,
    "빅데이터": BusinessDomain.DATA,
    "클라우드": BusinessDomain.INFRA,
    "인프라": BusinessDomain.INFRA,
    "서버": BusinessDomain.INFRA,
    "네트워크": BusinessDomain.INFRA,
    "사물인터넷": BusinessDomain.INFRA,
    "iot": BusinessDomain.INFRA,
    "보안": BusinessDomain.SECURITY,
    "ict": BusinessDomain.SI,
    "sw": BusinessDomain.SI,
    "소프트웨어": BusinessDomain.SI,
    "it서비스": BusinessDomain.MAINTENANCE,
    "유지보수": BusinessDomain.MAINTENANCE,
}
DOMAIN_PRIORITY = (
    BusinessDomain.AI,
    BusinessDomain.DX,
    BusinessDomain.SI,
    BusinessDomain.INFRA,
    BusinessDomain.DATA,
    BusinessDomain.SECURITY,
    BusinessDomain.MAINTENANCE,
)
FIELD_PRIORITY = ("title", "summary", "organization", "raw_source_name")


@dataclass(frozen=True, slots=True)
class KeywordSet:
    core: tuple[str, ...]
    supporting: tuple[str, ...]
    exclude: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KeywordMatchResult:
    eligible: bool
    business_domains: tuple[BusinessDomain, ...]
    primary_domain: BusinessDomain | None
    match_keywords: tuple[MatchedKeyword, ...]
    excluded_keywords: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class _MatchEvidence:
    keyword: str
    group: KeywordGroup
    domain: BusinessDomain
    field_index: int
    position: int


def evaluate_keywords(fields: dict[str, str | None], keywords: KeywordSet) -> KeywordMatchResult:
    """Evaluate eligibility and domain classification from configured keywords."""

    excluded = _find_excluded_keywords(fields, keywords.exclude)
    if excluded:
        return KeywordMatchResult(
            eligible=False,
            business_domains=(),
            primary_domain=None,
            match_keywords=(),
            excluded_keywords=excluded,
        )

    evidence = _collect_match_evidence(fields, keywords)
    if not evidence:
        return KeywordMatchResult(
            eligible=False,
            business_domains=(),
            primary_domain=None,
            match_keywords=(),
        )

    domains = tuple(
        domain
        for domain in DOMAIN_PRIORITY
        if any(item.domain == domain for item in evidence)
    )
    if not domains:
        return KeywordMatchResult(
            eligible=False,
            business_domains=(),
            primary_domain=None,
            match_keywords=(),
        )

    primary_domain = _select_primary_domain(evidence)
    match_keywords = tuple(
        MatchedKeyword(keyword=item.keyword, group=item.group, domain=item.domain)
        for item in _deduplicate_evidence(evidence)
    )
    return KeywordMatchResult(
        eligible=True,
        business_domains=domains,
        primary_domain=primary_domain,
        match_keywords=match_keywords,
    )


def _find_excluded_keywords(fields: dict[str, str | None], exclude_keywords: tuple[str, ...]) -> tuple[str, ...]:
    found: list[str] = []
    for field_name in FIELD_PRIORITY:
        text = _normalize_text(fields.get(field_name) or "")
        for keyword in exclude_keywords:
            if _contains_keyword(text, keyword):
                found.append(keyword)
    return tuple(dict.fromkeys(found))


def _collect_match_evidence(fields: dict[str, str | None], keywords: KeywordSet) -> tuple[_MatchEvidence, ...]:
    evidence: list[_MatchEvidence] = []
    keyword_groups = (
        (KeywordGroup.CORE, keywords.core),
        (KeywordGroup.SUPPORTING, keywords.supporting),
    )
    for field_index, field_name in enumerate(FIELD_PRIORITY):
        text = _normalize_text(fields.get(field_name) or "")
        if not text:
            continue
        for group, group_keywords in keyword_groups:
            for keyword in group_keywords:
                position = _find_keyword(text, keyword)
                if position < 0:
                    continue
                domain = KEYWORD_DOMAIN_MAP.get(_normalize_keyword(keyword))
                if domain is None:
                    continue
                evidence.append(
                    _MatchEvidence(
                        keyword=keyword,
                        group=group,
                        domain=domain,
                        field_index=field_index,
                        position=position,
                    )
                )
    return tuple(evidence)


def _select_primary_domain(evidence: tuple[_MatchEvidence, ...]) -> BusinessDomain:
    core_matches = [item for item in evidence if item.group == KeywordGroup.CORE]
    candidates = core_matches or list(evidence)
    return min(
        candidates,
        key=lambda item: (
            DOMAIN_PRIORITY.index(item.domain),
            item.field_index,
            item.position,
        ),
    ).domain


def _deduplicate_evidence(evidence: tuple[_MatchEvidence, ...]) -> tuple[_MatchEvidence, ...]:
    seen: set[tuple[str, KeywordGroup, BusinessDomain]] = set()
    result: list[_MatchEvidence] = []
    for item in evidence:
        key = (item.keyword, item.group, item.domain)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return tuple(result)


def _contains_keyword(text: str, keyword: str) -> bool:
    return _find_keyword(text, keyword) >= 0


def _find_keyword(text: str, keyword: str) -> int:
    normalized_keyword = _normalize_keyword(keyword)
    if not normalized_keyword:
        return -1
    if normalized_keyword in {"ai", "dx", "si"}:
        match = re.search(
            rf"(?<![a-z0-9]){re.escape(normalized_keyword)}(?![a-z0-9])",
            text,
        )
        return match.start() if match else -1
    return text.find(normalized_keyword)


def _normalize_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unicodedata.normalize("NFKC", value)
    value = value.casefold()
    return re.sub(r"[\s,()\[\]{}]+", " ", value).strip()


def _normalize_keyword(value: str) -> str:
    return _normalize_text(value)
