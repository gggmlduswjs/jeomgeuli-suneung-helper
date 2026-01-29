"""
수학1 교재 데이터 API
backend/data/math1 기반
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from app.core.config import settings

router = APIRouter()
MATH1_DATA_DIR = settings.API_DIR / "data" / "math1"


def _data_dir() -> Optional[Path]:
    if MATH1_DATA_DIR.exists():
        return MATH1_DATA_DIR
    return None


def _lectures_dir() -> Optional[Path]:
    d = _data_dir()
    if d:
        ld = d / "lectures"
        if ld.exists():
            return ld
    return None


@router.get("/math1/lectures")
async def get_lectures() -> List[Dict[str, Any]]:
    """수학1 강의 목록"""
    ld = _lectures_dir()
    if not ld:
        raise HTTPException(status_code=404, detail="수학1 교재를 찾을 수 없습니다.")

    j = ld / "lectures.json"
    if j.exists():
        with open(j, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return data.get("lectures", [])

    files = sorted(ld.glob("lecture_*.json"))
    files = [f for f in files if f.name != "lectures.json"]
    if not files:
        raise HTTPException(status_code=404, detail="수학1 강의 목록을 찾을 수 없습니다.")

    out = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
            out.append({"lecture_id": d.get("lecture_id"), "title": d.get("title", "")})
    return out


@router.get("/math1/lectures/{lecture_id}")
async def get_lecture(lecture_id: int) -> Dict[str, Any]:
    """수학1 강의 상세"""
    ld = _lectures_dir()
    if not ld:
        raise HTTPException(status_code=404, detail="수학1 교재를 찾을 수 없습니다.")

    p = ld / f"lecture_{lecture_id:02d}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"강의 {lecture_id}를 찾을 수 없습니다.")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
