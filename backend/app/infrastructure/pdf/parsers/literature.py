"""
문학 파서

⚠️ DEPRECATED: 이 클래스는 더 이상 사용되지 않습니다.
대신 UnifiedTemplateParser를 사용하세요.

과목별 파서는 통합 파서(UnifiedTemplateParser)로 대체되었습니다.
템플릿 기반으로 모든 과목을 동일한 프로세스로 파싱합니다.
"""
import re
import logging
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base import BaseParser
from .config_manager import ParserConfigManager
from .template_manager import TemplateManager
from .template import ParsingTemplate
from .section_extractor import ImprovedSectionExtractor
from app.core.config import settings
from app.infrastructure.pdf.constants import (
    DEFAULT_TOC_END_PAGE,
    DEFAULT_CONTENT_START_PAGE,
    DEFAULT_PARAGRAPH_Y_THRESHOLD,
    DEFAULT_LINE_Y_THRESHOLD,
    DEFAULT_WORD_X_THRESHOLD,
    TEMPLATE_MATCH_SAMPLE_SIZE,
    TEMPLATE_MATCH_PAGE_SAMPLE,
    DEBUG_TOC_PAGES,
    DEBUG_CONTENT_PAGES,
    DEBUG_TOC_TEXT_LIMIT,
    DEBUG_CONTENT_TEXT_LIMIT,
    LECTURE_TITLE_CHECK_LIMIT,
    APPROX_CHAR_WIDTH_PIXELS,
    MAX_VALID_LECTURE_NUMBER,
)

logger = logging.getLogger(__name__)


