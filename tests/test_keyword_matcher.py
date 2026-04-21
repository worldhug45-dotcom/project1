from unittest import TestCase

from app.filters import KeywordSet, evaluate_keywords


class KeywordMatcherTests(TestCase):
    def test_iot_keywords_map_to_infra_domain(self) -> None:
        result = evaluate_keywords(
            {
                "title": "사물인터넷(IoT) 측정기기 부착 지원사업",
                "summary": None,
                "organization": "경기도",
                "raw_source_name": "기업마당",
            },
            KeywordSet(
                core=("AI", "DX", "SI"),
                supporting=("사물인터넷", "IoT", "ICT", "SW", "소프트웨어"),
                exclude=("채용", "행사", "교육"),
            ),
        )

        self.assertTrue(result.eligible)
        self.assertEqual(result.primary_domain.value, "infra")
        self.assertEqual(tuple(domain.value for domain in result.business_domains), ("infra",))
        self.assertEqual(tuple(keyword.keyword for keyword in result.match_keywords), ("사물인터넷", "IoT"))

    def test_ict_and_sw_keywords_map_to_si_domain(self) -> None:
        result = evaluate_keywords(
            {
                "title": "비제조산업 점프업 기업 지원사업",
                "summary": "ICT/SW 분야 해당 기업 대상",
                "organization": "경상남도",
                "raw_source_name": "기업마당",
            },
            KeywordSet(
                core=("AI", "DX", "SI"),
                supporting=("사물인터넷", "IoT", "ICT", "SW", "소프트웨어"),
                exclude=("채용", "행사", "교육"),
            ),
        )

        self.assertTrue(result.eligible)
        self.assertEqual(result.primary_domain.value, "si")
        self.assertEqual(tuple(domain.value for domain in result.business_domains), ("si",))
        self.assertEqual(tuple(keyword.keyword for keyword in result.match_keywords), ("ICT", "SW"))
