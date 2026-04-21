"""Source adapters for external notice systems."""

from app.sources.bizinfo import (
    BIZINFO_API_ENDPOINT,
    BizinfoApiHttpClient,
    BizinfoFixtureSourceAdapter,
    BizinfoNoticeRaw,
    BizinfoSourceAdapter,
    load_bizinfo_fixture,
    parse_bizinfo_payload,
)
from app.sources.g2b import (
    G2B_BID_API_ENDPOINT,
    G2BApiHttpClient,
    G2BFixtureSourceAdapter,
    G2BNoticeRaw,
    G2BSourceAdapter,
    load_g2b_fixture,
    parse_g2b_payload,
)

__all__ = [
    "BIZINFO_API_ENDPOINT",
    "BizinfoApiHttpClient",
    "BizinfoFixtureSourceAdapter",
    "BizinfoNoticeRaw",
    "BizinfoSourceAdapter",
    "load_bizinfo_fixture",
    "parse_bizinfo_payload",
    "G2B_BID_API_ENDPOINT",
    "G2BApiHttpClient",
    "G2BFixtureSourceAdapter",
    "G2BNoticeRaw",
    "G2BSourceAdapter",
    "load_g2b_fixture",
    "parse_g2b_payload",
]
