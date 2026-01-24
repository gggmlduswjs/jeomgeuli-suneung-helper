"""
강의 콘텐츠 추출기
강의별 섹션 및 본문 추출 (textbook_pipeline 로직 이동)
"""
import re
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LectureContentsExtractor:
    """강의별 목차 및 콘텐츠 추출기"""
    
    def __init__(self, subject: str, config: Dict[str, Any] = None):
        """
        Args:
            subject: 과목명
            config: 설정 딕셔너리
        """
        self.subject = subject
        self.config = config or {}
        self.start_content_page = self.config.get('start_content_page', 8)
    
    def extract(
        self,
        all_ocr_data: List[Dict[str, Any]],
        lectures: List[Dict[str, Any]],
        parser: Any  # BaseParser 인스턴스
    ) -> List[Dict[str, Any]]:
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
        
        for lecture in lectures:
            lecture_id = lecture['lecture_id']
            lecture_page = lecture['page']
            
            # 실제 시작 페이지 찾기
            actual_start_page = self._find_actual_lecture_start_page(
                lecture_id,
                lecture['title'],
                all_ocr_data
            )
            
            if actual_start_page == -1:
                if lecture_page < self.start_content_page:
                    logger.warning(f"강의 {lecture_id}의 실제 시작 페이지를 찾지 못했습니다.")
                    continue
                else:
                    actual_start_page = lecture_page
            
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
            
            # 섹션 추출 (parser 사용)
            if hasattr(parser, 'extract_sections'):
                sections = parser.extract_sections(lecture_ocr_data)
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
        
        return lecture_contents
    
    def _match_content_to_sections(
        self,
        sections: List[Dict[str, Any]],
        content_paragraphs: List[Dict[str, Any]],
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        섹션별 content 매칭
        
        각 섹션에 해당하는 문단들을 찾아서 섹션의 content 필드에 할당
        """
        sections_with_content = []
        
        for section_idx, section in enumerate(sections):
            section_content = []
            section_page = section.get('page', 0)
            section_bbox = section.get('bbox', [0, 0, 0, 0])
            section_y = section_bbox[1] if len(section_bbox) > 1 else 0
            
            # 다음 섹션 찾기
            next_section = sections[section_idx + 1] if section_idx + 1 < len(sections) else None
            next_section_page = next_section.get('page', 9999) if next_section else 9999
            next_section_y = next_section.get('bbox', [0, 0, 0, 0])[1] if next_section and next_section.get('bbox') else 9999
            
            # 이전 섹션 찾기
            prev_section = sections[section_idx - 1] if section_idx > 0 else None
            prev_section_page = prev_section.get('page', 0) if prev_section else 0
            
            # 섹션 시작 페이지 결정
            section_start_page = max(prev_section_page + 1, section_page - 3) if prev_section else max(1, section_page - 3)
            
            # 문제 형식 패턴
            problem_patterns = [
                r'시하시오\.?$',
                r'적절하지 않은',
                r'설명으로 적절',
                r'적절한 것',
                r'고르고',
                r'서술하시오',
                r'^[①②③④⑤]',
                r'윗글에 대한',
                r'다음.*?설명으로',
                r'<보기>',
            ]
            
            # 작가 이름 패턴
            author_pattern = r'-\s*[가-힣]+\s*,\s*「[^」]+」'
            author_found = False
            
            # 섹션과 같은 페이지 또는 다음 섹션 전까지의 모든 문단 포함
            for para in content_paragraphs:
                para_text = para.get('text', '').strip()
                if not para_text:
                    continue
                
                # 특수 문자 제거
                para_text = re.sub(r'\(cid:\d+\)', '', para_text).strip()
                if not para_text or len(para_text) < 2:
                    continue
                
                # 불필요한 텍스트 제거
                exclude_patterns = [
                    r'^>>>\s*$',
                    r'^\d{4}학년도\s*$',
                    r'^\d{2}:\d{2}\s*$',
                    r'오후 \d{1,2}:\d{2}\s*$',
                    r'^\d{3} EBS\s*$',
                    r'^\[1부\]\s*$',
                ]
                if any(re.search(p, para_text) for p in exclude_patterns):
                    continue
                
                # 문제 형식 문단 제외
                is_problem_para = False
                for pattern in problem_patterns:
                    if re.search(pattern, para_text[:100]):
                        is_problem_para = True
                        break
                
                if is_problem_para:
                    continue
                
                # 작가 이름 패턴이 있으면 작가 정보까지만 포함
                is_work_para = False
                if re.search(author_pattern, para_text):
                    is_work_para = True
                
                if is_work_para:
                    author_match = re.search(author_pattern, para_text)
                    if author_match:
                        para_text = para_text[:author_match.end()].strip()
                        if not para_text:
                            author_found = True
                            continue
                        author_found = True
                elif author_found:
                    # 작가 정보 이후 문단은 모두 제외
                    continue
                
                para_page = para.get('page', 0)
                
                # 페이지 범위 체크
                if section_start_page <= para_page < next_section_page:
                    # 같은 페이지인 경우 y좌표 체크
                    if para_page == section_page:
                        para_y = para.get('y_start', 0)
                        
                        # 다음 섹션이 같은 페이지에 있으면 그 전까지만
                        if next_section and next_section.get('page') == section_page:
                            if para_y < next_section_y:
                                section_content.append(para_text)
                        else:
                            # 다음 섹션이 다른 페이지면 섹션 제목 아래 모든 문단 포함
                            if para_y >= section_y - 200:
                                section_content.append(para_text)
                    elif para_page < section_page:
                        # 섹션 이전 페이지의 문단도 포함
                        section_content.append(para_text)
                    else:
                        # 다른 페이지면 모두 포함
                        section_content.append(para_text)
                elif not next_section and para_page >= section_start_page:
                    # 마지막 섹션이면 이후 페이지의 모든 문단 포함
                    section_content.append(para_text)
            
            # 섹션 데이터 구성
            section_data = {
                "title": section.get('title', ''),
                "type": section.get('type', 'concept'),
                "page": section.get('page', 0),
                "content": section_content if section_content else []
            }
            
            sections_with_content.append(section_data)
        
        return sections_with_content
    
    def _find_actual_lecture_start_page(
        self,
        lecture_id: int,
        lecture_title: str,
        all_ocr_data: List[Dict[str, Any]]
    ) -> int:
        """실제 시작 페이지 찾기"""
        # 강의 번호 추출
        lecture_num_match = re.search(r'^(\d+)강', lecture_title)
        if not lecture_num_match:
            lecture_num_match = re.search(r'^(\d+)', lecture_title)
        
        if not lecture_num_match:
            return -1
        
        lecture_num = int(lecture_num_match.group(1))
        
        # 실제 콘텐츠 페이지에서 해당 번호 찾기
        for ocr_data in all_ocr_data:
            page_num = ocr_data.get('page_num', 0)
            if page_num < self.start_content_page:
                continue
            
            texts = ocr_data.get('text', [])
            if not texts:
                continue
            
            # 상위 20개 텍스트만 확인 (페이지 상단)
            for text in texts[:20]:
                cleaned = text.strip()
                if not cleaned:
                    continue
                
                # 강의 번호 매칭
                if cleaned == str(lecture_num):
                    return page_num
                if cleaned.startswith(f"{lecture_num} ") or cleaned.startswith(f"{lecture_num}강"):
                    return page_num
                if f"{lecture_num}강" in cleaned:
                    return page_num
        
        return -1
    
    def _find_lecture_page_range(
        self,
        lecture: Dict[str, Any],
        lectures: List[Dict[str, Any]],
        all_ocr_data: List[Dict[str, Any]],
        start_page: int
    ) -> tuple:
        """강의 페이지 범위 찾기"""
        lecture_id = lecture['lecture_id']
        next_lecture = next((l for l in lectures if l['lecture_id'] == lecture_id + 1), None)
        
        if next_lecture:
            # 다음 강의의 실제 시작 페이지 찾기
            next_actual_start = self._find_actual_lecture_start_page(
                next_lecture['lecture_id'],
                next_lecture['title'],
                all_ocr_data
            )
            
            if next_actual_start != -1 and next_actual_start > start_page:
                end_page = next_actual_start - 1
            else:
                next_page = next_lecture.get('page', 9999)
                if next_page > start_page:
                    end_page = next_page - 1
                else:
                    end_page = len(all_ocr_data)
        else:
            end_page = len(all_ocr_data)
        
        return start_page, end_page
