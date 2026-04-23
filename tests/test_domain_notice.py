from datetime import UTC, datetime
from unittest import TestCase

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


class NoticeModelTests(TestCase):
    def test_notice_accepts_valid_common_model(self) -> None:
        notice = Notice(
            source=NoticeSource.BIZINFO,
            notice_type=NoticeType.SUPPORT,
            business_domains=(BusinessDomain.AI,),
            primary_domain=BusinessDomain.AI,
            title="AI 기반 업무 자동화 지원사업",
            organization="중소벤처기업부",
            status=NoticeStatus.OPEN,
            url="https://example.com/notices/1",
            match_keywords=(
                MatchedKeyword(
                    keyword="AI",
                    group=KeywordGroup.CORE,
                    domain=BusinessDomain.AI,
                ),
            ),
            collected_at=datetime.now(UTC),
            source_notice_id="BIZ-1",
        )

        self.assertEqual(notice.primary_domain, BusinessDomain.AI)

    def test_notice_rejects_primary_domain_outside_business_domains(self) -> None:
        with self.assertRaises(ValueError):
            Notice(
                source=NoticeSource.BIZINFO,
                notice_type=NoticeType.SUPPORT,
                business_domains=(BusinessDomain.INFRA,),
                primary_domain=BusinessDomain.AI,
                title="AI 기반 업무 자동화 지원사업",
                organization="중소벤처기업부",
                status=NoticeStatus.OPEN,
                url="https://example.com/notices/1",
                match_keywords=(
                    MatchedKeyword(
                        keyword="AI",
                        group=KeywordGroup.CORE,
                        domain=BusinessDomain.AI,
                    ),
                ),
                collected_at=datetime.now(UTC),
            )

    def test_notice_rejects_naive_collected_at(self) -> None:
        with self.assertRaises(ValueError):
            Notice(
                source=NoticeSource.BIZINFO,
                notice_type=NoticeType.SUPPORT,
                business_domains=(BusinessDomain.AI,),
                primary_domain=BusinessDomain.AI,
                title="AI 기반 업무 자동화 지원사업",
                organization="중소벤처기업부",
                status=NoticeStatus.OPEN,
                url="https://example.com/notices/1",
                match_keywords=(
                    MatchedKeyword(
                        keyword="AI",
                        group=KeywordGroup.CORE,
                        domain=BusinessDomain.AI,
                    ),
                ),
                collected_at=datetime.now(),
            )

    def test_deduplication_key_prefers_source_notice_id(self) -> None:
        notice = Notice(
            source=NoticeSource.BIZINFO,
            notice_type=NoticeType.SUPPORT,
            business_domains=(BusinessDomain.AI,),
            primary_domain=BusinessDomain.AI,
            title="AI 기반 업무 자동화 지원사업",
            organization="중소벤처기업부",
            status=NoticeStatus.OPEN,
            url="https://example.com/notices/1",
            match_keywords=(
                MatchedKeyword(
                    keyword="AI",
                    group=KeywordGroup.CORE,
                    domain=BusinessDomain.AI,
                ),
            ),
            collected_at=datetime.now(UTC),
            source_notice_id="  BIZ-1  ",
        )

        key = DeduplicationKey.from_notice(notice)

        self.assertEqual(key.key_type, "source_notice_id")
        self.assertEqual(key.key_value, "BIZ-1")
