"""
수능특강 문학 콘텐츠 JSON 스키마

점자·음성·시험 모드에서 공통으로 사용할 스키마
"""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============= 문학 전용 스키마 =============

class Choice(BaseModel):
    """보기 (선택지)"""
    number: Optional[str] = Field(None, description="보기 번호 (①, 1, (1) 등)")
    text: str = Field(description="보기 텍스트")
    index: int = Field(description="0-based 인덱스 (①=0, ②=1, ...)")


class Passage(BaseModel):
    """지문"""
    type: Literal["passage"] = "passage"
    passage_id: str = Field(description="지문 고유 ID (예: LIT-01-P01)")
    title: Optional[str] = Field(None, description="작품명/제목")
    text: str = Field(description="지문 전체 텍스트")
    page_start: int = Field(description="시작 페이지")
    page_end: int = Field(description="종료 페이지")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="작가, 갈래 등")


class Question(BaseModel):
    """문제"""
    type: Literal["question"] = "question"
    question_id: str = Field(description="문제 고유 ID (예: LIT-01-Q01)")
    question_number: Optional[int] = Field(None, description="문제 번호")
    passage_id: Optional[str] = Field(None, description="참조하는 지문 ID")
    question_text: str = Field(description="문제 본문")
    choices: List[Choice] = Field(default_factory=list, description="보기 리스트")
    page: int = Field(description="페이지 번호")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LiteratureContent(BaseModel):
    """문학 콘텐츠 (최종 결과)"""
    version: str = Field(default="1.0", description="스키마 버전")
    subject: Literal["literature"] = "literature"
    book_id: Optional[str] = Field(None, description="교재 ID")
    title: Optional[str] = Field(None, description="교재 제목")
    
    # 지문 리스트
    passages: List[Passage] = Field(description="지문 리스트")
    
    # 문제 리스트
    questions: List[Question] = Field(description="문제 리스트")
    
    # 통계
    statistics: Dict[str, Any] = Field(description="파싱 통계")
    
    # 메타데이터
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============= 실제 예시 JSON =============

EXAMPLE_LITERATURE_JSON = {
    "version": "1.0",
    "subject": "literature",
    "book_id": "bk_literature_2026",
    "title": "2026 수능특강 문학",
    "passages": [
        {
            "type": "passage",
            "passage_id": "LIT-01-P01",
            "title": "황조가",
            "text": "철령 이화 우는 수이건\n마란은 아이다라도\n가시리 가시리 잇고\n배반 도다 사라하노라\n\n백설이 만발한 대에\n홀로 외로이 서 있으니\n하늘이 내게 주신 한 세상\n아 이별이여 이별이여",
            "page_start": 1,
            "page_end": 1,
            "metadata": {
                "genre": "고전시가",
                "period": "삼국시대",
                "author": "신라"
            }
        }
    ],
    "questions": [
        {
            "type": "question",
            "question_id": "LIT-01-Q01",
            "question_number": 1,
            "passage_id": "LIT-01-P01",
            "question_text": "다음 시의 화자의 심정으로 가장 적절한 것은?",
            "choices": [
                {
                    "number": "①",
                    "text": "이별의 슬픔과 아쉬움",
                    "index": 0
                },
                {
                    "number": "②",
                    "text": "사랑의 기쁨과 희열",
                    "index": 1
                },
                {
                    "number": "③",
                    "text": "고독과 절망",
                    "index": 2
                },
                {
                    "number": "④",
                    "text": "화합과 조화에 대한 갈망",
                    "index": 3
                },
                {
                    "number": "⑤",
                    "text": "자연에 대한 경외와 숭배",
                    "index": 4
                }
            ],
            "page": 1,
            "metadata": {
                "question_type": "화자의 심정",
                "difficulty": "medium"
            }
        },
        {
            "type": "question",
            "question_id": "LIT-01-Q02",
            "question_number": 2,
            "passage_id": "LIT-01-P01",
            "question_text": "윗글에 대한 이해로 적절하지 않은 것은?",
            "choices": [
                {
                    "number": "①",
                    "text": "대구법을 사용하여 대칭미를 살렸다.",
                    "index": 0
                },
                {
                    "number": "②",
                    "text": "자연물을 통해 감정을 표현했다.",
                    "index": 1
                },
                {
                    "number": "③",
                    "text": "직접적인 화법으로 감정을 드러냈다.",
                    "index": 2
                },
                {
                    "number": "④",
                    "text": "현실 도피적 경향을 보여준다.",
                    "index": 3
                },
                {
                    "number": "⑤",
                    "text": "삼국시대의 대표적인 향가이다.",
                    "index": 4
                }
            ],
            "page": 1,
            "metadata": {
                "question_type": "이해",
                "difficulty": "hard"
            }
        }
    ],
    "statistics": {
        "total_passages": 1,
        "total_questions": 2,
        "passages_with_questions": 1
    },
    "metadata": {
        "year": 2026,
        "extracted_at": "2026-01-01T00:00:00Z"
    }
}
