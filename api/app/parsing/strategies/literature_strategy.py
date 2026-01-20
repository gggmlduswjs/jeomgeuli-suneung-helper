"""
문학 과목 파싱 전략
"""
import re
import logging
from typing import List, Dict, Any

from .base_strategy import BaseParsingStrategy
from ..utils import group_texts_by_line, matches_patterns

logger = logging.getLogger(__name__)


class LiteratureParsingStrategy(BaseParsingStrategy):
    """문학 과목 파싱 전략"""
    
    def extract_lectures(self, all_ocr_data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        문학 강의 목록 추출
        
        Args:
            all_ocr_data: OCR 데이터 리스트
            config: 과목별 설정
            
        Returns:
            강의 리스트
        """
        lectures = []
        lecture_id = 1
        patterns = config.get('lecture_title_patterns', [])
        START_CONTENT_PAGE = config.get('start_content_page', 8)
        
        # 각 페이지에서 강의 제목 찾기
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts or len([t for t in texts if t.strip()]) == 0:
                continue
            
            # y좌표 기준으로 같은 줄의 단어들을 그룹화
            lines = group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 페이지 상단 영역 체크
            page_top_threshold = None
            if lines and len(lines) > 0 and len(lines[0]) > 0:
                first_line_y = lines[0][0]['top']
                if lines and len(lines[-1]) > 0:
                    last_line = lines[-1]
                    estimated_page_height = last_line[-1]['top'] + last_line[-1]['height']
                    page_top_threshold = first_line_y + (estimated_page_height * 0.4)
            
            # 평균 폰트 크기 계산
            min_title_height = 0
            if lines:
                total_height = sum(word['height'] for line in lines[:10] for word in line[:3])
                total_words = sum(len(line[:3]) for line in lines[:10])
                if total_words > 0:
                    avg_height = total_height / min(30, total_words)
                    min_title_height = avg_height * 1.0
            
            for line in lines:
                line_text = " ".join([word['text'] for word in line]).strip()
                
                if not line_text or len(line_text) < 5:
                    continue
                
                # 목차 형식 제외
                if re.search(r'\d{3,}', line_text) and len(line_text) < 50:
                    continue
                
                # 작품 제목 형식 제외
                if re.search(r'\([가-힣]+\)', line_text) and len(line_text) < 40:
                    continue
                
                # 문제 번호/지문 제외 (더 관대하게 수정)
                # 2자리 숫자로 시작하지만 "N강" 형식이 아니고, 텍스트가 매우 긴 경우만 제외
                if re.match(r'^\d{2,}\s+[가-힣]', line_text) and not re.search(r'^\d+강', line_text):
                    # 텍스트가 매우 긴 경우만 문제 지문으로 간주 (50자 이상)
                    if len(line_text) > 50:
                        continue
                
                # 매우 긴 텍스트는 문제 지문일 가능성이 높음
                if len(line_text) > 80 and re.match(r'^\d{2,}\s+[가-힣]{10,}', line_text) and not re.search(r'^\d+강', line_text):
                    continue
                
                # 페이지 상단 영역 체크
                line_y = line[0]['top']
                if page_top_threshold and line_y > page_top_threshold * 0.8:
                    continue
                
                # 큰 폰트 체크
                line_height = max(word['height'] for word in line)
                if min_title_height > 0 and line_height < min_title_height * 0.9:
                    continue
                
                # 패턴 매칭
                if matches_patterns(line_text, patterns):
                    # 강의 제목 검증: "N강" 또는 "작품으로 이해하기 N" 또는 "NN 장르명" 형식
                    # 검증을 완화하여 다양한 형식 허용 (OCR 오인식 대응)
                    is_valid_lecture = (
                        re.search(r'^\d+강', line_text) or  # "1강 |", "2강" 등
                        re.search(r'작품으로\s*이해하기\s*\d+', line_text) or  # "작품으로 이해하기 4"
                        re.search(r'^\d{2}\s+[가-힣]+', line_text) or  # "01 고전 시가", "02 현대시" 등 (공백 필수)
                        re.search(r'^\d{2}[가-힣]+', line_text) or  # "01고전시가" (공백 없이도 허용)
                        # 추가 패턴: 숫자로 시작하고 한글이 포함된 경우 (더 관대하게)
                        (re.match(r'^\d+', line_text) and re.search(r'[가-힣]', line_text) and len(line_text) >= 3 and len(line_text) <= 50)
                    )
                    if not is_valid_lecture:
                        # 디버깅: 왜 필터링되었는지 로그 (패턴 매칭은 되었지만 검증 실패)
                        if len(line_text) < 50 and re.match(r'^\d+', line_text):
                            print(f"    [필터링] 강의 제목 검증 실패: '{line_text[:40]}' (페이지 {page_num})")
                        continue
                    
                    # 문제/해설 페이지 제외
                    if page_num > 200:
                        if any(keyword in line_text for keyword in ["정답", "해설", "답", "문제", "보기"]):
                            continue
                        if not re.search(r'^\d+강\s*[|]', line_text) and len(line_text) < 20:
                            continue
                    
                    # bbox 계산
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    lectures.append({
                        "lecture_id": lecture_id,
                        "title": line_text,
                        "page": page_num,
                        "bbox": [left, top, right, bottom]
                    })
                    lecture_id += 1
                    logger.info(f"강의 발견: {line_text[:50]} (페이지 {page_num})")
        
        return lectures
    
    def extract_problems(self, all_ocr_data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        문학 문제 목록 추출
        
        Args:
            all_ocr_data: OCR 데이터 리스트
            config: 과목별 설정
            
        Returns:
            문제 리스트
        """
        problems = []
        problem_pattern = config.get('problem_number_pattern', r'^\d{2}$')
        START_CONTENT_PAGE = config.get('start_content_page', 8)
        
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            
            if page_num < START_CONTENT_PAGE:
                continue
            
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            lines = group_texts_by_line(texts, tops, lefts, widths, heights)
            
            for line in lines:
                line_text = " ".join([word['text'] for word in line]).strip()
                
                # 문제 번호 패턴 매칭
                if re.match(problem_pattern, line_text):
                    # bbox 계산
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    problem_id = line_text.strip()
                    problems.append({
                        "problem_id": problem_id,
                        "page": page_num,
                        "bbox": [left, top, right, bottom]
                    })
                    logger.debug(f"문제 발견: {problem_id} (페이지 {page_num})")
        
        return problems
