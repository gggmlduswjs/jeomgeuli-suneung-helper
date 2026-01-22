"""
메인 문서 파서
OCR 데이터 → 중간 구조(Intermediate Document) 변환

이 파서는 두 가지 모드를 지원합니다:
1. 블록 기반 파싱 (기존 방식): 중간 구조(IntermediateDocument) 생성
2. 강의 기반 파싱 (새 방식): 전략 패턴을 사용한 과목별 파싱
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .intermediate_schema import (
    IntermediateDocument,
    IntermediatePage,
    IntermediateBlock,
    BlockType,
    DocumentMetadata,
    LectureInfo
)
from .question_parser import QuestionParser
from .passage_parser import PassageParser
from .concept_parser import ConceptParser
from .example_parser import ExampleParser
from .parsing_rules import ParsingRules

# 전략 패턴 import
try:
    from .strategies import LiteratureParsingStrategy, Math1ParsingStrategy, EnglishParsingStrategy
    STRATEGIES_AVAILABLE = True
except ImportError:
    STRATEGIES_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    문서 파서 - PDF OCR 데이터를 중간 구조로 변환

    두 가지 모드 지원:
    1. parse(): 블록 기반 파싱 (IntermediateDocument 생성)
    2. parse_lectures(): 강의 기반 파싱 (전략 패턴 사용)
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: 설정 딕셔너리 (subject, lecture_title_patterns 등 포함)
        """
        self.config = config or {}
        self.subject = self.config.get('subject', 'literature')

        # 타입별 파서 초기화 (블록 기반 파싱용)
        self.parsers = {
            BlockType.QUESTION: QuestionParser(),
            BlockType.PASSAGE: PassageParser(),
            BlockType.CONCEPT: ConceptParser(),
            BlockType.EXAMPLE: ExampleParser(),
        }

        # 우선순위 순서로 정렬된 파서 리스트
        self.sorted_parsers = sorted(
            self.parsers.items(),
            key=lambda x: ParsingRules.get_priority(x[0].value)
        )

        # 전략 패턴 초기화 (강의 기반 파싱용)
        if STRATEGIES_AVAILABLE:
            self.strategies = {
                'literature': LiteratureParsingStrategy(),
                'math1': Math1ParsingStrategy(),
                'math': Math1ParsingStrategy(),  # 별칭
                'english': EnglishParsingStrategy()
            }
        else:
            self.strategies = {}

        logger.info(f"DocumentParser 초기화: {self.subject}")
        logger.info(f"파서 우선순위: {[p[0].value for p in self.sorted_parsers]}")
        if STRATEGIES_AVAILABLE:
            logger.info(f"전략 패턴 사용 가능: {list(self.strategies.keys())}")

    def parse_lectures(
        self,
        all_ocr_data: List[Dict[str, Any]],
        existing_problem_keys: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        OCR 데이터 → 강의 및 문제 추출 (전략 패턴 사용)

        Args:
            all_ocr_data: OCR 추출 데이터 (페이지별)
            existing_problem_keys: 이미 파싱된 문제 키 집합 (증분 파싱용)

        Returns:
            {
                'lectures': [...],
                'problems': [...],
                'metadata': {...}
            }
        """
        if not STRATEGIES_AVAILABLE:
            raise RuntimeError("전략 패턴이 사용 불가능합니다. strategies 모듈을 확인하세요.")

        strategy = self.strategies.get(self.subject)
        if not strategy:
            raise ValueError(f"Unknown subject: {self.subject}. Available: {list(self.strategies.keys())}")

        logger.info(f"강의 기반 파싱 시작: {self.subject}, {len(all_ocr_data)}개 페이지")

        # 전략을 사용해서 파싱
        lectures = strategy.extract_lectures(all_ocr_data, self.config)
        problems = strategy.extract_problems(all_ocr_data, self.config, existing_problem_keys)

        logger.info(f"강의 기반 파싱 완료: {len(lectures)}개 강의, {len(problems)}개 문제")

        return {
            'subject': self.subject,
            'lectures': lectures,
            'problems': problems,
            'metadata': {
                'total_lectures': len(lectures),
                'total_problems': len(problems),
                'total_pages': len(all_ocr_data)
            }
        }

    def parse(
        self,
        all_ocr_data: List[Dict[str, Any]],
        pdf_path: str,
        ocr_method: str = "pdfplumber"
    ) -> IntermediateDocument:
        """
        OCR 데이터 → 중간 구조 변환 (블록 기반 파싱)

        Args:
            all_ocr_data: OCR 추출 데이터 (페이지별)
            pdf_path: PDF 파일 경로
            ocr_method: OCR 방법 ("pdfplumber", "tesseract")

        Returns:
            IntermediateDocument
        """
        logger.info(f"문서 파싱 시작: {len(all_ocr_data)}개 페이지")

        # 중간 문서 초기화
        doc = IntermediateDocument(
            subject=self.subject,
            pdf_path=pdf_path,
            metadata=DocumentMetadata(
                parser_version="1.0.0",
                parse_timestamp=datetime.now().isoformat(),
                ocr_method=ocr_method,
                total_pages=len(all_ocr_data)
            )
        )

        # 각 페이지 파싱
        for page_ocr in all_ocr_data:
            page_num = page_ocr.get('page_num', 0)
            logger.debug(f"페이지 {page_num} 파싱 중...")

            # 줄 단위로 그룹화
            lines = self._group_texts_by_line(page_ocr)

            if not lines:
                logger.warning(f"페이지 {page_num}: 줄이 없음 (빈 페이지)")
                continue

            # 페이지 파싱
            page = self._parse_page(page_num, lines)
            doc.pages.append(page)

            logger.debug(
                f"페이지 {page_num} 완료: {page.stats.total_blocks}개 블록 "
                f"(개념:{page.stats.concept_count}, 작품:{page.stats.passage_count}, "
                f"문제:{page.stats.question_count})"
            )

        # 강의 정보 추출 (블록 기반)
        doc.lectures = self._extract_lecture_info(doc)

        # 메타데이터 업데이트
        doc.update_metadata()

        logger.info(
            f"문서 파싱 완료: {doc.metadata.total_pages}개 페이지, "
            f"{doc.metadata.total_blocks}개 블록, {len(doc.lectures)}개 강의"
        )

        return doc

    def _parse_page(
        self,
        page_num: int,
        lines: List[Dict[str, Any]]
    ) -> IntermediatePage:
        """
        페이지 파싱

        Args:
            page_num: 페이지 번호
            lines: 줄 데이터

        Returns:
            IntermediatePage
        """
        page = IntermediatePage(page_num=page_num)

        # 페이지 높이 계산
        page_height = max(
            line.get('top', 0) + line.get('height', 0)
            for line in lines
        ) if lines else 1000.0

        # 평균 폰트 크기 계산
        avg_font_size = self._calculate_avg_font_size(lines)

        # 이미 파싱된 줄 추적 (중복 방지)
        parsed_indices = set()

        block_counter = 1

        # 우선순위에 따라 블록 파싱
        for block_type, parser in self.sorted_parsers:
            logger.debug(f"  [{block_type.value}] 파싱 시작...")

            i = 0
            while i < len(lines):
                # 이미 파싱된 줄은 스킵
                if i in parsed_indices:
                    i += 1
                    continue

                # 블록 시작 가능 여부 확인
                can_start, confidence = parser.can_start_block(
                    lines, i, page_height, avg_font_size
                )

                if can_start:
                    # 블록 종료 지점 찾기
                    end_idx = parser.find_block_end(
                        lines, i, page_height, avg_font_size
                    )

                    # 블록 ID 생성
                    block_id = f"p{page_num}_b{block_counter}"

                    # 블록 파싱
                    block = parser.parse_block(
                        page_num=page_num,
                        block_id=block_id,
                        lines=lines,
                        start_idx=i,
                        end_idx=end_idx,
                        page_height=page_height,
                        avg_font_size=avg_font_size
                    )

                    block.metadata.confidence = confidence
                    page.blocks.append(block)

                    # 파싱된 줄 마킹
                    for idx in range(i, end_idx + 1):
                        parsed_indices.add(idx)

                    logger.debug(
                        f"    블록 발견: {block_id} [{block_type.value}] "
                        f"줄 {i}~{end_idx}, 신뢰도 {confidence:.2f}"
                    )

                    block_counter += 1
                    i = end_idx + 1
                else:
                    i += 1

        # 통계 업데이트
        page.update_stats()

        return page

    def _group_texts_by_line(
        self,
        ocr_data: Dict[str, Any],
        y_threshold: int = 10
    ) -> List[Dict[str, Any]]:
        """
        y좌표 기준으로 같은 줄의 단어들을 그룹화

        Args:
            ocr_data: OCR 데이터
            y_threshold: 같은 줄 판단 임계값

        Returns:
            줄별 데이터 리스트
        """
        texts = ocr_data.get('text', [])
        tops = ocr_data.get('top', [])
        lefts = ocr_data.get('left', [])
        widths = ocr_data.get('width', [])
        heights = ocr_data.get('height', [])

        if not texts:
            return []

        # 단어 정보 수집
        words = []
        for i in range(len(texts)):
            text = texts[i].strip() if i < len(texts) else ""
            if not text:
                continue

            word = {
                'text': text,
                'top': tops[i] if i < len(tops) else 0,
                'left': lefts[i] if i < len(lefts) else 0,
                'width': widths[i] if i < len(widths) else 0,
                'height': heights[i] if i < len(heights) else 0,
                'index': i
            }
            words.append(word)

        if not words:
            return []

        # y좌표 기준으로 정렬
        words.sort(key=lambda w: (w['top'], w['left']))

        # 같은 줄로 그룹화
        lines = []
        current_line_words = [words[0]]
        current_y = words[0]['top']

        for word in words[1:]:
            # 같은 줄인지 확인
            if abs(word['top'] - current_y) <= y_threshold:
                current_line_words.append(word)
            else:
                # 새 줄 시작
                if current_line_words:
                    line_dict = self._create_line_dict(current_line_words)
                    lines.append(line_dict)
                current_line_words = [word]
                current_y = word['top']

        # 마지막 줄 추가
        if current_line_words:
            line_dict = self._create_line_dict(current_line_words)
            lines.append(line_dict)

        return lines

    def _create_line_dict(self, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """단어들을 줄 딕셔너리로 변환"""
        # x좌표 기준으로 정렬 (왼쪽부터)
        words.sort(key=lambda w: w['left'])

        # 줄 텍스트 생성
        line_text = " ".join([w['text'] for w in words])

        # bbox 계산
        left = min(w['left'] for w in words)
        top = min(w['top'] for w in words)
        right = max(w['left'] + w['width'] for w in words)
        bottom = max(w['top'] + w['height'] for w in words)

        return {
            'text': line_text,
            'left': left,
            'top': top,
            'width': right - left,
            'height': bottom - top,
            'words': words
        }

    def _calculate_avg_font_size(self, lines: List[Dict[str, Any]]) -> float:
        """평균 폰트 크기 계산"""
        if not lines:
            return 12.0

        heights = [line.get('height', 0) for line in lines if line.get('height', 0) > 0]
        if not heights:
            return 12.0

        return sum(heights) / len(heights)

    def _extract_lecture_info(self, doc: IntermediateDocument) -> List[LectureInfo]:
        """
        블록에서 강의 정보 추출

        현재는 간단히 페이지별로 그룹화
        나중에 더 정교한 로직 추가 가능
        """
        lectures = []
        lecture_id = 1

        # 페이지별로 강의 구분 (간단한 버전)
        current_lecture_blocks = []
        current_start_page = None

        for page in doc.pages:
            if page.blocks:
                if current_start_page is None:
                    current_start_page = page.page_num

                for block in page.blocks:
                    current_lecture_blocks.append(block.block_id)
                    # 블록에 lecture_id 할당
                    block.metadata.lecture_id = lecture_id

        # 마지막 강의 추가
        if current_lecture_blocks:
            lectures.append(LectureInfo(
                lecture_id=lecture_id,
                title=f"강의 {lecture_id}",
                start_page=current_start_page or 1,
                end_page=doc.pages[-1].page_num if doc.pages else 1,
                block_ids=current_lecture_blocks
            ))

        return lectures

    def save_intermediate(
        self,
        doc: IntermediateDocument,
        output_path: Path
    ):
        """중간 구조를 JSON 파일로 저장"""
        import json

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(doc.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"중간 구조 저장 완료: {output_path}")

    def load_intermediate(
        self,
        input_path: Path
    ) -> IntermediateDocument:
        """JSON 파일에서 중간 구조 로드"""
        import json

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        doc = IntermediateDocument.from_dict(data)
        logger.info(f"중간 구조 로드 완료: {input_path}")

        return doc
