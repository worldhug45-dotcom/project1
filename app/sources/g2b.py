"""G2B source adapter and raw DTO parser."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain import NoticeSource
from app.ops import ConfigurationAppError, FatalError, RetryableError


G2B_BID_API_ENDPOINT = (
    "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc"
)
G2B_NOTICE_DETAIL_URL = "https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo={bid_notice_no}&bidPbancOrd={bid_notice_ord}"
G2B_API_KEY_REQUIRED_MESSAGE = (
    "나라장터 API 서비스키가 필요합니다. PROJECT1_G2B_API_KEY를 설정하세요."
)
G2B_API_KEY_INVALID_MESSAGE = (
    "나라장터 API 서비스키 인증에 실패했습니다. PROJECT1_G2B_API_KEY를 확인하세요."
)


class HttpClient(Protocol):
    """Minimal HTTP client contract for the G2B adapter."""

    def get_json(self) -> dict[str, Any]:
        """Return a decoded JSON payload from the configured endpoint."""
        ...


@dataclass(frozen=True, slots=True)
class G2BNoticeRaw:
    """Raw G2B bid notice DTO used at the Infrastructure boundary."""

    source_notice_id: str
    title: str
    organization: str
    posted_at: str | None
    end_at: str | None
    status: str | None
    url: str
    summary: str | None = None
    raw_source_name: str = "나라장터"
    bid_notice_no: str | None = None
    bid_notice_ord: str | None = None


@dataclass(slots=True)
class G2BApiHttpClient:
    """HTTP client skeleton for the official G2B bid notice API."""

    endpoint: str
    api_key: str
    timeout_seconds: int = 10
    retry_count: int = 3
    retry_backoff_seconds: int = 2
    page_size: int = 20
    inquiry_division: str = "1"
    inquiry_window_days: int = 7
    timezone_name: str = "Asia/Seoul"
    opener: Callable[..., Any] = urlopen
    sleeper: Callable[[float], None] = time.sleep
    now_provider: Callable[[tzinfo], datetime] = datetime.now

    def __post_init__(self) -> None:
        if not self.endpoint.strip():
            raise ConfigurationAppError("G2B API endpoint is required.")
        if not self.api_key.strip():
            raise ConfigurationAppError(G2B_API_KEY_REQUIRED_MESSAGE)
        if self.inquiry_division not in {"1", "3"}:
            raise ConfigurationAppError(
                "G2B inquiry_division currently supports only '1' or '3' in the MVP."
            )
        if self.inquiry_window_days < 0:
            raise ConfigurationAppError("G2B inquiry_window_days must be 0 or greater.")

    def get_json(self) -> dict[str, Any]:
        request = Request(
            self._build_request_url(),
            headers={
                "Accept": "application/json",
                "User-Agent": "project1/1.0",
            },
            method="GET",
        )
        last_error: BaseException | None = None
        for attempt in range(self.retry_count + 1):
            try:
                with self.opener(request, timeout=self.timeout_seconds) as response:
                    payload = json.load(response)
                if not isinstance(payload, dict):
                    raise FatalError(
                        "G2B API returned an unsupported JSON payload.",
                        source=NoticeSource.G2B.value,
                    )
                _raise_for_g2b_payload_error(payload)
                return payload
            except ConfigurationAppError:
                raise
            except RetryableError as exc:
                last_error = exc
                if attempt >= self.retry_count:
                    raise
            except HTTPError as exc:
                last_error = exc
                error_body = _read_http_error_body(exc)
                if _looks_like_auth_http_error(exc.code, error_body):
                    raise ConfigurationAppError(G2B_API_KEY_INVALID_MESSAGE) from exc
                if exc.code in {429} or 500 <= exc.code <= 599:
                    if attempt >= self.retry_count:
                        raise RetryableError(
                            f"G2B API request failed with HTTP {exc.code}.",
                            source=NoticeSource.G2B.value,
                        ) from exc
                else:
                    raise FatalError(
                        f"G2B API request failed with HTTP {exc.code}.",
                        source=NoticeSource.G2B.value,
                    ) from exc
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt >= self.retry_count:
                    raise RetryableError(
                        "G2B API request failed after retries.",
                        source=NoticeSource.G2B.value,
                    ) from exc
            except JSONDecodeError as exc:
                raise FatalError(
                    "G2B API returned invalid JSON.",
                    source=NoticeSource.G2B.value,
                ) from exc

            if attempt < self.retry_count and self.retry_backoff_seconds > 0:
                self.sleeper(self.retry_backoff_seconds)

        if isinstance(last_error, BaseException):
            raise RetryableError(
                "G2B API request failed after retries.",
                source=NoticeSource.G2B.value,
            ) from last_error
        raise RetryableError(
            "G2B API request failed after retries.",
            source=NoticeSource.G2B.value,
        )

    def _build_request_url(self) -> str:
        inquiry_begin, inquiry_end = self._build_inquiry_range()
        query = urlencode(
            {
                "serviceKey": self.api_key,
                "pageNo": "1",
                "numOfRows": str(self.page_size),
                "inqryDiv": self.inquiry_division,
                "inqryBgnDt": inquiry_begin,
                "inqryEndDt": inquiry_end,
                "type": "json",
            }
        )
        separator = "&" if "?" in self.endpoint else "?"
        return f"{self.endpoint}{separator}{query}"

    def _build_inquiry_range(self) -> tuple[str, str]:
        current_time = self.now_provider(_resolve_timezone(self.timezone_name))
        begin_time = current_time - timedelta(days=self.inquiry_window_days)
        return (
            begin_time.strftime("%Y%m%d%H%M"),
            current_time.strftime("%Y%m%d%H%M"),
        )


class G2BSourceAdapter:
    """NoticeSourcePort implementation for G2B."""

    source = NoticeSource.G2B

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def fetch(self) -> tuple[G2BNoticeRaw, ...]:
        payload = self._http_client.get_json()
        return parse_g2b_payload(payload)


class G2BFixtureSourceAdapter:
    """Fixture-backed source adapter for parser and normalizer tests."""

    source = NoticeSource.G2B

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path

    def fetch(self) -> tuple[G2BNoticeRaw, ...]:
        return load_g2b_fixture(self._fixture_path)


def load_g2b_fixture(path: Path) -> tuple[G2BNoticeRaw, ...]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return parse_g2b_payload(payload)


def parse_g2b_payload(payload: dict[str, Any]) -> tuple[G2BNoticeRaw, ...]:
    items = _extract_items(payload)
    return tuple(_parse_item(item) for item in items)


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    response = payload.get("response")
    if isinstance(response, dict):
        _raise_for_g2b_payload_error(payload)
        body = response.get("body")
        if isinstance(body, dict):
            body_items = _coerce_items(body.get("items"))
            if body_items is not None:
                return body_items
            if _has_zero_total_count(body):
                return []
    payload_items = _coerce_items(payload.get("items"))
    if payload_items is not None:
        return payload_items
    if _has_zero_total_count(payload):
        return []
    raise ValueError("G2B payload does not contain an items list.")


def _parse_item(item: dict[str, Any]) -> G2BNoticeRaw:
    bid_notice_no = _first_text(item, "bidNtceNo", "bidNoticeNo", "noticeNo")
    bid_notice_ord = _first_text(item, "bidNtceOrd", "bidNoticeOrd", "noticeOrd") or "000"
    source_notice_id = _build_source_notice_id(bid_notice_no, bid_notice_ord)
    title = _first_text(item, "bidNtceNm", "bidNoticeName", "title")
    organization = _first_text(
        item,
        "dminsttNm",
        "ntceInsttNm",
        "orderInsttNm",
        "organization",
    )
    url = _first_text(
        item,
        "bidNtceDtlUrl",
        "bidNtceUrl",
        "noticeUrl",
        "url",
    ) or _build_notice_url(bid_notice_no, bid_notice_ord)
    if not source_notice_id:
        raise ValueError("G2B notice is missing source_notice_id.")
    if not title:
        raise ValueError("G2B notice is missing title.")
    if not organization:
        raise ValueError("G2B notice is missing organization.")
    if not url:
        raise ValueError("G2B notice is missing url.")

    summary = _join_summary_parts(
        _first_text(item, "bidNtceDtlInfo", "summary", "noticeSummary"),
        _first_text(item, "bsnsDivNm", "prcmBsneSeNm", "procurementTypeName"),
        _first_text(item, "cntrctCnclsMthdNm", "contractMethodName"),
        _first_text(item, "bidMethdNm", "bidMethodName"),
    )

    return G2BNoticeRaw(
        source_notice_id=source_notice_id,
        title=title,
        organization=organization,
        posted_at=_first_text(item, "bidNtceDate", "bidNtceDt", "rgstDt", "postedAt"),
        end_at=_first_text(item, "bidClseDate", "bidClseDt", "endAt"),
        status=_first_text(item, "bidNtceSttusNm", "status", "bidStatus"),
        url=url,
        summary=summary,
        bid_notice_no=bid_notice_no,
        bid_notice_ord=bid_notice_ord,
    )


def _coerce_items(value: Any) -> list[dict[str, Any]] | None:
    if isinstance(value, list):
        items = [item for item in value if isinstance(item, dict)]
        return items or []
    if isinstance(value, dict):
        nested = value.get("item")
        if isinstance(nested, list):
            items = [item for item in nested if isinstance(item, dict)]
            return items or []
        if isinstance(nested, dict):
            return [nested]
        return [value]
    return None


def _has_zero_total_count(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for key in ("totalCount", "total_count", "totalCnt"):
        raw_count = value.get(key)
        if raw_count is None:
            continue
        try:
            return int(str(raw_count).strip()) == 0
        except ValueError:
            continue
    return False


def _first_text(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _join_summary_parts(*values: str | None) -> str | None:
    parts = [value for value in values if value]
    if not parts:
        return None
    return " | ".join(dict.fromkeys(parts))


def _build_source_notice_id(bid_notice_no: str | None, bid_notice_ord: str | None) -> str:
    if not bid_notice_no:
        return ""
    if bid_notice_ord:
        return f"{bid_notice_no}-{bid_notice_ord}"
    return bid_notice_no


def _build_notice_url(bid_notice_no: str | None, bid_notice_ord: str | None) -> str | None:
    if not bid_notice_no:
        return None
    return G2B_NOTICE_DETAIL_URL.format(
        bid_notice_no=bid_notice_no,
        bid_notice_ord=bid_notice_ord or "000",
    )


def _read_http_error_body(error: HTTPError) -> str:
    try:
        raw_body = error.read()
    except OSError:
        return ""
    if not raw_body:
        return ""
    return raw_body.decode("utf-8", errors="replace").strip()


def _looks_like_auth_http_error(status_code: int, error_body: str) -> bool:
    if status_code in {401, 403}:
        return True
    body_upper = error_body.upper()
    return "SERVICE KEY" in body_upper or "UNAUTHORIZED" in body_upper or "인증키" in error_body


def _raise_for_g2b_payload_error(payload: dict[str, Any]) -> None:
    header = _extract_g2b_error_header(payload)
    if not isinstance(header, dict):
        return

    result_code = str(header.get("resultCode", "")).strip()
    result_message = str(header.get("resultMsg", "")).strip()
    if not result_code or result_code == "00":
        return

    message_upper = result_message.upper()
    if "SERVICE KEY" in message_upper or "인증키" in result_message:
        raise ConfigurationAppError(G2B_API_KEY_INVALID_MESSAGE)
    raise FatalError(
        f"G2B API returned error {result_code}: {result_message or 'unknown error'}",
        source=NoticeSource.G2B.value,
    )


def _extract_g2b_error_header(payload: dict[str, Any]) -> dict[str, Any] | None:
    response = payload.get("response")
    if isinstance(response, dict):
        header = response.get("header")
        if isinstance(header, dict):
            return header

    response_error = payload.get("nkoneps.com.response.ResponseError")
    if isinstance(response_error, dict):
        header = response_error.get("header")
        if isinstance(header, dict):
            return header
    return None


def _resolve_timezone(value: str) -> tzinfo:
    try:
        return ZoneInfo(value)
    except ZoneInfoNotFoundError:
        if value == "Asia/Seoul":
            return timezone(timedelta(hours=9), name="Asia/Seoul")
        return UTC
