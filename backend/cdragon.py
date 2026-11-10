from __future__ import annotations

import datetime as dt
import json
import os
from typing import Any

import httpx

from .db import init_db, transaction


CDRAGON_URL = "https://raw.communitydragon.org/latest/cdragon/tft/ko_kr.json"


def _units(payload: dict[str, Any]) -> list[dict[str, Any]]:
    units = list(payload.get("champions", []))
    for set_data in payload.get("setData", []):
        if isinstance(set_data, dict):
            units.extend(set_data.get("champions", []))
    return units


def load_units(path: str | None = None, client: httpx.Client | None = None) -> int:
    http = client or httpx.Client(timeout=30)
    response = http.get(path or CDRAGON_URL)
    response.raise_for_status()
    payload = response.json()
    count = 0
    now = dt.datetime.now(dt.UTC).isoformat()
    set_number = int(os.getenv("CURRENT_SET_NUMBER", "18"))
    current = next((s for s in payload.get("setData", [])
                    if s.get("mutator") == f"TFTSet{set_number}"), None)
    if current is None:
        raise RuntimeError(f"CDragon에서 세트 {set_number}를 찾지 못했습니다.")
    init_db()
    with transaction() as db:
        db.execute("DELETE FROM units")
        db.execute("DELETE FROM items")
        for item in current.get("champions", []):
            unit_id = item.get("apiName") or item.get("id")
            # Set data also contains neutral minions and training entities (TFT_*).
            # Those appear with placeholder costs and are not selectable shop units.
            if not unit_id or not unit_id.startswith("DA_") or not 1 <= item.get("cost", 0) <= 5:
                continue
            name = item.get("name") or item.get("displayName") or unit_id
            db.execute(
                """INSERT INTO units(unit_id,name_ko,name_en,icon,set_number,updated_at,cost,traits_json)
                   VALUES(?,?,?,?,?,?,?,?)
                   ON CONFLICT(unit_id) DO UPDATE SET name_ko=excluded.name_ko,
                   name_en=excluded.name_en, icon=excluded.icon,
                   set_number=excluded.set_number, updated_at=excluded.updated_at,
                   cost=excluded.cost, traits_json=excluded.traits_json""",
                (unit_id, name, name, item.get("icon"), set_number, now,
                 item.get("cost"), json.dumps(item.get("traits", []), ensure_ascii=False)),
            )
            count += 1
        items = payload.get("items", [])
        recipes = [item for item in items if item.get("apiName", "").startswith("TFT_Item_")
                   and len(item.get("composition", [])) == 2
                   and all(part.startswith("TFT_Item_") for part in item["composition"])]
        component_ids = {part for item in recipes for part in item["composition"]}
        for item in items:
            item_id = item.get("apiName")
            if item_id not in component_ids and item not in recipes:
                continue
            db.execute("INSERT OR REPLACE INTO items VALUES(?,?,?,?)",
                       (item_id, item.get("name") or item_id, item.get("icon"),
                        json.dumps(item.get("composition", []))))
    return count
