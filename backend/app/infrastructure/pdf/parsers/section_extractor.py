"""
개선된 섹션 추출기

다중 전략을 사용하여 섹션 추출 정확도 향상.
리팩토링: 각 기능을 별도 모듈로 분리하여 유지보수성 향상.
"""
import logging
from typing import List, Optional

from .base import BaseParser
from .extraction_config import ExtractionConfig, DEFAULT_CONFIG
from .extraction_types import SectionExtractionResult
from .extraction_strategies import ExtractionStrategies
from app.infrastructure.pdf.types import OCRPageData, JSONDict

logger = logging.getLogger(__name__)


class ImprovedSectionExtractor:
    """개선된 섹션 추출기

    다중 전략을 사용하여 섹션 추출 정확도 향상:
    1. 패턴 매칭 (빠름, 정확도 70-80%)
    2. AI 분석 (느림, 정확도 85-95%)
    3. 휴리스틱 폴백 (안정성, 정확도 50-70%)

    리팩토링된 구조:
    - extraction_config: 모든 설정 및 상수
    - extraction_types: 타입 정의
    - pattern_matching: 패턴 매칭 로직
    - region_classifier: Y좌표 기반 영역 분류
    - text_block_classifier: 텍스트 블록 분류
    - extraction_strategies: 추출 전략 구현
    """

    def __init__(
        self,
        config: JSONDict,
        parser: Optional[BaseParser] = None,
        enable_ai: bool = False,
        api_key: Optional[str] = None
    ):
        """
        Args:
            config: 파서 설정 딕셔너리
            parser: BaseParser 인스턴스 (AI 파싱용)
            enable_ai: AI 분석 활성화 여부
            api_key: OpenAI API 키 (AI 사용 시)
        """
        self.config = config
        self.parser = parser
        self.enable_ai = enable_ai
        self.api_key = api_key

        # Load extraction configuration
        self.extraction_config = DEFAULT_CONFIG

        # Initialize strategies
        self.strategies = ExtractionStrategies(
            config=config,
            parser=parser,
            config_obj=self.extraction_config
        )

        # Log initialization
        region_text_examples = config.get('region_text_examples', {})
        region_hints = config.get('region_hints', {})
        lecture_page_ranges = config.get('lecture_page_ranges', {})

        if region_text_examples:
            total_examples = sum(len(v) for v in region_text_examples.values())
            logger.info(
                f"[SectionExtractor] region_text_examples 활성화: "
                f"{list(region_text_examples.keys())} ({total_examples}개 예시)"
            )
        elif region_hints:
            logger.info(
                f"[SectionExtractor] region_hints 활성화 (하위 호환): "
                f"{list(region_hints.keys())}"
            )
        else:
            logger.info(
                "[SectionExtractor] region_hints/region_text_examples 없음 "
                "(기본 패턴만 사용)"
            )

        if lecture_page_ranges:
            logger.info(
                f"[SectionExtractor] 강의별 페이지 범위 활성화: "
                f"{len(lecture_page_ranges)}개 강의"
            )

        # Log classifier/validator status
        if self.strategies.font_classifier.enabled:
            logger.info("[SectionExtractor] FontBasedClassifier 활성화")
        if self.strategies.layout_validator.enabled:
            logger.info("[SectionExtractor] LayoutBasedValidator 활성화")
        if self.strategies.problem_matcher.enabled:
            logger.info("[SectionExtractor] ProblemPatternMatcher 활성화")
        if self.strategies.spacing_validator.enabled:
            logger.info("[SectionExtractor] SectionSpacingValidator 활성화")

    def extract(
        self,
        lecture_ocr_data: List[OCRPageData]
    ) -> SectionExtractionResult:
        """섹션 추출 (다중 전략)

        Args:
            lecture_ocr_data: 강의에 해당하는 OCR 데이터 리스트

        Returns:
            SectionExtractionResult
        """
        if not lecture_ocr_data:
            return SectionExtractionResult(
                sections=[],
                confidence=0.0,
                method='none',
                metadata={'error': 'OCR 데이터가 비어있음'}
            )

        # OCR 데이터 전처리
        try:
            from .text_preprocessor import TextPreprocessor
            processed_ocr_data = TextPreprocessor.preprocess_ocr_data(
                lecture_ocr_data
            )
        except Exception as e:
            logger.warning(f"OCR 전처리 실패, 원본 데이터 사용: {e}")
            processed_ocr_data = lecture_ocr_data

        # 1. 패턴 매칭 시도 (빠름)
        pattern_result = self.strategies.extract_by_pattern(processed_ocr_data)

        if pattern_result['confidence'] >= self.extraction_config.pattern_confidence_threshold:
            logger.info(
                f"패턴 매칭 성공: {len(pattern_result['sections'])}개 섹션 "
                f"(신뢰도: {pattern_result['confidence']:.2f})"
            )
            return SectionExtractionResult(
                sections=pattern_result['sections'],
                confidence=pattern_result['confidence'],
                method='pattern',
                metadata=pattern_result.get('metadata', {})
            )

        # 2. AI 분석 시도 (패턴 매칭 실패 시)
        if self.enable_ai and self.parser:
            try:
                ai_result = self.strategies.extract_by_ai(processed_ocr_data)
                if ai_result['confidence'] >= self.extraction_config.ai_confidence_threshold:
                    logger.info(
                        f"AI 분석 성공: {len(ai_result['sections'])}개 섹션 "
                        f"(신뢰도: {ai_result['confidence']:.2f})"
                    )
                    return SectionExtractionResult(
                        sections=ai_result['sections'],
                        confidence=ai_result['confidence'],
                        method='ai',
                        metadata=ai_result.get('metadata', {})
                    )
            except Exception as e:
                logger.warning(f"AI 분석 실패, 휴리스틱으로 전환: {e}")

        # 3. 휴리스틱 폴백 (안정성)
        heuristic_result = self.strategies.extract_by_heuristic(processed_ocr_data)

        # 패턴 결과와 병합 (신뢰도가 낮아도 일부 섹션은 유용할 수 있음)
        combined_sections = self.strategies.merge_sections(
            pattern_result['sections'],
            heuristic_result['sections']
        )

        # 최종 신뢰도 계산
        final_confidence = max(
            pattern_result['confidence'],
            heuristic_result['confidence']
        )

        logger.info(
            f"휴리스틱 폴백 사용: {len(combined_sections)}개 섹션 "
            f"(신뢰도: {final_confidence:.2f})"
        )

        return SectionExtractionResult(
            sections=combined_sections,
            confidence=final_confidence,
            method='heuristic' if not pattern_result['sections'] else 'combined',
            metadata={
                'pattern_sections': len(pattern_result['sections']),
                'heuristic_sections': len(heuristic_result['sections']),
                'merged_sections': len(combined_sections)
            }
        )

    # Backward compatibility: Keep method signatures for internal use
    def _merge_sections(self, sections1, sections2):
        """Backward compatibility wrapper for merge_sections"""
        return self.strategies.merge_sections(sections1, sections2)
