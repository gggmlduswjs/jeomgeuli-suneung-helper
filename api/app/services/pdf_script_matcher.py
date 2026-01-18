"""
PDF-강의대본 매칭 서비스
강의대본에서 추출한 PDF 참조 정보와 실제 PDF 내용을 매칭
"""
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class PDFScriptMatcher:
    """PDF-강의대본 매칭기"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def match_references(
        self, 
        pdf_references: List[Dict], 
        pdf_content: Optional[Dict] = None
    ) -> List[Dict]:
        """
        PDF 참조 정보와 실제 PDF 내용 매칭
        
        Args:
            pdf_references: 강의대본에서 추출한 PDF 참조 정보 리스트
            pdf_content: PDF 파싱 결과 (선택)
            
        Returns:
            매칭된 참조 정보 리스트 (신뢰도 포함)
        """
        matched_refs = []
        
        for ref in pdf_references:
            ref_type = ref.get('type')
            
            if ref_type == 'problem':
                # 문제 번호 매칭
                matched = self._match_problem(ref, pdf_content)
            elif ref_type == 'page':
                # 페이지 번호 매칭
                matched = self._match_page(ref, pdf_content)
            elif ref_type == 'section':
                # 섹션 이름 매칭
                matched = self._match_section(ref, pdf_content)
            else:
                matched = ref.copy()
                matched['confidence'] = 0.0
                matched['matched'] = False
            
            matched_refs.append(matched)
        
        return matched_refs
    
    def _match_problem(self, ref: Dict, pdf_content: Optional[Dict]) -> Dict:
        """
        문제 번호 매칭
        
        Args:
            ref: 참조 정보 {'type': 'problem', 'number': 1, ...}
            pdf_content: PDF 파싱 결과
            
        Returns:
            매칭 결과 (신뢰도 포함)
        """
        result = ref.copy()
        result['matched'] = False
        result['confidence'] = 0.0
        
        if not pdf_content:
            return result
        
        # PDF에서 문제 찾기
        problem_number = ref.get('number')
        
        # PDF 구조에서 문제 번호 검색
        # 실제 구현은 PDF 파싱 결과 구조에 따라 달라짐
        if 'lessons' in pdf_content:
            for lesson in pdf_content['lessons']:
                if 'units' in lesson:
                    for unit in lesson['units']:
                        # 문제 번호 추출 시도
                        unit_title = unit.get('title', '')
                        if f'{problem_number}번' in unit_title or f'문제 {problem_number}' in unit_title:
                            result['matched'] = True
                            result['confidence'] = 0.9
                            result['matched_unit_id'] = unit.get('unit_id')
                            result['matched_lesson_id'] = lesson.get('lesson_id')
                            break
        
        return result
    
    def _match_page(self, ref: Dict, pdf_content: Optional[Dict]) -> Dict:
        """
        페이지 번호 매칭
        
        Args:
            ref: 참조 정보 {'type': 'page', 'number': 15, ...}
            pdf_content: PDF 파싱 결과
            
        Returns:
            매칭 결과 (신뢰도 포함)
        """
        result = ref.copy()
        result['matched'] = False
        result['confidence'] = 0.0
        
        if not pdf_content:
            return result
        
        page_number = ref.get('number')
        
        # PDF에서 페이지 찾기
        # 실제 구현은 PDF 파싱 결과 구조에 따라 달라짐
        # 여기서는 간단한 구현만 제공
        
        return result
    
    def _match_section(self, ref: Dict, pdf_content: Optional[Dict]) -> Dict:
        """
        섹션 이름 매칭
        
        Args:
            ref: 참조 정보 {'type': 'section', 'name': '고전시가', ...}
            pdf_content: PDF 파싱 결과
            
        Returns:
            매칭 결과 (신뢰도 포함)
        """
        result = ref.copy()
        result['matched'] = False
        result['confidence'] = 0.0
        
        if not pdf_content:
            return result
        
        section_name = ref.get('name', '')
        
        # 섹션 이름 정규화
        normalized_name = self._normalize_section_name(section_name)
        
        # PDF에서 섹션 찾기
        if 'lessons' in pdf_content:
            for lesson in pdf_content['lessons']:
                lesson_title = lesson.get('title', '')
                if normalized_name in lesson_title or self._fuzzy_match(normalized_name, lesson_title):
                    result['matched'] = True
                    result['confidence'] = 0.8
                    result['matched_lesson_id'] = lesson.get('lesson_id')
                    break
        
        return result
    
    def _normalize_section_name(self, name: str) -> str:
        """섹션 이름 정규화"""
        # 공백 제거
        normalized = re.sub(r'\s+', '', name)
        
        # 매핑 테이블
        mappings = {
            '교과서개념': '교과서 개념',
            '고전시가': '고전시가',
            '현대시': '현대시',
            '고전산문': '고전 산문',
            '현대소설': '현대 소설',
            '극수필': '극 수필',
            '갈래복합': '갈래 복합',
            '실전': '실전',
        }
        
        return mappings.get(normalized, name)
    
    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """퍼지 매칭 (간단한 구현)"""
        pattern_lower = pattern.lower()
        text_lower = text.lower()
        
        # 부분 문자열 매칭
        if pattern_lower in text_lower:
            return True
        
        # 단어 단위 매칭
        pattern_words = set(re.findall(r'[가-힣]+', pattern_lower))
        text_words = set(re.findall(r'[가-힣]+', text_lower))
        
        if pattern_words and text_words:
            overlap = len(pattern_words & text_words)
            if overlap >= len(pattern_words) * 0.5:  # 50% 이상 겹치면 매칭
                return True
        
        return False
    
    def calculate_confidence(self, ref: Dict, match_result: Dict) -> float:
        """
        매칭 신뢰도 계산
        
        Args:
            ref: 원본 참조 정보
            match_result: 매칭 결과
            
        Returns:
            신뢰도 (0.0 ~ 1.0)
        """
        if not match_result.get('matched'):
            return 0.0
        
        confidence = 0.5  # 기본 신뢰도
        
        # 참조 타입에 따른 가중치
        ref_type = ref.get('type')
        if ref_type == 'problem':
            # 문제 번호는 정확도가 높음
            confidence = 0.9
        elif ref_type == 'page':
            # 페이지 번호도 비교적 정확
            confidence = 0.8
        elif ref_type == 'section':
            # 섹션 이름은 퍼지 매칭이므로 낮음
            confidence = 0.7
        
        # 컨텍스트 정보가 있으면 신뢰도 증가
        if ref.get('context'):
            confidence += 0.1
        
        return min(1.0, confidence)