class LiteratureParser(BaseParser):
    """
    ⚠️ DEPRECATED: UnifiedTemplateParser를 사용하세요.
    
    이 클래스는 하위 호환성을 위해 유지되지만, 새로운 코드에서는
    UnifiedTemplateParser를 사용해야 합니다.
    """

    def __init__(
        self, 
        config_path: Optional[Path] = None,
        template: Optional[ParsingTemplate] = None,
        enable_ai_parsing: bool = False
    ):
        warnings.warn(
            "LiteratureParser is deprecated. Use UnifiedTemplateParser instead.",
            DeprecationWarning,
            stacklevel=2
        )
        warnings.warn(
            "LiteratureParser is deprecated. Use UnifiedTemplateParser instead.",
            DeprecationWarning,
            stacklevel=2
        )
        """
        Args:
            config_path: config.json 경로 (None이면 기본 경로 사용)
            template: 사용할 템플릿 (None이면 자동 매칭 시도)
            enable_ai_parsing: AI 파싱 활성화 여부 (섹션 추출 개선용)
        """
        self.config_path = config_path
        self.template = template
        self.template_manager = TemplateManager()
        self.enable_ai_parsing = enable_ai_parsing
        
        # 템플릿이 제공되면 템플릿의 패턴 사용, 아니면 config.json 사용
        if template:
            self.config = self._template_to_config(template)
            logger.info(f"템플릿 사용: {template.name} (신뢰도: {template.confidence})")
        else:
            self.config = ParserConfigManager.load_config('literature', config_path)
    
    def _template_to_config(self, template: ParsingTemplate) -> Dict[str, Any]:
        """템플릿을 config 형식으로 변환
        
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
            config['problem_number_pattern'] = template.patterns.get('problem_number_pattern', r'^\d{2}$')

        # 설정 매핑
        if template.config:
            config['toc_end_page'] = template.config.get('toc_end_page', DEFAULT_TOC_END_PAGE)
            config['start_content_page'] = template.config.get('start_content_page', DEFAULT_CONTENT_START_PAGE)
            config['paragraph_y_threshold'] = template.config.get('paragraph_y_threshold', DEFAULT_PARAGRAPH_Y_THRESHOLD)
            config['unit_order'] = template.config.get('unit_order', ['concept', 'passage', 'problem'])
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
        
        # 기본값 설정
        if not config.get('lecture_title_patterns'):
            config['lecture_title_patterns'] = [r'^\d+강\s+[가-힣]+', r'^\d+\s+[가-힣]+']
        if not config.get('toc_lecture_patterns'):
            config['toc_lecture_patterns'] = [r'^\d+강\s*\|\s*[가-힣]', r'^\d+강\s*\|']
        
        return config
    
    def try_match_template(self, ocr_data: List[Dict[str, Any]], threshold: float = 0.85) -> Optional[ParsingTemplate]:
        """OCR 데이터에서 템플릿 매칭 시도
        
        Args:
            ocr_data: 페이지별 OCR 결과 리스트
            threshold: 최소 신뢰도 임계값
            
        Returns:
            매칭된 템플릿 또는 None
        """
        if not ocr_data:
            return None

        # 첫 TEMPLATE_MATCH_PAGE_SAMPLE 페이지의 텍스트 추출
        sample_pages = ocr_data[:TEMPLATE_MATCH_PAGE_SAMPLE]
        sample_texts = []
        
        for page_data in sample_pages:
            texts = page_data.get('text', [])
            if texts:
                # 텍스트를 줄 단위로 결합
                page_text = ' '.join(str(t) for t in texts[:TEMPLATE_MATCH_SAMPLE_SIZE])
                sample_texts.append(page_text)
        
        pdf_text = '\n'.join(sample_texts)
        
        if not pdf_text:
            return None
        
        # 템플릿 매칭 시도
        match_result = self.template_manager.match_template(
            pdf_text=pdf_text,
            subject='literature',
            threshold=threshold
        )
        
        if match_result:
            template, confidence = match_result
            logger.info(f"템플릿 매칭 성공: {template.name} (신뢰도: {confidence:.2f})")
            self.template = template
            self.config = self._template_to_config(template)
            return template
        
        return None


    def parse(self, ocr_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        OCR 데이터를 파싱하여 문학 콘텐츠 추출

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
                    logger.info(f"자동 템플릿 매칭 성공: {matched_template.name}")
            
            # 강의 추출
            lectures = self.extract_lectures(ocr_data)
            
            # 문제 추출
            problems = self.extract_problems(ocr_data)

            template_name = self.template.name if self.template else "config.json"
            logger.info(f"문학 파싱 완료: {len(lectures)}개 강의, {len(problems)}개 문제 (템플릿: {template_name})")

            return {
                'lectures': lectures,
                'problems': problems,
                'metadata': {
                    'total_lectures': len(lectures),
                    'total_problems': len(problems),
                    'status': 'implemented',
                    'template_used': template_name if self.template else None
                }
            }
        except Exception as e:
            logger.error(f"문학 파싱 중 오류 발생: {e}", exc_info=True)
            return {
                'lectures': [],
                'problems': [],
                'metadata': {
                    'total_lectures': 0,
                    'total_problems': 0,
                    'status': 'error',
                    'error': str(e)
                }
            }

    def _merge_adjacent_texts(
        self,
        ocr_page: Dict[str, Any],
        y_threshold: int = DEFAULT_LINE_Y_THRESHOLD,
        x_threshold: int = DEFAULT_WORD_X_THRESHOLD
    ) -> List[str]:
        """
        인접한 텍스트를 합쳐서 단어/문장 만들기

        Args:
            ocr_page: OCR 페이지 데이터
            y_threshold: 같은 줄로 판단할 y 좌표 차이
            x_threshold: 같은 단어로 판단할 x 좌표 차이

        Returns:
            합쳐진 텍스트 리스트
        """
        texts = ocr_page.get('text', [])
        lefts = ocr_page.get('left', [])
        tops = ocr_page.get('top', [])

        if not texts or len(texts) != len(lefts) or len(texts) != len(tops):
            return texts

        # 텍스트를 좌표와 함께 저장
        items = [(texts[i], lefts[i], tops[i]) for i in range(len(texts))]

        # y 좌표(top)로 그룹화 (같은 줄)
        lines = {}
        for text, left, top in items:
            # 비슷한 y 좌표를 찾음
            found_line = False
            for line_y in lines.keys():
                if abs(top - line_y) <= y_threshold:
                    lines[line_y].append((text, left, top))
                    found_line = True
                    break
            if not found_line:
                lines[top] = [(text, left, top)]

        # 각 줄별로 x 좌표로 정렬하고 인접한 텍스트 합치기
        merged_texts = []
        for line_y in sorted(lines.keys()):
            line_items = sorted(lines[line_y], key=lambda x: x[1])  # x 좌표로 정렬

            if not line_items:
                continue

            current_text = line_items[0][0]
            prev_right = line_items[0][1] + len(line_items[0][0]) * APPROX_CHAR_WIDTH_PIXELS

            for i in range(1, len(line_items)):
                text, left, top = line_items[i]

                # 인접한 텍스트인지 확인
                if left - prev_right <= x_threshold:
                    # 공백 없이 합치기
                    current_text += text
                else:
                    # 새로운 단어 시작
                    if current_text.strip():
                        merged_texts.append(current_text.strip())
                    current_text = text

                prev_right = left + len(text) * APPROX_CHAR_WIDTH_PIXELS

            # 마지막 텍스트 추가
            if current_text.strip():
                merged_texts.append(current_text.strip())

        return merged_texts

    def extract_lectures(self, ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        강의 목록 추출

        Args:
            ocr_data: 페이지별 OCR 결과 리스트

        Returns:
            강의 리스트
        """
        try:
            lectures = []
            START_PAGE = self.config.get('start_content_page', DEFAULT_CONTENT_START_PAGE)
            TOC_END_PAGE = self.config.get('toc_end_page', DEFAULT_TOC_END_PAGE)
            content_patterns = self.config.get('lecture_title_patterns', [])
            toc_patterns = self.config.get('toc_lecture_patterns', [])
            
            # 템플릿에 저장된 TOC 강의 목록이 있으면 우선 사용 (관리자가 입력한 정보)
            toc_lecture_list = self.config.get('toc_lecture_list', [])
            if toc_lecture_list:
                logger.info(f"템플릿에 저장된 TOC 강의 목록 사용: {len(toc_lecture_list)}개")
                for lecture_info in toc_lecture_list:
                    lecture_data = {
                        'lecture_id': lecture_info.get('lecture_id'),
                        'title': lecture_info.get('title', ''),
                        'page': lecture_info.get('start_page', 0),  # 시작 페이지 저장
                        'start_page': lecture_info.get('start_page'),  # 페이지 범위 정보
                        'end_page': lecture_info.get('end_page'),  # 페이지 범위 정보
                        'source': 'template_toc'  # 템플릿의 TOC 텍스트에서 추출
                    }
                    if lecture_data['start_page']:
                        logger.info(f"강의 {lecture_data['lecture_id']}: {lecture_data['start_page']}~{lecture_data['end_page'] or '끝'}페이지")
                    lectures.append(lecture_data)
                logger.info(f"[템플릿 TOC] {len(lectures)}개 강의 로드 완료 (페이지 범위 정보 포함)")
                # 템플릿에서 강의 목록을 가져왔으므로 OCR 기반 추출은 스킵
                return lectures

            if not content_patterns:
                logger.warning("강의 제목 패턴이 설정되지 않았습니다. 기본 패턴 사용")
                content_patterns = [r'^\d+강\s+[가-힣]+', r'^\d+\s+[가-힣]+']

            if not toc_patterns:
                toc_patterns = [r'^\d+강\s*\|\s*[가-힣]', r'^\d+강\s*\|']

            logger.info(f"강의 추출 시작...")
            logger.info(f"  - TOC 추출 범위: 페이지 1-{TOC_END_PAGE}")
            logger.info(f"  - 컨텐츠 추출 시작: 페이지 {START_PAGE}+")

            # 1단계: TOC에서 강의 추출 (페이지 1-7, 텍스트가 깨끗함)
            for ocr_page in ocr_data:
                page_num = ocr_page.get('page_num', 0)
                if page_num <= 0 or page_num > TOC_END_PAGE:
                    continue

                # 인접한 텍스트 합치기
                merged_texts = self._merge_adjacent_texts(ocr_page)

                if not merged_texts:
                    continue

                # 디버깅: TOC 페이지의 텍스트 출력
                if page_num in DEBUG_TOC_PAGES:
                    logger.debug(f"TOC Page {page_num} 상위 {DEBUG_TOC_TEXT_LIMIT}개 텍스트:")
                    for i, text in enumerate(merged_texts[:DEBUG_TOC_TEXT_LIMIT]):
                        logger.debug(f"  [{i}] {text[:80]}")

                # TOC에서 강의 제목 찾기
                for text in merged_texts:
                    cleaned = text.strip()
                    if not cleaned:
                        continue

                    # TOC 패턴 매칭 (예: "1강 | 시의 표현과 형식")
                    for pattern in toc_patterns:
                        match = re.search(pattern, cleaned)
                        if match:
                            # 강의 번호 추출
                            lecture_num_match = re.search(r'^(\d+)', cleaned)
                            if lecture_num_match:
                                lecture_id = int(lecture_num_match.group(1))

                                # 유효한 강의 번호인지 확인
                                if lecture_id > MAX_VALID_LECTURE_NUMBER:
                                    continue

                                # 제목 정리 (페이지 번호 등 제거)
                                title = cleaned
                                # "1강 | 시의 표현과 형식 >>> 고전 시가" 형식에서 앞부분만
                                if '>>>' in title:
                                    title = title.split('>>>')[0].strip()

                                # TOC 특수 형식 처리
                                # 방법 1: 숫자 2개 패턴 뒤의 내용 제거 (작품 목록 시작)
                                # "2강 | 시의 내용 02 정 과정곡..." -> "2강 | 시의 내용"
                                if re.search(r'\s+\d{2}\s+[가-힣]', title):
                                    title = re.sub(r'\s+\d{2}\s+.*$', '', title)

                                # 방법 2: 일반적인 강의 제목 끝나는 패턴 이후 내용 제거
                                # "4강 | 소설의 내용 구성 요소 어화 세상..." -> "4강 | 소설의 내용 구성 요소"
                                ending_patterns = [
                                    (r'^(.+?요소)\s+[가-힣]{2,}.*$', r'\1'),  # "요소" 뒤에 작품명 (모든 것 제거)
                                    (r'^(.+?맥락)\s+\d{2}.*$', r'\1'),        # "맥락" 뒤에 번호 (모든 것 제거)
                                    (r'^(.+?특징)\s+\d{2}.*$', r'\1'),        # "특징" 뒤에 번호 (모든 것 제거)
                                ]
                                for pattern, replacement in ending_patterns:
                                    if re.search(pattern, title):
                                        title = re.sub(pattern, replacement, title).strip()
                                        break

                                # 뒤에 숫자 3개 연속 오면 페이지 번호로 판단하고 제거
                                title = re.sub(r'\s+\d{3}$', '', title)

                                # 중복 체크
                                if not any(l['lecture_id'] == lecture_id for l in lectures):
                                    lectures.append({
                                        'lecture_id': lecture_id,
                                        'title': title,
                                        'page': page_num,
                                        'source': 'toc'
                                    })
                                    logger.info(f"[TOC] 강의 감지: {title} (페이지 {page_num})")
                                    break

            # 2단계: 컨텐츠 페이지에서 강의 추출 (페이지 8+, CID 폰트 문제 있을 수 있음)
            # TOC에서 이미 추출했다면 스킵할 수도 있지만, 혹시 모르니 시도
            if len(lectures) == 0:
                logger.info(f"TOC에서 강의를 찾지 못했습니다. 컨텐츠 페이지에서 시도합니다...")

                for ocr_page in ocr_data:
                    page_num = ocr_page.get('page_num', 0)
                    if page_num < START_PAGE:
                        continue

                    # 인접한 텍스트 합치기
                    merged_texts = self._merge_adjacent_texts(ocr_page)

                    if not merged_texts:
                        continue

                    # 디버깅: 컨텐츠 페이지의 합쳐진 텍스트 출력
                    if page_num in DEBUG_CONTENT_PAGES:
                        logger.debug(f"Content Page {page_num} 합쳐진 상위 {DEBUG_CONTENT_TEXT_LIMIT}개 텍스트:")
                        for i, text in enumerate(merged_texts[:DEBUG_CONTENT_TEXT_LIMIT]):
                            logger.debug(f"  [{i}] {text}")

                    # 상위 LECTURE_TITLE_CHECK_LIMIT개 텍스트 확인 (페이지 상단)
                    for text in merged_texts[:LECTURE_TITLE_CHECK_LIMIT]:
                        cleaned = text.strip()
                        if not cleaned:
                            continue

                        # 강의 제목 패턴 매칭
                        for pattern in content_patterns:
                            match = re.search(pattern, cleaned)
                            if match:
                                # 강의 번호 추출
                                lecture_num_match = re.search(r'^(\d+)', cleaned)
                                if lecture_num_match:
                                    lecture_id = int(lecture_num_match.group(1))
                                    # 중복 체크
                                    if not any(l['lecture_id'] == lecture_id for l in lectures):
                                        lectures.append({
                                            'lecture_id': lecture_id,
                                            'title': cleaned,
                                            'page': page_num,
                                            'source': 'content'
                                        })
                                        logger.info(f"[CONTENT] 강의 감지: {cleaned} (페이지 {page_num})")
                                        break

            # lecture_id 순서대로 정렬
            lectures.sort(key=lambda x: x['lecture_id'])

            logger.info(f"강의 추출 완료: {len(lectures)}개 강의 발견")
            for lec in lectures:
                logger.info(f"  - 강의 {lec['lecture_id']}: {lec['title']}")

            return lectures
        except Exception as e:
            logger.error(f"강의 추출 중 오류 발생: {e}", exc_info=True)
            return []

    def extract_problems(self, ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        문제 추출
        
        Args:
            ocr_data: 페이지별 OCR 결과 리스트
            
        Returns:
            문제 리스트
        """
        try:
            problems = []
            START_PAGE = self.config.get('start_content_page', DEFAULT_CONTENT_START_PAGE)
            problem_pattern = self.config.get('problem_number_pattern', r'^\d{2}$')
            
            for ocr_page in ocr_data:
                page_num = ocr_page.get('page_num', 0)
                if page_num < START_PAGE:
                    continue
                
                texts = ocr_page.get('text', [])
                if not texts:
                    continue
                
                for text in texts:
                    cleaned = text.strip()
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
            logger.error(f"문제 추출 중 오류 발생: {e}", exc_info=True)
            return []

    def extract_sections(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        섹션 추출 (개선된 다중 전략 사용)
        
        추출 대상:
        1. 메인 개념 섹션: "1. 시적 표현", "2. 시의 형식" (type: "concept")
        2. 본문 섹션: "작품으로 이해하기 - 박두진 [해]" (type: "content")
        
        Args:
            lecture_ocr_data: 강의에 해당하는 OCR 데이터 리스트
            
        Returns:
            섹션 리스트
        """
        try:
            # 개선된 섹션 추출기 사용
            # AI 파싱 활성화 여부 확인
            enable_ai = (
                self.enable_ai_parsing 
                if hasattr(self, 'enable_ai_parsing') 
                else False
            )
            
            api_key = None
            if enable_ai:
                api_key = getattr(settings, 'OPENAI_API_KEY', None)
            
            extractor = ImprovedSectionExtractor(
                config=self.config,
                parser=self if enable_ai else None,
                enable_ai=enable_ai and api_key is not None,
                api_key=api_key
            )
            
            result = extractor.extract(lecture_ocr_data)
            
            # 결과 로깅
            logger.info(
                f"섹션 추출 완료: {len(result.sections)}개 섹션 "
                f"(방법: {result.method}, 신뢰도: {result.confidence:.2f})"
            )
            
            return result.sections
            
        except Exception as e:
            logger.error(f"섹션 추출 중 오류 발생: {e}", exc_info=True)
            # 폴백: 기존 방식 시도
            try:
                return self._extract_sections_fallback(lecture_ocr_data)
            except Exception as fallback_error:
                logger.error(f"폴백 섹션 추출도 실패: {fallback_error}")
                return []
    
    def _extract_sections_fallback(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """폴백 섹션 추출 (기존 방식)
        
        개선된 추출기가 실패할 경우 사용
        """
        sections = []
        concept_patterns = self.config.get('concept_title_patterns', [])
        content_patterns = self.config.get('content_header_patterns', [])
        START_PAGE = self.config.get('start_content_page', 8)
        
        # 강의의 실제 시작 페이지 찾기
        if lecture_ocr_data:
            actual_start_page = min(ocr_data.get('page_num', 0) for ocr_data in lecture_ocr_data)
            search_start_page = min(START_PAGE, actual_start_page)
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
            lines = self.group_lines(ocr_data, y_threshold=10)
            
            # 각 줄을 문장으로 결합하고 패턴 매칭
            for line_idx, line in enumerate(lines):
                line_text = self.join_line_text(line)
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                # 특수 문자 제거
                cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                
                # 목차 형식 제외
                if re.search(r'\d{3}', cleaned_line) and len(cleaned_line) < 30:
                    continue
                
                section_type = None
                section_title = None
                
                # 1. 메인 개념 섹션 확인 ("1. 시적 표현", "2. 시의 형식")
                main_concept_match = re.match(r'^(\d+)\s*[\.]\s*([가-힣\s]{2,20})$', cleaned_line)
                if main_concept_match:
                    section_type = "concept"
                    section_title = cleaned_line
                # 대체 패턴: "1 시적 표현" (점 없음)
                elif re.match(r'^\d+\s+[가-힣]{2,}\s*[가-힣]*$', cleaned_line) and len(cleaned_line.split()) <= 3:
                    section_type = "concept"
                    section_title = cleaned_line
                # 2. 본문 섹션 확인 ("작품으로 이해하기")
                elif self.matches_patterns(cleaned_line, content_patterns):
                    section_type = "content"
                    section_title = cleaned_line
                    # 다음 줄에서 작품 제목 찾기
                    if line_idx + 1 < len(lines):
                        next_line = lines[line_idx + 1]
                        next_text = self.join_line_text(next_line).strip()
                        next_cleaned = re.sub(r'\(cid:\d+\)', '', next_text).strip()
                        # 작품 제목 패턴 확인
                        if re.search(r'[가-힣]+\s*\[[가-힣]+\]', next_cleaned) or re.search(r'[가-힣]+\s*「[가-힣]+」', next_cleaned):
                            section_title = f"{cleaned_line} - {next_cleaned}"
                
                if section_type and section_title:
                    # bbox 계산
                    bbox = self.get_line_bbox(line)
                    
                    sections.append({
                        "title": section_title,
                        "type": section_type,
                        "page": page_num,
                        "bbox": bbox
                    })
        
        return sections

    def extract_content_paragraphs(
        self,
        lecture_ocr_data: List[Dict[str, Any]],
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        섹션별 문단 추출
        
        각 섹션에 해당하는 문단들을 추출하여 섹션별로 그룹화
        
        Args:
            lecture_ocr_data: 강의에 해당하는 OCR 데이터 리스트
            sections: 이미 추출된 섹션 리스트
            
        Returns:
            문단 리스트
        """
        try:
            all_paragraphs = []
            threshold = self.config.get('paragraph_y_threshold', DEFAULT_PARAGRAPH_Y_THRESHOLD)
            
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
                    if self.matches_patterns(cleaned_line, section_patterns):
                        continue
                    
                    # 개념 제목 패턴도 제외
                    concept_patterns = self.config.get('concept_title_patterns', [])
                    if self.matches_patterns(cleaned_line, concept_patterns):
                        continue
                    
                    # 본문 헤더 패턴도 제외
                    content_patterns = self.config.get('content_header_patterns', [])
                    if self.matches_patterns(cleaned_line, content_patterns):
                        continue
                    
                    # 문제 번호 패턴도 제외
                    problem_pattern = self.config.get('problem_number_pattern', r'^\d{2}$')
                    if re.match(problem_pattern, cleaned_line):
                        continue
                    
                    # 제외 패턴들
                    exclude_patterns = [
                        r'정답과 해설',
                        r'다음 글을 읽고',
                        r'물음에 답하시오',
                    ]
                    if any(re.search(p, cleaned_line) for p in exclude_patterns):
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
                        
                        # 새 문단 초기화
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
            logger.error(f"문단 추출 중 오류 발생: {e}", exc_info=True)
            return []
