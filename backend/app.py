from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .db import connect, init_db
from .patch_notes import fetch_official_patch_notes
from .recommend import recommend_items, recommend_units

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


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


class ItemRecommendationRequest(BaseModel):
    item_ids: list[str] = Field(max_length=20)


@app.get("/health")
def health():
    with connect() as db:
        row = db.execute(
            "SELECT key,value FROM app_meta WHERE key IN ('last_batch_at','sample_n','n_min','reference_updated_at','reference_comp_n','reference_source')"
        ).fetchall()
    return {"ok": True, "meta": {item["key"]: item["value"] for item in row}}


@app.get("/units")
def units():
    with connect() as db:
        return [
            dict(row)
            for row in db.execute(
                "SELECT unit_id,name_ko,name_en,icon,cost,traits_json FROM units ORDER BY name_ko"
            )
        ]


@app.post("/recommend/units")
def recommend(request: RecommendationRequest):
    unit_ids = list(dict.fromkeys(request.unit_ids))
    if not unit_ids:
        raise HTTPException(status_code=400, detail="유닛을 1개 이상 입력해 주세요.")
    return {"recommendations": recommend_units(unit_ids, request.top_n)}


@app.get("/items")
def items():
    with connect() as db:
        return [dict(row) for row in db.execute(
            "SELECT item_id,name_ko,icon,components_json FROM items ORDER BY name_ko")]


@app.post("/recommend/items")
def items_recommendation(request: ItemRecommendationRequest):
    return {"recommendations": recommend_items(request.item_ids)}


@app.get("/patch-notes")
def patch_notes():
    try:
        return fetch_official_patch_notes()
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"공식 패치 노트를 불러오지 못했습니다: {error}")
