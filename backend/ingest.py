from __future__ import annotations

import datetime as dt
import os
from typing import Iterable

from .db import init_db, json_text, transaction
from .riot import RiotClient


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _participant_units(participant: dict) -> list[str]:
    return sorted(
        {unit.get("character_id") or unit.get("characterId") for unit in participant.get("units", [])}
        - {None}
    )


def _store_match(db, match: dict) -> None:
    info = match.get("info", {})
    metadata = match.get("metadata", {})
    match_id = metadata.get("match_id")
    if not match_id:
        return
    db.execute(
        """INSERT OR REPLACE INTO matches
           (match_id,game_datetime,game_version,queue_id,set_number,raw_json,fetched_at)
           VALUES(?,?,?,?,?,?,?)""",
        (match_id, info.get("game_datetime"), info.get("game_version"),
         info.get("queue_id"), info.get("tft_set_number"), json_text(match), _now()),
    )
    for participant in info.get("participants", []):
        puuid = participant.get("puuid")
        if not puuid:
            continue
        db.execute(
            """INSERT OR REPLACE INTO participants
            (match_id,puuid,placement,units_json,traits_json,augments_json,items_json)
            VALUES(?,?,?,?,?,?,?)""",
            (match_id, puuid, participant.get("placement", 99),
             json_text(_participant_units(participant)),
             json_text(participant.get("traits", [])),
             json_text(participant.get("augments", [])),
             json_text(participant.get("items", []))),
        )


def collect(client: RiotClient | None = None, page_limit: int = 20,
            matches_per_player: int | None = None) -> tuple[int, int]:
    """Seed KR Emerald+ and persist recent ASIA match details."""
    init_db()
    riot = client or RiotClient()
    count_players = count_matches = 0
    per_player = matches_per_player or int(os.getenv("SEED_MATCHES_PER_PLAYER", "20"))
    seed = riot.seed_players(page_limit=page_limit)
    with transaction() as db:
        for player in seed:
            puuid = player.get("puuid")
            if not puuid:
                continue
            db.execute(
                """INSERT OR REPLACE INTO players
                (puuid,summoner_id,tier,division,league_points,updated_at)
                VALUES(?,?,?,?,?,?)""",
                (puuid, player.get("summonerId"), player.get("tier"),
                 player.get("rank"), player.get("leaguePoints", 0), _now()),
            )
            count_players += 1
            for match_id in riot.match_ids(puuid, per_player):
                if db.execute("SELECT 1 FROM matches WHERE match_id=?", (match_id,)).fetchone():
                    continue
                match = riot.match(match_id)
                _store_match(db, match)
                count_matches += 1
    return count_players, count_matches


def ingest_matches(matches: Iterable[dict]) -> int:
    """Test/helper path for loading API-shaped match details without a Riot call."""
    match_list = list(matches)
    init_db()
    with transaction() as db:
        for match in match_list:
            _store_match(db, match)
    return len(match_list)
