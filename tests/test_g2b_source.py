from io import BytesIO
from pathlib import Path
from datetime import datetime
from urllib.error import HTTPError
from unittest import TestCase

from app.filters import KeywordSet
from app.infrastructure.settings import G2B_API_KEY_ENV_VAR
from app.normalizers import G2BNoticeNormalizer
from app.ops import ConfigurationAppError, FatalError
from app.sources import (
    G2BApiHttpClient,
    G2BFixtureSourceAdapter,
    G2BNoticeRaw,
    G2BSourceAdapter,
    parse_g2b_payload,
)


FIXTURE_PATH = Path("tests/fixtures/g2b/bid_notices.json")
KEYWORDS = KeywordSet(
    core=("AI", "DX", "SI"),
    supporting=("data", "cloud", "infra", "security", "유지보수"),
    exclude=("hiring", "training", "행사"),
)


class G2BSourceTests(TestCase):
    def test_fixture_adapter_fetches_raw_notices(self) -> None:
        adapter = G2BFixtureSourceAdapter(FIXTURE_PATH)

        notices = adapter.fetch()

        self.assertEqual(len(notices), 2)
        self.assertIsInstance(notices[0], G2BNoticeRaw)
        self.assertEqual(notices[0].source_notice_id, "R26BK00000001-000")

    def test_parse_payload_accepts_top_level_items_shape(self) -> None:
        notices = parse_g2b_payload(
            {
                "items": [
                    {
                        "bidNtceNo": "R26BK1",
                        "bidNtceOrd": "001",
                        "bidNtceNm": "Cloud maintenance bid",
                        "dminsttNm": "MSS",
                        "bidNtceDtlUrl": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK1&bidPbancOrd=001",
                    }
                ]
            }
        )

        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0].source_notice_id, "R26BK1-001")
        self.assertIsNone(notices[0].summary)

    def test_source_adapter_parses_official_response_shape(self) -> None:
        adapter = G2BSourceAdapter(
            _StaticHttpClient(
                {
                    "response": {
                        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                        "body": {
                            "items": {
                                "item": [
                                    {
                                        "bidNtceNo": "R26BK100",
                                        "bidNtceOrd": "000",
                                        "bidNtceNm": "AI operation maintenance service",
                                        "dminsttNm": "MSS",
                                        "bidNtceDtlUrl": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK100&bidPbancOrd=000",
                                        "bidNtceDate": "2026-04-21",
                                        "bidClseDate": "2026-05-02 10:00",
                                        "bidNtceDtlInfo": "AI and cloud maintenance"
                                    }
                                ]
                            }
                        }
                    }
                }
            )
        )

        notices = adapter.fetch()

        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0].source_notice_id, "R26BK100-000")
        self.assertEqual(notices[0].posted_at, "2026-04-21")
        self.assertEqual(notices[0].end_at, "2026-05-02 10:00")

    def test_parse_payload_returns_empty_tuple_when_total_count_is_zero(self) -> None:
        notices = parse_g2b_payload(
            {
                "response": {
                    "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                    "body": {
                        "pageNo": 1,
                        "numOfRows": 20,
                        "totalCount": 0,
                    },
                }
            }
        )

        self.assertEqual(notices, ())

    def test_api_http_client_builds_request_with_service_key_without_logging_it(self) -> None:
        captured: dict[str, str] = {}

        def opener(request, timeout: int):
            captured["url"] = request.full_url
            captured["timeout"] = str(timeout)
            return _BytesResponse(
                {
                    "response": {
                        "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                        "body": {
                            "items": [
                                {
                                    "bidNtceNo": "R26BK200",
                                    "bidNtceOrd": "000",
                                    "bidNtceNm": "Cloud maintenance bid",
                                    "dminsttNm": "MSS",
                                    "bidNtceDtlUrl": "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK200&bidPbancOrd=000"
                                }
                            ]
                        }
                    }
                }
            )

        client = G2BApiHttpClient(
            endpoint="https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc",
            api_key="secret-key",
            timeout_seconds=7,
            retry_count=0,
            page_size=5,
            inquiry_window_days=2,
            opener=opener,
            sleeper=lambda _seconds: None,
            now_provider=lambda tz: datetime(2026, 4, 21, 15, 30, tzinfo=tz),
        )

        payload = client.get_json()

        self.assertIn("serviceKey=secret-key", captured["url"])
        self.assertIn("numOfRows=5", captured["url"])
        self.assertIn("inqryDiv=1", captured["url"])
        self.assertIn("inqryBgnDt=202604191530", captured["url"])
        self.assertIn("inqryEndDt=202604211530", captured["url"])
        self.assertEqual(captured["timeout"], "7")
        self.assertIn("response", payload)

    def test_api_http_client_rejects_invalid_service_key_without_echoing_secret(self) -> None:
        client = G2BApiHttpClient(
            endpoint="https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc",
            api_key="secret-key",
            retry_count=0,
            opener=lambda request, timeout: _BytesResponse(
                {
                    "response": {
                        "header": {
                            "resultCode": "30",
                            "resultMsg": "SERVICE KEY IS NOT REGISTERED ERROR."
                        }
                    }
                }
            ),
            sleeper=lambda _seconds: None,
        )

        with self.assertRaises(ConfigurationAppError) as context:
            client.get_json()

        self.assertIn(G2B_API_KEY_ENV_VAR, str(context.exception))
        self.assertNotIn("secret-key", str(context.exception))

    def test_api_http_client_treats_http_401_as_configuration_error(self) -> None:
        def opener(request, timeout: int):
            raise HTTPError(
                request.full_url,
                401,
                "Unauthorized",
                hdrs=None,
                fp=BytesIO(b"Unauthorized"),
            )

        client = G2BApiHttpClient(
            endpoint="https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc",
            api_key="secret-key",
            retry_count=0,
            opener=opener,
            sleeper=lambda _seconds: None,
        )

        with self.assertRaises(ConfigurationAppError) as context:
            client.get_json()

        self.assertIn(G2B_API_KEY_ENV_VAR, str(context.exception))
        self.assertNotIn("secret-key", str(context.exception))

    def test_api_http_client_handles_top_level_response_error_payload(self) -> None:
        client = G2BApiHttpClient(
            endpoint="https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc",
            api_key="secret-key",
            retry_count=0,
            opener=lambda request, timeout: _BytesResponse(
                {
                    "nkoneps.com.response.ResponseError": {
                        "header": {
                            "resultCode": "08",
                            "resultMsg": "필수값 입력 에러",
                        }
                    }
                }
            ),
            sleeper=lambda _seconds: None,
        )

        with self.assertRaisesRegex(FatalError, "필수값 입력 에러"):
            client.get_json()

    def test_normalizer_converts_eligible_raw_notice_to_notice(self) -> None:
        raw_notice = G2BNoticeRaw(
            source_notice_id="R26BK300-000",
            title="AI 기반 정보시스템 통합 유지보수 용역",
            organization="한국디지털진흥원",
            posted_at="2026/04/21",
            end_at="2026/05/02 10:00",
            status="공고중",
            url="https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK300&bidPbancOrd=000",
            summary="AI data cloud 유지보수 사업",
        )
        normalizer = G2BNoticeNormalizer(KEYWORDS)

        notice = normalizer.normalize(raw_notice)

        self.assertEqual(notice.source.value, "g2b")
        self.assertEqual(notice.notice_type.value, "bid")
        self.assertEqual(notice.primary_domain.value, "ai")
        self.assertEqual(notice.posted_at.isoformat(), "2026-04-21")
        self.assertEqual(notice.end_at.isoformat(), "2026-05-02")
        self.assertEqual(notice.status.value, "open")

    def test_normalizer_keeps_notice_when_optional_date_is_free_form(self) -> None:
        raw_notice = G2BNoticeRaw(
            source_notice_id="R26BK301-000",
            title="AI 운영 지원 용역",
            organization="한국디지털진흥원",
            posted_at="2026/04/21",
            end_at="사업별 상이",
            status="공고중",
            url="https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK301&bidPbancOrd=000",
            summary="AI cloud maintenance",
        )
        normalizer = G2BNoticeNormalizer(KEYWORDS)

        notice = normalizer.normalize(raw_notice)

        self.assertEqual(notice.posted_at.isoformat(), "2026-04-21")
        self.assertIsNone(notice.end_at)


class _StaticHttpClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def get_json(self) -> dict[str, object]:
        return self._payload


class _BytesResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        import io
        import json

        self._buffer = io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def __enter__(self):
        return self._buffer

    def __exit__(self, exc_type, exc, traceback) -> None:
        self._buffer.close()
