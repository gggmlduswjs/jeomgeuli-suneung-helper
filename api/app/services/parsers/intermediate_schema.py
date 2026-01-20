"""
중간 구조 (Intermediate Representation) 스키마
파싱 결과를 담는 데이터 클래스
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


class BlockType(str, Enum):
    """블록 타입"""
    CONCEPT = "concept"
    PASSAGE = "passage"
    QUESTION = "question"
    EXAMPLE = "example"
    UNKNOWN = "unknown"


@dataclass
class Word:
    """단어 정보"""
    text: str
    bbox: List[int]  # [x0, y0, x1, y1]
    confidence: float = 1.0


@dataclass
class Line:
    """줄 정보"""
    line_num: int
    text: str
    words: List[Word] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_num": self.line_num,
            "text": self.text,
            "words": [asdict(w) for w in self.words]
        }


@dataclass
class BlockMetadata:
    """블록 메타데이터"""
    lecture_id: Optional[int] = None
    concept_id: Optional[str] = None
    passage_id: Optional[str] = None
    question_id: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    work_title: Optional[str] = None
    confidence: float = 0.0
    signals_matched: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BlockStatus:
    """블록 파싱 상태"""
    parsed: bool = True
    verified: bool = False
    has_errors: bool = False
    error_messages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntermediateBlock:
    """중간 구조 블록"""
    block_id: str  # "p8_b1" (페이지8_블록1)
    block_type: BlockType
    page: int
    bbox: List[int]  # [x0, y0, x1, y1]
    y_position: float  # 페이지 내 상대 위치 (0.0 ~ 1.0)
    font_size_avg: float
    raw_lines: List[Line] = field(default_factory=list)
    metadata: BlockMetadata = field(default_factory=BlockMetadata)
    status: BlockStatus = field(default_factory=BlockStatus)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화용)"""
        return {
            "block_id": self.block_id,
            "block_type": self.block_type.value,
            "page": self.page,
            "bbox": self.bbox,
            "y_position": self.y_position,
            "font_size_avg": self.font_size_avg,
            "raw_lines": [line.to_dict() for line in self.raw_lines],
            "metadata": self.metadata.to_dict(),
            "status": self.status.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntermediateBlock':
        """딕셔너리에서 복원"""
        # raw_lines 복원
        raw_lines = []
        for line_data in data.get('raw_lines', []):
            words = [
                Word(**word_data)
                for word_data in line_data.get('words', [])
            ]
            raw_lines.append(Line(
                line_num=line_data['line_num'],
                text=line_data['text'],
                words=words
            ))

        return cls(
            block_id=data['block_id'],
            block_type=BlockType(data['block_type']),
            page=data['page'],
            bbox=data['bbox'],
            y_position=data['y_position'],
            font_size_avg=data['font_size_avg'],
            raw_lines=raw_lines,
            metadata=BlockMetadata(**data.get('metadata', {})),
            status=BlockStatus(**data.get('status', {}))
        )

    def get_text(self) -> str:
        """블록의 전체 텍스트 반환"""
        return "\n".join(line.text for line in self.raw_lines)


@dataclass
class PageStats:
    """페이지 통계"""
    total_blocks: int = 0
    concept_count: int = 0
    passage_count: int = 0
    question_count: int = 0
    example_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntermediatePage:
    """페이지 단위 중간 구조"""
    page_num: int
    blocks: List[IntermediateBlock] = field(default_factory=list)
    stats: PageStats = field(default_factory=PageStats)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_num": self.page_num,
            "blocks": [block.to_dict() for block in self.blocks],
            "stats": self.stats.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntermediatePage':
        blocks = [
            IntermediateBlock.from_dict(block_data)
            for block_data in data.get('blocks', [])
        ]
        return cls(
            page_num=data['page_num'],
            blocks=blocks,
            stats=PageStats(**data.get('stats', {}))
        )

    def update_stats(self):
        """통계 업데이트"""
        self.stats.total_blocks = len(self.blocks)
        self.stats.concept_count = sum(1 for b in self.blocks if b.block_type == BlockType.CONCEPT)
        self.stats.passage_count = sum(1 for b in self.blocks if b.block_type == BlockType.PASSAGE)
        self.stats.question_count = sum(1 for b in self.blocks if b.block_type == BlockType.QUESTION)
        self.stats.example_count = sum(1 for b in self.blocks if b.block_type == BlockType.EXAMPLE)


@dataclass
class LectureInfo:
    """강의 경계 정보"""
    lecture_id: int
    title: str
    start_page: int
    end_page: int
    block_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentMetadata:
    """문서 메타데이터"""
    parser_version: str = "1.0.0"
    parse_timestamp: str = ""
    ocr_method: str = "pdfplumber"
    total_pages: int = 0
    total_blocks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntermediateDocument:
    """문서 전체 중간 구조"""
    subject: str
    pdf_path: str
    pages: List[IntermediatePage] = field(default_factory=list)
    lectures: List[LectureInfo] = field(default_factory=list)
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화용)"""
        return {
            "subject": self.subject,
            "pdf_path": self.pdf_path,
            "pages": [page.to_dict() for page in self.pages],
            "lectures": [lecture.to_dict() for lecture in self.lectures],
            "metadata": self.metadata.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntermediateDocument':
        """딕셔너리에서 복원"""
        pages = [
            IntermediatePage.from_dict(page_data)
            for page_data in data.get('pages', [])
        ]
        lectures = [
            LectureInfo(**lecture_data)
            for lecture_data in data.get('lectures', [])
        ]
        return cls(
            subject=data['subject'],
            pdf_path=data['pdf_path'],
            pages=pages,
            lectures=lectures,
            metadata=DocumentMetadata(**data.get('metadata', {}))
        )

    def find_block_by_id(self, block_id: str) -> Optional[IntermediateBlock]:
        """블록 ID로 블록 찾기"""
        for page in self.pages:
            for block in page.blocks:
                if block.block_id == block_id:
                    return block
        return None

    def get_lecture_blocks(self, lecture_id: int) -> List[IntermediateBlock]:
        """특정 강의의 모든 블록 가져오기"""
        lecture = next((l for l in self.lectures if l.lecture_id == lecture_id), None)
        if not lecture:
            return []

        blocks = []
        for block_id in lecture.block_ids:
            block = self.find_block_by_id(block_id)
            if block:
                blocks.append(block)
        return blocks

    def update_metadata(self):
        """메타데이터 업데이트"""
        self.metadata.total_pages = len(self.pages)
        self.metadata.total_blocks = sum(len(page.blocks) for page in self.pages)
