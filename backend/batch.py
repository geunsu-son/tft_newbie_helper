from __future__ import annotations

import datetime as dt
import json
import math
import os
from collections import Counter
from dataclasses import dataclass

from .db import init_db, transaction
from .ingest import collect


@dataclass
class Board:
    units: set[str]
    placement: int


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def cluster_boards(boards: list[Board], threshold: float = 0.5) -> list[list[Board]]:
    """Connected components over Jaccard-similar final boards."""
    parent = list(range(len(boards)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for left in range(len(boards)):
        for right in range(left + 1, len(boards)):
            if jaccard(boards[left].units, boards[right].units) >= threshold:
                union(left, right)
    groups: dict[int, list[Board]] = {}
    for index, board in enumerate(boards):
        groups.setdefault(find(index), []).append(board)
    return list(groups.values())


def _core_units(boards: list[Board]) -> list[str]:
    minimum_frequency = max(1, math.ceil(len(boards) * 0.5))
    counts = Counter(unit for board in boards for unit in board.units)
    return sorted(unit for unit, count in counts.items() if count >= minimum_frequency)


def _performance(boards: list[Board]) -> tuple[float, float, float, float]:
    avg = sum(board.placement for board in boards) / len(boards)
    top4 = sum(board.placement <= 4 for board in boards) / len(boards)
    wins = sum(board.placement == 1 for board in boards) / len(boards)
    placement_score = max(0.0, min(1.0, (8.0 - avg) / 7.0))
    return avg, top4, wins, (placement_score + top4 + wins) / 3


def build_features(path=None) -> tuple[int, int]:
    init_db(path)
    with transaction(path) as db:
        rows = db.execute(
            "SELECT units_json, placement FROM participants WHERE placement BETWEEN 1 AND 8"
        ).fetchall()
        boards = [Board(set(json.loads(row["units_json"])), row["placement"]) for row in rows]
        n_total = len(boards)
        n_min = max(30, math.ceil(0.005 * n_total))
        groups = cluster_boards(boards)
        now = dt.datetime.now(dt.UTC).isoformat()
        db.execute("DELETE FROM unit_cluster_index")
        db.execute("DELETE FROM clusters")
        visible_id = 0
        for group in groups:
            if len(group) < n_min:
                continue
            core = _core_units(group)
            avg, top4, wins, performance = _performance(group)
            visible_id += 1
            label = " · ".join(core[:5]) or f"클러스터 {visible_id}"
            db.execute(
                """INSERT INTO clusters
                (cluster_id,label,core_units_json,avg_placement,top4_rate,win_rate,
                 sample_n,n_min,performance_score,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (visible_id, label, json.dumps(core, ensure_ascii=False), avg, top4,
                 wins, len(group), n_min, performance, now),
            )
            for unit in core:
                db.execute(
                    "INSERT INTO unit_cluster_index(unit_id,cluster_id) VALUES(?,?)",
                    (unit, visible_id),
                )
        db.execute(
            "INSERT OR REPLACE INTO app_meta(key,value) VALUES('last_batch_at',?)", (now,)
        )
        db.execute(
            "INSERT OR REPLACE INTO app_meta(key,value) VALUES('sample_n',?)", (str(n_total),)
        )
        db.execute(
            "INSERT OR REPLACE INTO app_meta(key,value) VALUES('n_min',?)", (str(n_min),)
        )
    return n_total, n_min


def run_batch(path=None, do_collect: bool = True) -> dict[str, int | str]:
    init_db(path)
    started = dt.datetime.now(dt.UTC).isoformat()
    with transaction(path) as db:
        cursor = db.execute(
            "INSERT INTO batch_runs(started_at,status) VALUES(?,?)", (started, "running")
        )
        run_id = cursor.lastrowid
    try:
        players = matches = 0
        if do_collect:
            players, matches = collect(
                page_limit=int(os.getenv("LEAGUE_PAGE_LIMIT", "20")),
                matches_per_player=int(os.getenv("SEED_MATCHES_PER_PLAYER", "20")),
            )
        sample_n, n_min = build_features(path)
        finished = dt.datetime.now(dt.UTC).isoformat()
        with transaction(path) as db:
            db.execute(
                """UPDATE batch_runs SET finished_at=?,status='success',sample_n=?,n_min=?
                   WHERE id=?""",
                (finished, sample_n, n_min, run_id),
            )
        return {"players": players, "matches": matches, "sample_n": sample_n, "n_min": n_min}
    except Exception as error:
        with transaction(path) as db:
            db.execute(
                "UPDATE batch_runs SET finished_at=?,status='failed',error=? WHERE id=?",
                (dt.datetime.now(dt.UTC).isoformat(), str(error), run_id),
            )
        raise
