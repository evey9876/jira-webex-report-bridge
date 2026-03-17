from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .config import Settings, load_settings
from .jira_client import fetch_jira_updates
from .report_builder import build_report_payload, build_webex_message, render_markdown
from .webex_client import send_webex_message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jira-webex-report")
    parser.add_argument(
        "--config",
        default="config/report_config.json",
        help="Path to JSON config file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("fetch")
    subparsers.add_parser("render")

    render_sample = subparsers.add_parser("render-sample")
    render_sample.add_argument("--input", required=True, help="Path to saved Jira JSON response")

    send_parser = subparsers.add_parser("send")
    send_parser.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = load_settings(args.config)

    if args.command == "fetch":
        jira_response = fetch_jira_updates(settings.jira)
        output_paths = _write_report_inputs(settings, jira_response)
        print(f"Fetched Jira issues and wrote raw response to {output_paths['jira_response']}")
        return 0

    if args.command == "render":
        jira_response = _load_or_fetch_jira_response(settings)
        outputs = _render_outputs(settings, jira_response)
        print(f"Wrote report files to {outputs['markdown']} and {outputs['json']}")
        return 0

    if args.command == "render-sample":
        jira_response = _load_json(Path(args.input))
        outputs = _render_outputs(settings, jira_response)
        print(f"Wrote sample-based report files to {outputs['markdown']} and {outputs['json']}")
        return 0

    if args.command == "send":
        jira_response = _load_or_fetch_jira_response(settings)
        outputs = _render_outputs(settings, jira_response)
        message = Path(outputs["webex_payload"]).read_text(encoding="utf-8")
        if args.dry_run:
            print(message)
            return 0
        response = send_webex_message(settings.webex, message)
        print(f"Sent Webex message with id {response.get('id', 'unknown')}")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


def _load_or_fetch_jira_response(settings: Settings) -> dict[str, Any]:
    path = settings.output.directory / "jira_search_response.json"
    if path.exists():
        return _load_json(path)
    jira_response = fetch_jira_updates(settings.jira)
    _write_report_inputs(settings, jira_response)
    return jira_response


def _render_outputs(settings: Settings, jira_response: dict[str, Any]) -> dict[str, Path]:
    report = build_report_payload(jira_response, settings.report)
    markdown = render_markdown(report, settings.report.audience, settings.report.owner_name)
    webex_message = build_webex_message(markdown, report, settings.report.audience)

    output_dir = settings.output.directory
    output_dir.mkdir(parents=True, exist_ok=True)

    report_json_path = output_dir / "jira_report.json"
    report_markdown_path = output_dir / "jira_report.md"
    webex_payload_path = output_dir / "webex_payload.json"

    report_json_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    report_markdown_path.write_text(markdown, encoding="utf-8")
    webex_payload_path.write_text(webex_message, encoding="utf-8")

    return {
        "json": report_json_path,
        "markdown": report_markdown_path,
        "webex_payload": webex_payload_path,
    }


def _write_report_inputs(settings: Settings, jira_response: dict[str, Any]) -> dict[str, Path]:
    output_dir = settings.output.directory
    output_dir.mkdir(parents=True, exist_ok=True)
    jira_response_path = output_dir / "jira_search_response.json"
    jira_response_path.write_text(
        json.dumps(jira_response, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return {"jira_response": jira_response_path}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

