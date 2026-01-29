"""
문학 교재 데이터 API
생성된 PDF 파이프라인 데이터를 제공
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from pydantic import BaseModel

from app.core.config import settings
from app.utils.ai_utils import get_openai_client, check_openai_available

router = APIRouter()

# 데이터 경로 (backend/data/literature)
LITERATURE_DATA_DIR = settings.API_DIR / "data" / "literature"


def get_literature_data_dir() -> Optional[Path]:
    """문학 데이터 디렉토리 찾기 (backend/data/literature 직접 사용)"""
    if LITERATURE_DATA_DIR.exists():
        return LITERATURE_DATA_DIR
    return None


def get_lectures_dir() -> Optional[Path]:
    """강의 디렉토리 찾기"""
    data_dir = get_literature_data_dir()
    if data_dir:
        lectures_dir = data_dir / "lectures"
        if lectures_dir.exists():
            return lectures_dir
    return None


@router.get("/literature/lectures")
async def get_lectures() -> List[Dict[str, Any]]:
    """문학 강의 목록 조회"""
    lectures_dir = get_lectures_dir()
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
async def get_lecture(lecture_id: int) -> Dict[str, Any]:
    """문학 강의 상세 조회"""
    lectures_dir = get_lectures_dir()
    if not lectures_dir:
        raise HTTPException(status_code=404, detail="문학 교재를 찾을 수 없습니다. 교재를 먼저 업로드해주세요.")
    
    # lecture_XX.json 파일 찾기 (XX는 2자리 숫자)
    lecture_json = lectures_dir / f"lecture_{lecture_id:02d}.json"
    if not lecture_json.exists():
        raise HTTPException(status_code=404, detail=f"강의 {lecture_id}를 찾을 수 없습니다.")
    
    with open(lecture_json, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/literature/problems")
async def get_problems() -> List[Dict[str, Any]]:
    """문학 문제 목록 조회"""
    book_dir = get_literature_data_dir()
    if not book_dir:
        return []

    # problems 디렉토리 확인
    problems_dir = book_dir / "problems"
    if not problems_dir.exists():
        return []

    problems = []
    for problem_file in sorted(problems_dir.glob("problem_*.json")):
        with open(problem_file, "r", encoding="utf-8") as f:
            problems.append(json.load(f))
    return problems


@router.get("/literature/problems/{problem_id}")
async def get_problem(problem_id: str) -> Dict[str, Any]:
    """문학 문제 상세 조회

    문제 ID만으로 파일 찾기 (새 형식: problem_p{page}_{id}.json 또는 기존 형식: problem_{id}.json)
    """
    book_dir = get_literature_data_dir()
    if not book_dir:
        raise HTTPException(status_code=404, detail="문학 교재를 찾을 수 없습니다.")

    problems_dir = book_dir / "problems"
    if not problems_dir.exists():
        raise HTTPException(status_code=404, detail=f"문제 디렉토리를 찾을 수 없습니다.")

    # 새 형식 먼저 시도: problem_p*_{problem_id}.json
    problem_files = list(problems_dir.glob(f"*{problem_id}*.json"))
    if not problem_files:
        # 기존 형식 시도: problem_{problem_id}.json
        problem_json = problems_dir / f"problem_{problem_id}.json"
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
    book_dir = get_literature_data_dir()
    if not book_dir:
        return []

    concepts_images_dir = book_dir / "concepts_images"
    if not concepts_images_dir.exists():
        return []

    images = []
    for img_file in sorted(concepts_images_dir.glob("*.png")):
        images.append(f"/api/data/literature/concepts_images/{img_file.name}")
    return images


@router.get("/literature/images/content")
async def get_content_images() -> List[str]:
    """본문 이미지 목록"""
    book_dir = get_literature_data_dir()
    if not book_dir:
        return []

    content_images_dir = book_dir / "content_images"
    if not content_images_dir.exists():
        return []

    images = []
    for img_file in sorted(content_images_dir.glob("*.png")):
        images.append(f"/api/data/literature/content_images/{img_file.name}")
    return images


@router.get("/literature/content")
async def get_content_list() -> List[Dict[str, Any]]:
    """본문 목록 조회 (이미지 + 메타데이터)"""
    book_dir = get_literature_data_dir()
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
async def get_content(content_id: str) -> Dict[str, Any]:
    """본문 상세 조회 (content_id는 "p{page}_{id}" 형식, 예: "p09_01")"""
    book_dir = get_literature_data_dir()
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
async def get_problem_images() -> List[str]:
    """문제 이미지 목록"""
    book_dir = get_literature_data_dir()
    if not book_dir:
        return []

    problems_images_dir = book_dir / "problems_images"
    if not problems_images_dir.exists():
        return []

    images = []
    for img_file in sorted(problems_images_dir.glob("*.png")):
        images.append(f"/api/data/literature/problems_images/{img_file.name}")
    return images


# AI 설명 요청/응답 모델
class ExplainConceptRequest(BaseModel):
    concept_title: str
    concept_content: List[str]
    subject: str = "literature"


class ExplainConceptResponse(BaseModel):
    concept_title: str
    original_content: List[str]
    ai_explanation: str
    subject: str


class ExplainContentRequest(BaseModel):
    content_title: str
    content_text: List[str]
    subject: str = "literature"


class ExplainContentResponse(BaseModel):
    content_title: str
    original_text: List[str]
    ai_explanation: str
    subject: str


class ExplainProblemRequest(BaseModel):
    problem_id: str
    question_text: str
    choices: Dict[str, str]
    passage: Optional[List[str]] = None
    subject: str = "literature"


class ExplainProblemResponse(BaseModel):
    problem_id: str
    question_text: str
    choices: Dict[str, str]
    passage: Optional[List[str]] = None
    ai_explanation: str
    subject: str


@router.post("/literature/ai/explain-concept", response_model=ExplainConceptResponse)
async def explain_concept(request: ExplainConceptRequest = Body(...)):
    """AI 개념 설명"""
    try:
        # OpenAI API 사용 가능 여부 확인
        if not check_openai_available():
            return ExplainConceptResponse(
                concept_title=request.concept_title,
                original_content=request.concept_content,
                ai_explanation="OpenAI API 키를 설정하면 AI 설명을 제공할 수 있습니다.",
                subject=request.subject
            )

        # OpenAI API 호출
        client = get_openai_client()
        
        # 프롬프트 구성
        system_prompt = """당신은 문학 교육 전문가입니다. 
