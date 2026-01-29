"""
섹션 추출기 테스트
"""
import pytest
from app.infrastructure.pdf.parsers.section_extractor import (
    ImprovedSectionExtractor,
    SectionExtractionResult
)
from app.infrastructure.pdf.parsers.base import BaseParser


class TestImprovedSectionExtractor:
    """개선된 섹션 추출기 테스트"""
    
    def test_extract_by_pattern_success(self):
        """패턴 매칭 성공 테스트"""
        config = {
            'concept_title_patterns': [r'^(\d+)\s*[\.]\s*([가-힣\s]{2,20})$'],
            'content_header_patterns': [r'작품으로 이해하기'],
            'start_content_page': 8
        }
        
        extractor = ImprovedSectionExtractor(config=config)
        
        ocr_data = [
            {
                'page_num': 8,
                'text': ['1.', '시적', '표현'],
                'top': [100, 100, 100],
                'left': [50, 80, 120],
                'width': [20, 30, 40],
                'height': [15, 15, 15]
            }
        ]
        
        result = extractor.extract(ocr_data)
        
        assert result.method in ['pattern', 'heuristic', 'combined']
        assert len(result.sections) > 0
        assert result.confidence >= 0.0
    
    def test_extract_fallback_when_pattern_fails(self):
        """패턴 실패 시 폴백 테스트"""
        config = {
            'concept_title_patterns': [],
            'content_header_patterns': [],
            'start_content_page': 8
        }
        
        extractor = ImprovedSectionExtractor(config=config)
        
        ocr_data = [
            {
                'page_num': 8,
                'text': ['임의', '텍스트'],
                'top': [100, 120],
                'left': [50, 50],
                'width': [50, 50],
                'height': [15, 15]
            }
        ]
        
        result = extractor.extract(ocr_data)
        
        assert result.method in ['heuristic', 'combined']
        assert result.sections is not None
        # 폴백이라도 최소한 빈 배열보다는 나음 (휴리스틱이 작동할 수 있음)
    
    def test_merge_sections(self):
        """섹션 병합 테스트"""
        config = {'start_content_page': 8}
        extractor = ImprovedSectionExtractor(config=config)
        
        sections1 = [
            {'title': '1. 시적 표현', 'type': 'concept', 'page': 8, 'bbox': [0, 0, 100, 20]}
        ]
        
        sections2 = [
            {'title': '2. 시의 형식', 'type': 'concept', 'page': 8, 'bbox': [0, 30, 100, 50]}
        ]
        
        merged = extractor._merge_sections(sections1, sections2)
        
        assert len(merged) == 2
        assert merged[0]['title'] == '1. 시적 표현'
        assert merged[1]['title'] == '2. 시의 형식'
    
    def test_merge_sections_duplicate_removal(self):
        """섹션 병합 시 중복 제거 테스트"""
        config = {'start_content_page': 8}
        extractor = ImprovedSectionExtractor(config=config)
        
        sections1 = [
            {'title': '1. 시적 표현', 'type': 'concept', 'page': 8, 'bbox': [0, 0, 100, 20]}
        ]
        
        sections2 = [
            {'title': '1. 시적 표현', 'type': 'concept', 'page': 8, 'bbox': [0, 0, 100, 20]}
        ]
        
        merged = extractor._merge_sections(sections1, sections2)
        
        assert len(merged) == 1  # 중복 제거됨
