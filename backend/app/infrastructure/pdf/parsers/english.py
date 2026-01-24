"""
영어 파서

⚠️ DEPRECATED: 이 클래스는 더 이상 사용되지 않습니다.
대신 UnifiedTemplateParser를 사용하세요.

과목별 파서는 통합 파서(UnifiedTemplateParser)로 대체되었습니다.
템플릿 기반으로 모든 과목을 동일한 프로세스로 파싱합니다.
"""
import re
import logging
import warnings
from pathlib import Path
from typing import List, Optional

from .base import BaseParser
from .config_manager import ParserConfigManager
from .template_manager import TemplateManager
from .template import ParsingTemplate
from .section_extractor import ImprovedSectionExtractor
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


class EnglishParser(BaseParser):
    """
    ⚠️ DEPRECATED: UnifiedTemplateParser를 사용하세요.
    
    이 클래스는 하위 호환성을 위해 유지되지만, 새로운 코드에서는
    UnifiedTemplateParser를 사용해야 합니다.
    """

    def __init__(self, config_path: Optional[Path] = None, template: Optional[ParsingTemplate] = None):
        """
        Args:
            config_path: config.json 경로 (None이면 기본 경로 사용)
            template: 사용할 템플릿 (None이면 자동 매칭 시도)
        """
        warnings.warn(
            "EnglishParser is deprecated. Use UnifiedTemplateParser instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.config_path = config_path
        self.template = template
        self.template_manager = TemplateManager()
        
        # 템플릿이 제공되면 템플릿의 패턴 사용, 아니면 config.json 사용
        if template:
            self.config = self._template_to_config(template)
            logger.info(f"템플릿 사용: {template.name} (신뢰도: {template.confidence})")
        else:
            self.config = ParserConfigManager.load_config('english', config_path)
    
    def _template_to_config(self, template: ParsingTemplate) -> JSONDict:
        """템플릿을 config 형식으로 변환 (문학 파서와 동일한 구조)

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
            config['lecture_title_patterns'] = [r'Unit\s*\d+', r'^\d+단원', r'^\d+\s*Unit']
        
        return config
    
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
            subject='english',
            threshold=threshold
        )
        
        if match_result:
            template, confidence = match_result
            logger.info(f"템플릿 매칭 성공: {template.name} (신뢰도: {confidence:.2f})")
            self.template = template
            self.config = self._template_to_config(template)
            return template
        
        return None

    def parse(self, ocr_data: List[OCRPageData]) -> ParsingResult:
        """
        OCR 데이터를 파싱하여 영어 콘텐츠 추출

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
            logger.info(f"영어 파싱 완료: {len(lectures)}개 강의, {len(problems)}개 문제 (템플릿: {template_name})")

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
            logger.error(f"영어 파싱 중 오류 발생: {e}", exc_info=True)
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

    def extract_lectures(self, ocr_data: List[OCRPageData]) -> List[LectureInfo]:
        """
        강의 목록 추출 (문학 파서와 동일한 로직)

        템플릿에 저장된 TOC 강의 목록이 있으면 우선 사용
        
        Args:
            ocr_data: 페이지별 OCR 결과 리스트
            
        Returns:
            강의 리스트
        """
        try:
            lectures = []
            
            # 템플릿에 저장된 TOC 강의 목록이 있으면 우선 사용 (관리자가 입력한 정보)
            toc_lecture_list = self.config.get('toc_lecture_list', [])
            if toc_lecture_list:
                logger.info(f"\n[EnglishParser] 템플릿에 저장된 TOC 강의 목록 사용: {len(toc_lecture_list)}개")
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

            # 1) TOC 기반 강의 추출 (가능하면 TOC를 “정답”으로 사용)
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

                        # 영어는 대소문자/공백이 다양해서 IGNORECASE로 매칭
                        matched = False
                        for p in toc_patterns:
                            try:
                                if re.search(p, line_text, re.IGNORECASE):
                                    matched = True
                                    break
                            except re.error:
                                continue
                        if not matched:
                            continue

                        title = re.sub(r'\s+\d{1,3}\s*$', '', line_text).strip()
                        m = re.search(r'(\d+)', title)
                        parsed_id = int(m.group(1)) if m else lecture_id

                        if not any(l['lecture_id'] == parsed_id for l in lectures):
                            lectures.append({
                                'lecture_id': parsed_id,
                                'title': title,
                                'page': page_num,
                                'bbox': self.get_line_bbox(line)
                            })
                            lecture_id = max(lecture_id, parsed_id + 1)

                if lectures:
                    lectures.sort(key=lambda x: x['lecture_id'])
                    return lectures

            for ocr_page in ocr_data:
                page_num = ocr_page.get('page_num', 0)
                if page_num < START_PAGE:
                    continue

                texts = ocr_page.get('text', [])
                tops = ocr_page.get('top', [])
                lefts = ocr_page.get('left', [])
                widths = ocr_page.get('width', [])
                heights = ocr_page.get('height', [])

                if not texts:
                    continue

                # 줄 단위로 그룹화
                lines = self.group_lines(ocr_page, y_threshold=10)

                # 페이지 상단 영역 체크 (상단 30%)
                page_top_threshold = None
                if lines:
                    first_line_y = lines[0][0]['top'] if lines[0] else 0
                    if lines and lines[-1]:
                        last_line = lines[-1]
                        estimated_page_height = last_line[-1]['top'] + last_line[-1]['height']
                        page_top_threshold = first_line_y + (estimated_page_height * 0.3)

                # 평균 폰트 크기 계산
                min_title_height = 0
                if lines:
                    total_height = sum(word['height'] for line in lines[:10] for word in line[:3])
                    total_words = sum(len(line[:3]) for line in lines[:10])
                    if total_words > 0:
                        avg_height = total_height / min(30, total_words)
                        min_title_height = avg_height * 1.0

                for line in lines:
                    line_text = self.join_line_text(line).strip()

                    if not line_text or len(line_text) < 3:
                        continue

                    # 페이지 상단 영역 체크
                    line_y = line[0]['top']
                    if page_top_threshold and line_y > page_top_threshold:
                        continue

                    # 큰 폰트 체크
                    line_height = max(word['height'] for word in line)
                    if min_title_height > 0 and line_height < min_title_height * 0.9:
                        continue

                    # 패턴 매칭 (대소문자 무시)
                    line_text_lower = line_text.lower()
                    matched = False
                    for pattern in patterns:
                        if re.search(pattern, line_text_lower, re.IGNORECASE):
                            matched = True
                            break

                    if matched:
                        bbox = self.get_line_bbox(line)
                        
                        # 중복 체크
                        if not any(l['lecture_id'] == lecture_id for l in lectures):
                            lectures.append({
                                'lecture_id': lecture_id,
                                'title': line_text,
                                'page': page_num,
                                'bbox': bbox
                            })
                            lecture_id += 1
                            logger.debug(f"영어 Unit 감지: {line_text[:50]} (페이지 {page_num})")

            # lecture_id 순서대로 정렬
            lectures.sort(key=lambda x: x['lecture_id'])
            return lectures
        except Exception as e:
            logger.error(f"영어 강의 추출 중 오류 발생: {e}", exc_info=True)
            return []

    def extract_problems(self, ocr_data: List[OCRPageData]) -> List[ProblemInfo]:
        """
        문제 추출

        Args:
            ocr_data: 페이지별 OCR 결과 리스트

        Returns:
            문제 리스트
        """
        try:
            problems = []
            START_PAGE = self.config.get('start_content_page', 1)
            problem_pattern = self.config.get('problem_number_pattern', r'^\d+\.')
            problem_id = 1

            for ocr_page in ocr_data:
                page_num = ocr_page.get('page_num', 0)
                if page_num < START_PAGE:
                    continue

                texts = ocr_page.get('text', [])
                if not texts:
                    continue

                lines = self.group_lines(ocr_page, y_threshold=10)

                # 문제 번호가 있는 줄 찾기
                problem_starts = []
                for line_idx, line in enumerate(lines):
                    line_text = self.join_line_text(line).strip()

                    # 문제 번호 패턴 매칭 ("1.", "2." 등)
                    if re.match(problem_pattern, line_text):
                        problem_starts.append({
                            "number": line_text,
                            "line_idx": line_idx,
                            "y": line[0]['top']
                        })

                # 각 문제 영역 추출
                for j, problem_start in enumerate(problem_starts):
                    start_line_idx = problem_start['line_idx']
                    end_line_idx = problem_starts[j + 1]['line_idx'] if j + 1 < len(problem_starts) else len(lines)

                    # 문제 영역의 모든 줄 추출
                    problem_lines = lines[start_line_idx:end_line_idx]

                    # 전체 텍스트 추출
                    full_text = " ".join([self.join_line_text(line) for line in problem_lines])

                    # 선택지 추출 (①~⑤ 또는 1)~5) 형식)
                    choices = {}
                    choice_patterns = [
                        r'[①②③④⑤]\s*(.+?)(?=[①②③④⑤]|$)',
                        r'(\d+)\)\s*(.+?)(?=\d+\)|$)',
                    ]

                    for pattern in choice_patterns:
                        matches = re.finditer(pattern, full_text)
                        for match in matches:
                            if len(match.groups()) >= 2:
                                choice_num = match.group(1) if match.group(1) else str(len(choices) + 1)
                                choice_text = match.group(2).strip()
                                if choice_text:
                                    choices[choice_num] = choice_text

                    # bbox 계산
                    all_words = [word for line in problem_lines for word in line]
                    bbox = self.get_line_bbox(all_words) if all_words else [0, 0, 0, 0]

                    problems.append({
                        "problem_id": f"{problem_id:02d}",
                        "page": page_num,
                        "bbox": bbox,
                        "text": full_text,
                        "choices": choices if choices else {}
                    })
                    problem_id += 1

            return problems
        except Exception as e:
            logger.error(f"영어 문제 추출 중 오류 발생: {e}", exc_info=True)
            return []

    def extract_sections(
        self,
        lecture_ocr_data: List[OCRPageData]
    ) -> List[SectionData]:
        """
        섹션 추출 (개선된 다중 전략 사용, 문학 파서와 동일)

        Args:
            lecture_ocr_data: 강의에 해당하는 OCR 데이터 리스트

        Returns:
            섹션 리스트
        """
        try:
            # 개선된 섹션 추출기 사용 (문학 파서와 동일)
            extractor = ImprovedSectionExtractor(
                config=self.config,
                parser=None,  # 영어는 AI 파싱 비활성화
                enable_ai=False,
                api_key=None
            )
            
            result = extractor.extract(lecture_ocr_data)
            
            # 결과 로깅
            logger.info(
                f"영어 섹션 추출 완료: {len(result.sections)}개 섹션 "
                f"(방법: {result.method}, 신뢰도: {result.confidence:.2f})"
            )
            
            return result.sections
            
        except Exception as e:
            logger.error(f"영어 섹션 추출 중 오류 발생: {e}", exc_info=True)
            # 폴백: 기존 방식 시도
            try:
                return self._extract_sections_fallback(lecture_ocr_data)
            except Exception as fallback_error:
                logger.error(f"폴백 섹션 추출도 실패: {fallback_error}")
                return []
    
    def _extract_sections_fallback(
        self,
        lecture_ocr_data: List[OCRPageData]
    ) -> List[SectionData]:
        """폴백 섹션 추출 (기존 방식)"""
        sections = []
        START_PAGE = self.config.get('start_content_page', 1)
        
        # 영어 섹션 패턴: "Passage 1", "지문 1", "Grammar", "Vocabulary" 등
        passage_patterns = [
            r'^Passage\s*\d+',
            r'^지문\s*\d+',
        ]
        grammar_patterns = [
            r'^Grammar',
            r'^문법',
        ]
        vocab_patterns = [
            r'^Vocabulary',
            r'^어휘',
        ]

        for ocr_data in lecture_ocr_data:
            page_num = ocr_data.get('page_num', 0)
            if page_num < START_PAGE:
                continue

            lines = self.group_lines(ocr_data, y_threshold=10)

            for line in lines:
                line_text = self.join_line_text(line).strip()
                if not line_text:
                    continue

                cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                section_type = None
                section_title = None

                # 지문 섹션 확인
                for pattern in passage_patterns:
                    if re.match(pattern, cleaned_line, re.IGNORECASE):
                        section_type = "passage"
                        section_title = cleaned_line
                        break

                # 문법 섹션 확인
                if not section_type:
                    for pattern in grammar_patterns:
                        if re.match(pattern, cleaned_line, re.IGNORECASE):
                            section_type = "grammar"
                            section_title = cleaned_line
                            break

                # 어휘 섹션 확인
                if not section_type:
                    for pattern in vocab_patterns:
                        if re.match(pattern, cleaned_line, re.IGNORECASE):
                            section_type = "vocabulary"
                            section_title = cleaned_line
                            break

                if section_type and section_title:
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
        lecture_ocr_data: List[OCRPageData],
        sections: List[SectionData]
    ) -> List[ParagraphData]:
        """
        섹션별 문단 추출

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
                lines = self.group_lines(ocr_data, y_threshold=threshold)

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
                    line_text = self.join_line_text(line).strip()
                    if not line_text:
                        continue

                    # 섹션 제목 패턴 제외
                    cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                    
                    # 문제 번호 패턴 제외
                    problem_pattern = self.config.get('problem_number_pattern', r'^\d+\.')
                    if re.match(problem_pattern, cleaned_line):
                        continue

                    line_y = line[0]['top']

                    # 같은 문단인지 확인
                    if prev_line_y is not None and abs(line_y - prev_line_y) < threshold:
                        if current_paragraph['text']:
                            current_paragraph['text'] += " " + line_text
                        else:
                            current_paragraph['text'] = line_text
                            current_paragraph['y_start'] = line_y
                            current_paragraph['bbox'] = self.get_line_bbox(line)

                        if current_paragraph['bbox']:
                            line_bbox = self.get_line_bbox(line)
                            current_paragraph['bbox'][0] = min(current_paragraph['bbox'][0], line_bbox[0])
                            current_paragraph['bbox'][1] = min(current_paragraph['bbox'][1], line_bbox[1])
                            current_paragraph['bbox'][2] = max(current_paragraph['bbox'][2], line_bbox[2])
                            current_paragraph['bbox'][3] = max(current_paragraph['bbox'][3], line_bbox[3])

                        current_paragraph['y_end'] = line_y
                    else:
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

                if current_paragraph['text']:
                    paragraphs.append(current_paragraph)

                all_paragraphs.extend(paragraphs)

            return all_paragraphs
        except Exception as e:
            logger.error(f"영어 문단 추출 중 오류 발생: {e}", exc_info=True)
            return []
