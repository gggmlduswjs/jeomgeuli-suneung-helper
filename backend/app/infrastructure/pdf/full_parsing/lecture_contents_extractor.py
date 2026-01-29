"""
강의 콘텐츠 추출기
강의별 섹션 및 본문 추출 (textbook_pipeline 로직 이동)
"""
import re
import logging
from typing import List, Optional, Tuple
from pathlib import Path

from app.infrastructure.pdf.parsers.lecture_title_validator import LectureTitleValidator
from app.infrastructure.pdf.parsers.base import BaseParser
from app.infrastructure.pdf.types import (
    OCRPageData,
    LectureInfo,
    SectionData,
    ParagraphData,
    JSONDict,
)

logger = logging.getLogger(__name__)


class LectureContentsExtractor:
    """강의별 목차 및 콘텐츠 추출기"""

    def __init__(self, subject: str, config: Optional[JSONDict] = None):
        """
        Args:
            subject: 과목명
            config: 설정 딕셔너리
        """
        self.subject = subject
        self.config = config or {}
        # start_content_page가 None이거나 유효하지 않으면 기본값 사용
        start_content_page = self.config.get('start_content_page', 8)
        self.start_content_page = start_content_page if start_content_page is not None and isinstance(start_content_page, int) else 8
        
        # 강의 제목 검증기 초기화 (TOC 정보 활용)
        toc_text = self.config.get('toc_text')
        toc_lecture_list = self.config.get('toc_lecture_list', [])
        if toc_text or toc_lecture_list:
            self.title_validator = LectureTitleValidator(
                toc_text=toc_text,
                toc_lecture_list=toc_lecture_list
            )
            logger.info(f"[LectureContentsExtractor] 강의 제목 검증기 활성화 (TOC 텍스트: {bool(toc_text)}, 강의 목록: {len(toc_lecture_list)}개)")
        else:
            self.title_validator = None
    
    def extract(
        self,
        all_ocr_data: List[OCRPageData],
        lectures: List[LectureInfo],
        parser: BaseParser
    ) -> List[JSONDict]:
        """
        강의별 목차 및 콘텐츠 추출

        Args:
            all_ocr_data: 전체 OCR 데이터
            lectures: 강의 목록
            parser: 파서 인스턴스 (섹션 추출용)

        Returns:
            강의 콘텐츠 리스트 (각 섹션에 content 포함)
        """
        lecture_contents = []
        
        # 이전 강의의 끝 페이지를 추적 (강의 시작 페이지 추정용)
        # start_content_page가 None이 아니고 int인지 확인
        if self.start_content_page is not None and isinstance(self.start_content_page, int):
            prev_lecture_end_page = self.start_content_page - 1
        else:
            prev_lecture_end_page = 7  # 기본값 (start_content_page가 8이므로)
            logger.warning(f"start_content_page가 유효하지 않음 ({self.start_content_page}), 기본값 사용")
        
        for lecture in lectures:
            lecture_id = lecture['lecture_id']
            lecture_page = lecture.get('page')  # None일 수 있음
            
            # 실제 시작 페이지 찾기
            actual_start_page = self._find_actual_lecture_start_page(
                lecture_id,
                lecture['title'],
                all_ocr_data,
                prev_lecture_end_page  # 이전 강의 끝 페이지를 힌트로 전달
            )
            
            if actual_start_page == -1:
                # TOC에서 발견된 강의의 경우, 이전 강의 정보를 이용해 추정
                if (lecture_page is not None and 
                    isinstance(lecture_page, int) and 
                    isinstance(self.start_content_page, int) and
                    lecture_page < self.start_content_page):
                    # 이전 강의가 있으면 그 끝 페이지 다음부터 시작
                    if prev_lecture_end_page >= self.start_content_page:
                        # 이전 강의 끝 페이지 + 1을 추정 시작 페이지로 사용
                        estimated_start = prev_lecture_end_page + 1
                        logger.info(f"강의 {lecture_id}의 시작 페이지를 추정: {estimated_start} (이전 강의 끝: {prev_lecture_end_page})")
                        actual_start_page = estimated_start
                    else:
                        # 첫 강의이거나 이전 강의 정보가 없으면 start_content_page 사용
                        actual_start_page = self.start_content_page
                        logger.info(f"강의 {lecture_id}의 시작 페이지를 기본값으로 설정: {actual_start_page}")
                elif lecture_page is not None and isinstance(lecture_page, int):
                    actual_start_page = lecture_page
                else:
                    # lecture_page가 None이거나 유효하지 않으면 기본값 사용
                    actual_start_page = self.start_content_page
                    logger.warning(f"강의 {lecture_id}의 페이지 정보가 유효하지 않음 (lecture_page={lecture_page}), 기본값 사용: {actual_start_page}")
            
            # 강의 페이지 범위 찾기
            start_page, end_page = self._find_lecture_page_range(
                lecture,
                lectures,
                all_ocr_data,
                actual_start_page
            )
            
            # 해당 페이지들의 OCR 데이터
            lecture_ocr_data = [
                ocr_data for ocr_data in all_ocr_data
                if start_page <= ocr_data['page_num'] <= end_page
            ]
            
            if not lecture_ocr_data:
                lecture_contents.append({
                    "lecture_id": lecture_id,
                    "title": lecture['title'],
                    "sections": [],
                    "content": [],
                    "page": actual_start_page,
                    "start_page": start_page,
                    "end_page": end_page
                })
                continue
            
            # 섹션 추출 (parser 사용, 이미지 크롭 포함)
            if hasattr(parser, 'extract_sections'):
                sections = parser.extract_sections(lecture_ocr_data, crop_images=True)
            else:
                sections = []
            
            # 문단 추출 (parser 사용)
            if hasattr(parser, 'extract_content_paragraphs'):
                content_paragraphs = parser.extract_content_paragraphs(lecture_ocr_data, sections)
            else:
                content_paragraphs = []
            
            # 섹션별 content 매칭
            sections_with_content = self._match_content_to_sections(
                sections,
                content_paragraphs,
                lecture_ocr_data
            )
            
            lecture_contents.append({
                "lecture_id": lecture_id,
                "title": lecture['title'],
                "sections": sections_with_content,
                "content": content_paragraphs,  # 전체 문단도 유지 (하위 호환성)
                "page": actual_start_page,
                "start_page": start_page,
                "end_page": end_page
            })
            
            # 다음 강의를 위한 끝 페이지 업데이트
            prev_lecture_end_page = end_page
        
        return lecture_contents
    
    def _extract_text_in_bbox(
        self,
        ocr_data: OCRPageData,
        bbox: List[int],
        margin: int = 10
    ) -> List[str]:
        """
        bbox 내의 텍스트만 추출

        Args:
            ocr_data: OCR 데이터 (text, left, top, width, height 리스트 포함)
            bbox: [x_min, y_min, x_max, y_max] 좌표
            margin: bbox 경계에서의 여유 픽셀 (기본 10px)

        Returns:
            bbox 내의 텍스트 리스트
        """
        if not bbox or len(bbox) != 4:
            return []

        x_min, y_min, x_max, y_max = bbox
        texts = ocr_data.get('text', [])
        lefts = ocr_data.get('left', [])
        tops = ocr_data.get('top', [])
        widths = ocr_data.get('width', [])
        heights = ocr_data.get('height', [])

        if not texts or not lefts or not tops:
            return []

        extracted_texts = []

        for i in range(len(texts)):
            text = texts[i].strip()
            if not text:
                continue

            # 텍스트 위치 정보
            x = lefts[i] if i < len(lefts) else 0
            y = tops[i] if i < len(tops) else 0
            w = widths[i] if i < len(widths) else 0
            h = heights[i] if i < len(heights) else 0

            # 텍스트의 중심점이 bbox 내에 있는지 확인 (margin 포함)
            text_center_x = x + w / 2
            text_center_y = y + h / 2

            if (x_min - margin <= text_center_x <= x_max + margin and
                y_min - margin <= text_center_y <= y_max + margin):

                # CID 제거
                text = re.sub(r'\(cid:\d+\)', '', text).strip()
                if text and len(text) >= 2:
                    extracted_texts.append(text)

        return extracted_texts

    def _match_content_to_sections(
        self,
        sections: List[SectionData],
        content_paragraphs: List[ParagraphData],
        lecture_ocr_data: List[OCRPageData]
    ) -> List[SectionData]:
        """
        섹션별 content 매칭 (bbox 기반)

        각 섹션의 bbox 좌표 내의 텍스트만 추출하여 content에 할당
        """
        sections_with_content = []

        for section in sections:
            section_page = section.get('page', 0)
            section_bbox = section.get('bbox', [0, 0, 0, 0])
            section_type = section.get('type', 'concept')

            # 해당 페이지의 OCR 데이터 찾기
            page_ocr_data = None
            for ocr_data in lecture_ocr_data:
                if ocr_data.get('page_num') == section_page:
                    page_ocr_data = ocr_data
                    break

            section_content = []

            if page_ocr_data and section_bbox and len(section_bbox) == 4:
                # bbox 내의 텍스트 추출
                raw_texts = self._extract_text_in_bbox(
                    page_ocr_data,
                    section_bbox,
                    margin=20  # 20px 여유
                )

                logger.debug(
                    f"[Content Extract] {section_type} 섹션 "
                    f"(페이지 {section_page}, bbox {section_bbox}): "
                    f"{len(raw_texts)}개 텍스트 추출"
                )

                # 불필요한 텍스트 필터링
                exclude_patterns = [
                    r'^>>>\s*$',
                    r'^\d{4}학년도\s*$',
                    r'^\d{2}:\d{2}\s*$',
                    r'오후 \d{1,2}:\d{2}\s*$',
                    r'^\d{3} EBS\s*$',
                    r'^\[1부\]\s*$',
                    r'^EBS\s+수능특강',
                    r'^문학\s*$',
                    r'^\d+\s*$',  # 숫자만 있는 줄
                ]

                for text in raw_texts:
                    # 제외 패턴 체크
                    if any(re.search(p, text) for p in exclude_patterns):
                        continue

                    # 너무 짧은 텍스트 제외 (단, 숫자는 포함)
                    if len(text) < 2 and not re.search(r'\d+', text):
                        continue

                    section_content.append(text)

                logger.info(
                    f"[Content Extract] {section_type} 섹션 "
                    f"(페이지 {section_page}): "
                    f"{len(section_content)}개 텍스트 저장"
                )
            else:
                logger.warning(
                    f"[Content Extract] {section_type} 섹션 "
                    f"(페이지 {section_page}): "
                    f"OCR 데이터 또는 bbox 없음"
                )

            # 섹션 데이터 구성
            section_data = {
                "title": section.get('title', ''),
                "type": section_type,
                "page": section_page,
                "bbox": section_bbox,
                "content": section_content,
                "image_path": section.get('image_path'),  # 이미지 경로 유지
                "image_filename": section.get('image_filename')  # 파일명 유지
            }

            sections_with_content.append(section_data)

        return sections_with_content
    
    def _find_actual_lecture_start_page(
        self,
        lecture_id: int,
        lecture_title: str,
        all_ocr_data: List[OCRPageData],
        search_start_hint: Optional[int] = None
    ) -> int:
        """실제 시작 페이지 찾기 (개선된 버전)

        Args:
            lecture_id: 강의 ID
            lecture_title: 강의 제목
            all_ocr_data: 전체 OCR 데이터
            search_start_hint: 검색 시작 힌트 (이전 강의의 끝 페이지)
        """
        # 강의 번호 추출
        lecture_num_match = re.search(r'^(\d+)강', lecture_title)
        if not lecture_num_match:
            lecture_num_match = re.search(r'^(\d+)', lecture_title)
        
        if not lecture_num_match:
            return -1
        
        lecture_num = int(lecture_num_match.group(1))
        
        # TOC 텍스트로 강의 제목 검증 및 보정
        corrected_title = lecture_title
        if self.title_validator:
            is_valid, suggested_title, confidence = self.title_validator.validate_lecture_title(
                extracted_title=lecture_title,
                page_num=search_start_hint or self.start_content_page,
                lecture_id=lecture_id
            )
            
            if suggested_title and confidence > 0.5:
                if not is_valid:
                    logger.info(
                        f"[강의 제목 보정] '{lecture_title}' -> '{suggested_title}' "
                        f"(신뢰도: {confidence:.2f}, 강의 ID: {lecture_id})"
                    )
                corrected_title = suggested_title
        
        # 강의 제목에서 핵심 키워드 추출 (예: "시의표현과형식" -> "시의", "표현", "형식")
        title_keywords = []
        # "1강|시의표현과형식" 형식에서 제목 부분만 추출
        title_part = corrected_title.split('|')[-1].split('>>>')[0].strip()
        # 한글 키워드 추출 (2글자 이상)
        title_keywords = re.findall(r'[가-힣]{2,}', title_part)
        
        # 강의 제목 패턴 가져오기
        lecture_patterns = self.config.get('lecture_title_patterns', [])
        if not lecture_patterns:
            lecture_patterns = [r'^\d+강\s+[가-힣]+', r'^\d+\s+[가-힣]+']
        
        # 실제 콘텐츠 페이지에서 해당 강의 찾기
        # 검색 시작: 힌트가 있으면 그 다음 페이지부터, 없으면 start_content_page부터
        search_start = search_start_hint + 1 if search_start_hint and search_start_hint >= self.start_content_page else self.start_content_page
        # 검색 범위: 시작 페이지부터 최대 50페이지까지
        search_end_page = min(search_start + 50, len(all_ocr_data))
        
        for ocr_data in all_ocr_data:
            page_num = ocr_data.get('page_num', 0)
            if page_num < search_start or page_num > search_end_page:
                continue
            
            texts = ocr_data.get('text', [])
            if not texts:
                continue
            
            # 상위 50개 텍스트 확인 (페이지 상단, 더 넓은 범위)
            for text in texts[:50]:
                cleaned = text.strip()
                if not cleaned:
                    continue
                
                # CID 제거
                cleaned = re.sub(r'\(cid:\d+\)', '', cleaned).strip()
                
                # 방법 1: 강의 제목 패턴 매칭
                for pattern in lecture_patterns:
                    match = re.search(pattern, cleaned)
                    if match:
                        # 강의 번호 확인
                        num_match = re.search(r'^(\d+)', cleaned)
                        if num_match and int(num_match.group(1)) == lecture_num:
                            return page_num
                
                # 방법 2: 강의 번호 + 키워드 매칭
                if lecture_num_match:
                    # "N강" 형식 확인
                    if re.search(rf'^{lecture_num}강', cleaned):
                        # 키워드가 있으면 일부라도 포함되는지 확인
                        if not title_keywords or any(kw in cleaned for kw in title_keywords[:2]):
                            return page_num
                    
                    # "N " 형식 확인
                    if cleaned.startswith(f"{lecture_num} ") or cleaned.startswith(f"{lecture_num}."):
                        # 키워드 확인
                        if not title_keywords or any(kw in cleaned for kw in title_keywords[:2]):
                            return page_num
                
                # 방법 3: 단순 강의 번호 매칭 (마지막 수단)
                if cleaned == str(lecture_num):
                    return page_num
        
        return -1
    
    def _find_lecture_page_range(
        self,
        lecture: LectureInfo,
        lectures: List[LectureInfo],
        all_ocr_data: List[OCRPageData],
        start_page: int
    ) -> Tuple[int, int]:
        """강의 페이지 범위 찾기

        우선순위:
        1. 템플릿의 lecture_page_ranges
        2. TOC의 toc_lecture_list
        3. _find_actual_lecture_start_page로 동적 탐색
        """
        # start_page 유효성 검증
        if start_page is None or not isinstance(start_page, int):
            logger.warning(f"강의 {lecture.get('lecture_id')}의 시작 페이지가 유효하지 않음: {start_page}, 기본값 사용")
            start_page = self.start_content_page

        lecture_id = lecture['lecture_id']

        # 1. 템플릿의 lecture_page_ranges 확인
        lecture_page_ranges = self.config.get('lecture_page_ranges', {})
        if str(lecture_id) in lecture_page_ranges:
            range_info = lecture_page_ranges[str(lecture_id)]
            if range_info and 'end' in range_info:
                template_end = range_info['end']
                if template_end and isinstance(template_end, int):
                    logger.debug(f"강의 {lecture_id} 범위: 템플릿 사용 {start_page}~{template_end}")
                    return start_page, template_end

        # 2. TOC 정보 확인
        toc_lecture_list = self.config.get('toc_lecture_list', [])
        current_toc = next((l for l in toc_lecture_list if l.get('lecture_id') == lecture_id), None)
        next_toc = next((l for l in toc_lecture_list if l.get('lecture_id') == lecture_id + 1), None)

        if next_toc and next_toc.get('start_page'):
            toc_end = next_toc['start_page'] - 1
            if isinstance(toc_end, int) and toc_end > start_page:
                logger.debug(f"강의 {lecture_id} 범위: TOC 사용 {start_page}~{toc_end}")
                return start_page, toc_end
        elif current_toc and current_toc.get('end_page'):
            toc_end = current_toc['end_page']
            if isinstance(toc_end, int) and toc_end > start_page:
                logger.debug(f"강의 {lecture_id} 범위: TOC end_page 사용 {start_page}~{toc_end}")
                return start_page, toc_end

        # 3. 다음 강의 동적 탐색
        next_lecture = next((l for l in lectures if l['lecture_id'] == lecture_id + 1), None)

        if next_lecture:
            # 다음 강의의 실제 시작 페이지 찾기 (현재 강의 시작 페이지를 힌트로 전달)
            next_actual_start = self._find_actual_lecture_start_page(
                next_lecture['lecture_id'],
                next_lecture['title'],
                all_ocr_data,
                search_start_hint=start_page  # 현재 강의 시작 페이지를 힌트로 전달
            )
            
            if next_actual_start != -1 and isinstance(start_page, int) and next_actual_start > start_page:
                end_page = next_actual_start - 1
            else:
                # next_lecture의 페이지 정보 확인 (start_page 우선, 없으면 page)
                # None 체크 및 타입 검증 추가
                next_page = next_lecture.get('start_page') or next_lecture.get('page')
                if next_page is not None and isinstance(next_page, int) and isinstance(start_page, int) and next_page > start_page:
                    end_page = next_page - 1
                else:
                    # 페이지 정보가 없거나 유효하지 않으면 전체 끝까지
                    end_page = len(all_ocr_data)
        else:
            end_page = len(all_ocr_data)
        
        return start_page, end_page
