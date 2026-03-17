from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    email: str
    api_token: str
    jql: str
    max_results: int
    fields: list[str]


@dataclass(frozen=True)
class ReportConfig:
    title: str
    audience: str
    owner_name: str
    intro: str
    done_statuses: set[str]
    in_progress_statuses: set[str]
    blocked_statuses: set[str]
    risk_priorities: set[str]
    top_n: int
    references: list[str]
    parameters: dict[str, Any]


@dataclass(frozen=True)
class WebexConfig:
    access_token: str
    room_id: str | None
    to_person_email: str | None
    to_person_id: str | None


@dataclass(frozen=True)
class OutputConfig:
    directory: Path


@dataclass(frozen=True)
class Settings:
    jira: JiraConfig
    report: ReportConfig
    webex: WebexConfig
    output: OutputConfig
    config_path: Path


def load_settings(config_path: str | Path) -> Settings:
    path = Path(config_path).expanduser().resolve()
    data = json.loads(path.read_text(encoding="utf-8"))

    jira_data = data["jira"]
    report_data = data["report"]
    webex_data = data["webex"]
    output_data = data.get("output", {})

    return Settings(
        jira=JiraConfig(
            base_url=jira_data["base_url"].rstrip("/"),
            email=jira_data["email"],
            api_token=jira_data["api_token"],
            jql=jira_data["jql"],
            max_results=int(jira_data.get("max_results", 25)),
            fields=list(jira_data.get("fields", [])),
        ),
        report=ReportConfig(
            title=report_data["title"],
            audience=report_data["audience"],
            owner_name=report_data["owner_name"],
            intro=report_data["intro"],
            done_statuses={value.lower() for value in report_data.get("done_statuses", [])},
            in_progress_statuses={
                value.lower() for value in report_data.get("in_progress_statuses", [])
            },
            blocked_statuses={value.lower() for value in report_data.get("blocked_statuses", [])},
            risk_priorities={value.lower() for value in report_data.get("risk_priorities", [])},
            top_n=int(report_data.get("top_n", 5)),
            references=list(report_data.get("references", [])),
            parameters=dict(report_data.get("parameters", {})),
        ),
        webex=WebexConfig(
            access_token=webex_data["access_token"],
            room_id=webex_data.get("room_id"),
            to_person_email=webex_data.get("to_person_email"),
            to_person_id=webex_data.get("to_person_id"),
        ),
        output=OutputConfig(
            directory=(path.parent / output_data.get("directory", "output")).resolve()
        ),
        config_path=path,
    )
