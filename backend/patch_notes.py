from __future__ import annotations

import re
from urllib.parse import urljoin
from typing import Any

import httpx
from bs4 import BeautifulSoup


OFFICIAL_URL = "https://teamfighttactics.leagueoflegends.com/ko-kr/news/tags/patch-notes/"


def fetch_official_patch_notes(url: str | None = None) -> dict[str, Any]:
    """Fetch a small, reviewable buff/nerf view from the official notes page."""
    if url is None:
        listing = httpx.get(OFFICIAL_URL, timeout=30, follow_redirects=True)
        listing.raise_for_status()
        soup = BeautifulSoup(listing.text, "html.parser")
        link = soup.find("a", href=re.compile(r"/news/game-updates/teamfight-tactics-patch-\d+-\d+/?$"))
        if not link:
            raise RuntimeError("최신 패치 노트 링크를 찾지 못했습니다.")
        url = urljoin(OFFICIAL_URL, link["href"])
    response = httpx.get(url, timeout=30, follow_redirects=True)
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
    if not changes:
        for item in soup.find_all("li"):
            if item.find_parent("li"):
                continue
            text = item.get_text(" ", strip=True)
            if "⇒" in text or "→" in text:
                heading = item.find_previous(["h3", "h4"])
                changes.append({"type": heading.get_text(" ", strip=True) if heading else "변경", "text": text[:500]})
    return {"source": url, "title": soup.title.get_text(strip=True) if soup.title else "최신 패치 노트", "changes": changes}
