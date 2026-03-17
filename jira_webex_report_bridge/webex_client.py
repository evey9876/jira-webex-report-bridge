from __future__ import annotations

from typing import Any

import requests

from .config import WebexConfig


def send_webex_message(settings: WebexConfig, message: str) -> dict[str, Any]:
    response = requests.post(
        "https://webexapis.com/v1/messages",
        headers={
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        },
        json={"roomId": settings.room_id, "markdown": message},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

