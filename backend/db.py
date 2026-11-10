from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
  puuid TEXT PRIMARY KEY, summoner_id TEXT, tier TEXT, division TEXT,
  league_points INTEGER, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS matches (
  match_id TEXT PRIMARY KEY, game_datetime INTEGER, game_version TEXT,
  queue_id INTEGER, set_number INTEGER, raw_json TEXT NOT NULL,
  fetched_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS participants (
  match_id TEXT NOT NULL, puuid TEXT NOT NULL, placement INTEGER NOT NULL,
  units_json TEXT NOT NULL, traits_json TEXT NOT NULL, augments_json TEXT NOT NULL,
  items_json TEXT NOT NULL, PRIMARY KEY(match_id, puuid)
);
CREATE TABLE IF NOT EXISTS units (
  unit_id TEXT PRIMARY KEY, name_ko TEXT NOT NULL, name_en TEXT,
  icon TEXT, set_number INTEGER, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
  item_id TEXT PRIMARY KEY, name_ko TEXT NOT NULL, icon TEXT,
  components_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cluster_items (
  cluster_id INTEGER NOT NULL, item_id TEXT NOT NULL, frequency REAL NOT NULL,
  PRIMARY KEY(cluster_id, item_id)
);
CREATE TABLE IF NOT EXISTS reference_comps (
  comp_id TEXT PRIMARY KEY, name TEXT NOT NULL, units_json TEXT NOT NULL,
  items_json TEXT NOT NULL, avg_placement REAL, top4_rate REAL,
  win_rate REAL, sample_n INTEGER, source_url TEXT NOT NULL,
  patch TEXT NOT NULL, region TEXT NOT NULL, tier TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reference_comp_unit_items (
  comp_id TEXT NOT NULL, unit_id TEXT NOT NULL, items_json TEXT NOT NULL,
  PRIMARY KEY(comp_id, unit_id)
);
CREATE TABLE IF NOT EXISTS batch_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL,
  finished_at TEXT, status TEXT NOT NULL, sample_n INTEGER DEFAULT 0,
  n_min INTEGER DEFAULT 0, error TEXT
);
CREATE TABLE IF NOT EXISTS clusters (
  cluster_id INTEGER PRIMARY KEY, label TEXT NOT NULL, core_units_json TEXT NOT NULL,
  avg_placement REAL NOT NULL, top4_rate REAL NOT NULL, win_rate REAL NOT NULL,
  sample_n INTEGER NOT NULL, n_min INTEGER NOT NULL, performance_score REAL NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS unit_cluster_index (
  unit_id TEXT NOT NULL, cluster_id INTEGER NOT NULL,
  PRIMARY KEY(unit_id, cluster_id)
);
CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def database_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", "data/tft.sqlite3"))


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    db_path = Path(path) if path else database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(path: str | Path | None = None) -> None:
    with connect(path) as connection:
        connection.executescript(SCHEMA)
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(units)")}
        if "cost" not in columns:
            connection.execute("ALTER TABLE units ADD COLUMN cost INTEGER")
        if "traits_json" not in columns:
            connection.execute("ALTER TABLE units ADD COLUMN traits_json TEXT NOT NULL DEFAULT '[]'")


@contextmanager
def transaction(path: str | Path | None = None):
    connection = connect(path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def json_text(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
