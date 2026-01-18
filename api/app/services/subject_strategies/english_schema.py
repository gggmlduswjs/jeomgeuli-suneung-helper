"""
수능특강 영어 콘텐츠 JSON 스키마

시험 모드 / 음성 모드 / 점자 모드에서 공통 사용 가능한 스키마
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============= 영어 전용 스키마 =============

class Choice(BaseModel):
    """보기 (선택지)"""
    label: Optional[str] = Field(None, description="보기 라벨 (①, ② 등)")
    number: Optional[str] = Field(None, description="보기 번호")
    text: str = Field(description="보기 텍스트")
    index: int = Field(description="0-based 인덱스 (①=0, ②=1, ...)")
    char_count: Optional[int] = Field(None, description="문자 수")
    word_count: Optional[int] = Field(None, description="단어 수")


class Passage(BaseModel):
    """지문"""
    type: Literal["passage"] = "passage"
    passage_id: str = Field(description="지문 고유 ID (예: ENG-01-P01)")
    sentences: List[str] = Field(description="문장 배열 (순수 텍스트)")
    sentences_detail: Optional[List[Dict[str, Any]]] = Field(None, description="문장 상세 정보")
    full_text: str = Field(description="지문 전체 텍스트")
    placeholders: List[Dict[str, Any]] = Field(default_factory=list, description="빈칸 위치 (___ 유지)")
    page: int = Field(description="페이지 번호")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Question(BaseModel):
    """문제"""
    type: Literal["question"] = "question"
    question_id: str = Field(description="문제 고유 ID (예: ENG-01-Q01)")
    question_number: Optional[int] = Field(None, description="문제 번호")
    question_type: Literal["blank", "ordering", "insertion", "main_idea", "detail", "general"] = Field(
        description="문제 유형"
    )
    passage_id: Optional[str] = Field(None, description="참조하는 지문 ID")
    question: str = Field(description="문제 본문")
    choices: List[Choice] = Field(default_factory=list, description="보기 리스트")
    page: int = Field(description="페이지 번호")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnglishContent(BaseModel):
    """영어 콘텐츠 (최종 결과)"""
    version: str = Field(default="1.0", description="스키마 버전")
    subject: Literal["english"] = "english"
    book_id: Optional[str] = Field(None, description="교재 ID")
    title: Optional[str] = Field(None, description="교재 제목")
    
    # 페이지별 구조
    pages: Dict[str, Dict[str, Any]] = Field(description="페이지별 구조")
    
    # 단위 리스트 (passages + questions)
    units: List[Dict[str, Any]] = Field(description="콘텐츠 단위 리스트")
    
    # 통계
    statistics: Dict[str, Any] = Field(description="파싱 통계")
    
    # 메타데이터
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============= 실제 예시 JSON =============

EXAMPLE_ENGLISH_JSON = {
    "version": "1.0",
    "subject": "english",
    "book_id": "bk_english_2026",
    "title": "2026 수능특강 영어",
    "pages": {
        "1": {
            "page": 1,
            "passages": ["ENG-01-P01"],
            "questions": ["ENG-01-Q01", "ENG-01-Q02"]
        }
    },
    "units": [
        {
            "type": "passage",
            "passage_id": "ENG-01-P01",
            "sentences": [
                "The quick brown fox jumps over the lazy dog.",
                "This is a sample passage for English reading comprehension.",
                "Students need to understand the main idea of the text.",
                "Some sentences may contain ___ that need to be filled in."
            ],
            "sentences_detail": [
                {
                    "index": 0,
                    "text": "The quick brown fox jumps over the lazy dog.",
                    "char_count": 44,
                    "word_count": 9,
                    "has_placeholder": False
                },
                {
                    "index": 1,
                    "text": "This is a sample passage for English reading comprehension.",
                    "char_count": 60,
                    "word_count": 8,
                    "has_placeholder": False
                },
                {
                    "index": 2,
                    "text": "Students need to understand the main idea of the text.",
                    "char_count": 52,
                    "word_count": 10,
                    "has_placeholder": False
                },
                {
                    "index": 3,
                    "text": "Some sentences may contain ___ that need to be filled in.",
                    "char_count": 58,
                    "word_count": 11,
                    "has_placeholder": True
                }
            ],
            "full_text": "The quick brown fox jumps over the lazy dog. This is a sample passage for English reading comprehension. Students need to understand the main idea of the text. Some sentences may contain ___ that need to be filled in.",
            "placeholders": [
                {
                    "position": 168,
                    "length": 3,
                    "type": "blank",
                    "context": "contain ___ that need"
                }
            ],
            "page": 1,
            "metadata": {
                "sentence_count": 4,
                "char_count": 214,
                "word_count": 38
            }
        },
        {
            "type": "question",
            "question_id": "ENG-01-Q01",
            "question_number": 1,
            "question_type": "blank",
            "passage_id": "ENG-01-P01",
            "question": "다음 빈칸에 들어갈 말로 가장 적절한 것은?",
            "choices": [
                {
                    "label": "①",
                    "number": "①",
                    "text": "words",
                    "index": 0,
                    "char_count": 5,
                    "word_count": 1
                },
                {
                    "label": "②",
                    "number": "②",
                    "text": "ideas",
                    "index": 1,
                    "char_count": 5,
                    "word_count": 1
                },
                {
                    "label": "③",
                    "number": "③",
                    "text": "sentences",
                    "index": 2,
                    "char_count": 9,
                    "word_count": 1
                },
                {
                    "label": "④",
                    "number": "④",
                    "text": "paragraphs",
                    "index": 3,
                    "char_count": 10,
                    "word_count": 1
                },
                {
                    "label": "⑤",
                    "number": "⑤",
                    "text": "articles",
                    "index": 4,
                    "char_count": 8,
                    "word_count": 1
                }
            ],
            "page": 1,
            "metadata": {
                "difficulty": "medium"
            }
        },
        {
            "type": "question",
            "question_id": "ENG-01-Q02",
            "question_number": 2,
            "question_type": "ordering",
            "passage_id": "ENG-01-P01",
            "question": "다음 문장들을 논리적으로 배열할 때, 세 번째에 올 문장은?",
            "choices": [
                {
                    "label": "①",
                    "number": "①",
                    "text": "(A) First sentence",
                    "index": 0
                },
                {
                    "label": "②",
                    "number": "②",
                    "text": "(B) Second sentence",
                    "index": 1
                },
                {
                    "label": "③",
                    "number": "③",
                    "text": "(C) Third sentence",
                    "index": 2
                }
            ],
            "page": 1,
            "metadata": {
                "difficulty": "hard"
            }
        }
    ],
    "statistics": {
        "total_units": 3,
        "passages": 1,
        "questions": 2,
        "question_types": {
            "blank": 1,
            "ordering": 1
        },
        "total_sentences": 4
    },
    "metadata": {
        "year": 2026,
        "extracted_at": "2026-01-01T00:00:00Z"
    }
}
