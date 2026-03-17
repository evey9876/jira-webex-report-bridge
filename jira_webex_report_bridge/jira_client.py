from __future__ import annotations

from typing import Any

import requests

from .config import JiraConfig


def fetch_jira_updates(settings: JiraConfig) -> dict[str, Any]:
    response = requests.post(
        f"{settings.base_url}/rest/api/3/search/jql",
        auth=(settings.email, settings.api_token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json={
            "jql": settings.jql,
            "maxResults": settings.max_results,
            "fields": settings.fields,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

