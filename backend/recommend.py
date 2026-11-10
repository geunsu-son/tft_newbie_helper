from __future__ import annotations

import json
from collections import Counter

from .db import connect


def recommend_units(unit_ids: list[str], top_n: int = 5, path=None) -> list[dict]:
    selected = set(unit_ids)
    if not selected:
        return []
    with connect(path) as db:
        reference_rows = db.execute("SELECT * FROM reference_comps").fetchall()
        if reference_rows:
            items_by_comp: dict[str, dict[str, list[str]]] = {}
            for item_row in db.execute("SELECT comp_id,unit_id,items_json FROM reference_comp_unit_items"):
                items_by_comp.setdefault(item_row["comp_id"], {})[item_row["unit_id"]] = json.loads(item_row["items_json"])
            result = []
            for row in reference_rows:
                core = set(json.loads(row["units_json"]))
                overlap = len(selected & core)
                if overlap < 1:
                    continue
                similarity = overlap / len(selected | core)
                result.append({
                    "cluster_id": row["comp_id"], "deck_name": row["name"],
                    "avg_placement": row["avg_placement"], "top4_rate": row["top4_rate"],
                    "win_rate": row["win_rate"], "similarity": similarity,
                    "score": similarity, "next_units": sorted(core - selected),
                    "unit_ids": json.loads(row["units_json"]),
                    "item_ids": json.loads(row["items_json"]),
                    "items_by_unit": items_by_comp.get(row["comp_id"], {}),
                    "sample_n": row["sample_n"], "source_url": row["source_url"],
                    "patch": row["patch"], "region": row["region"], "tier": row["tier"],
                })
            return sorted(result, key=lambda value: value["score"], reverse=True)[:top_n]
        rows = db.execute(
            """SELECT c.*, u.unit_id
            FROM clusters c JOIN unit_cluster_index u ON u.cluster_id=c.cluster_id
            WHERE u.unit_id IN ({})""".format(",".join("?" * len(selected))),
            tuple(selected),
        ).fetchall()
    by_cluster: dict[int, dict] = {}
    for row in rows:
        item = by_cluster.setdefault(row["cluster_id"], dict(row))
        item.setdefault("_matched", set()).add(row["unit_id"])
    result = []
    for item in by_cluster.values():
        core = set(json.loads(item["core_units_json"]))
        overlap = len(selected & core)
        if overlap < 1:
            continue
        unit_score = overlap / len(core) if core else 0.0
        final_score = 0.65 * unit_score + 0.35 * item["performance_score"]
        missing = sorted(core - selected)
        result.append({
            "cluster_id": item["cluster_id"],
            "deck_name": item["label"],
            "avg_placement": round(item["avg_placement"], 2),
            "top4_rate": round(item["top4_rate"], 4),
            "win_rate": round(item["win_rate"], 4),
            "similarity": round(unit_score, 4),
            "score": round(final_score, 4),
            "next_units": missing[:5],
            "sample_n": item["sample_n"],
        })
    return sorted(result, key=lambda value: value["score"], reverse=True)[:top_n]


def recommend_items(item_ids: list[str], top_n: int = 5, path=None) -> list[dict]:
    if not item_ids:
        return []
    with connect(path) as db:
        items = {row["item_id"]: json.loads(row["components_json"])
                 for row in db.execute("SELECT item_id,components_json FROM items")}
        selected = Counter(item_ids)
        completed = {item_id for item_id in selected if items.get(item_id)}
        components = sum(count for item_id, count in selected.items()
                         if item_id in items and not items[item_id])
        if not completed and components < 3:
            return []
        for item_id, recipe in items.items():
            if recipe and all(selected[part] >= count for part, count in Counter(recipe).items()):
                completed.add(item_id)
        if not completed:
            return []
        reference_rows = db.execute("SELECT * FROM reference_comps").fetchall()
        if reference_rows:
            items_by_comp: dict[str, dict[str, list[str]]] = {}
            for item_row in db.execute("SELECT comp_id,unit_id,items_json FROM reference_comp_unit_items"):
                items_by_comp.setdefault(item_row["comp_id"], {})[item_row["unit_id"]] = json.loads(item_row["items_json"])
            result = []
            for row in reference_rows:
                deck_items = set(json.loads(row["items_json"]))
                matched = sorted(completed & deck_items)
                if not matched:
                    continue
                result.append({
                    "cluster_id": row["comp_id"], "deck_name": row["name"],
                    "avg_placement": row["avg_placement"], "top4_rate": row["top4_rate"],
                    "win_rate": row["win_rate"], "sample_n": row["sample_n"],
                    "matched_items": matched, "score": len(matched) / len(deck_items),
                    "unit_ids": json.loads(row["units_json"]),
                    "item_ids": json.loads(row["items_json"]),
                    "items_by_unit": items_by_comp.get(row["comp_id"], {}),
                    "source_url": row["source_url"], "patch": row["patch"],
                    "region": row["region"], "tier": row["tier"],
                })
            return sorted(result, key=lambda value: value["score"], reverse=True)[:top_n]
        rows = db.execute(
            "SELECT c.*, i.item_id, i.frequency FROM clusters c JOIN cluster_items i "
            "ON c.cluster_id=i.cluster_id WHERE i.item_id IN ({})".format(
                ",".join("?" * len(completed))), tuple(completed)).fetchall()
    result = {}
    for row in rows:
        entry = result.setdefault(row["cluster_id"], {
            "cluster_id": row["cluster_id"], "deck_name": row["label"],
            "avg_placement": round(row["avg_placement"], 2),
            "top4_rate": row["top4_rate"], "win_rate": row["win_rate"],
            "sample_n": row["sample_n"], "matched_items": [], "score": 0})
        entry["matched_items"].append(row["item_id"])
        entry["score"] = max(entry["score"], row["frequency"])
    return sorted(result.values(), key=lambda row: row["score"], reverse=True)[:top_n]
