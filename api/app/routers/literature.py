"""
문학 교재 데이터 API
생성된 PDF 파이프라인 데이터를 제공
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pathlib import Path
import json

router = APIRouter()

# 데이터 경로 (api/data/literature)
LITERATURE_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "literature"
LECTURES_DIR = LITERATURE_DATA_DIR / "lectures"
PROBLEMS_DIR = LITERATURE_DATA_DIR / "problems"
CONTENT_DIR = LITERATURE_DATA_DIR / "content"  # 본문 JSON
CONCEPTS_IMAGES_DIR = LITERATURE_DATA_DIR / "concepts_images"
CONTENT_IMAGES_DIR = LITERATURE_DATA_DIR / "content_images"
PROBLEMS_IMAGES_DIR = LITERATURE_DATA_DIR / "problems_images"


@router.get("/literature/lectures")
async def get_lectures() -> List[Dict[str, Any]]:
    """문학 강의 목록 조회"""
    lectures_json = LECTURES_DIR / "lectures.json"
    if not lectures_json.exists():
        raise HTTPException(status_code=404, detail="강의 목록을 찾을 수 없습니다.")
    
    with open(lectures_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        # lectures.json은 배열 형태이므로 직접 반환
        if isinstance(data, list):
            return data
        # 혹시 객체 형태라면 "lectures" 키에서 가져오기
        return data.get("lectures", [])


@router.get("/literature/lectures/{lecture_id}")
async def get_lecture(lecture_id: int) -> Dict[str, Any]:
    """문학 강의 상세 조회"""
    lecture_json = LECTURES_DIR / f"lecture_{lecture_id:02d}.json"
    if not lecture_json.exists():
        raise HTTPException(status_code=404, detail=f"강의 {lecture_id}를 찾을 수 없습니다.")
    
    with open(lecture_json, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/literature/problems")
async def get_problems() -> List[Dict[str, Any]]:
    """문학 문제 목록 조회"""
    problems = []
    for problem_file in sorted(PROBLEMS_DIR.glob("problem_*.json")):
        with open(problem_file, "r", encoding="utf-8") as f:
            problems.append(json.load(f))
    return problems


@router.get("/literature/problems/{problem_id}")
async def get_problem(problem_id: str) -> Dict[str, Any]:
    """문학 문제 상세 조회
    
    문제 ID만으로 파일 찾기 (새 형식: problem_p{page}_{id}.json 또는 기존 형식: problem_{id}.json)
    """
    # 새 형식 먼저 시도: problem_p*_{problem_id}.json
    problem_files = list(PROBLEMS_DIR.glob(f"problem_p*_{problem_id}.json"))
    if not problem_files:
        # 기존 형식 시도: problem_{problem_id}.json
        problem_json = PROBLEMS_DIR / f"problem_{problem_id}.json"
        if problem_json.exists():
            problem_files = [problem_json]
    
    if not problem_files:
        raise HTTPException(status_code=404, detail=f"문제 {problem_id}를 찾을 수 없습니다.")
    
    # 첫 번째 매칭 파일 사용
    with open(problem_files[0], "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/literature/images/concepts")
async def get_concept_images() -> List[str]:
    """개념 이미지 목록"""
    images = []
    for img_file in sorted(CONCEPTS_IMAGES_DIR.glob("*.png")):
        images.append(f"/api/data/literature/concepts_images/{img_file.name}")
    return images


@router.get("/literature/images/content")
async def get_content_images() -> List[str]:
    """본문 이미지 목록"""
    images = []
    for img_file in sorted(CONTENT_IMAGES_DIR.glob("*.png")):
        images.append(f"/api/data/literature/content_images/{img_file.name}")
    return images


@router.get("/literature/content")
async def get_content_list() -> List[Dict[str, Any]]:
    """본문 목록 조회 (이미지 + 메타데이터)"""
    content_list = []
    # content 디렉토리에서 JSON 파일 찾기
    for json_file in sorted(CONTENT_DIR.glob("content_*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            content_list.append(json.load(f))
    return content_list


@router.get("/literature/content/{content_id}")
async def get_content(content_id: str) -> Dict[str, Any]:
    """본문 상세 조회 (content_id는 "p{page}_{id}" 형식, 예: "p09_01")"""
    # content_id 형식: "p09_01" 또는 "09_01"
    if not content_id.startswith('p'):
        content_id = f"p{content_id}"
    
    content_json = CONTENT_DIR / f"content_{content_id}.json"
    if not content_json.exists():
        raise HTTPException(status_code=404, detail=f"본문 {content_id}를 찾을 수 없습니다.")
    
    with open(content_json, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/literature/images/problems")
async def get_problem_images() -> List[str]:
    """문제 이미지 목록"""
    images = []
    for img_file in sorted(PROBLEMS_IMAGES_DIR.glob("*.png")):
        images.append(f"/api/data/literature/problems_images/{img_file.name}")
    return images
