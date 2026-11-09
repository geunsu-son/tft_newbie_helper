from __future__ import annotations

import json

from .db import connect


def recommend_units(unit_ids: list[str], top_n: int = 5, path=None) -> list[dict]:
    selected = set(unit_ids)
    if len(selected) < 2:
        return []
    with connect(path) as db:
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
        unit_score = len(selected & core) / len(core) if core else 0.0
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
