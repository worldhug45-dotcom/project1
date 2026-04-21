"""Bizinfo source adapter and raw DTO parser."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.domain import NoticeSource
from app.ops import ConfigurationAppError, FatalError, RetryableError


BIZINFO_API_ENDPOINT = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"


class HttpClient(Protocol):
    """Minimal HTTP client contract for the Bizinfo adapter."""

    def get_json(self) -> dict[str, Any]:
        """Return a decoded JSON payload from the configured endpoint."""
        ...


@dataclass(frozen=True, slots=True)
class BizinfoNoticeRaw:
    """Raw Bizinfo notice DTO used at the Infrastructure boundary."""

    source_notice_id: str
    title: str
    organization: str
    posted_at: str | None
    end_at: str | None
    status: str | None
    url: str
    summary: str | None = None
    raw_source_name: str = "기업마당"


@dataclass(slots=True)
class BizinfoApiHttpClient:
    """HTTP client for the official Bizinfo support notice API."""

    endpoint: str
    cert_key: str
    timeout_seconds: int = 10
    retry_count: int = 3
    retry_backoff_seconds: int = 2
    page_size: int = 20
    opener: Callable[..., Any] = urlopen
    sleeper: Callable[[float], None] = time.sleep

    def __post_init__(self) -> None:
        if not self.endpoint.strip():
            raise ConfigurationAppError("Bizinfo API endpoint is required.")
        if not self.cert_key.strip():
            raise ConfigurationAppError(
                "Bizinfo API 인증키가 필요합니다. PROJECT1_BIZINFO_CERT_KEY를 설정하세요."
            )

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
                        "Bizinfo API returned an unsupported JSON payload.",
                        source=NoticeSource.BIZINFO.value,
                    )
                _raise_for_bizinfo_payload_error(payload)
                return payload
            except ConfigurationAppError:
                raise
            except RetryableError as exc:
                last_error = exc
                if attempt >= self.retry_count:
                    raise
            except HTTPError as exc:
                last_error = exc
                if exc.code in {429} or 500 <= exc.code <= 599:
                    if attempt >= self.retry_count:
                        raise RetryableError(
                            f"Bizinfo API request failed with HTTP {exc.code}.",
                            source=NoticeSource.BIZINFO.value,
                        ) from exc
                else:
                    raise FatalError(
                        f"Bizinfo API request failed with HTTP {exc.code}.",
                        source=NoticeSource.BIZINFO.value,
                    ) from exc
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt >= self.retry_count:
                    raise RetryableError(
                        "Bizinfo API request failed after retries.",
                        source=NoticeSource.BIZINFO.value,
                    ) from exc
            except JSONDecodeError as exc:
                raise FatalError(
                    "Bizinfo API returned invalid JSON.",
                    source=NoticeSource.BIZINFO.value,
                ) from exc

            if attempt < self.retry_count and self.retry_backoff_seconds > 0:
                self.sleeper(self.retry_backoff_seconds)

        if isinstance(last_error, BaseException):
            raise RetryableError(
                "Bizinfo API request failed after retries.",
                source=NoticeSource.BIZINFO.value,
            ) from last_error
        raise RetryableError(
            "Bizinfo API request failed after retries.",
            source=NoticeSource.BIZINFO.value,
        )

    def _build_request_url(self) -> str:
        query = urlencode(
            {
                "crtfcKey": self.cert_key,
                "dataType": "json",
                "searchCnt": str(self.page_size),
            }
        )
        separator = "&" if "?" in self.endpoint else "?"
        return f"{self.endpoint}{separator}{query}"


class BizinfoSourceAdapter:
    """NoticeSourcePort implementation for Bizinfo."""

    source = NoticeSource.BIZINFO

    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    def fetch(self) -> tuple[BizinfoNoticeRaw, ...]:
        payload = self._http_client.get_json()
        return parse_bizinfo_payload(payload)


class BizinfoFixtureSourceAdapter:
    """Fixture-backed source adapter for parser and normalizer tests."""

    source = NoticeSource.BIZINFO

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path

    def fetch(self) -> tuple[BizinfoNoticeRaw, ...]:
        return load_bizinfo_fixture(self._fixture_path)


def load_bizinfo_fixture(path: Path) -> tuple[BizinfoNoticeRaw, ...]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return parse_bizinfo_payload(payload)


def parse_bizinfo_payload(payload: dict[str, Any]) -> tuple[BizinfoNoticeRaw, ...]:
    items = _extract_items(payload)
    return tuple(_parse_item(item) for item in items)


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    json_array = payload.get("jsonArray")
    if isinstance(json_array, dict):
        json_array_items = _coerce_items(json_array.get("item"))
        if json_array_items is not None:
            return json_array_items
    json_array_items = _coerce_items(json_array)
    if json_array_items is not None:
        return json_array_items
    body = payload.get("body")
    if isinstance(body, dict):
        body_items = _coerce_items(body.get("items"))
        if body_items is not None:
            return body_items
    response = payload.get("response")
    if isinstance(response, dict):
        body = response.get("body")
        if isinstance(body, dict):
            response_items = _coerce_items(body.get("items"))
            if response_items is not None:
                return response_items
    payload_items = _coerce_items(payload.get("items"))
    if payload_items is not None:
        return payload_items
    req_err = _first_available_error_message(payload)
    if req_err is not None:
        raise ValueError(f"Bizinfo payload returned an error: {req_err}")
    raise ValueError("Bizinfo payload does not contain an items list.")


def _parse_item(item: dict[str, Any]) -> BizinfoNoticeRaw:
    source_notice_id = _first_text(item, "pblancId", "seq", "id", "source_notice_id")
    title = _first_text(item, "pblancNm", "title")
    organization = _first_text(item, "jrsdInsttNm", "author", "organization", "department")
    url = _first_text(item, "pblancUrl", "link", "url")
    if not source_notice_id:
        raise ValueError("Bizinfo notice is missing source_notice_id.")
    if not title:
        raise ValueError("Bizinfo notice is missing title.")
    if not organization:
        raise ValueError("Bizinfo notice is missing organization.")
    if not url:
        raise ValueError("Bizinfo notice is missing url.")
    return BizinfoNoticeRaw(
        source_notice_id=source_notice_id,
        title=title,
        organization=organization,
        posted_at=_extract_posted_at(item),
        end_at=_extract_end_at(item),
        status=_optional_text(item, "pblancSttusNm", "status"),
        url=url,
        summary=_optional_text(item, "bsnsSumryCn", "summary", "description"),
    )


def _first_text(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _optional_text(item: dict[str, Any], *keys: str) -> str | None:
    value = _first_text(item, *keys)
    return value or None


def _extract_posted_at(item: dict[str, Any]) -> str | None:
    value = _optional_text(item, "creatPnttm", "posted_at", "startDate", "pubDate")
    if value is None:
        return None
    return value.split()[0]


def _extract_end_at(item: dict[str, Any]) -> str | None:
    direct_value = _optional_text(item, "reqstEndDe", "end_at", "endDate")
    if direct_value is not None:
        return direct_value
    period = _optional_text(item, "reqstBeginEndDe", "reqstDt")
    if period is None:
        return None
    if "~" in period:
        _start, end = period.split("~", maxsplit=1)
        return end.strip()
    return period.strip()


def _raise_for_bizinfo_payload_error(payload: dict[str, Any]) -> None:
    message = _first_available_error_message(payload)
    if message is None:
        return
    if "인증키" in message:
        raise ConfigurationAppError(
            "Bizinfo API 인증에 실패했습니다. PROJECT1_BIZINFO_CERT_KEY를 확인하세요."
        )
    raise FatalError(
        f"Bizinfo API returned an error payload: {message}",
        source=NoticeSource.BIZINFO.value,
    )


def _coerce_items(value: object) -> list[dict[str, Any]] | None:
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value
    if isinstance(value, dict) and _looks_like_notice_item(value):
        return [value]
    return None


def _looks_like_notice_item(value: dict[str, Any]) -> bool:
    notice_keys = (
        "pblancId",
        "pblancNm",
        "jrsdInsttNm",
        "pblancUrl",
        "seq",
        "link",
        "id",
        "source_notice_id",
    )
    return any(key in value for key in notice_keys)


def _first_available_error_message(payload: dict[str, Any]) -> str | None:
    message = _optional_text(payload, "reqErr", "error", "message")
    if message is not None:
        return message
    json_array = payload.get("jsonArray")
    if isinstance(json_array, dict):
        return _optional_text(json_array, "reqErr", "error", "message")
    return None
