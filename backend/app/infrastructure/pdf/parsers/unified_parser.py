"""
통합 파서
템플릿 기반으로 모든 과목을 동일한 프로세스로 파싱
과목별 차이는 템플릿의 패턴과 설정으로 처리
"""
import re
import logging
from pathlib import Path
from typing import List, Optional

from .base import BaseParser
from .config_manager import ParserConfigManager
from .template_manager import TemplateManager
from .template import ParsingTemplate
from .section_extractor import ImprovedSectionExtractor
from .lecture_boundary_validator import LectureBoundaryValidator
from app.core.config import settings
from app.infrastructure.pdf.types import (
    OCRPageData,
    ParsingResult,
    LectureInfo,
    ProblemInfo,
    SectionData,
    ParagraphData,
    JSONDict,
)

logger = logging.getLogger(__name__)


class UnifiedTemplateParser(BaseParser):
    """
    통합 템플릿 기반 파서
    
    모든 과목(literature, math1, english)을 동일한 프로세스로 파싱
    과목별 차이는 템플릿의 패턴과 설정으로 처리
    """
    
    def __init__(
        self,
        subject: str,
        config_path: Optional[Path] = None,
        template: Optional[ParsingTemplate] = None,
        enable_ai_parsing: bool = False
    ):
        """
        Args:
            subject: 과목명 ('literature', 'math1', 'english')
            config_path: config.json 경로 (템플릿이 없을 때만 사용)
            template: 사용할 템플릿 (None이면 자동 매칭 시도)
            enable_ai_parsing: AI 파싱 활성화 여부
        """
        # 기본 region_hints (최후의 폴백)
        self._default_region_hints = {
            'literature': {
                'concept': {'y_min': 0.11, 'y_max': 0.84},
                'passage': {'y_min': 0.12, 'y_max': 0.54},
                'problem': {'y_min': 0.10, 'y_max': 0.81}
            },
            'math1': {
                'concept': {'y_min': 0.10, 'y_max': 0.80},
                'passage': {'y_min': 0.15, 'y_max': 0.50},
                'problem': {'y_min': 0.12, 'y_max': 0.85}
            },
            'english': {
                'concept': {'y_min': 0.10, 'y_max': 0.75},
                'passage': {'y_min': 0.15, 'y_max': 0.55},
                'problem': {'y_min': 0.12, 'y_max': 0.80}
            }
        }
        self.subject = subject
        self.config_path = config_path
        self.template = template
        self.template_manager = TemplateManager()
        self.enable_ai_parsing = enable_ai_parsing
        self._template_warning_logged = False  # 템플릿 없음 경고를 한 번만 로깅하기 위한 플래그
        
        # 템플릿이 제공되면 템플릿의 패턴 사용, 아니면 config.json 사용
        if template:
            self.config = self._template_to_config(template)
            logger.info(f"[UnifiedParser] 템플릿 사용: {template.name} (신뢰도: {template.confidence})")
        else:
            self.config = ParserConfigManager.load_config(subject, config_path)
            logger.info(f"[UnifiedParser] config.json 사용: {subject}")

        # 최후의 안전장치: region_hints가 없으면 기본값 사용
        if not self.config.get('region_hints'):
            if subject in self._default_region_hints:
                self.config['region_hints'] = self._default_region_hints[subject]
                logger.warning(
                    f"[UnifiedParser] ⚠️ region_hints 없음 - 기본값 사용 ({subject})\n"
                    f"  개념: {self.config['region_hints']['concept']}\n"
                    f"  본문: {self.config['region_hints']['passage']}\n"
                    f"  문제: {self.config['region_hints']['problem']}"
                )
            else:
                logger.error(
                    f"[UnifiedParser] ⚠️ region_hints 없음 및 기본값도 없음 ({subject})\n"
                    f"  섹션 추출이 실패할 수 있습니다."
                )
    
    def _template_to_config(self, template: ParsingTemplate) -> JSONDict:
        """템플릿을 config 형식으로 변환 (모든 과목 공통)

        Args:
            template: ParsingTemplate 인스턴스

        Returns:
            config 딕셔너리
        """
        config = {}
        
        # 패턴 매핑
        if template.patterns:
            config['lecture_title_patterns'] = template.patterns.get('lecture_title_patterns', [])
            config['toc_lecture_patterns'] = template.patterns.get('toc_lecture_patterns', [])
            config['concept_title_patterns'] = template.patterns.get('concept_title_patterns', [])
            config['content_header_patterns'] = template.patterns.get('content_header_patterns', [])
            config['section_title_patterns'] = template.patterns.get('section_title_patterns', [])
            config['problem_number_pattern'] = template.patterns.get('problem_number_pattern', r'^\d+\.')
        
        # 설정 매핑
        if template.config:
            config['toc_end_page'] = template.config.get('toc_end_page', 7)
            config['start_content_page'] = template.config.get('start_content_page', 1)
            config['paragraph_y_threshold'] = template.config.get('paragraph_y_threshold', 20)
            
            # 커리큘럼 구조 정보 (템플릿 우선, 없으면 과목별 기본값)
            default_curriculum = ParserConfigManager.get_default_config(self.subject)
            config['unit_order'] = template.config.get('unit_order', default_curriculum.get('unit_order', ['concept', 'passage', 'problem']))
            config['is_lecture_based'] = template.config.get('is_lecture_based', default_curriculum.get('is_lecture_based', True))
            config['lecture_units'] = template.config.get('lecture_units', default_curriculum.get('lecture_units', ['concept', 'passage', 'problem']))
            
            if config.get('is_lecture_based'):
                logger.info(f"[템플릿] 커리큘럼 구조: 강의 기반, 단위 순서: {config['unit_order']}, 단위 목록: {config['lecture_units']}")
            else:
                logger.info(f"[템플릿] 커리큘럼 구조: 비강의 기반, 단위 순서: {config['unit_order']}")
            
            # region_hints (하위 호환성)
            region_hints = template.config.get('region_hints', {})
            config['region_hints'] = region_hints
            if region_hints:
                logger.info(f"[템플릿] region_hints 로드: {list(region_hints.keys())} ({len(region_hints)}개 레이블)")
            
            # 영역 내 텍스트 예시 (패턴 학습용) - 우선 사용
            region_text_examples = template.config.get('region_text_examples', {})
            config['region_text_examples'] = region_text_examples
            if region_text_examples:
                logger.info(f"[템플릿] region_text_examples 로드: {list(region_text_examples.keys())} ({sum(len(v) for v in region_text_examples.values())}개 예시)")
                for label, examples in region_text_examples.items():
                    logger.info(f"  - {label}: {len(examples)}개 예시")
            
            # 관리자가 입력한 TOC 텍스트 및 강의 목록 (파싱 시 우선 사용)
            if 'toc_text' in template.config:
                config['toc_text'] = template.config.get('toc_text')
                if config['toc_text']:
                    logger.info(f"[템플릿] TOC 텍스트 로드: {len(config['toc_text'])}자 (강의 제목 검증에 활용)")
            
            if 'toc_lecture_list' in template.config:
                toc_lecture_list = template.config.get('toc_lecture_list', [])
                config['toc_lecture_list'] = toc_lecture_list
                if toc_lecture_list:
                    logger.info(f"[템플릿] TOC 강의 목록 로드: {len(toc_lecture_list)}개")
                    # 강의별 페이지 범위 정보를 빠르게 조회할 수 있도록 맵 생성
                    lecture_page_ranges = {}
                    for lecture in toc_lecture_list:
                        lecture_id = lecture.get('lecture_id')
                        start_page = lecture.get('start_page')
                        end_page = lecture.get('end_page')
                        if lecture_id is not None and start_page is not None:
                            lecture_page_ranges[lecture_id] = {
                                'start_page': start_page,
                                'end_page': end_page
                            }
                    config['lecture_page_ranges'] = lecture_page_ranges
                    if lecture_page_ranges:
                        logger.info(f"[템플릿] 강의별 페이지 범위 로드: {len(lecture_page_ranges)}개 강의")
            
            # Priority 1: 새로운 필드 로드
            if 'font_info' in template.config:
                config['font_info'] = template.config.get('font_info')
                if config['font_info']:
                    logger.info(f"[템플릿] 폰트 정보 로드: {list(config['font_info'].keys())}")
            
            if 'layout_info' in template.config:
                config['layout_info'] = template.config.get('layout_info')
                if config['layout_info']:
                    logger.info(f"[템플릿] 레이아웃 정보 로드: 활성화")
            
            if 'problem_patterns' in template.config:
                config['problem_patterns'] = template.config.get('problem_patterns')
                if config['problem_patterns']:
                    logger.info(f"[템플릿] 문제 패턴 로드: 활성화")
            
            if 'section_spacing' in template.config:
                config['section_spacing'] = template.config.get('section_spacing')
                if config['section_spacing']:
                    logger.info(f"[템플릿] 섹션 간격 정보 로드: 활성화")
        
        # 기본값 설정 (과목별 기본 패턴 및 커리큘럼 구조)
        default_curriculum = ParserConfigManager.get_default_config(self.subject)
        
        if not config.get('lecture_title_patterns'):
            config['lecture_title_patterns'] = default_curriculum.get('lecture_title_patterns', [])
        
        if not config.get('toc_lecture_patterns'):
            config['toc_lecture_patterns'] = default_curriculum.get('toc_lecture_patterns', [])
        
        # 커리큘럼 구조 정보가 없으면 과목별 기본값 사용
        for key in ['unit_order', 'is_lecture_based', 'lecture_units']:
            if key not in config:
                default_value = default_curriculum.get(key)
                if default_value is not None:
                    config[key] = default_value
                else:
                    # 최종 fallback (과목별 기본값도 없을 때)
                    fallback_values = {
                        'unit_order': ['concept', 'passage', 'problem'],
                        'is_lecture_based': True,
                        'lecture_units': ['concept', 'passage', 'problem']
                    }
                    config[key] = fallback_values.get(key)
        
        return config
    
    def _match_pattern(self, text: str, patterns: List[str]) -> bool:
        """패턴 매칭 헬퍼 (영어는 대소문자 무시)
        
        Args:
            text: 매칭할 텍스트
            patterns: 정규식 패턴 리스트
            
        Returns:
            매칭 여부
        """
        if not text or not patterns:
            return False
        
        flags = re.IGNORECASE if self.subject == 'english' else 0
        
        for pattern in patterns:
            try:
                if re.search(pattern, text, flags):
                    return True
            except re.error:
                continue
        
        return False
    
    def try_match_template(self, ocr_data: List[OCRPageData], threshold: float = 0.85) -> Optional[ParsingTemplate]:
        """OCR 데이터에서 템플릿 매칭 시도"""
        if not ocr_data:
            return None
        
        # 첫 3-5페이지의 텍스트 추출
        sample_pages = ocr_data[:5]
        sample_texts = []
        
        for page_data in sample_pages:
            texts = page_data.get('text', [])
            if texts:
                page_text = ' '.join(str(t) for t in texts[:50])
                sample_texts.append(page_text)
        
        pdf_text = '\n'.join(sample_texts)
        
        if not pdf_text:
            return None
        
        # 템플릿 매칭 시도
        match_result = self.template_manager.match_template(
            pdf_text=pdf_text,
            subject=self.subject,
            threshold=threshold
        )
        
        if match_result:
            template, confidence = match_result
            logger.info(f"[UnifiedParser] 템플릿 매칭 성공: {template.name} (신뢰도: {confidence:.2f})")
            self.template = template
            self.config = self._template_to_config(template)
            return template
        
        return None
    
    def parse(self, ocr_data: List[OCRPageData]) -> ParsingResult:
        """
        OCR 데이터를 파싱하여 구조화된 데이터 반환 (모든 과목 공통)

        Args:
            ocr_data: 페이지별 OCR 결과 리스트

        Returns:
            {
                'lectures': [...],
                'problems': [...],
                'metadata': {...}
            }
        """
        try:
            # 템플릿이 없으면 자동 매칭 시도
            if not self.template:
                matched_template = self.try_match_template(ocr_data)
                if matched_template:
                    logger.info(f"[UnifiedParser] 자동 템플릿 매칭 성공: {matched_template.name}")
            
            # 강의 추출
            lectures = self.extract_lectures(ocr_data)
            
            # 문제 추출
            problems = self.extract_problems(ocr_data)
            
            template_name = self.template.name if self.template else "config.json"
            logger.info(f"[UnifiedParser] {self.subject} 파싱 완료: {len(lectures)}개 강의, {len(problems)}개 문제 (템플릿: {template_name})")
            
            return {
                'lectures': lectures,
                'problems': problems,
                'metadata': {
                    'total_lectures': len(lectures),
                    'total_problems': len(problems),
                    'status': 'implemented',
                    'template_used': template_name if self.template else None,
                    'subject': self.subject
                }
            }
        except Exception as e:
            logger.error(f"[UnifiedParser] {self.subject} 파싱 중 오류 발생: {e}", exc_info=True)
            return {
                'lectures': [],
                'problems': [],
                'metadata': {
                    'total_lectures': 0,
                    'total_problems': 0,
                    'status': 'error',
                    'error': str(e),
                    'subject': self.subject
                }
            }
    
    def extract_lectures(self, ocr_data: List[OCRPageData]) -> List[LectureInfo]:
        """
        강의 목록 추출 (모든 과목 공통 로직)

        템플릿에 저장된 TOC 강의 목록이 있으면 우선 사용
        """
        try:
            lectures = []
            
            # 템플릿에 저장된 TOC 강의 목록이 있으면 우선 사용 (관리자가 입력한 정보)
            toc_lecture_list = self.config.get('toc_lecture_list', [])
            if toc_lecture_list:
                logger.info(f"\n[UnifiedParser] 템플릿에 저장된 TOC 강의 목록 사용: {len(toc_lecture_list)}개")
                for lecture_info in toc_lecture_list:
                    lecture_data = {
                        'lecture_id': lecture_info.get('lecture_id'),
                        'title': lecture_info.get('title', ''),
                        'page': lecture_info.get('start_page', 0),
                        'start_page': lecture_info.get('start_page'),
                        'end_page': lecture_info.get('end_page'),
                        'source': 'template_toc'
                    }
                    if lecture_data['start_page']:
                        logger.info(f"강의 {lecture_data['lecture_id']}: {lecture_data['start_page']}~{lecture_data['end_page'] or '끝'}페이지")
                    lectures.append(lecture_data)
                logger.info(f"✅ [템플릿 TOC] {len(lectures)}개 강의 로드 완료 (페이지 범위 정보 포함)")
                return lectures
            
            # 기존 로직 (TOC 강의 목록이 없을 때만)
            START_PAGE = self.config.get('start_content_page', 1)
            patterns = self.config.get('lecture_title_patterns', [])
            toc_patterns = self.config.get('toc_lecture_patterns', [])
            toc_end_page = self.config.get('toc_end_page', 7)
            lecture_id = 1
            
            # 1) TOC 기반 강의 추출
            if toc_patterns:
                for ocr_page in ocr_data:
                    page_num = ocr_page.get('page_num', 0)
                    if page_num <= 0 or page_num > toc_end_page:
                        continue
                    
                    lines = self.group_lines(ocr_page, y_threshold=10)
                    for line in lines:
                        line_text = self.join_line_text(line).strip()
                        if not line_text:
                            continue
                        
                        # 패턴 매칭
                        matched = self._match_pattern(line_text, toc_patterns)
                        
                        if not matched:
                            continue
                        
                        # 강의 번호와 제목 추출
                        title = re.sub(r'\s+\d{1,4}\s*$', '', line_text).strip()
                        m = re.search(r'(\d+)', title)
                        parsed_id = int(m.group(1)) if m else lecture_id
                        
                        if not any(l['lecture_id'] == parsed_id for l in lectures):
                            lectures.append({
                                'lecture_id': parsed_id,
                                'title': title,
                                'page': page_num,
                                'bbox': self.get_line_bbox(line),
                                'source': 'toc'
                            })
                            lecture_id = max(lecture_id, parsed_id + 1)
                
                if lectures:
                    lectures.sort(key=lambda x: x['lecture_id'])
                    return lectures
            
            # 2) 본문 페이지에서 강의 추출
            for ocr_page in ocr_data:
                page_num = ocr_page.get('page_num', 0)
                if page_num < START_PAGE:
                    continue
                
                texts = ocr_page.get('text', [])
                if not texts:
                    continue
                
                lines = self.group_lines(ocr_page, y_threshold=10)
                
                for line in lines:
                    line_text = self.join_line_text(line).strip()
                    if not line_text or len(line_text) < 3:
                        continue
                    
                    # 패턴 매칭
                    matched = self._match_pattern(line_text, patterns)
                    
                    if matched:
                        bbox = self.get_line_bbox(line)
                        
                        # 중복 체크
                        if not any(l['lecture_id'] == lecture_id for l in lectures):
                            lectures.append({
                                'lecture_id': lecture_id,
                                'title': line_text,
                                'page': page_num,
                                'bbox': bbox,
                                'source': 'content'
                            })
                            lecture_id += 1
            
            # lecture_id 순서대로 정렬
            lectures.sort(key=lambda x: x['lecture_id'])
            logger.info(f"[UnifiedParser] 강의 추출 완료: {len(lectures)}개 강의 발견")
            
            # TOC 강의 목록으로 경계 검증 및 보정
            toc_lecture_list = self.config.get('toc_lecture_list', [])
            if toc_lecture_list and len(toc_lecture_list) > 0:
                validator = LectureBoundaryValidator(toc_lecture_list)
                validation_result = validator.validate_lecture_boundaries(lectures)
                
                validated_lectures = validation_result['validated_lectures']
                validation_summary = validation_result['validation_summary']
                
                logger.info(
                    f"[UnifiedParser] 강의 경계 검증 완료: "
                    f"TOC {validation_summary['total_toc_lectures']}개, "
                    f"추출 {validation_summary['total_extracted_lectures']}개, "
                    f"누락 {validation_summary['missing_count']}개, "
                    f"최종 {validation_summary['final_count']}개"
                )
                
                # 검증 결과를 메타데이터에 추가
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['lecture_validation'] = validation_summary
                
                return validated_lectures
            
            return lectures
            
        except Exception as e:
            logger.error(f"[UnifiedParser] 강의 추출 중 오류 발생: {e}", exc_info=True)
            return []
    
    def extract_problems(self, ocr_data: List[OCRPageData]) -> List[ProblemInfo]:
        """
        문제 추출 (모든 과목 공통 로직)

        Args:
            ocr_data: 페이지별 OCR 결과 리스트

        Returns:
            문제 리스트
        """
        try:
            from .problem_pattern_matcher import ProblemPatternMatcher
            
            problems = []
            START_PAGE = self.config.get('start_content_page', 1)
            problem_pattern = self.config.get('problem_number_pattern', r'^\d+\.')
            
            # 문제 패턴 매칭기 초기화
            problem_matcher = ProblemPatternMatcher(self.config.get('problem_patterns'))
            
            for ocr_page in ocr_data:
                page_num = ocr_page.get('page_num', 0)
                if page_num < START_PAGE:
                    continue
                
                texts = ocr_page.get('text', [])
                if not texts:
                    continue
                
                for text in texts:
                    cleaned = text.strip()
                    
                    # 문제 패턴 매칭기 사용 (활성화된 경우)
                    if problem_matcher.enabled:
                        match_result = problem_matcher.match_problem_number(cleaned)
                        if match_result and match_result.get('confidence', 0) >= 0.7:
                            problem_id = match_result.get('number', cleaned)
                            # 중복 체크
                            if not any(p['problem_id'] == problem_id and p['page'] == page_num for p in problems):
                                problems.append({
                                    'problem_id': problem_id,
                                    'page': page_num,
                                    'confidence': match_result.get('confidence', 0.7),
                                    'from_pattern_matcher': True
                                })
                    else:
                        # 기존 로직 (하위 호환)
                        if re.match(problem_pattern, cleaned):
                            problem_id = cleaned
                            # 중복 체크
                            if not any(p['problem_id'] == problem_id and p['page'] == page_num for p in problems):
                                problems.append({
                                    'problem_id': problem_id,
                                    'page': page_num
                                })
            
            return problems
        except Exception as e:
            logger.error(f"[UnifiedParser] 문제 추출 중 오류 발생: {e}", exc_info=True)
            return []
    
    def extract_sections(
        self,
        lecture_ocr_data: List[OCRPageData]
    ) -> List[SectionData]:
        """
        섹션 추출 (개선된 다중 전략 사용, 모든 과목 공통)

        Args:
            lecture_ocr_data: 강의에 해당하는 OCR 데이터 리스트

        Returns:
            섹션 리스트
        """
        try:
            # 개선된 섹션 추출기 사용 (모든 과목 공통)
            api_key = None
            if self.enable_ai_parsing:
                api_key = getattr(settings, 'OPENAI_API_KEY', None)
            
            extractor = ImprovedSectionExtractor(
                config=self.config,
                parser=None,  # AI 파싱은 선택적
                enable_ai=self.enable_ai_parsing and api_key is not None,
                api_key=api_key
            )
            
            result = extractor.extract(lecture_ocr_data)
            
            # 결과 로깅
            logger.info(
                f"[UnifiedParser] {self.subject} 섹션 추출 완료: {len(result.sections)}개 섹션 "
                f"(방법: {result.method}, 신뢰도: {result.confidence:.2f})"
            )
            
            # 템플릿 사용 여부 확인
            if self.template:
                logger.info(f"[UnifiedParser] 템플릿 사용 중: {self.template.name}")
                if self.config.get('toc_lecture_list'):
                    logger.info(f"[UnifiedParser] TOC 강의 목록 사용: {len(self.config.get('toc_lecture_list', []))}개")
                if self.config.get('region_text_examples'):
                    total_examples = sum(len(v) for v in self.config.get('region_text_examples', {}).values())
                    logger.info(f"[UnifiedParser] region_text_examples 사용: {total_examples}개 예시")
            else:
                # 템플릿 없음 경고는 한 번만 로깅 (반복 로깅 방지)
                if not self._template_warning_logged:
                    logger.warning(f"[UnifiedParser] 템플릿 없음 - 관리자 입력 정보를 사용하지 못함 (config.json 사용 중)")
                    self._template_warning_logged = True
            
            # 섹션 추출 실패 시 경고
            if len(result.sections) == 0:
                logger.warning(
                    f"[UnifiedParser] 섹션 추출 실패 - bbox가 비어있을 수 있음. "
                    f"템플릿 사용 여부: {self.template is not None}, "
                    f"region_text_examples: {bool(self.config.get('region_text_examples'))}"
                )
            
            return result.sections
            
        except Exception as e:
            logger.error(f"[UnifiedParser] {self.subject} 섹션 추출 중 오류 발생: {e}", exc_info=True)
            return []
    
    def extract_content_paragraphs(
        self,
        lecture_ocr_data: List[OCRPageData],
        sections: List[SectionData]
    ) -> List[ParagraphData]:
        """
        섹션별 문단 추출 (모든 과목 공통 로직)

        Args:
            lecture_ocr_data: 강의에 해당하는 OCR 데이터 리스트
            sections: 이미 추출된 섹션 리스트
            
        Returns:
            문단 리스트
        """
        try:
            all_paragraphs = []
            threshold = self.config.get('paragraph_y_threshold', 20)
            
            for ocr_data in lecture_ocr_data:
                page_num = ocr_data.get('page_num', 0)
                texts = ocr_data.get('text', [])
                tops = ocr_data.get('top', [])
                lefts = ocr_data.get('left', [])
                widths = ocr_data.get('width', [])
                heights = ocr_data.get('height', [])
                
                if not texts:
                    continue
                
                # y좌표 기준으로 줄 그룹화
                lines = self.group_lines(ocr_data, y_threshold=threshold)
                
                # 줄들을 문단으로 결합
                paragraphs = []
                current_paragraph = {
                    "text": "",
                    "y_start": None,
                    "y_end": None,
                    "page": page_num,
                    "bbox": None
                }
                
                prev_line_y = None
                
                for line in lines:
                    line_text = self.join_line_text(line)
                    line_text = line_text.strip()
                    
                    if not line_text:
                        continue
                    
                    # 섹션 제목이면 스킵
                    cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                    
                    # 섹션 제목 패턴 제외
                    section_patterns = self.config.get('section_title_patterns', [])
                    concept_patterns = self.config.get('concept_title_patterns', [])
                    content_patterns = self.config.get('content_header_patterns', [])
                    problem_pattern = self.config.get('problem_number_pattern', r'^\d+\.')
                    
                    if (self.matches_patterns(cleaned_line, section_patterns) or
                        self.matches_patterns(cleaned_line, concept_patterns) or
                        self.matches_patterns(cleaned_line, content_patterns) or
                        re.match(problem_pattern, cleaned_line)):
                        continue
                    
                    line_y = line[0]['top']
                    
                    # 같은 문단인지 확인 (y좌표 차이)
                    if prev_line_y is not None and abs(line_y - prev_line_y) < threshold:
                        # 같은 문단에 추가
                        if current_paragraph['text']:
                            current_paragraph['text'] += " " + line_text
                        else:
                            current_paragraph['text'] = line_text
                            current_paragraph['y_start'] = line_y
                            current_paragraph['bbox'] = self.get_line_bbox(line)
                        
                        # bbox 확장
                        if current_paragraph['bbox']:
                            line_bbox = self.get_line_bbox(line)
                            current_paragraph['bbox'][0] = min(current_paragraph['bbox'][0], line_bbox[0])
                            current_paragraph['bbox'][1] = min(current_paragraph['bbox'][1], line_bbox[1])
                            current_paragraph['bbox'][2] = max(current_paragraph['bbox'][2], line_bbox[2])
                            current_paragraph['bbox'][3] = max(current_paragraph['bbox'][3], line_bbox[3])
                        
                        current_paragraph['y_end'] = line_y
                    else:
                        # 새 문단 시작
                        if current_paragraph['text']:
                            paragraphs.append(current_paragraph.copy())
                        
                        current_paragraph = {
                            "text": line_text,
                            "y_start": line_y,
                            "y_end": line_y,
                            "page": page_num,
                            "bbox": self.get_line_bbox(line)
                        }
                    
                    prev_line_y = line_y
                
                # 마지막 문단 추가
                if current_paragraph['text']:
                    paragraphs.append(current_paragraph)
                
                all_paragraphs.extend(paragraphs)
            
            return all_paragraphs
            
        except Exception as e:
            logger.error(f"[UnifiedParser] {self.subject} 문단 추출 중 오류 발생: {e}", exc_info=True)
            return []
