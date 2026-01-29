"""
영어 교재 데이터 API
backend/data/english 기반
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from app.core.config import settings

router = APIRouter()
ENGLISH_DATA_DIR = settings.API_DIR / "data" / "english"


def _data_dir() -> Optional[Path]:
    if ENGLISH_DATA_DIR.exists():
        return ENGLISH_DATA_DIR
    return None


def _lectures_dir() -> Optional[Path]:
    d = _data_dir()
    if d:
        ld = d / "lectures"
        if ld.exists():
            return ld
    return None


@router.get("/english/lectures")
async def get_lectures() -> List[Dict[str, Any]]:
    """영어 강의 목록"""
    ld = _lectures_dir()
    if not ld:
        raise HTTPException(status_code=404, detail="영어 교재를 찾을 수 없습니다.")

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
        raise HTTPException(status_code=404, detail="영어 강의 목록을 찾을 수 없습니다.")

    out = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
            out.append({"lecture_id": d.get("lecture_id"), "title": d.get("title", "")})
    return out


@router.get("/english/lectures/{lecture_id}")
async def get_lecture(lecture_id: int) -> Dict[str, Any]:
    """영어 강의 상세"""
    ld = _lectures_dir()
    if not ld:
        raise HTTPException(status_code=404, detail="영어 교재를 찾을 수 없습니다.")

    p = ld / f"lecture_{lecture_id:02d}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"강의 {lecture_id}를 찾을 수 없습니다.")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/english/problems")
async def get_problems() -> List[Dict[str, Any]]:
    """영어 문제 목록"""
    d = _data_dir()
    if not d:
        return []
    pd = d / "problems"
    if not pd.exists():
        return []
    out = []
    for f in sorted(pd.glob("problem_*.json")):
        with open(f, "r", encoding="utf-8") as fp:
            out.append(json.load(fp))
    return out


@router.get("/english/problems/{problem_id}")
async def get_problem(problem_id: str) -> Dict[str, Any]:
    """영어 문제 상세 (problem_id 예: problem_p12_01, 01 등)"""
    d = _data_dir()
    if not d:
        raise HTTPException(status_code=404, detail="영어 교재를 찾을 수 없습니다.")
    pd = d / "problems"
    if not pd.exists():
        raise HTTPException(status_code=404, detail="문제 디렉토리를 찾을 수 없습니다.")

    candidates = list(pd.glob(f"*{problem_id}*.json"))
    if not candidates:
        q = pd / f"problem_{problem_id}.json"
        if q.exists():
            candidates = [q]
    if not candidates:
        raise HTTPException(status_code=404, detail=f"문제 {problem_id}를 찾을 수 없습니다.")

    with open(candidates[0], "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/english/images/concepts")
async def get_concept_images() -> List[str]:
    d = _data_dir()
    if not d:
        return []
    cd = d / "concepts_images"
    if not cd.exists():
        return []
    return [f"/api/data/english/concepts_images/{f.name}" for f in sorted(cd.glob("*.png"))]


@router.get("/english/images/content")
async def get_content_images() -> List[str]:
    d = _data_dir()
    if not d:
        return []
    cd = d / "content_images"
    if not cd.exists():
        return []
    return [f"/api/data/english/content_images/{f.name}" for f in sorted(cd.glob("*.png"))]


@router.get("/english/images/problems")
async def get_problem_images() -> List[str]:
    d = _data_dir()
    if not d:
        return []
    pd = d / "problems_images"
    if not pd.exists():
        return []
    return [f"/api/data/english/problems_images/{f.name}" for f in sorted(pd.glob("*.png"))]


@router.get("/english/content")
async def get_content_list() -> List[Dict[str, Any]]:
    d = _data_dir()
    if not d:
        return []
    cd = d / "content"
    if not cd.exists():
        return []
    out = []
    for f in sorted(cd.glob("content_*.json")):
        with open(f, "r", encoding="utf-8") as fp:
            out.append(json.load(fp))
    return out


@router.get("/english/content/{content_id}")
async def get_content(content_id: str) -> Dict[str, Any]:
    d = _data_dir()
    if not d:
        raise HTTPException(status_code=404, detail="영어 교재를 찾을 수 없습니다.")
    cd = d / "content"
    if not cd.exists():
        raise HTTPException(status_code=404, detail="본문 디렉토리를 찾을 수 없습니다.")
    cid = content_id if content_id.startswith("p") else f"p{content_id}"
    p = cd / f"content_{cid}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"본문 {content_id}를 찾을 수 없습니다.")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
