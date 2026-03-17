from __future__ import annotations

import json
from pathlib import Path
import unittest

from jira_webex_report_bridge.config import load_settings
from jira_webex_report_bridge.report_builder import build_report_payload, render_markdown


class ReportBuilderTest(unittest.TestCase):
    def test_build_report_payload_categorizes_items(self) -> None:
        fixture_dir = Path(__file__).resolve().parents[1]
        settings = load_settings(fixture_dir / "config" / "report_config.example.json")
        jira_payload = json.loads(
            (fixture_dir / "sample_data" / "jira_search_response.json").read_text(
                encoding="utf-8"
            )
        )

        report = build_report_payload(jira_payload, settings.report)
        markdown = render_markdown(report, settings.report.audience, settings.report.owner_name)

        self.assertEqual(len(report.done_items), 1)
        self.assertEqual(len(report.in_progress_items), 1)
        self.assertEqual(len(report.blocked_items), 1)
        self.assertEqual(len(report.risk_items), 2)
        self.assertIn("OPS-102", markdown)
        self.assertIn("Weekly Jira Delivery Update", markdown)


if __name__ == "__main__":
    unittest.main()
