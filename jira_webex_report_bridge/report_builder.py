from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .config import ReportConfig


@dataclass(frozen=True)
class IssueSummary:
    key: str
    summary: str
    status: str
    assignee: str
    priority: str
    due_date: str | None
    labels: list[str]
    issue_type: str
    updated: str


@dataclass(frozen=True)
class ReportPayload:
    title: str
    generated_at: str
    headline: str
    intro: str
    done_items: list[IssueSummary]
    in_progress_items: list[IssueSummary]
    blocked_items: list[IssueSummary]
    risk_items: list[IssueSummary]
    next_actions: list[str]
    references: list[str]
    parameters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "generated_at": self.generated_at,
            "headline": self.headline,
            "intro": self.intro,
            "done_items": [asdict(item) for item in self.done_items],
            "in_progress_items": [asdict(item) for item in self.in_progress_items],
            "blocked_items": [asdict(item) for item in self.blocked_items],
            "risk_items": [asdict(item) for item in self.risk_items],
            "next_actions": self.next_actions,
            "references": self.references,
            "parameters": self.parameters,
        }


def build_report_payload(jira_response: dict[str, Any], config: ReportConfig) -> ReportPayload:
    issues = [_normalize_issue(issue) for issue in jira_response.get("issues", [])]

    done_items = [item for item in issues if item.status.lower() in config.done_statuses]
    in_progress_items = [
        item for item in issues if item.status.lower() in config.in_progress_statuses
    ]
    blocked_items = [item for item in issues if item.status.lower() in config.blocked_statuses]
    risk_items = [item for item in issues if item.priority.lower() in config.risk_priorities]

    headline = (
        f"{len(done_items)} done, "
        f"{len(in_progress_items)} in progress, "
        f"{len(blocked_items)} blocked, "
        f"{len(risk_items)} high-risk items in scope."
    )

    next_actions = _build_next_actions(done_items, in_progress_items, blocked_items, risk_items)

    return ReportPayload(
        title=config.title,
        generated_at=datetime.now(timezone.utc).isoformat(),
        headline=headline,
        intro=config.intro,
        done_items=done_items[: config.top_n],
        in_progress_items=in_progress_items[: config.top_n],
        blocked_items=blocked_items[: config.top_n],
        risk_items=risk_items[: config.top_n],
        next_actions=next_actions[: config.top_n],
        references=config.references,
        parameters=config.parameters,
    )


def render_markdown(report: ReportPayload, audience: str, owner_name: str) -> str:
    sections = [
        f"# {report.title}",
        "",
        f"Prepared for: {audience}",
        f"Prepared by: {owner_name}",
        f"Generated at: {report.generated_at}",
        "",
        report.intro,
        "",
        f"## Headline",
        report.headline,
        "",
        "## Wins",
        _render_issue_list(report.done_items, empty_line="No completed items in the current pull."),
        "",
        "## In Progress",
        _render_issue_list(
            report.in_progress_items,
            empty_line="No active work items matched the current reporting filter.",
        ),
        "",
        "## Blockers And Risks",
        _render_issue_list(
            _dedupe_issues(report.blocked_items + report.risk_items),
            empty_line="No blocked or high-risk items matched the current reporting filter.",
        ),
        "",
        "## Next Actions",
        _render_text_list(report.next_actions, empty_line="No next actions generated."),
        "",
        "## References",
        _render_text_list(report.references, empty_line="No references supplied."),
        "",
        "## Parameters",
        _render_parameters(report.parameters),
    ]
    return "\n".join(sections).strip() + "\n"


def build_webex_message(markdown_report: str, report: ReportPayload, audience: str) -> str:
    return (
        f"{report.title}\n"
        f"For: {audience}\n\n"
        f"{report.headline}\n\n"
        f"{_truncate(markdown_report, 6500)}"
    )


def _normalize_issue(issue: dict[str, Any]) -> IssueSummary:
    fields = issue.get("fields", {})
    return IssueSummary(
        key=issue.get("key", "UNKNOWN"),
        summary=fields.get("summary") or "No summary",
        status=(fields.get("status") or {}).get("name", "Unknown"),
        assignee=((fields.get("assignee") or {}).get("displayName") or "Unassigned"),
        priority=(fields.get("priority") or {}).get("name", "Unknown"),
        due_date=fields.get("duedate"),
        labels=list(fields.get("labels") or []),
        issue_type=(fields.get("issuetype") or {}).get("name", "Unknown"),
        updated=fields.get("updated") or "",
    )


def _build_next_actions(
    done_items: list[IssueSummary],
    in_progress_items: list[IssueSummary],
    blocked_items: list[IssueSummary],
    risk_items: list[IssueSummary],
) -> list[str]:
    actions: list[str] = []
    if blocked_items:
        actions.append(
            f"Resolve blocker on {blocked_items[0].key} with {blocked_items[0].assignee}."
        )
    if risk_items:
        actions.append(f"Review mitigation plan for {risk_items[0].key}.")
    if in_progress_items:
        actions.append(f"Track delivery progress on {in_progress_items[0].key}.")
    if done_items:
        actions.append(f"Close the loop on completed item {done_items[0].key}.")
    return actions


def _render_issue_list(items: list[IssueSummary], empty_line: str) -> str:
    if not items:
        return empty_line
    lines = []
    for item in items:
        detail = (
            f"- {item.key}: {item.summary} "
            f"[status: {item.status}; priority: {item.priority}; assignee: {item.assignee}"
        )
        if item.due_date:
            detail += f"; due: {item.due_date}"
        detail += "]"
        lines.append(detail)
    return "\n".join(lines)


def _render_text_list(items: list[str], empty_line: str) -> str:
    if not items:
        return empty_line
    return "\n".join(f"- {item}" for item in items)


def _render_parameters(parameters: dict[str, Any]) -> str:
    if not parameters:
        return "No parameters supplied."
    return "\n".join(f"- {key}: {value}" for key, value in parameters.items())


def _dedupe_issues(items: list[IssueSummary]) -> list[IssueSummary]:
    seen: set[str] = set()
    deduped: list[IssueSummary] = []
    for item in items:
        if item.key in seen:
            continue
        seen.add(item.key)
        deduped.append(item)
    return deduped


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
