"""
점자 변환, 음성 출력, 시험 모드에서 공통으로 사용할 JSON 스키마

이 스키마는 모든 과목에서 공통으로 사용되며,
과목별 특성은 metadata로 확장 가능합니다.
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============= 공통 스키마 =============

class FormulaImage(BaseModel):
    """수식 이미지"""
    image_path: str = Field(description="이미지 파일 경로")
    bbox: List[float] = Field(description="좌표 [x0, y0, x1, y1]")
    page: int = Field(description="페이지 번호")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Choice(BaseModel):
    """선택지"""
    number: Optional[str] = Field(None, description="보기 번호 (①, 1, (1) 등)")
    text: str = Field(description="보기 텍스트")
    index: int = Field(description="0-based 인덱스")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Question(BaseModel):
    """문제"""
    question_number: Optional[int] = Field(None, description="문제 번호")
    question_stem: str = Field(description="문제 지문")
    question_type: Optional[str] = Field(None, description="문제 유형 (blank, ordering 등)")
    choices: List[Choice] = Field(default_factory=list, description="선택지 리스트")
    formula_images: List[FormulaImage] = Field(default_factory=list, description="수식 이미지")
    passage_id: Optional[str] = Field(None, description="참조하는 지문 ID")
    answer: Optional[int] = Field(None, description="정답 (0-based 인덱스)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============= 과목별 확장 스키마 =============

class Paragraph(BaseModel):
    """문단 (국어용)"""
    index: int = Field(description="문단 번호")
    text: str = Field(description="문단 텍스트")
    char_count: int = Field(description="문자 수")
    sentence_count: int = Field(description="문장 수")


class Passage(BaseModel):
    """지문 (국어/영어용)"""
    passage_id: str = Field(description="지문 고유 ID")
    title: Optional[str] = Field(None, description="지문 제목/작품명")
    paragraphs: Optional[List[Paragraph]] = Field(None, description="문단 배열 (국어)")
    sentences: Optional[List[Dict[str, Any]]] = Field(None, description="문장 배열 (영어)")
    full_text: str = Field(description="전체 텍스트")
    placeholders: Optional[List[Dict[str, Any]]] = Field(None, description="빈칸 위치 (영어)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Concept(BaseModel):
    """개념 설명 (수학용)"""
    title: str = Field(description="개념 제목")
    content: str = Field(description="개념 내용")
    formula_images: List[FormulaImage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============= 최종 문항 스키마 =============

class ContentUnit(BaseModel):
    """콘텐츠 단위 (문제 또는 지문)"""
    unit_id: str = Field(description="단위 고유 ID")
    type: Literal["question", "passage", "concept"] = Field(description="타입")
    subject: Literal["math", "korean", "english"] = Field(description="과목")
    
    # 문제 관련
    question: Optional[Question] = None
    
    # 지문 관련
    passage: Optional[Passage] = None
    
    # 개념 관련 (수학)
    concept: Optional[Concept] = None
    
    # 공통 메타데이터
    page: int = Field(description="페이지 번호")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="과목별 확장 메타데이터")


class StructuredContent(BaseModel):
    """구조화된 콘텐츠 (최종 결과)"""
    version: str = Field(default="1.0", description="스키마 버전")
    subject: Literal["math", "korean", "english"] = Field(description="과목")
    book_id: Optional[str] = Field(None, description="교재 ID")
    title: Optional[str] = Field(None, description="교재 제목")
    
    # 페이지별 구조
    pages: Dict[str, Dict[str, Any]] = Field(description="페이지별 구조")
    
    # 단위 리스트
    units: List[ContentUnit] = Field(description="콘텐츠 단위 리스트")
    
    # 통계
    statistics: Dict[str, Any] = Field(description="파싱 통계")
    
    # 메타데이터
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============= JSON 예시 =============

EXAMPLE_MATH_JSON = {
    "version": "1.0",
    "subject": "math",
    "book_id": "bk_math_2026",
    "title": "2026 수능특강 수학Ⅰ",
    "pages": {
        "1": {
            "page": 1,
            "units": ["unit_1", "unit_2"],
            "formulas": ["formula_1"]
        }
    },
    "units": [
        {
            "unit_id": "unit_1",
            "type": "concept",
            "subject": "math",
            "concept": {
                "title": "다항식의 연산",
                "content": "다항식의 덧셈과 뺄셈은...",
                "formula_images": [
                    {
                        "image_path": "data/formulas/formula_1.png",
                        "bbox": [100, 200, 300, 250],
                        "page": 1,
                        "metadata": {}
                    }
                ],
                "metadata": {}
            },
            "page": 1,
            "metadata": {}
        },
        {
            "unit_id": "unit_2",
            "type": "question",
            "subject": "math",
            "question": {
                "question_number": 1,
                "question_stem": "다음 중 옳은 것은?",
                "question_type": None,
                "choices": [
                    {
                        "number": "①",
                        "text": "x² + 2x + 1 = (x+1)²",
                        "index": 0,
                        "metadata": {}
                    },
                    {
                        "number": "②",
                        "text": "x² - 1 = (x-1)(x+1)",
                        "index": 1,
                        "metadata": {}
                    }
                ],
                "formula_images": [],
                "passage_id": None,
                "answer": 0,
                "metadata": {
                    "difficulty": "easy",
                    "topic": "다항식"
                }
            },
            "page": 1,
            "metadata": {}
        }
    ],
    "statistics": {
        "total_units": 2,
        "questions": 1,
        "concepts": 1,
        "formula_images": 1
    },
    "metadata": {
        "year": 2026,
        "extracted_at": "2026-01-01T00:00:00Z"
    }
}

EXAMPLE_KOREAN_JSON = {
    "version": "1.0",
    "subject": "korean",
    "book_id": "bk_korean_2026",
    "title": "2026 수능특강 문학",
    "pages": {
        "1": {
            "page": 1,
            "passages": ["passage_1"],
            "questions": ["question_1"]
        }
    },
    "units": [
        {
            "unit_id": "passage_1",
            "type": "passage",
            "subject": "korean",
            "passage": {
                "passage_id": "passage_1",
                "title": "황조가",
                "paragraphs": [
                    {
                        "index": 0,
                        "text": "철령 이화 우는 수이건",
                        "char_count": 13,
                        "sentence_count": 1
                    },
                    {
                        "index": 1,
                        "text": "마란은 아이다라도",
                        "char_count": 11,
                        "sentence_count": 1
                    }
                ],
                "full_text": "철령 이화 우는 수이건\n마란은 아이다라도",
                "metadata": {
                    "genre": "고전시가",
                    "period": "삼국시대"
                }
            },
            "page": 1,
            "metadata": {}
        },
        {
            "unit_id": "question_1",
            "type": "question",
            "subject": "korean",
            "question": {
                "question_number": 1,
                "question_stem": "다음 시의 화자의 심정으로 가장 적절한 것은?",
                "question_type": None,
                "choices": [
                    {
                        "number": "①",
                        "text": "이별의 슬픔",
                        "index": 0,
                        "metadata": {"char_count": 7}
                    },
                    {
                        "number": "②",
                        "text": "사랑의 기쁨",
                        "index": 1,
                        "metadata": {"char_count": 7}
                    }
                ],
                "formula_images": [],
                "passage_id": "passage_1",
                "answer": 0,
                "metadata": {}
            },
            "page": 1,
            "metadata": {}
        }
    ],
    "statistics": {
        "total_units": 2,
        "passages": 1,
        "questions": 1,
        "total_paragraphs": 2
    },
    "metadata": {}
}
