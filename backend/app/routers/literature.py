"""
문학 교재 데이터 API
생성된 PDF 파이프라인 데이터를 제공
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Book, Subject
from app.core.config import settings

router = APIRouter()

# 데이터 경로 (api/data/literature)
LITERATURE_DATA_DIR = settings.API_DIR / "data" / "literature"


def get_latest_book_dir(db: Session) -> Optional[Path]:
    """가장 최근 문학 교재 디렉토리 찾기"""
    # DB에서 가장 최근 문학 교재 찾기
    latest_book = db.query(Book).filter(
        Book.subject == Subject.KOREAN
    ).order_by(Book.created_at.desc()).first()
    
    if not latest_book:
        return None
    
    # 교재별 디렉토리: data/literature/{book_id}/
    book_dir = LITERATURE_DATA_DIR / latest_book.book_id
    if book_dir.exists():
        return book_dir
    
    return None


def get_lectures_dir(db: Session) -> Optional[Path]:
    """강의 디렉토리 찾기"""
    book_dir = get_latest_book_dir(db)
    if book_dir:
        lectures_dir = book_dir / "lectures"
        if lectures_dir.exists():
            return lectures_dir
    return None


@router.get("/literature/lectures")
async def get_lectures(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """문학 강의 목록 조회"""
    lectures_dir = get_lectures_dir(db)
    if not lectures_dir:
        raise HTTPException(status_code=404, detail="문학 교재를 찾을 수 없습니다. 교재를 먼저 업로드해주세요.")
    
    # lectures.json 파일 찾기
    lectures_json = lectures_dir / "lectures.json"
    if lectures_json.exists():
        with open(lectures_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            # lectures.json은 배열 형태이므로 직접 반환
            if isinstance(data, list):
                return data
            # 혹시 객체 형태라면 "lectures" 키에서 가져오기
            return data.get("lectures", [])
    
    # lectures.json이 없으면 개별 lecture_*.json 파일에서 목록 생성
    lecture_files = sorted(lectures_dir.glob("lecture_*.json"))
    lecture_files = [f for f in lecture_files if f.name != "lectures.json"]
    
    if not lecture_files:
        raise HTTPException(status_code=404, detail="강의 목록을 찾을 수 없습니다.")
    
    lectures = []
    for lecture_file in lecture_files:
        with open(lecture_file, "r", encoding="utf-8") as f:
            lecture_data = json.load(f)
            # lecture_id와 title만 추출
            lectures.append({
                "lecture_id": lecture_data.get("lecture_id"),
                "title": lecture_data.get("title", "")
            })
    
    return lectures


@router.get("/literature/lectures/{lecture_id}")
async def get_lecture(lecture_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """문학 강의 상세 조회"""
    lectures_dir = get_lectures_dir(db)
    if not lectures_dir:
        raise HTTPException(status_code=404, detail="문학 교재를 찾을 수 없습니다. 교재를 먼저 업로드해주세요.")
    
    # lecture_XX.json 파일 찾기 (XX는 2자리 숫자)
    lecture_json = lectures_dir / f"lecture_{lecture_id:02d}.json"
    if not lecture_json.exists():
        raise HTTPException(status_code=404, detail=f"강의 {lecture_id}를 찾을 수 없습니다.")
    
    with open(lecture_json, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/literature/problems")
async def get_problems(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """문학 문제 목록 조회"""
    book_dir = get_latest_book_dir(db)
    if not book_dir:
        raise HTTPException(status_code=404, detail="문학 교재를 찾을 수 없습니다. 교재를 먼저 업로드해주세요.")

    problems_images_dir = book_dir / "problems_images"
    if not problems_images_dir.exists():
        return []

    problems = []
    for problem_file in sorted(problems_images_dir.glob("problem_*.json")):
        with open(problem_file, "r", encoding="utf-8") as f:
            problems.append(json.load(f))
    return problems


@router.get("/literature/problems/{problem_id}")
async def get_problem(problem_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """문학 문제 상세 조회

    문제 ID만으로 파일 찾기 (새 형식: problem_p{page}_{id}.json 또는 기존 형식: problem_{id}.json)
    """
    book_dir = get_latest_book_dir(db)
    if not book_dir:
        raise HTTPException(status_code=404, detail="문학 교재를 찾을 수 없습니다. 교재를 먼저 업로드해주세요.")

    problems_images_dir = book_dir / "problems_images"
    if not problems_images_dir.exists():
        raise HTTPException(status_code=404, detail=f"문제 {problem_id}를 찾을 수 없습니다.")

    # 새 형식 먼저 시도: problem_p*_{problem_id}.json
    problem_files = list(problems_images_dir.glob(f"problem_p*_{problem_id}.json"))
    if not problem_files:
        # 기존 형식 시도: problem_{problem_id}.json
        problem_json = problems_images_dir / f"problem_{problem_id}.json"
        if problem_json.exists():
            problem_files = [problem_json]

    if not problem_files:
        raise HTTPException(status_code=404, detail=f"문제 {problem_id}를 찾을 수 없습니다.")

    # 첫 번째 매칭 파일 사용
    with open(problem_files[0], "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/literature/images/concepts")
async def get_concept_images(db: Session = Depends(get_db)) -> List[str]:
    """개념 이미지 목록"""
    book_dir = get_latest_book_dir(db)
    if not book_dir:
        return []

    concepts_images_dir = book_dir / "concepts_images"
    if not concepts_images_dir.exists():
        return []

    images = []
    for img_file in sorted(concepts_images_dir.glob("*.png")):
        images.append(f"/api/data/literature/{book_dir.name}/concepts_images/{img_file.name}")
    return images


@router.get("/literature/images/content")
async def get_content_images(db: Session = Depends(get_db)) -> List[str]:
    """본문 이미지 목록"""
    book_dir = get_latest_book_dir(db)
    if not book_dir:
        return []

    content_images_dir = book_dir / "content_images"
    if not content_images_dir.exists():
        return []

    images = []
    for img_file in sorted(content_images_dir.glob("*.png")):
        images.append(f"/api/data/literature/{book_dir.name}/content_images/{img_file.name}")
    return images


@router.get("/literature/content")
async def get_content_list(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """본문 목록 조회 (이미지 + 메타데이터)"""
    book_dir = get_latest_book_dir(db)
    if not book_dir:
        return []

    content_dir = book_dir / "content"
    if not content_dir.exists():
        return []

    content_list = []
    # content 디렉토리에서 JSON 파일 찾기
    for json_file in sorted(content_dir.glob("content_*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            content_list.append(json.load(f))
    return content_list


@router.get("/literature/content/{content_id}")
async def get_content(content_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """본문 상세 조회 (content_id는 "p{page}_{id}" 형식, 예: "p09_01")"""
    book_dir = get_latest_book_dir(db)
    if not book_dir:
        raise HTTPException(status_code=404, detail="문학 교재를 찾을 수 없습니다. 교재를 먼저 업로드해주세요.")

    content_dir = book_dir / "content"
    if not content_dir.exists():
        raise HTTPException(status_code=404, detail=f"본문 {content_id}를 찾을 수 없습니다.")

    # content_id 형식: "p09_01" 또는 "09_01"
    if not content_id.startswith('p'):
        content_id = f"p{content_id}"

    content_json = content_dir / f"content_{content_id}.json"
    if not content_json.exists():
        raise HTTPException(status_code=404, detail=f"본문 {content_id}를 찾을 수 없습니다.")

    with open(content_json, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/literature/images/problems")
async def get_problem_images(db: Session = Depends(get_db)) -> List[str]:
    """문제 이미지 목록"""
    book_dir = get_latest_book_dir(db)
    if not book_dir:
        return []

    problems_images_dir = book_dir / "problems_images"
    if not problems_images_dir.exists():
        return []

    images = []
    for img_file in sorted(problems_images_dir.glob("*.png")):
        images.append(f"/api/data/literature/{book_dir.name}/problems_images/{img_file.name}")
    return images
