from __future__ import annotations

import os
import time
from typing import Any

import httpx


class RiotClient:
    """Minimal TFT league/match client. API keys are read only from the environment."""

    def __init__(self, api_key: str | None = None, client: httpx.Client | None = None):
        self.api_key = api_key or os.getenv("RIOT_API_KEY")
        if not self.api_key:
            raise RuntimeError("RIOT_API_KEY 환경변수가 필요합니다.")
        self.client = client or httpx.Client(timeout=30)

    def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        for attempt in range(4):
            response = self.client.get(
                url, params=params, headers={"X-Riot-Token": self.api_key}
            )
            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", "2"))
                time.sleep(min(retry_after * (attempt + 1), 30))
                continue
            response.raise_for_status()
            return response.json()
        raise RuntimeError(f"Riot API rate limit exceeded: {url}")

    def league(self, path: str) -> dict:
        return self._get(f"https://kr.api.riotgames.com/tft/league/v1/{path}")

    def match(self, match_id: str) -> dict:
        return self._get(f"https://asia.api.riotgames.com/tft/match/v1/matches/{match_id}")

    def match_ids(self, puuid: str, count: int = 20) -> list[str]:
        return self._get(
            f"https://asia.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids",
            {"start": 0, "count": count},
        )

    def seed_players(self, page_limit: int = 20) -> list[dict]:
        entries: list[dict] = []
        for path in ("challenger", "grandmaster", "master"):
            entries.extend(self.league(path).get("entries", []))
        for tier in ("EMERALD", "DIAMOND"):
            for division in ("I", "II", "III", "IV"):
                for page in range(1, page_limit + 1):
                    page_entries = self.league(
                        f"entries/{tier}/{division}?page={page}"
                    )
                    if not page_entries:
                        break
                    entries.extend(page_entries)
        return entries
