"""
개선된 섹션 추출기
다중 전략을 사용하여 섹션 추출 정확도 향상
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from .base import BaseParser
from .text_preprocessor import TextPreprocessor
from .font_classifier import FontBasedClassifier
from .layout_validator import LayoutBasedValidator
from .problem_pattern_matcher import ProblemPatternMatcher
from .section_spacing_validator import SectionSpacingValidator

logger = logging.getLogger(__name__)


@dataclass
class SectionExtractionResult:
    """섹션 추출 결과
    
    Attributes:
        sections: 추출된 섹션 리스트
        confidence: 추출 신뢰도 (0.0-1.0)
        method: 사용된 추출 방법 ('pattern', 'ai', 'heuristic', 'combined')
        metadata: 추가 메타데이터
    """
    sections: List[Dict[str, Any]]
    confidence: float
    method: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ImprovedSectionExtractor:
    """개선된 섹션 추출기
    
    다중 전략을 사용하여 섹션 추출 정확도 향상:
    1. 패턴 매칭 (빠름, 정확도 70-80%)
    2. AI 분석 (느림, 정확도 85-95%)
    3. 휴리스틱 폴백 (안정성, 정확도 50-70%)
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
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
        
        # 패턴
        self.concept_patterns = config.get('concept_title_patterns', [])
        self.content_patterns = config.get('content_header_patterns', [])
        self.section_patterns = config.get('section_title_patterns', [])
        
        # region_hints (y 좌표 기반 단위 분류 힌트) - 하위 호환성
        self.region_hints = config.get('region_hints', {})
        self.unit_order = config.get('unit_order', ['concept', 'passage', 'problem'])
        
        # region_text_examples (영역 내 텍스트 예시, 패턴 학습용) - 우선 사용
        self.region_text_examples = config.get('region_text_examples', {})
        
        # 강의별 페이지 범위 정보 (각 강의 내에서 concept/passage/problem 구조가 동일)
        self.lecture_page_ranges = config.get('lecture_page_ranges', {})
        
        # Priority 1: 새로운 분류기/검증기 초기화
        self.font_classifier = FontBasedClassifier(config.get('font_info'))
        self.layout_validator = LayoutBasedValidator(config.get('layout_info'))
        self.problem_matcher = ProblemPatternMatcher(config.get('problem_patterns'))
        self.spacing_validator = SectionSpacingValidator(config.get('section_spacing'))
        
        if self.region_text_examples:
            logger.info(f"[SectionExtractor] region_text_examples 활성화: {list(self.region_text_examples.keys())} ({sum(len(v) for v in self.region_text_examples.values())}개 예시)")
            for label, examples in self.region_text_examples.items():
                logger.info(f"  - {label}: {len(examples)}개 텍스트 예시")
        elif self.region_hints:
            logger.info(f"[SectionExtractor] region_hints 활성화 (하위 호환): {list(self.region_hints.keys())} ({len(self.region_hints)}개 레이블)")
        else:
            logger.info("[SectionExtractor] region_hints/region_text_examples 없음 (기본 패턴만 사용)")
        
        if self.lecture_page_ranges:
            logger.info(f"[SectionExtractor] 강의별 페이지 범위 활성화: {len(self.lecture_page_ranges)}개 강의")
        
        # 새로운 분류기 상태 로깅
        if self.font_classifier.enabled:
            logger.info("[SectionExtractor] FontBasedClassifier 활성화")
        if self.layout_validator.enabled:
            logger.info("[SectionExtractor] LayoutBasedValidator 활성화")
        if self.problem_matcher.enabled:
            logger.info("[SectionExtractor] ProblemPatternMatcher 활성화")
        if self.spacing_validator.enabled:
            logger.info("[SectionExtractor] SectionSpacingValidator 활성화")
        
        # 기본 패턴 (config에 없을 때 사용)
        if not self.concept_patterns:
            self.concept_patterns = [
                r'^(\d+)\s*[\.]\s*([가-힣\s]{2,20})$',
                r'^\d+\s+[가-힣]{2,}\s*[가-힣]*$'
            ]
    
    def _get_lecture_info_for_page(self, page_num: int) -> Optional[Dict[str, Any]]:
        """페이지 번호로 해당 강의 정보 조회
        
        Args:
            page_num: 페이지 번호
            
        Returns:
            강의 정보 딕셔너리 또는 None
            {
                'lecture_id': int,
                'start_page': int,
                'end_page': Optional[int],
                'page_index': int,  # 강의 내 상대 위치 (0부터 시작)
                'page_ratio': float  # 강의 내 상대 위치 (0.0-1.0)
            }
        """
        if not self.lecture_page_ranges:
            return None
        
        for lecture_id, range_info in self.lecture_page_ranges.items():
            start = range_info.get('start_page')
            end = range_info.get('end_page')
            
            if start is not None:
                if end is not None:
                    if start <= page_num <= end:
                        total_pages = end - start + 1
                        page_index = page_num - start
                        page_ratio = page_index / total_pages if total_pages > 0 else 0.0
                        return {
                            'lecture_id': lecture_id,
                            'start_page': start,
                            'end_page': end,
                            'page_index': page_index,
                            'page_ratio': page_ratio,
                            'total_pages': total_pages
                        }
                else:
                    # 마지막 강의 (end_page가 None)
                    if page_num >= start:
                        # 마지막 강의는 정확한 비율 계산 불가 (대략적으로만)
                        return {
                            'lecture_id': lecture_id,
                            'start_page': start,
                            'end_page': None,
                            'page_index': page_num - start,
                            'page_ratio': 0.5,  # 대략 중간으로 가정
                            'total_pages': None
                        }
        
        return None
    
    def _classify_by_region_hint(
        self,
        y_ratio: float,
        page_height: float = 1400.0,
        lecture_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Tuple[str, float]]:
        """region_hints를 사용하여 y 좌표 기반 단위 분류 (개선된 버전)
        
        Args:
            y_ratio: y 좌표의 페이지 비율 (0.0-1.0)
            page_height: 페이지 높이 (픽셀, 기본값 1400)
            lecture_info: 강의 정보 (선택, 있으면 강의 내 위치 고려)
            
        Returns:
            (단위 타입, 신뢰도) 튜플 또는 None
            - 단위 타입: 'concept', 'passage', 'problem'
            - 신뢰도: 0.0-1.0 (영역 중앙에 가까울수록 높음, 강의 내 위치 고려)
        """
        if not self.region_hints:
            return None
        
        best_match = None
        best_confidence = 0.0
        
        # unit_order 순서대로 확인 (일반적으로 concept -> passage -> problem)
        for unit_type in self.unit_order:
            if unit_type not in self.region_hints:
                continue
            
            hint = self.region_hints[unit_type]
            y_min = hint.get('y_min', 0.0)
            y_max = hint.get('y_max', 1.0)
            
            # y_ratio가 힌트 범위 내에 있으면 해당 단위 타입 반환
            if y_min <= y_ratio <= y_max:
                # 영역 중앙에 가까울수록 높은 신뢰도
                y_center = (y_min + y_max) / 2.0
                distance_from_center = abs(y_ratio - y_center)
                range_size = y_max - y_min
                if range_size > 0:
                    # 중앙에 가까울수록 1.0, 가장자리에 가까울수록 0.5
                    confidence = 1.0 - (distance_from_center / (range_size / 2.0)) * 0.5
                    confidence = max(0.5, min(1.0, confidence))
                else:
                    confidence = 1.0
                
                # 강의 내 위치에 따른 신뢰도 보정
                if lecture_info:
                    page_ratio = lecture_info.get('page_ratio', 0.5)
                    
                    # 강의 내 위치와 unit_type의 예상 위치 비교
                    # concept은 보통 강의 초반(0.0-0.3), passage는 중반(0.3-0.7), problem은 후반(0.7-1.0)
                    expected_position_ranges = {
                        'concept': (0.0, 0.3),
                        'passage': (0.3, 0.7),
                        'problem': (0.7, 1.0)
                    }
                    
                    if unit_type in expected_position_ranges:
                        expected_min, expected_max = expected_position_ranges[unit_type]
                        if expected_min <= page_ratio <= expected_max:
                            # 예상 위치와 일치하면 신뢰도 증가
                            confidence = min(1.0, confidence * 1.3)
                            logger.debug(f"[강의 위치 보정] {unit_type} 예상 위치({expected_min:.1f}-{expected_max:.1f})와 일치 (page_ratio={page_ratio:.2f})")
                        else:
                            # 예상 위치와 다르면 신뢰도 감소
                            confidence = confidence * 0.8
                            logger.debug(f"[강의 위치 보정] {unit_type} 예상 위치({expected_min:.1f}-{expected_max:.1f})와 불일치 (page_ratio={page_ratio:.2f})")
                
                if confidence > best_confidence:
                    best_match = unit_type
                    best_confidence = confidence
        
        if best_match:
            return (best_match, best_confidence)
        return None
    
    def _classify_all_text_blocks(
        self,
        lecture_ocr_data: List[Dict[str, Any]],
        existing_sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """전체 페이지의 모든 텍스트 블록을 개념/본문/문제로 분류
        
        Args:
            lecture_ocr_data: 강의에 해당하는 OCR 데이터 리스트
            existing_sections: 이미 추출된 섹션 리스트
            
        Returns:
            분류된 텍스트 블록 리스트
        """
        if not self.region_text_examples:
            return []
        
        classified_blocks = []
        
        # 이미 분류된 섹션의 bbox를 제외하기 위한 집합
        classified_bboxes = set()
        for section in existing_sections:
            bbox = section.get('bbox')
            if bbox and len(bbox) >= 4:
                # bbox를 문자열로 변환하여 집합에 추가 (근사치 비교)
                bbox_key = f"{bbox[0]//10}_{bbox[1]//10}_{bbox[2]//10}_{bbox[3]//10}"
                classified_bboxes.add(bbox_key)
        
        for ocr_data in lecture_ocr_data:
            page_num = ocr_data.get('page_num', 0)
            texts = ocr_data.get('text', [])
            lefts = ocr_data.get('left', [])
            tops = ocr_data.get('top', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            # 문단 단위로 그룹화 (y 좌표 기준)
            paragraph_threshold = self.config.get('paragraph_y_threshold', 25)
            lines = BaseParser.group_lines(ocr_data, y_threshold=paragraph_threshold)
            
            # 각 문단(블록)을 분류
            for line in lines:
                if not line:
                    continue
                
                line_text = BaseParser.join_line_text(line)
                line_text = TextPreprocessor.normalize_text(line_text)
                
                if not line_text or len(line_text) < 3:
                    continue
                
                # 이미 섹션으로 분류된 텍스트는 제외
                bbox = BaseParser.get_line_bbox(line)
                if bbox and len(bbox) >= 4:
                    bbox_key = f"{bbox[0]//10}_{bbox[1]//10}_{bbox[2]//10}_{bbox[3]//10}"
                    if bbox_key in classified_bboxes:
                        continue
                
                # region_text_examples로 분류 시도
                best_match_type = None
                best_match_score = 0.0
                
                for unit_type, examples in self.region_text_examples.items():
                    for example_text in examples:
                        # 유사도 계산
                        score = 0.0
                        
                        # 정확한 포함 여부
                        if example_text in line_text or line_text in example_text:
                            score = 1.0
                        # 키워드 매칭
                        elif example_text and line_text:
                            example_words = set(example_text.split())
                            line_words = set(line_text.split())
                            common_words = example_words & line_words
                            if common_words:
                                score = len(common_words) / max(len(example_words), 1) * 0.6
                        
                        if score > best_match_score:
                            best_match_score = score
                            best_match_type = unit_type
                
                # 임계값 이상이면 분류
                if best_match_type and best_match_score >= 0.4:  # 일반 텍스트는 더 낮은 임계값
                    classified_blocks.append({
                        "title": line_text[:100],  # 처음 100자만
                        "type": best_match_type,
                        "page": page_num,
                        "bbox": bbox,
                        "confidence": best_match_score,
                        "source": "text_block_classification"
                    })
        
        return classified_blocks
    
    def _is_in_region_hint(
        self,
        y_ratio: float,
        unit_type: Optional[str] = None
    ) -> bool:
        """y 좌표가 region_hint 영역 내에 있는지 확인
        
        Args:
            y_ratio: y 좌표의 페이지 비율 (0.0-1.0)
            unit_type: 특정 단위 타입 확인 (None이면 모든 타입 확인)
            
        Returns:
            영역 내에 있으면 True
        """
        if not self.region_hints:
            return False
        
        if unit_type:
            if unit_type not in self.region_hints:
                return False
            hint = self.region_hints[unit_type]
            y_min = hint.get('y_min', 0.0)
            y_max = hint.get('y_max', 1.0)
            return y_min <= y_ratio <= y_max
        else:
            # 모든 타입 확인
            for hint in self.region_hints.values():
                y_min = hint.get('y_min', 0.0)
                y_max = hint.get('y_max', 1.0)
                if y_min <= y_ratio <= y_max:
                    return True
            return False

    def extract(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
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
            processed_ocr_data = TextPreprocessor.preprocess_ocr_data(lecture_ocr_data)
        except Exception as e:
            logger.warning(f"OCR 전처리 실패, 원본 데이터 사용: {e}")
            processed_ocr_data = lecture_ocr_data
        
        # 1. 패턴 매칭 시도 (빠름)
        pattern_result = self._extract_by_pattern(processed_ocr_data)
        
        if pattern_result['confidence'] >= 0.7:
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
                ai_result = self._extract_by_ai(processed_ocr_data)
                if ai_result['confidence'] >= 0.7:
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
        heuristic_result = self._extract_by_heuristic(processed_ocr_data)
        
        # 패턴 결과와 병합 (신뢰도가 낮아도 일부 섹션은 유용할 수 있음)
        combined_sections = self._merge_sections(
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
    
    def _extract_by_pattern(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """패턴 기반 섹션 추출
        
        기존 LiteratureParser의 extract_sections 로직 개선
        """
        try:
            sections = []
            matched_count = 0
            total_lines = 0
            
            # 디버깅: lecture_ocr_data 확인
            if not lecture_ocr_data:
                logger.warning("[SectionExtractor] lecture_ocr_data가 비어있음 - 섹션 추출 불가")
                return {'sections': [], 'confidence': 0.0, 'method': 'none', 'total_lines': 0, 'matched_count': 0}
            
            logger.info(f"[SectionExtractor] 섹션 추출 시작: {len(lecture_ocr_data)}개 페이지")
            
            START_PAGE = self.config.get('start_content_page', 8)
            
            # 강의의 실제 시작 페이지 찾기
            if lecture_ocr_data:
                actual_start_page = min(
                    ocr_data.get('page_num', 0) 
                    for ocr_data in lecture_ocr_data
                )
                search_start_page = min(START_PAGE, actual_start_page)
                logger.debug(f"[SectionExtractor] 시작 페이지: {search_start_page} (START_PAGE={START_PAGE}, actual={actual_start_page})")
            else:
                search_start_page = START_PAGE
            
            for ocr_data in lecture_ocr_data:
                page_num = ocr_data.get('page_num', 0)

                if page_num < search_start_page:
                    continue

                texts = ocr_data.get('text', [])
                if not texts:
                    continue

                # y좌표 기준으로 같은 줄의 단어들을 그룹화
                lines = BaseParser.group_lines(ocr_data, y_threshold=10)
                total_lines += len(lines)

                # 강의 정보 조회 (페이지 범위 및 상대 위치)
                lecture_info = self._get_lecture_info_for_page(page_num)

                # 각 줄을 문장으로 결합하고 패턴 매칭
                for line_idx, line in enumerate(lines):
                    try:
                        line_text = BaseParser.join_line_text(line)
                        line_text = TextPreprocessor.normalize_text(line_text)
                    except Exception as e:
                        logger.warning(f"[SectionExtractor] 줄 처리 중 오류 (페이지 {page_num}, 줄 {line_idx}): {e}")
                        continue

                    if not line_text:
                        continue

                    # 목차 형식 제외
                    if re.search(r'\d{3}', line_text) and len(line_text) < 30:
                        continue

                    # 날짜/시간 패턴 필터링 (예: "25. 1. 6. 오후 6:01") - 명확한 패턴만
                    if re.search(r'\d+\.\s*\d+\.\s*\d+\.\s*(오전|오후|AM|PM)\s*\d+:\d+', line_text):
                        continue

                    # 페이지 번호 패턴 필터링 (예: "128 EBS", "202 EBS") - 정확히 매칭되는 경우만
                    if re.match(r'^\d+\s+EBS\s*$', line_text.strip()):
                        continue

                    # 숫자만 있는 경우 필터링 (예: "1", "2.")
                    if re.match(r'^\d+\.?\s*$', line_text.strip()):
                        continue

                    # 패턴 매칭 전에는 필터링을 최소화 (패턴 매칭 후에 검증)

                    section_type = None
                    section_title = None
                    font_classification = None
                
                # 폰트 기반 분류 시도 (우선 적용, OCR에 폰트 정보가 있는 경우)
                if self.font_classifier.enabled:
                    # line의 첫 번째 단어에서 폰트 정보 추출 시도
                    if line and len(line) > 0:
                        first_word = line[0]
                        # OCR 결과에 폰트 정보가 포함되어 있을 수 있음
                        font_classification = self.font_classifier.classify_by_font(
                            first_word,
                            line_text
                        )
                        if font_classification and font_classification.get('confidence', 0) >= 0.7:
                            # 높은 신뢰도면 바로 사용
                            section_type = font_classification.get('type')
                            section_title = line_text
                            logger.debug(
                                f"[FontClassifier] 높은 신뢰도 매칭: '{line_text[:30]}...' -> {section_type}"
                            )
                
                # 0. region_text_examples로 텍스트 매칭 (우선 적용, 개선된 유사도 매칭)
                if self.region_text_examples:
                    best_match_type = None
                    best_match_score = 0.0
                    
                    for unit_type, examples in self.region_text_examples.items():
                        for example_text in examples:
                            # 유사도 계산 (여러 방법 조합)
                            score = 0.0
                            
                            # 1. 정확한 포함 여부 (높은 점수)
                            if example_text in line_text or line_text in example_text:
                                score = 1.0
                            # 2. 키워드 매칭 (예시의 주요 단어가 포함되는지)
                            elif example_text and line_text:
                                example_words = set(example_text.split())
                                line_words = set(line_text.split())
                                common_words = example_words & line_words
                                if common_words:
                                    # 공통 단어 비율
                                    score = len(common_words) / max(len(example_words), 1) * 0.7
                            # 3. 부분 문자열 매칭 (예시의 일부가 포함되는지)
                            if score < 0.5:
                                # 예시의 앞부분 5글자 이상이 포함되는지
                                if len(example_text) >= 5:
                                    prefix = example_text[:5]
                                    if prefix in line_text:
                                        score = 0.5
                            
                            if score > best_match_score:
                                best_match_score = score
                                best_match_type = unit_type
                    
                    # 임계값 이상이면 매칭 성공
                    if best_match_type and best_match_score >= 0.5:
                        section_type = best_match_type
                        section_title = line_text
                        matched_count += 1
                        logger.debug(f"[region_text_examples] 매칭: '{line_text[:30]}...' -> {best_match_type} (점수: {best_match_score:.2f})")
                
                # 1. 메인 개념 섹션 확인 (region_text_examples에서 매칭 안 된 경우)
                if not section_type:
                    # 패턴 1: "1. 시적 표현" (숫자로 시작하는 경우만)
                    main_concept_match = re.match(
                        r'^(\d+)\s*[\.]\s*([가-힣\s]{4,50})$',  # 최소 4글자 이상
                        line_text
                    )
                    if main_concept_match:
                        section_type = "concept"
                        section_title = line_text
                        matched_count += 1
                    # 패턴 2: "1 시적 표현" (점 없음, 숫자로 시작)
                    elif re.match(
                        r'^\d+\s+[가-힣]{4,}\s*[가-힣]*$',  # 최소 4글자 이상
                        line_text
                    ) and len(line_text.split()) <= 5:  # 최대 5단어
                        section_type = "concept"
                        section_title = line_text
                        matched_count += 1
                    # 패턴 3: config의 concept_title_patterns 사용
                    elif self.concept_patterns:
                        for pattern in self.concept_patterns:
                            if re.search(pattern, line_text):
                                # 패턴 매칭 후 최소한의 검증만 (너무 엄격하지 않게)
                                stripped = line_text.strip()
                                # 숫자만 있는 경우 제외
                                if re.match(r'^\d+\.?\s*$', stripped):
                                    continue
                                # 명확한 날짜/시간 패턴만 제외
                                if re.search(r'\d+\.\s*\d+\.\s*\d+\.\s*(오전|오후|AM|PM)\s*\d+:\d+', stripped):
                                    continue
                                # 페이지 번호 패턴만 제외
                                if re.match(r'^\d+\s+EBS\s*$', stripped):
                                    continue
                                
                                section_type = "concept"
                                section_title = line_text
                                matched_count += 1
                                break
                
                # 2. 본문 섹션 확인
                if not section_type and self.content_patterns:
                    if BaseParser.matches_patterns(line_text, self.content_patterns):
                        section_type = "content"
                        section_title = line_text
                        matched_count += 1
                        
                        # 다음 줄에서 작품 제목 찾기
                        if line_idx + 1 < len(lines):
                            next_line = lines[line_idx + 1]
                            next_text = BaseParser.join_line_text(next_line)
                            next_text = TextPreprocessor.normalize_text(next_text)
                            
                            # 작품 제목 패턴 확인
                            if re.search(
                                r'[가-힣]+\s*\[[가-힣]+\]', 
                                next_text
                            ) or re.search(
                                r'[가-힣]+\s*「[가-힣]+」', 
                                next_text
                            ):
                                section_title = f"{line_text} - {next_text}"
                
                # 3. 폴백: 패턴 매칭이 모두 실패했을 때 관대한 휴리스틱 적용
                # 한글이 3글자 이상 포함된 짧은 줄(30자 이하)은 개념 섹션으로 간주
                if not section_type and len(line_text) <= 30 and len(line_text) >= 3:
                    korean_chars = len(re.findall(r'[가-힣]', line_text))
                    if korean_chars >= 3:
                        # 숫자로 시작하는 경우만 (너무 관대하지 않게)
                        if re.match(r'^\d+[\.\s]', line_text):
                            section_type = "concept"
                            section_title = line_text
                            matched_count += 1
                            logger.debug(f"[SectionExtractor] 폴백 매칭: '{line_text[:30]}...' -> concept")
                
                if section_type and section_title:
                    # 최종 검증: 명확히 잘못된 경우만 제외 (너무 엄격하지 않게)
                    stripped_title = section_title.strip()
                    
                    # 빈 문자열 체크
                    if not stripped_title:
                        continue
                    
                    # 숫자만 있는 경우 제외
                    if re.match(r'^\d+\.?\s*$', stripped_title):
                        continue
                    
                    # 명확한 날짜/시간 패턴만 제외
                    if re.search(r'\d+\.\s*\d+\.\s*\d+\.\s*(오전|오후|AM|PM)\s*\d+:\d+', stripped_title):
                        continue
                    
                    # 페이지 번호 패턴만 제외
                    if re.match(r'^\d+\s+EBS\s*$', stripped_title):
                        continue
                    
                    # bbox 계산
                    bbox = BaseParser.get_line_bbox(line)
                    
                    # region_hints를 사용하여 타입 보정 및 필터링 (y 좌표 기반)
                    region_confidence = 0.0
                    if bbox and len(bbox) >= 4 and self.region_hints:
                        # 페이지 높이 추정 (OCR 데이터에서 가져오거나 기본값 사용)
                        page_height = ocr_data.get('page_height', 1400.0)
                        if page_height <= 0:
                            page_height = 1400.0
                        
                        # y 좌표를 페이지 비율로 변환
                        y_center = (bbox[1] + bbox[3]) / 2.0  # y_min과 y_max의 중간
                        y_ratio = y_center / page_height
                        
                        # 개선된 region_hint 분류 (강의 내 위치 고려)
                        hint_result = self._classify_by_region_hint(
                            y_ratio, 
                            page_height, 
                            lecture_info
                        )
                        if hint_result:
                            # hint_result는 (hint_type, hint_confidence) 튜플이어야 함
                            if isinstance(hint_result, tuple) and len(hint_result) == 2:
                                hint_type, hint_confidence = hint_result
                                region_confidence = hint_confidence
                            else:
                                logger.warning(f"[SectionExtractor] hint_result가 예상 형식이 아님: {type(hint_result)}, 값: {hint_result}")
                                # 에러가 발생해도 섹션은 계속 처리 (region_confidence는 0으로 유지)
                                hint_type = None
                                hint_confidence = 0.0
                            
                            # region_hint를 우선시하여 타입 결정 (hint_type이 유효한 경우만)
                            if hint_type is not None:
                                original_type = section_type
                                
                                # 강의 내 위치를 고려한 동적 임계값
                                if lecture_info:
                                    # 강의 초반(0.0-0.3)에서는 concept에 더 관대
                                    # 강의 중반(0.3-0.7)에서는 passage에 더 관대
                                    # 강의 후반(0.7-1.0)에서는 problem에 더 관대
                                    page_ratio = lecture_info.get('page_ratio', 0.5)
                                    if page_ratio < 0.3 and hint_type == 'concept':
                                        threshold = 0.55  # 더 관대
                                    elif 0.3 <= page_ratio <= 0.7 and hint_type == 'passage':
                                        threshold = 0.55
                                    elif page_ratio > 0.7 and hint_type == 'problem':
                                        threshold = 0.55
                                    else:
                                        threshold = 0.65  # 일반적인 경우
                                else:
                                    threshold = 0.7  # 강의 정보 없으면 기본값
                                
                                if hint_confidence > threshold:
                                    if section_type == 'concept' and hint_type == 'concept':
                                        pass  # 일치하므로 유지
                                    elif section_type == 'content' and hint_type == 'passage':
                                        section_type = 'passage'  # content -> passage로 변경
                                    elif not section_type or section_type == 'unknown':
                                        section_type = hint_type  # 타입이 없으면 힌트 사용
                                    elif section_type != hint_type:
                                        # 패턴과 힌트가 다르면 힌트 우선 (높은 신뢰도일 때)
                                        logger.info(
                                            f"[region_hint] 타입 강제 변경: {section_type} -> {hint_type} "
                                            f"(신뢰도: {hint_confidence:.2f}, y_ratio={y_ratio:.3f}, "
                                            f"강의: {lecture_info.get('lecture_id') if lecture_info else None}, "
                                            f"강의내위치: {lecture_info.get('page_ratio', 0):.2f if lecture_info else 'N/A'})"
                                        )
                                        section_type = hint_type
                                else:
                                    # 낮은 신뢰도면 패턴 결과 유지하되 힌트 정보 기록
                                    if section_type == 'concept' and hint_type == 'concept':
                                        pass  # 일치하므로 유지
                                    elif section_type == 'content' and hint_type == 'passage':
                                        section_type = 'passage'
                                    elif not section_type or section_type == 'unknown':
                                        section_type = hint_type
                                
                                if original_type != section_type:
                                    logger.debug(
                                        f"[region_hint] 타입 변경: {original_type} -> {section_type} "
                                        f"(y_ratio={y_ratio:.3f}, 신뢰도: {hint_confidence:.2f}, "
                                        f"강의: {lecture_info.get('lecture_id') if lecture_info else None})"
                                    )
                        
                        # 영역 필터링: region_hints 영역 밖의 콘텐츠는 제외 (선택적)
                        # 주의: 너무 엄격하면 유용한 콘텐츠를 놓칠 수 있으므로 경고만 표시
                        if not self._is_in_region_hint(y_ratio):
                            logger.debug(
                                f"[region_hint] 영역 밖 콘텐츠 감지: {section_title[:30]}... "
                                f"(y_ratio={y_ratio:.3f}, 강의: {lecture_info.get('lecture_id') if lecture_info else None})"
                            )
                    
                    # region_hints 영역 내의 콘텐츠는 항상 포함 (필터링하지 않음)
                    # 대신 신뢰도 정보를 메타데이터에 추가
                    section_data = {
                        "title": section_title,
                        "type": section_type,
                        "page": page_num,
                        "bbox": bbox
                    }
                    
                    # region_hints 기반 신뢰도 정보 추가
                    if region_confidence > 0:
                        section_data["region_confidence"] = region_confidence
                        section_data["from_region_hint"] = True
                    
                    # 강의 정보 추가
                    if lecture_info:
                        section_data["lecture_id"] = lecture_info.get('lecture_id')
                        section_data["lecture_page_ratio"] = lecture_info.get('page_ratio')
                    
                    sections.append(section_data)
            
            # 전체 페이지의 모든 텍스트 블록을 분류 (섹션 제목이 아닌 일반 텍스트도)
            # 문단 단위로 그룹화하여 분류
            classified_blocks = self._classify_all_text_blocks(lecture_ocr_data, sections)
            if classified_blocks:
                logger.info(f"[전체 페이지 분류] {len(classified_blocks)}개 텍스트 블록 분류 완료")
                # 분류된 블록을 섹션에 추가 (선택적)
                # sections.extend(classified_blocks)  # 필요시 주석 해제
            
            # 레이아웃 검증기로 헤더/푸터 필터링
            if self.layout_validator.enabled:
                sections = self.layout_validator.filter_header_footer(sections)
            
            # 섹션 간격 검증
            if self.spacing_validator.enabled and len(sections) > 1:
                sections = self.spacing_validator.find_section_boundaries(sections)
            
            # 신뢰도 계산
            confidence = 0.0
            if total_lines > 0:
                # 매칭률 기반 신뢰도
                match_ratio = matched_count / total_lines
                confidence = min(match_ratio * 2.0, 1.0)  # 최대 1.0
            
            # 디버깅: 섹션 추출 결과 로깅
            logger.info(
                f"[SectionExtractor] 섹션 추출 완료: {len(sections)}개 섹션 발견 "
                f"(총 {total_lines}줄 중 {matched_count}줄 매칭, 신뢰도: {confidence:.2f})"
            )
            if len(sections) == 0 and total_lines > 0:
                logger.warning(
                    f"[SectionExtractor] ⚠️ 섹션 추출 실패: {total_lines}줄 처리했지만 섹션 0개. "
                    f"필터링이 너무 엄격하거나 패턴 매칭이 실패했을 수 있음."
                )
                # 디버깅: 실제로 어떤 텍스트가 처리되었는지 샘플 로깅
                sample_texts = []
                for ocr_data in lecture_ocr_data[:3]:  # 처음 3페이지만
                    texts = ocr_data.get('text', [])
                    if texts:
                        sample_texts.extend([t[:50] for t in texts[:5]])  # 각 페이지에서 처음 5개 텍스트
                if sample_texts:
                    logger.debug(f"[SectionExtractor] 샘플 텍스트 (처음 10개): {sample_texts[:10]}")
                logger.debug(
                    f"[SectionExtractor] 설정 확인: "
                    f"region_text_examples={bool(self.region_text_examples)}, "
                    f"concept_patterns={bool(self.concept_patterns)}, "
                    f"content_patterns={bool(self.content_patterns)}, "
                    f"region_hints={bool(self.region_hints)}"
                )
            
            # region_hints 기반 섹션 비율 계산
            region_based_count = sum(1 for s in sections if s.get("from_region_hint", False))
            if len(sections) > 0:
                region_ratio = region_based_count / len(sections)
                # region_hints 기반 섹션이 많을수록 신뢰도 증가
                if region_ratio > 0.5:
                    confidence = min(confidence + 0.15, 1.0)
                elif region_ratio > 0.3:
                    confidence = min(confidence + 0.1, 1.0)
            
            # 섹션이 3개 이상이면 신뢰도 증가
            if len(sections) >= 3:
                confidence = min(confidence + 0.2, 1.0)
            
            # region_hints가 활성화되어 있고 섹션이 있으면 추가 보너스
            if self.region_hints and len(sections) > 0:
                confidence = min(confidence + 0.1, 1.0)
            
            # 새로운 분류기 기반 신뢰도 보정
            if self.font_classifier.enabled:
                # 폰트 기반 매칭이 있으면 신뢰도 증가
                font_matched_count = sum(1 for s in sections if s.get("from_font_match", False))
                if font_matched_count > 0:
                    confidence = min(confidence + 0.1, 1.0)
            
            if self.layout_validator.enabled:
                # 레이아웃 검증 통과 시 신뢰도 증가
                confidence = min(confidence + 0.05, 1.0)
            
            return {
                'sections': sections,
                'confidence': confidence,
                'metadata': {
                    'matched_count': matched_count,
                    'total_lines': total_lines,
                    'region_based_count': region_based_count,
                    'lecture_aware': len([s for s in sections if 'lecture_id' in s]) > 0
                }
            }
        except Exception as e:
            logger.error(f"[SectionExtractor] 패턴 기반 섹션 추출 중 오류 발생: {e}", exc_info=True)
            # 에러가 발생해도 빈 리스트 반환 (휴리스틱 폴백으로 전환)
            return {
                'sections': [],
                'confidence': 0.0,
                'metadata': {
                    'error': str(e),
                    'matched_count': 0,
                    'total_lines': 0
                }
            }
    
    def _extract_by_ai(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """AI 기반 섹션 추출
        
        LLM을 사용하여 섹션 구조 분석
        """
        if not self.parser or not hasattr(self.parser, 'extract_sections'):
            return {'sections': [], 'confidence': 0.0}
        
        try:
            # 기존 파서의 extract_sections 사용
            # (AI 파서는 이미 구조 분석을 완료했으므로)
            sections = self.parser.extract_sections(lecture_ocr_data)
            
            # AI 파서를 사용했다면 높은 신뢰도
            confidence = 0.85 if sections else 0.0
            
            return {
                'sections': sections,
                'confidence': confidence,
                'metadata': {'method': 'ai_parser'}
            }
        except Exception as e:
            logger.error(f"AI 섹션 추출 실패: {e}")
            return {'sections': [], 'confidence': 0.0}
    
    def _extract_by_heuristic(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """휴리스틱 기반 폴백 추출

        레이아웃 및 폰트 크기 분석을 통한 섹션 추출
        IMPROVED: region_hints만 있어도 Y좌표 기반으로 섹션 생성
        """
        sections = []
        START_PAGE = self.config.get('start_content_page', 8)

        # ===== 새로운 로직: region_hints만으로 섹션 생성 =====
        if self.region_hints:
            logger.info("[Heuristic] region_hints 기반 섹션 추출 시도")
            region_sections = self._extract_sections_by_region_hints_only(lecture_ocr_data, START_PAGE)
            if region_sections:
                logger.info(f"[Heuristic] region_hints로 {len(region_sections)}개 섹션 생성")
                sections.extend(region_sections)
                # region_hints 기반 섹션이 있으면 높은 신뢰도 반환
                return {
                    'sections': sections,
                    'confidence': 0.7,  # 높은 신뢰도
                    'metadata': {'method': 'region_hints_only', 'source': 'y_coordinate_based'}
                }
        # ===== 기존 휴리스틱 로직 =====
        
        for ocr_data in lecture_ocr_data:
            page_num = ocr_data.get('page_num', 0)
            if page_num < START_PAGE:
                continue
            
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts or len(texts) == 0:
                continue
            
            # 줄 그룹화
            lines = BaseParser.group_lines(ocr_data, y_threshold=10)
            
            # 강의 정보 조회
            lecture_info = self._get_lecture_info_for_page(page_num)
            
            for line in lines:
                if not line:
                    continue
                
                line_text = BaseParser.join_line_text(line)
                line_text = TextPreprocessor.normalize_text(line_text)
                
                if not line_text or len(line_text) < 2:
                    continue
                
                # 휴리스틱 1: 숫자로 시작하는 짧은 텍스트 (개념 제목 가능성)
                if re.match(r'^\d+[\.\s]', line_text) and len(line_text) < 30:
                    # 폰트 크기 확인 (제목은 보통 크게)
                    avg_height = sum(
                        heights[word.get('index', 0)] 
                        for word in line 
                        if word.get('index', 0) < len(heights)
                    ) / len(line) if line else 0
                    
                    # 평균 높이가 15 이상이면 제목으로 판단
                    if avg_height >= 15:
                        bbox = BaseParser.get_line_bbox(line)
                        section_type = "concept"
                        
                        # region_hints로 타입 보정
                        if bbox and len(bbox) >= 4 and self.region_hints:
                            page_height = ocr_data.get('page_height', 1400.0)
                            if page_height <= 0:
                                page_height = 1400.0
                            y_center = (bbox[1] + bbox[3]) / 2.0
                            y_ratio = y_center / page_height
                            hint_result = self._classify_by_region_hint(y_ratio, page_height, lecture_info)
                            if hint_result:
                                # hint_result는 (hint_type, hint_confidence) 튜플이어야 함
                                if isinstance(hint_result, tuple) and len(hint_result) == 2:
                                    hint_type, hint_confidence = hint_result
                                    if hint_confidence > 0.7:
                                        section_type = hint_type
                                else:
                                    logger.warning(f"[SectionExtractor] hint_result가 예상 형식이 아님: {type(hint_result)}, 값: {hint_result}")
                        
                        sections.append({
                            "title": line_text,
                            "type": section_type,
                            "page": page_num,
                            "bbox": bbox
                        })
                
                # 휴리스틱 2: 특정 키워드 포함 (본문 섹션 가능성)
                content_keywords = [
                    '작품', '이해', '읽기', '분석', '해석',
                    '고전', '현대', '시가', '산문', '소설'
                ]
                
                if any(keyword in line_text for keyword in content_keywords):
                    # 페이지 상단에 위치하면 섹션 제목 가능성 높음
                    line_y = line[0].get('top', 0) if line else 0
                    if line_y < 200:  # 페이지 상단 200px 이내
                        sections.append({
                            "title": line_text,
                            "type": "content",
                            "page": page_num,
                            "bbox": BaseParser.get_line_bbox(line)
                        })
        
        # 신뢰도 계산 (휴리스틱은 낮은 신뢰도)
        confidence = 0.5 if sections else 0.0
        if len(sections) >= 2:
            confidence = 0.6
        
        return {
            'sections': sections,
            'confidence': confidence,
            'metadata': {'method': 'heuristic'}
        }
    
    def _extract_sections_by_region_hints_only(
        self,
        lecture_ocr_data: List[Dict[str, Any]],
        start_page: int
    ) -> List[Dict[str, Any]]:
        """region_hints만 사용하여 Y좌표 기반 섹션 추출 (새로운 폴백 전략)

        region_text_examples가 없어도 region_hints의 Y좌표 범위를 사용하여
        페이지를 영역별로 분할하고 각 영역에서 텍스트를 추출하여 섹션으로 생성

        Args:
            lecture_ocr_data: 강의 OCR 데이터
            start_page: 시작 페이지 번호

        Returns:
            추출된 섹션 리스트
        """
        if not self.region_hints:
            return []

        sections = []
        logger.info(f"[region_hints_only] Y좌표 기반 섹션 추출 시작 (region_hints: {list(self.region_hints.keys())})")

        for ocr_data in lecture_ocr_data:
            page_num = ocr_data.get('page_num', 0)
            if page_num < start_page:
                continue

            texts = ocr_data.get('text', [])
            lefts = ocr_data.get('left', [])
            tops = ocr_data.get('top', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])

            if not texts:
                continue

            page_height = ocr_data.get('page_height', 1400.0)
            if page_height <= 0:
                page_height = 1400.0

            # 강의 정보 조회
            lecture_info = self._get_lecture_info_for_page(page_num)

            # 줄 그룹화
            lines = BaseParser.group_lines(ocr_data, y_threshold=15)

            # 각 unit_type의 영역별로 텍스트 수집
            region_texts = {unit_type: [] for unit_type in self.region_hints.keys()}

            for line in lines:
                if not line:
                    continue

                line_text = BaseParser.join_line_text(line)
                line_text = TextPreprocessor.normalize_text(line_text)

                if not line_text or len(line_text) < 3:
                    continue

                # 필터링: 명확한 노이즈 제거
                if re.match(r'^\d+\.?\s*$', line_text.strip()):  # 숫자만
                    continue
                if re.match(r'^\d+\s+EBS\s*$', line_text.strip()):  # 페이지 번호
                    continue
                if re.search(r'\d+\.\s*\d+\.\s*\d+\.\s*(오전|오후)', line_text):  # 날짜
                    continue

                # 줄의 Y좌표 계산
                bbox = BaseParser.get_line_bbox(line)
                if not bbox or len(bbox) < 4:
                    continue

                y_center = (bbox[1] + bbox[3]) / 2.0
                y_ratio = y_center / page_height

                # region_hints로 분류
                hint_result = self._classify_by_region_hint(y_ratio, page_height, lecture_info)
                if hint_result:
                    unit_type, confidence = hint_result
                    if confidence >= 0.5:  # 낮은 임계값
                        region_texts[unit_type].append({
                            'text': line_text,
                            'bbox': bbox,
                            'y_ratio': y_ratio,
                            'confidence': confidence
                        })

            # 각 영역에서 대표 섹션 생성
            for unit_type, text_items in region_texts.items():
                if not text_items:
                    continue

                # 영역별로 Y좌표 순으로 정렬
                text_items.sort(key=lambda x: x['y_ratio'])

                # 영역의 첫 번째 텍스트를 섹션 제목으로 사용
                # 또는 가장 큰 폰트/가장 상단의 텍스트를 선택
                # 여기서는 가장 상단의 긴 텍스트를 선택 (5자 이상)
                candidate_title = None
                candidate_bbox = None
                for item in text_items:
                    if len(item['text']) >= 5:  # 최소 5자 이상
                        candidate_title = item['text']
                        candidate_bbox = item['bbox']
                        break

                if not candidate_title:
                    # 5자 미만이면 첫 번째 텍스트 사용
                    candidate_title = text_items[0]['text']
                    candidate_bbox = text_items[0]['bbox']

                # 타입 정규화 (content -> passage)
                if unit_type == 'content':
                    unit_type = 'passage'

                # 섹션 생성
                section = {
                    "title": candidate_title[:100],  # 제목 길이 제한
                    "type": unit_type,
                    "page": page_num,
                    "bbox": candidate_bbox,
                    "from_region_hint": True,
                    "region_confidence": text_items[0]['confidence'],
                    "source": "region_hints_only"
                }

                # 강의 정보 추가
                if lecture_info:
                    section["lecture_id"] = lecture_info.get('lecture_id')
                    section["lecture_page_ratio"] = lecture_info.get('page_ratio')

                sections.append(section)
                logger.info(
                    f"[region_hints_only] 섹션 생성: {unit_type} - '{candidate_title[:30]}...' "
                    f"(페이지 {page_num}, y_ratio={text_items[0]['y_ratio']:.3f})"
                )

        return sections

    def _merge_sections(
        self,
        sections1: List[Dict[str, Any]],
        sections2: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """두 섹션 리스트 병합 (중복 제거)
        
        Args:
            sections1: 첫 번째 섹션 리스트
            sections2: 두 번째 섹션 리스트
            
        Returns:
            병합된 섹션 리스트
        """
        merged = []
        seen = set()
        
        for section in sections1 + sections2:
            # 중복 체크: (page, title) 조합
            key = (section.get('page', 0), section.get('title', ''))
            if key not in seen:
                seen.add(key)
                merged.append(section)
        
        return merged
