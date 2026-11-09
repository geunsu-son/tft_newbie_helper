from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .db import connect, init_db
from .patch_notes import fetch_official_patch_notes
from .recommend import recommend_units
from .scheduler import start_scheduler

load_dotenv()
_scheduler = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _scheduler
    init_db()
    _scheduler = start_scheduler(run_now=os.getenv("RUN_BATCH_ON_START", "1") == "1")
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)


app = FastAPI(title="TFT 뉴비 헬퍼", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class RecommendationRequest(BaseModel):
    unit_ids: list[str] = Field(min_length=0, max_length=10)
    top_n: int = Field(default=5, ge=3, le=5)


@app.get("/health")
def health():
    with connect() as db:
        row = db.execute(
            "SELECT key,value FROM app_meta WHERE key IN ('last_batch_at','sample_n','n_min')"
        ).fetchall()
    return {"ok": True, "meta": {item["key"]: item["value"] for item in row}}


@app.get("/units")
def units():
    with connect() as db:
        return [
            dict(row)
            for row in db.execute(
                "SELECT unit_id,name_ko,name_en,icon FROM units ORDER BY name_ko"
            )
        ]


@app.post("/recommend/units")
def recommend(request: RecommendationRequest):
    unit_ids = list(dict.fromkeys(request.unit_ids))
    if len(unit_ids) < 2:
        raise HTTPException(status_code=400, detail="유닛을 2개 이상 입력해 주세요.")
    return {"recommendations": recommend_units(unit_ids, request.top_n)}


@app.get("/patch-notes")
def patch_notes():
    try:
        return fetch_official_patch_notes()
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"공식 패치 노트를 불러오지 못했습니다: {error}")
