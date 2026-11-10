from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .db import init_db, transaction


def import_snapshot(path: str | Path = "data/lolchess_snapshot.tsv") -> int:
    rows = [line.rstrip("\n").split("\t") for line in Path(path).read_text(encoding="utf-8").splitlines() if line]
    unit_items_path = Path(path).with_name("lolchess_unit_items.tsv")
    unit_items_by_key = {}
    for line in unit_items_path.read_text(encoding="utf-8").splitlines():
        guide_key, assignments = line.split("\t", 1)
        unit_items_by_key[guide_key] = {
            unit_id: item_names.split("|")
            for assignment in assignments.split(";") if assignment
            for unit_id, item_names in [assignment.split("=", 1)]
        }
    init_db()
    now = dt.datetime.now(dt.UTC).isoformat()
    imported = []
    special_units = {
        "돌껍질 나무": "DA_Elderwood18_StonebarkTree",
        "생명꽃": "DA_Elderwood18_Lifeblossom",
        "깊은숲 수호자": "DA_Elderwood18_Protector",
    }
    with transaction() as db:
        units_by_name = {row["name_ko"]: row["unit_id"] for row in db.execute(
            "SELECT unit_id,name_ko FROM units ORDER BY unit_id")}
        items_by_name = {}
        for row in db.execute(
            "SELECT item_id,name_ko FROM items ORDER BY item_id LIKE '%Corrupted%',item_id"
        ):
            items_by_name.setdefault(row["name_ko"], row["item_id"])
        for name, guide_key, names, item_names, *_ in rows:
            unit_ids = []
            for unit_name in names.split(","):
                unit_id = special_units.get(unit_name) or units_by_name.get(unit_name)
                if unit_name == "감시자":
                    unit_id = "DA_Sentinel18"
                if not unit_id:
                    raise RuntimeError(f"Community Dragon 유닛 데이터에 '{unit_name}'이 없습니다. 먼저 load-cdragon을 실행하세요.")
                unit_ids.append(unit_id)
            item_ids = list(dict.fromkeys(
                items_by_name[item_name] for item_name in item_names.split(",")
                if item_name in items_by_name
            ))
            items_by_unit = unit_items_by_key.get(guide_key, {})
            if set(items_by_unit) - set(unit_ids):
                raise RuntimeError(f"'{name}'의 유닛별 아이템 대상이 덱 구성과 일치하지 않습니다.")
            comp_id = "lolchess-" + guide_key
            source_url = f"https://lolchess.gg/builder/guide/{guide_key}?type=guide"
            imported.append((comp_id, name, unit_ids, item_ids, items_by_unit, source_url, now))
        for name, unit_id in special_units.items():
            db.execute(
                "INSERT OR REPLACE INTO units(unit_id,name_ko,name_en,icon,set_number,updated_at,cost,traits_json) VALUES(?,?,?,?,?,?,?,?)",
                (unit_id, name, name, None, 18, now, 0, "[]"),
            )
        db.execute("DELETE FROM reference_comps")
        db.execute("DELETE FROM reference_comp_unit_items")
        for comp_id, name, unit_ids, item_ids, items_by_unit, source_url, updated_at in imported:
            db.execute(
                "INSERT INTO reference_comps VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (comp_id, name, json.dumps(unit_ids), json.dumps(item_ids), None,
                 None, None, None, source_url, "18.6", "글로벌", "추천 메타", updated_at),
            )
            for unit_id, names in items_by_unit.items():
                db.execute(
                    "INSERT INTO reference_comp_unit_items VALUES(?,?,?)",
                    (comp_id, unit_id, json.dumps(names, ensure_ascii=False)),
                )
        db.execute("INSERT OR REPLACE INTO app_meta VALUES('reference_updated_at',?)", (now,))
        db.execute("INSERT OR REPLACE INTO app_meta VALUES('reference_comp_n',?)", (str(len(imported)),))
        db.execute("INSERT OR REPLACE INTO app_meta VALUES('reference_source','LoLCHESS 추천 메타')")
    public_snapshot = Path(path).resolve().parent.parent / "frontend" / "public" / "lolchess_unit_items.json"
    public_snapshot.parent.mkdir(parents=True, exist_ok=True)
    public_snapshot.write_text(json.dumps(unit_items_by_key, ensure_ascii=False), encoding="utf-8")
    return len(imported)
