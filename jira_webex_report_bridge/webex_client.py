from __future__ import annotations

from typing import Any

import requests

from .config import WebexConfig


def send_webex_message(settings: WebexConfig, message: str) -> dict[str, Any]:
    payload = _build_payload(settings, message)
    response = requests.post(
        "https://webexapis.com/v1/messages",
        headers={
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _build_payload(settings: WebexConfig, message: str) -> dict[str, Any]:
    payload: dict[str, Any] = {"markdown": message}

    if settings.room_id:
        payload["roomId"] = settings.room_id
        return payload

    if settings.to_person_email:
        payload["toPersonEmail"] = settings.to_person_email
        return payload

    if settings.to_person_id:
        payload["toPersonId"] = settings.to_person_id
        return payload

    raise ValueError("Webex target is missing. Set room_id, to_person_email, or to_person_id.")