학생들이 문학 개념을 쉽게 이해할 수 있도록 명확하고 친절하게 설명해주세요.
예시를 들어 설명하면 더 좋습니다."""

        content_text = "\n".join(request.concept_content)
        user_prompt = f"""다음 문학 개념을 학생이 이해하기 쉽게 설명해주세요.

**개념 제목**: {request.concept_title}

**개념 내용**:
{content_text}

위 개념을 학생이 쉽게 이해할 수 있도록 친절하고 명확하게 설명해주세요."""

        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        explanation = response.choices[0].message.content.strip()

        return ExplainConceptResponse(
            concept_title=request.concept_title,
            original_content=request.concept_content,
            ai_explanation=explanation,
            subject=request.subject
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 설명 생성 실패: {str(e)}"
        )


@router.post("/literature/ai/explain-content", response_model=ExplainContentResponse)
async def explain_content(request: ExplainContentRequest = Body(...)):
    """AI 본문 설명"""
    try:
        # OpenAI API 사용 가능 여부 확인
        if not check_openai_available():
            return ExplainContentResponse(
                content_title=request.content_title,
                original_text=request.content_text,
                ai_explanation="OpenAI API 키를 설정하면 AI 설명을 제공할 수 있습니다.",
                subject=request.subject
            )

        # OpenAI API 호출
        client = get_openai_client()
        
        # 프롬프트 구성
        system_prompt = """당신은 문학 작품 해석 전문가입니다. 
학생들이 작품의 의미와 표현 기법을 이해할 수 있도록 명확하고 친절하게 설명해주세요."""

        content_text = "\n".join(request.content_text)
        user_prompt = f"""다음 문학 작품을 학생이 이해하기 쉽게 설명해주세요.

**작품 제목**: {request.content_title}

**작품 본문**:
{content_text}

위 작품의 주제, 표현 기법, 작가의 의도 등을 학생이 쉽게 이해할 수 있도록 친절하고 명확하게 설명해주세요."""

        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        explanation = response.choices[0].message.content.strip()

        return ExplainContentResponse(
            content_title=request.content_title,
            original_text=request.content_text,
            ai_explanation=explanation,
            subject=request.subject
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 설명 생성 실패: {str(e)}"
        )


@router.post("/literature/ai/explain-problem", response_model=ExplainProblemResponse)
async def explain_problem(request: ExplainProblemRequest = Body(...)):
    """AI 문제 설명"""
    try:
        # OpenAI API 사용 가능 여부 확인
        if not check_openai_available():
            return ExplainProblemResponse(
                problem_id=request.problem_id,
                question_text=request.question_text,
                choices=request.choices,
                passage=request.passage,
                ai_explanation="OpenAI API 키를 설정하면 AI 설명을 제공할 수 있습니다.",
                subject=request.subject
            )

        # OpenAI API 호출
        client = get_openai_client()
        
        # 프롬프트 구성
        system_prompt = """당신은 문학 문제 해설 전문가입니다. 
학생들이 문제를 이해하고 정답을 찾을 수 있도록 명확하고 친절하게 설명해주세요."""

        choices_text = "\n".join([f"{k}. {v}" for k, v in sorted(request.choices.items())])
        passage_text = "\n".join(request.passage) if request.passage else ""
        
        user_prompt = f"""다음 문학 문제를 학생이 이해하기 쉽게 설명해주세요.

**문제**:
{request.question_text}

"""
        if passage_text:
            user_prompt += f"""**지문**:
{passage_text}

"""
        user_prompt += f"""**선택지**:
{choices_text}

위 문제의 해결 방법과 정답을 찾는 과정을 학생이 쉽게 이해할 수 있도록 친절하고 명확하게 설명해주세요."""

        # OpenAI API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        explanation = response.choices[0].message.content.strip()

        return ExplainProblemResponse(
            problem_id=request.problem_id,
            question_text=request.question_text,
            choices=request.choices,
            passage=request.passage,
            ai_explanation=explanation,
            subject=request.subject
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 설명 생성 실패: {str(e)}"
        )
