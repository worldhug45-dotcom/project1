import json
from pathlib import Path
from unittest import TestCase

from app.ops.observation import (
    load_observation_history,
    parse_collect_observation_lines,
    render_observation_log,
    save_observation_history,
    upsert_observation_record,
)
from tests.temp_utils import temporary_directory


class CollectObservationTests(TestCase):
    def test_parse_collect_observation_lines_builds_summary_and_skip_distribution(self) -> None:
        lines = [
            json.dumps(
                {
                    "action": "collect",
                    "event_type": "run_started",
                    "run_id": "20260420T101010101010Z_abc12345",
                    "status": "running",
                    "timestamp": "2026-04-20T10:10:10+09:00",
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "action": "collect",
                    "event_type": "collect_diagnostic",
                    "run_id": "20260420T101010101010Z_abc12345",
                    "status": "running",
                    "source": "bizinfo",
                    "metadata": {
                        "title": "AI 지원사업",
                        "organization": "MSS",
                        "eligible": True,
                        "outcome": "saved",
                        "skip_reason": None,
                        "matched_core_keywords": ["AI"],
                        "matched_supporting_keywords": ["클라우드"],
                        "matched_excluded_keywords": [],
                        "primary_domain": "ai",
                        "detail_message": None,
                    },
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "action": "collect",
                    "event_type": "collect_diagnostic",
                    "run_id": "20260420T101010101010Z_abc12345",
                    "status": "running",
                    "source": "bizinfo",
                    "metadata": {
                        "title": "일반 행사 공고",
                        "organization": "MSS",
                        "eligible": False,
                        "outcome": "skipped",
                        "skip_reason": "excluded_keyword",
                        "matched_core_keywords": [],
                        "matched_supporting_keywords": [],
                        "matched_excluded_keywords": ["행사"],
                        "primary_domain": None,
                        "detail_message": None,
                    },
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "action": "collect",
                    "summary_type": "run_summary",
                    "run_id": "20260420T101010101010Z_abc12345",
                    "status": "success",
                    "collected_count": 2,
                    "saved_count": 1,
                    "skipped_count": 1,
                    "error_count": 0,
                    "exported_files": [],
                    "source_results": [
                        {
                            "source": "bizinfo",
                            "collected_count": 2,
                            "saved_count": 1,
                            "skipped_count": 1,
                            "error_count": 0,
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        ]

        record = parse_collect_observation_lines(lines)

        self.assertEqual(record.observed_on, "2026-04-20")
        self.assertEqual(record.run_id, "20260420T101010101010Z_abc12345")
        self.assertEqual(record.fetched_count, 2)
        self.assertEqual(record.saved_count, 1)
        self.assertEqual(record.skipped_count, 1)
        self.assertEqual(record.error_count, 0)
        self.assertEqual(record.skip_reason_count("excluded_keyword"), 1)
        self.assertEqual(record.skip_reason_count("no_keyword_match"), 0)
        self.assertEqual(record.saved_examples[0].matched_core_keywords, ("AI",))
        self.assertEqual(record.skipped_examples[0].matched_excluded_keywords, ("행사",))

    def test_history_round_trip_and_render_observation_log(self) -> None:
        lines = [
            json.dumps(
                {
                    "action": "collect",
                    "event_type": "run_started",
                    "run_id": "20260420T111111111111Z_def67890",
                    "status": "running",
                    "timestamp": "2026-04-20T11:11:11+09:00",
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "action": "collect",
                    "event_type": "collect_diagnostic",
                    "run_id": "20260420T111111111111Z_def67890",
                    "status": "running",
                    "source": "bizinfo",
                    "metadata": {
                        "title": "스마트 제조 플랫폼 지원",
                        "organization": "Agency",
                        "eligible": False,
                        "outcome": "skipped",
                        "skip_reason": "no_keyword_match",
                        "matched_core_keywords": [],
                        "matched_supporting_keywords": [],
                        "matched_excluded_keywords": [],
                        "primary_domain": None,
                        "detail_message": "candidate for next round",
                    },
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "action": "collect",
                    "summary_type": "run_summary",
                    "run_id": "20260420T111111111111Z_def67890",
                    "status": "success",
                    "collected_count": 5,
                    "saved_count": 0,
                    "skipped_count": 5,
                    "error_count": 0,
                    "exported_files": [],
                    "source_results": [],
                },
                ensure_ascii=False,
            ),
        ]
        record = parse_collect_observation_lines(lines)
        records = upsert_observation_record((), record)

        with temporary_directory() as directory:
            history_path = Path(directory) / "observations.json"
            save_observation_history(history_path, records)
            reloaded = load_observation_history(history_path)

        self.assertEqual(reloaded[0].run_id, record.run_id)
        self.assertEqual(reloaded[0].skip_reason_count("no_keyword_match"), 1)

        markdown = render_observation_log(
            reloaded,
            config_path="config/settings.local.toml",
            source_mode="api",
            next_round_candidates=("플랫폼", "IP"),
        )

        self.assertIn("# 기업마당 collect 관찰 기록", markdown)
        self.assertIn("config/settings.local.toml", markdown)
        self.assertIn("no_keyword_match", markdown)
        self.assertIn("스마트 제조 플랫폼 지원", markdown)
        self.assertIn("플랫폼", markdown)
        self.assertIn("## 누적 요약", markdown)
        self.assertIn("누적 관찰 일수", markdown)
        self.assertIn("excluded_keyword 재검토 후보", markdown)
