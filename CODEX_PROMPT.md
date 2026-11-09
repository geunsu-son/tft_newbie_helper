# Codex 작업 지시 프롬프트 (복사용)

아래 블록을 Codex에 그대로 붙여 넣으세요.

---

You are implementing **TFT 뉴비 헬퍼** in this repository.

## Read first (required)

1. `PRD.md` — product requirements (Korean). Follow it strictly.
2. `TASKS.md` — MVP task breakdown with acceptance criteria.
3. `README.md` — scope summary.

## Goal

Deliver **MVP only** (M0–M3 in TASKS.md):

- Local-only web app (bind localhost / private LAN). No public hosting.
- KR Emerald+ match collection via Riot TFT-LEAGUE-V1 + TFT-MATCH-V1 (ASIA).
- Local SQLite + batch on process start and daily 15:00 Asia/Seoul with catch-up if the machine was off.
- Unit recommendation: require **≥2 units**; Jaccard clustering; scores per PRD formulas (0)–(2); recompute `n_min` every batch; Top-N from precomputed tables (no Riot match call on recommend).
- Simple patch notes buff/nerf view from official TFT patch notes.
- Korean UI. Riot disclaimer in README/UI.
- **Do NOT** implement item-based recommend, augment weights, or emblem score in MVP (those are M4 / post-MVP in PRD).

## Proposed stack (unless you have a strong reason; document if you change)

- Backend: Python FastAPI
- DB: SQLite
- Scheduler: APScheduler (or equivalent)
- Frontend: React + Vite

## Constraints

- Personal Riot API key via `.env` only — never commit secrets. Provide `.env.example`.
- No client overlay, LCU, memory reading, auto-play.
- No scraping lolchess.gg / tft.op.gg as primary data.
- No Legend win-rate display.
- Data-driven champions/items from Community Dragon (no hardcoded set roster in UI).

## Done when

All **M0–M3 acceptance criteria** in `TASKS.md` are checked off, and README documents how to run locally (install, migrate/init DB, start API, start frontend, run/verify batch).

Start with M1 PoC (league seed + one match fetch + CDragon load), then M2 clustering/batch, then M3 UI. Commit in logical milestones.

---
