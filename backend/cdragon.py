from __future__ import annotations

import datetime as dt
from typing import Any

import httpx

from .db import transaction


CDRAGON_URL = "https://raw.communitydragon.org/latest/cdragon/tft/en_us.json"


def _items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("items", "champions", "setData"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    return []


def load_units(path: str | None = None, client: httpx.Client | None = None) -> int:
    http = client or httpx.Client(timeout=30)
    response = http.get(path or CDRAGON_URL)
    response.raise_for_status()
    payload = response.json()
    count = 0
    now = dt.datetime.now(dt.UTC).isoformat()
    with transaction() as db:
        for item in _items(payload):
            unit_id = item.get("apiName") or item.get("id")
            if not unit_id or "TFTUnit" not in unit_id:
                continue
            name = item.get("name") or item.get("displayName") or unit_id
            db.execute(
                """INSERT INTO units(unit_id,name_ko,name_en,icon,set_number,updated_at)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(unit_id) DO UPDATE SET name_ko=excluded.name_ko,
                   name_en=excluded.name_en, icon=excluded.icon,
                   set_number=excluded.set_number, updated_at=excluded.updated_at""",
                (unit_id, name, name, item.get("icon"), None, now),
            )
            count += 1
    return count
