"""
강의 제목 검증기
TOC 텍스트를 활용한 강의 제목 검증 및 보정
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class LectureTitleValidator:
    """TOC 텍스트를 활용한 강의 제목 검증 및 보정"""
    
    def __init__(
        self,
        toc_text: Optional[str] = None,
        toc_lecture_list: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Args:
            toc_text: 전체 목차 텍스트
            toc_lecture_list: 강의 목록 (페이지 정보 포함)
        """
        self.toc_text = toc_text or ""
        self.toc_lecture_list = toc_lecture_list or []
        
        # TOC에서 강의 제목 키워드 추출
        self.lecture_keywords = self._extract_keywords()
        
        # 강의 ID별 제목 맵 생성
        self.lecture_title_map = {
            l.get('lecture_id'): l.get('title', '')
            for l in self.toc_lecture_list
            if l.get('lecture_id') is not None
        }
    
    def _extract_keywords(self) -> Dict[int, List[str]]:
        """TOC 텍스트에서 강의별 키워드 추출"""
        keywords_map = {}
        
        if not self.toc_text:
            return keywords_map
        
        # TOC 텍스트를 줄 단위로 분석
        lines = self.toc_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 강의 번호 추출
            lecture_num_match = re.search(r'^(\d+)강', line)
            if not lecture_num_match:
                continue
            
            lecture_num = int(lecture_num_match.group(1))
            
            # 제목 부분 추출 (강의 번호 제외)
            title_part = re.sub(r'^\d+강\s*[|]\s*', '', line).strip()
            title_part = re.sub(r'\s+\d{3}$', '', title_part)  # 페이지 번호 제거
            
            # 키워드 추출 (2글자 이상 한글)
            keywords = re.findall(r'[가-힣]{2,}', title_part)
            
            if keywords:
                keywords_map[lecture_num] = keywords
        
        return keywords_map
    
    def validate_lecture_title(
        self,
        extracted_title: str,
        page_num: int,
        lecture_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str], float]:
        """추출된 강의 제목 검증 및 보정
        
        Args:
            extracted_title: 추출된 강의 제목
            page_num: 페이지 번호
            lecture_id: 강의 ID (있는 경우)
            
        Returns:
            (유효성, 보정된 제목, 신뢰도) 튜플
        """
        if not self.toc_text and not self.toc_lecture_list:
            return (False, None, 0.0)
        
        # 방법 1: lecture_id로 직접 매칭
        if lecture_id and lecture_id in self.lecture_title_map:
            expected_title = self.lecture_title_map[lecture_id]
            similarity = self._calculate_similarity(extracted_title, expected_title)
            
            if similarity > 0.7:
                return (True, expected_title, similarity)
            elif similarity > 0.5:
                return (False, expected_title, similarity)
        
        # 방법 2: 페이지 번호로 예상 강의 찾기
        expected_lecture = self._find_expected_lecture_by_page(page_num)
        if expected_lecture:
            expected_title = expected_lecture.get('title', '')
            similarity = self._calculate_similarity(extracted_title, expected_title)
            
            if similarity > 0.7:
                return (True, expected_title, similarity)
            elif similarity > 0.5:
                return (False, expected_title, similarity)
        
        # 방법 3: 강의 번호로 키워드 매칭
        lecture_num_match = re.search(r'^(\d+)', extracted_title)
        if lecture_num_match:
            lecture_num = int(lecture_num_match.group(1))
            if lecture_num in self.lecture_keywords:
                expected_keywords = self.lecture_keywords[lecture_num]
                extracted_keywords = re.findall(r'[가-힣]{2,}', extracted_title)
                
                # 키워드 일치도 계산
                common_keywords = set(expected_keywords) & set(extracted_keywords)
                if common_keywords:
                    match_ratio = len(common_keywords) / max(len(expected_keywords), 1)
                    if match_ratio > 0.5:
                        # TOC에서 정확한 제목 찾기
                        for lecture in self.toc_lecture_list:
                            if lecture.get('lecture_id') == lecture_num:
                                return (True, lecture.get('title', extracted_title), match_ratio)
        
        return (False, None, 0.0)
    
    def suggest_lecture_title(
        self,
        page_num: int,
        lecture_id: Optional[int] = None
    ) -> Optional[str]:
        """페이지 번호로 예상 강의 제목 제안
        
        Args:
            page_num: 페이지 번호
            lecture_id: 강의 ID (있는 경우)
            
        Returns:
            예상 강의 제목 또는 None
        """
        # lecture_id로 직접 조회
        if lecture_id and lecture_id in self.lecture_title_map:
            return self.lecture_title_map[lecture_id]
        
        # 페이지 번호로 예상 강의 찾기
        expected_lecture = self._find_expected_lecture_by_page(page_num)
        if expected_lecture:
            return expected_lecture.get('title')
        
        return None
    
    def _find_expected_lecture_by_page(
        self,
        page_num: int
    ) -> Optional[Dict[str, Any]]:
        """페이지 번호로 예상 강의 찾기"""
        if not self.toc_lecture_list:
            return None
        
        # 페이지 범위로 강의 찾기
        for lecture in self.toc_lecture_list:
            start_page = lecture.get('start_page')
            end_page = lecture.get('end_page')
            
            if start_page is not None:
                if end_page is not None:
                    if start_page <= page_num <= end_page:
                        return lecture
                else:
                    # end_page가 없으면 다음 강의 시작 전까지
                    next_lecture = self._find_next_lecture(lecture.get('lecture_id'))
                    if next_lecture:
                        next_start = next_lecture.get('start_page')
                        if next_start and page_num < next_start:
                            return lecture
                    elif page_num >= start_page:
                        # 마지막 강의인 경우
                        return lecture
        
        return None
    
    def _find_next_lecture(
        self,
        current_lecture_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """다음 강의 찾기"""
        if current_lecture_id is None:
            return None
        
        for lecture in self.toc_lecture_list:
            if lecture.get('lecture_id') == current_lecture_id + 1:
                return lecture
        
        return None
    
    def _calculate_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """두 텍스트의 유사도 계산 (0.0-1.0)"""
        if not text1 or not text2:
            return 0.0
        
        # 정규화: 강의 번호, 특수문자 제거
        def normalize(text: str) -> str:
            # 강의 번호 제거
            text = re.sub(r'^\d+강\s*[|]?\s*', '', text)
            # 특수문자 제거
            text = re.sub(r'[^\w\s가-힣]', '', text)
            return text.strip()
        
        norm1 = normalize(text1)
        norm2 = normalize(text2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # SequenceMatcher로 유사도 계산
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # 키워드 기반 보정
        words1 = set(re.findall(r'[가-힣]{2,}', norm1))
        words2 = set(re.findall(r'[가-힣]{2,}', norm2))
        
        if words1 and words2:
            common_words = words1 & words2
            word_similarity = len(common_words) / max(len(words1), len(words2))
            # 두 유사도의 평균
            similarity = (similarity + word_similarity) / 2.0
        
        return similarity
