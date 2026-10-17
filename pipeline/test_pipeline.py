"""Invariant tests for labeling, value score, and equivalence."""

from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.catalog import assign_label, context_score, hermes_fit
from pipeline.compute import calculate_value_score
from pipeline.ingest.openrouterlist import expand_weekly
from pipeline.schema import BenchmarkType, ModelSnapshot, RouteVaultLabel


class LabelTests(unittest.TestCase):
    def test_planner_needs_agentic_and_intel(self):
        self.assertEqual(
            assign_label(55, 70, 50, 12.0, 1000),
            RouteVaultLabel.PROJECT_PLANNER,
        )

    def test_budget_on_low_price(self):
        self.assertEqual(
            assign_label(10, 10, 5, 0.4, 128),
            RouteVaultLabel.BUDGET_EVERYDAY,
        )

    def test_junior_from_coding(self):
        self.assertEqual(
            assign_label(20, 40, 10, 3.0, 128),
            RouteVaultLabel.JUNIOR_DEV,
        )

    def test_hermes_recommended(self):
        self.assertEqual(hermes_fit(55, 70, 50, 200), "Recommended")
        self.assertEqual(hermes_fit(10, 10, 5, 32), "Limited")

    def test_context_score_bounded(self):
        self.assertGreater(context_score(128), 20)
        self.assertLessEqual(context_score(2000), 100)


class ValueTests(unittest.TestCase):
    def test_cheaper_wins_same_benches(self):
        benches = {
            BenchmarkType.REASONING: 50,
            BenchmarkType.CODING: 50,
            BenchmarkType.TOOL_USE: 50,
        }
        expensive = ModelSnapshot(
            model_id="a", date=date.today(), input_price=10, output_price=10, benchmarks=benches
        )
        cheap = ModelSnapshot(
            model_id="b", date=date.today(), input_price=1, output_price=1, benchmarks=benches
        )
        self.assertGreater(calculate_value_score(cheap), calculate_value_score(expensive))

    def test_empty_benches_zero(self):
        snap = ModelSnapshot(model_id="z", date=date.today(), input_price=1, output_price=1)
        self.assertEqual(calculate_value_score(snap), 0.0)


class HistoryExpandTests(unittest.TestCase):
    def test_does_not_invent_before_first_seen(self):
        rec = {
            "first_seen": "2026-07-01",
            "points": [["2026-07-01", 2.0, 10.0], ["2026-07-15", 1.0, 5.0]],
        }
        series = expand_weekly(
            rec,
            window_start=date(2026, 2, 1),
            window_end=date(2026, 7, 29),
        )
        self.assertTrue(series)
        self.assertGreaterEqual(series[0][0], date(2026, 7, 1))
        self.assertNotIn(date(2026, 3, 1), [d for d, *_ in series])
        mid = next(row for row in series if row[0] == date(2026, 7, 15))
        self.assertEqual(mid[1:], (1.0, 5.0))

    def test_holds_last_known_price(self):
        rec = {
            "first_seen": "2026-06-01",
            "points": [["2026-06-01", 0.3, 1.2]],
        }
        series = expand_weekly(
            rec,
            window_start=date(2026, 6, 1),
            window_end=date(2026, 6, 29),
        )
        self.assertGreaterEqual(len(series), 4)
        self.assertTrue(all(row[1:] == (0.3, 1.2) for row in series))


class ExportContractTests(unittest.TestCase):
    def test_dataset_if_present(self):
        path = ROOT / "code" / "routevault-staging" / "data" / "dataset.json"
        if not path.exists():
            self.skipTest("dataset.json not generated")
        data = json.loads(path.read_text())
        self.assertIn("models", data)
        self.assertIn("honesty", data)
        self.assertGreaterEqual(len(data["models"]), 1)
        self.assertEqual(data["honesty"]["prices"], "live")
        for m in data["models"]:
            self.assertIn("model_id", m)
            self.assertIn("openrouter_id", m)
            self.assertIn("rv_label", m)
            self.assertGreaterEqual(m["total_price"], 0)
        tiers = {t["tier"] for t in data["equivalence"]}
        self.assertIn("Project Planner", tiers)
        self.assertTrue(all("/" in (t.get("pick_openrouter_id") or "x/y") for t in data["equivalence"] if t.get("pick")))


class NewsFilterTests(unittest.TestCase):
    def test_drops_politics_keeps_models(self):
        from pipeline.ingest.news import is_politics, parse_feed, news_id

        self.assertTrue(is_politics("Senate votes on AI bill", "Congress debates"))
        self.assertFalse(is_politics("OpenAI releases GPT-5.6", "API pricing dropped"))
        rss = b"""<?xml version="1.0"?>
        <rss><channel>
          <item>
            <title>OpenAI drops API prices</title>
            <link>https://example.com/ai</link>
            <description>Tokens cheaper</description>
          </item>
          <item>
            <title>Trump holds rally</title>
            <link>https://example.com/pol</link>
            <description>Campaign trail</description>
          </item>
        </channel></rss>"""
        items = parse_feed(rss, "Test")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.com/ai")
        self.assertEqual(items[0]["id"], news_id("https://example.com/ai"))


class DiscoverTests(unittest.TestCase):
    def test_promotes_aa_and_skips_free(self):
        from pipeline.discover import scan_new_models, should_promote

        raw = [
            {
                "id": "acme/titan-1:free",
                "name": "Titan Free",
                "pricing": {"prompt": "0", "completion": "0"},
                "benchmarks": {"artificial_analysis": {"intelligence_index": 80}},
            },
            {
                "id": "acme/titan-1",
                "name": "Titan",
                "pricing": {"prompt": "0.000002", "completion": "0.000004"},
                "benchmarks": {"artificial_analysis": {"intelligence_index": 80, "coding_index": 70}},
            },
            {
                "id": "acme/unknown-chat",
                "name": "Unknown",
                "pricing": {"prompt": "0.000001", "completion": "0.000001"},
                "benchmarks": {},
            },
        ]
        self.assertFalse(should_promote(raw[0]))
        self.assertTrue(should_promote(raw[1]))
        found, promote = scan_new_models(raw, known_openrouter_ids=set())
        ids = {r["openrouter_id"] for r in found}
        self.assertIn("acme/titan-1", ids)
        self.assertIn("acme/unknown-chat", ids)
        self.assertNotIn("acme/titan-1:free", ids)
        self.assertEqual([m["id"] for m in promote], ["acme/titan-1"])


if __name__ == "__main__":
    unittest.main()
