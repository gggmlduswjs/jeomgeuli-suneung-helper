"""
수능특강 수학Ⅰ 콘텐츠 JSON 스키마

점자·음성·시험 모드에서 공통으로 사용할 스키마
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============= 수학Ⅰ 전용 스키마 =============

class FormulaImage(BaseModel):
    """수식 이미지"""
    formula_id: str = Field(description="수식 고유 ID")
    image_path: str = Field(description="이미지 파일 경로")
    bbox: List[float] = Field(description="좌표 [x0, y0, x1, y1]")
    page: int = Field(description="페이지 번호")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Choice(BaseModel):
    """보기 (선택지)"""
    number: Optional[str] = Field(None, description="보기 번호 (①, 1, (1) 등)")
    text: str = Field(description="보기 텍스트")
    index: int = Field(description="0-based 인덱스 (①=0, ②=1, ...)")
    bbox: Optional[List[float]] = Field(None, description="좌표 (선택적)")
    page: Optional[int] = Field(None, description="페이지 번호 (선택적)")


class ConceptItem(BaseModel):
    """개념 설명"""
    type: Literal["concept"] = "concept"
    section: Literal["concept"] = "concept"
    text: str = Field(description="개념 설명 텍스트")
    formulas: List[FormulaImage] = Field(default_factory=list, description="수식 이미지")
    page: int = Field(description="페이지 번호")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QuestionItem(BaseModel):
    """문제"""
    type: Literal["question"] = "question"
    question_id: str = Field(description="문제 고유 ID (예: M1-01-EX-01)")
    question_number: Optional[int] = Field(None, description="문제 번호")
    section: Literal["example", "exercise"] = Field(description="섹션 (예제/유제)")
    chapter: Optional[str] = Field(None, description="단원 (예: 01, 02)")
    body: str = Field(description="문제 본문")
    choices: List[Choice] = Field(default_factory=list, description="보기 리스트")
    formula_images: List[FormulaImage] = Field(default_factory=list, description="수식 이미지")
    page: int = Field(description="페이지 번호")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="추가 메타데이터 (difficulty 등)"
    )


class Math1Content(BaseModel):
    """수학Ⅰ 콘텐츠 (최종 결과)"""
    version: str = Field(default="1.0", description="스키마 버전")
    subject: Literal["math1"] = "math1"
    book_id: Optional[str] = Field(None, description="교재 ID")
    title: Optional[str] = Field(None, description="교재 제목")
    chapter: Optional[str] = Field(None, description="단원")
    
    # 페이지별 구조
    pages: Dict[str, Dict[str, Any]] = Field(description="페이지별 구조")
    
    # 아이템 리스트 (concepts + questions)
    items: List[Dict[str, Any]] = Field(description="콘텐츠 아이템 리스트")
    
    # 수식 이미지 리스트
    formula_images: List[FormulaImage] = Field(description="전체 수식 이미지")
    
    # 통계
    statistics: Dict[str, Any] = Field(description="파싱 통계")
    
    # 메타데이터
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============= 실제 예시 JSON =============

EXAMPLE_MATH1_JSON = {
    "version": "1.0",
    "subject": "math1",
    "book_id": "bk_math1_2026",
    "title": "2026 수능특강 수학Ⅰ",
    "chapter": "01",
    "pages": {
        "1": {
            "page": 1,
            "sections": ["concept", "example"],
            "questions": ["M1-01-EX-01"],
            "formulas": ["formula_1", "formula_2"]
        }
    },
    "items": [
        {
            "type": "concept",
            "section": "concept",
            "text": "지수의 정의\n\n$a^n$ (단, $a > 0$, $n$은 실수)",
            "formulas": [
                {
                    "formula_id": "formula_1",
                    "image_path": "data/formulas/M1-01-formula-1.png",
                    "bbox": [150, 200, 250, 250],
                    "page": 1,
                    "metadata": {}
                }
            ],
            "page": 1,
            "metadata": {}
        },
        {
            "type": "question",
            "question_id": "M1-01-EX-01",
            "question_number": 1,
            "section": "example",
            "chapter": "01",
            "body": "다음 중 옳은 것은?",
            "choices": [
                {
                    "number": "①",
                    "text": "$2^3 \\times 2^4 = 2^7$",
                    "index": 0,
                    "bbox": [100, 400, 400, 420],
                    "page": 1
                },
                {
                    "number": "②",
                    "text": "$(2^3)^4 = 2^{12}$",
                    "index": 1,
                    "bbox": [100, 430, 400, 450],
                    "page": 1
                },
                {
                    "number": "③",
                    "text": "$2^5 \\div 2^2 = 2^3$",
                    "index": 2,
                    "bbox": [100, 460, 400, 480],
                    "page": 1
                },
                {
                    "number": "④",
                    "text": "$2^{-2} = \\frac{1}{4}$",
                    "index": 3,
                    "bbox": [100, 490, 400, 510],
                    "page": 1
                },
                {
                    "number": "⑤",
                    "text": "$\\sqrt[3]{8} = 2$",
                    "index": 4,
                    "bbox": [100, 520, 400, 540],
                    "page": 1
                }
            ],
            "formula_images": [
                {
                    "formula_id": "formula_2",
                    "image_path": "data/formulas/M1-01-EX-01-formula-1.png",
                    "bbox": [200, 300, 300, 350],
                    "page": 1,
                    "metadata": {}
                }
            ],
            "page": 1,
            "metadata": {
                "difficulty": "easy",
                "topic": "지수"
            }
        }
    ],
    "formula_images": [
        {
            "formula_id": "formula_1",
            "image_path": "data/formulas/M1-01-formula-1.png",
            "bbox": [150, 200, 250, 250],
            "page": 1,
            "metadata": {}
        },
        {
            "formula_id": "formula_2",
            "image_path": "data/formulas/M1-01-EX-01-formula-1.png",
            "bbox": [200, 300, 300, 350],
            "page": 1,
            "metadata": {}
        }
    ],
    "statistics": {
        "total_items": 2,
        "concepts": 1,
        "questions": 1,
        "formula_images": 2,
        "sections": {
            "concept": 1,
            "example": 1,
            "exercise": 0
        }
    },
    "metadata": {
        "year": 2026,
        "extracted_at": "2026-01-01T00:00:00Z"
    }
}
