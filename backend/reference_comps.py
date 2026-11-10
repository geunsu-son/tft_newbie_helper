"""One-shot import of the user-selected public composition page."""

import datetime as dt
import json
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from .db import init_db, transaction


SOURCE_URL = "https://op.gg/ko/tft/meta-trends/comps?version=set18-v38&runId=20261109T180319Z"


def import_comps(url: str = SOURCE_URL) -> tuple[int, int]:
    response = httpx.get(url, timeout=40, follow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select('[id^="tft-comp-"]')
    if not cards:
        raise RuntimeError("조합 카드를 찾지 못했습니다. 기존 데이터를 유지합니다.")

    init_db()
    saved = 0
    now = dt.datetime.now(dt.UTC).isoformat()
    with transaction() as db:
        unit_names = {row["name_ko"]: row["unit_id"] for row in db.execute(
            "SELECT unit_id,name_ko FROM units")}
        item_names = {}
        for row in db.execute("SELECT item_id,name_ko FROM items ORDER BY item_id LIKE '%Corrupted%', item_id"):
            item_names.setdefault(row["name_ko"], row["item_id"])
        db.execute("DELETE FROM reference_comps")
        for card in cards:
            title = card.find("h2")
            if title is None:
                continue
            unit_ids = list(dict.fromkeys(
                unit_names[name] for image in card.find_all("img")
                if "tft-champion/tiles" in image.get("src", "")
                if (name := (image.parent.get("aria-label") or image.get("alt"))) in unit_names
            ))
            if len(unit_ids) < 2:
                continue
            item_ids = list(dict.fromkeys(
                item_names[name] for image in card.find_all("img")
                if "tft-item/" in image.get("src", "")
                if (name := image.get("alt")) in item_names
            ))
            stats = {term.get_text(" ", strip=True): term.find_next_sibling().get_text(" ", strip=True)
                     for term in card.find_all("dt") if term.find_next_sibling()}
            href = title.find("a").get("href") if title.find("a") else url
            db.execute(
                """INSERT INTO reference_comps VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (card["id"], title.get_text(" ", strip=True),
                 json.dumps(unit_ids), json.dumps(item_ids),
                 float(stats["평균 순위"]) if "평균 순위" in stats else None,
                 float(stats["순방 확률"].rstrip("%")) / 100 if "순방 확률" in stats else None,
                 float(stats["승률"].rstrip("%")) / 100 if "승률" in stats else None,
                 int(stats["게임 수"].replace(",", "")) if "게임 수" in stats else None,
                 urljoin(url, href), "18.6", "글로벌", "플래티넘+", now),
            )
            saved += 1
        if not saved:
            raise RuntimeError("매핑된 조합이 없어 기존 데이터를 유지합니다.")
        db.execute("INSERT OR REPLACE INTO app_meta VALUES('reference_updated_at',?)", (now,))
        db.execute("INSERT OR REPLACE INTO app_meta VALUES('reference_comp_n',?)", (str(saved),))
    return saved, len(cards)
