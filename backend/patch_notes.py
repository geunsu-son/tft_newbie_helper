from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup


OFFICIAL_URL = (
    "https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/"
    "teamfight-tactics-patch-18-6/"
)


def fetch_official_patch_notes(url: str = OFFICIAL_URL) -> dict[str, Any]:
    """Fetch a small, reviewable buff/nerf view from the official notes page."""
    response = httpx.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    changes: list[dict[str, str]] = []
    current_section = ""
    for heading in soup.find_all(["h2", "h3", "h4"]):
        current_section = heading.get_text(" ", strip=True)
        if not re.search(r"buff|nerf|상향|하향", current_section, re.I):
            continue
        sibling = heading.find_next_sibling()
        if sibling:
            text = sibling.get_text(" ", strip=True)
            if text:
                changes.append({"type": current_section, "text": text[:500]})
    return {"source": url, "changes": changes}
