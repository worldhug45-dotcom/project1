from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest import TestCase

from app.filters import KeywordSet
from app.normalizers import BizinfoNoticeNormalizer
from app.ops import ConfigurationAppError
from app.sources import (
    BizinfoApiHttpClient,
    BizinfoFixtureSourceAdapter,
    BizinfoNoticeRaw,
    BizinfoSourceAdapter,
    parse_bizinfo_payload,
)


FIXTURE_PATH = Path("tests/fixtures/bizinfo/support_notices.json")
KEYWORDS = KeywordSet(
    core=("AI", "DX", "SI"),
    supporting=("data", "infra", "cloud", "security"),
    exclude=("hiring", "training"),
)


class BizinfoSourceTests(TestCase):
    def test_fixture_adapter_fetches_raw_notices(self) -> None:
        adapter = BizinfoFixtureSourceAdapter(FIXTURE_PATH)

        notices = adapter.fetch()

        self.assertEqual(len(notices), 2)
        self.assertIsInstance(notices[0], BizinfoNoticeRaw)
        self.assertEqual(notices[0].source_notice_id, "BIZ-2026-0001")

    def test_parse_payload_accepts_top_level_items_shape(self) -> None:
        notices = parse_bizinfo_payload(
            {
                "items": [
                    {
                        "pblancId": "BIZ-1",
                        "pblancNm": "Cloud support notice",
                        "jrsdInsttNm": "MSS",
                        "pblancUrl": "https://www.bizinfo.go.kr/notice/BIZ-1",
                    }
                ]
            }
        )

        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0].source_notice_id, "BIZ-1")
        self.assertIsNone(notices[0].summary)

    def test_source_adapter_parses_official_json_array_shape(self) -> None:
        adapter = BizinfoSourceAdapter(
            _StaticHttpClient(
                {
                    "jsonArray": {
                        "item": [
                            {
                                "pblancId": "PBLN_1",
                                "pblancNm": "AI automation support",
                                "jrsdInsttNm": "MSS",
                                "pblancUrl": "https://www.bizinfo.go.kr/web/view.do?pblancId=PBLN_1",
                                "bsnsSumryCn": "AI support",
                                "creatPnttm": "2026-04-01 09:00:00",
                                "reqstBeginEndDe": "20260401 ~ 20260430",
                            }
                        ]
                    }
                }
            )
        )

        notices = adapter.fetch()

        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0].source_notice_id, "PBLN_1")
        self.assertEqual(notices[0].posted_at, "2026-04-01")
        self.assertEqual(notices[0].end_at, "20260430")

    def test_source_adapter_accepts_single_item_object_shape(self) -> None:
        adapter = BizinfoSourceAdapter(
            _StaticHttpClient(
                {
                    "jsonArray": {
                        "item": {
                            "pblancId": "PBLN_SINGLE",
                            "pblancNm": "AI automation support",
                            "jrsdInsttNm": "MSS",
                            "pblancUrl": "https://www.bizinfo.go.kr/web/view.do?pblancId=PBLN_SINGLE",
                            "creatPnttm": "2026-04-01 09:00:00",
                            "reqstBeginEndDe": "20260401 ~ 20260430",
                        }
                    }
                }
            )
        )

        notices = adapter.fetch()

        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0].source_notice_id, "PBLN_SINGLE")

    def test_source_adapter_accepts_json_array_list_shape(self) -> None:
        adapter = BizinfoSourceAdapter(
            _StaticHttpClient(
                {
                    "jsonArray": [
                        {
                            "pblancId": "PBLN_LIST",
                            "pblancNm": "AI automation support",
                            "jrsdInsttNm": "MSS",
                            "pblancUrl": "https://www.bizinfo.go.kr/web/view.do?pblancId=PBLN_LIST",
                            "creatPnttm": "2026-04-01 09:00:00",
                            "reqstBeginEndDe": "2026-04-01 ~ 2026-04-30",
                        }
                    ]
                }
            )
        )

        notices = adapter.fetch()

        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0].source_notice_id, "PBLN_LIST")
        self.assertEqual(notices[0].end_at, "2026-04-30")

    def test_api_http_client_builds_request_with_cert_key_without_logging_it(self) -> None:
        captured: dict[str, str] = {}

        def opener(request, timeout: int):
            captured["url"] = request.full_url
            captured["timeout"] = str(timeout)
            return _BytesResponse(
                {
                    "jsonArray": {
                        "item": [
                            {
                                "pblancId": "PBLN_1",
                                "pblancNm": "AI automation support",
                                "jrsdInsttNm": "MSS",
                                "pblancUrl": "https://www.bizinfo.go.kr/web/view.do?pblancId=PBLN_1",
                            }
                        ]
                    }
                }
            )

        client = BizinfoApiHttpClient(
            endpoint="https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do",
            cert_key="secret-key",
            timeout_seconds=7,
            retry_count=0,
            page_size=5,
            opener=opener,
            sleeper=lambda _seconds: None,
        )

        payload = client.get_json()

        self.assertIn("crtfcKey=secret-key", captured["url"])
        self.assertIn("searchCnt=5", captured["url"])
        self.assertEqual(captured["timeout"], "7")
        self.assertIn("jsonArray", payload)

    def test_api_http_client_rejects_invalid_cert_key_without_echoing_secret(self) -> None:
        client = BizinfoApiHttpClient(
            endpoint="https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do",
            cert_key="secret-key",
            retry_count=0,
            opener=lambda request, timeout: _BytesResponse(
                {"reqErr": "존재하지 않는 인증키 입니다."}
            ),
            sleeper=lambda _seconds: None,
        )

        with self.assertRaises(ConfigurationAppError) as context:
            client.get_json()

        self.assertIn("PROJECT1_BIZINFO_CERT_KEY", str(context.exception))
        self.assertNotIn("secret-key", str(context.exception))

    def test_normalizer_converts_eligible_raw_notice_to_notice(self) -> None:
        raw_notice = BizinfoNoticeRaw(
            source_notice_id="BIZ-1",
            title="AI automation support",
            organization="MSS",
            posted_at="2026-04-01",
            end_at="20260430",
            status="접수중",
            url="https://www.bizinfo.go.kr/web/view.do?pblancId=BIZ-1",
            summary="AI data support",
        )
        normalizer = BizinfoNoticeNormalizer(KEYWORDS)

        notice = normalizer.normalize(raw_notice)

        self.assertEqual(notice.source.value, "bizinfo")
        self.assertEqual(notice.notice_type.value, "support")
        self.assertEqual(notice.primary_domain.value, "ai")
        self.assertEqual(notice.posted_at.isoformat(), "2026-04-01")
        self.assertEqual(notice.end_at.isoformat(), "2026-04-30")
        self.assertEqual(notice.status.value, "open")

    def test_normalizer_keeps_notice_when_optional_date_is_free_form(self) -> None:
        raw_notice = BizinfoNoticeRaw(
            source_notice_id="BIZ-2",
            title="AI support notice",
            organization="MOTIE",
            posted_at="2026-04-01",
            end_at="사업별 상이",
            status="접수중",
            url="https://www.bizinfo.go.kr/web/view.do?pblancId=BIZ-2",
            summary="AI support",
        )
        normalizer = BizinfoNoticeNormalizer(
            KeywordSet(
                core=("AI", "DX", "SI"),
                supporting=("data", "infra", "cloud"),
                exclude=("hiring", "training"),
            )
        )

        notice = normalizer.normalize(raw_notice)

        self.assertEqual(notice.source_notice_id, "BIZ-2")
        self.assertEqual(notice.primary_domain.value, "ai")
        self.assertEqual(notice.posted_at.isoformat(), "2026-04-01")
        self.assertIsNone(notice.end_at)


class _StaticHttpClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def get_json(self) -> dict[str, object]:
        return dict(self._payload)


class _BytesResponse(BytesIO):
    def __init__(self, payload: dict[str, object]) -> None:
        super().__init__(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def __enter__(self) -> "_BytesResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None
