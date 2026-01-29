"""
템플릿 매니저 테스트
"""
import pytest
import tempfile
from pathlib import Path
import json

from app.infrastructure.pdf.parsers.template_manager import TemplateManager
from app.infrastructure.pdf.parsers.template import ParsingTemplate


class TestTemplateManager:
    """TemplateManager 테스트"""
    
    def test_match_ebs_literature_template(self):
        """EBS 문학 교재 템플릿 매칭 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / "templates"
            manager = TemplateManager(template_dir=template_dir)
            
            # 테스트 템플릿 생성
            template = ParsingTemplate(
                name="ebs_수능특강_문학_2026",
                subject="literature",
                version="2026",
                description="EBS 수능특강 문학 2026",
                patterns={
                    "lecture_title_patterns": [
                        r'^\d+강\s+[가-힣]+',
                        r'^\d+\s+[가-힣]+'
                    ],
                    "toc_lecture_patterns": [
                        r'^\d+강\s*\|\s*[가-힣]'
                    ],
                    "problem_number_pattern": r'^\d{2}$'
                },
                config={
                    "toc_end_page": 7,
                    "start_content_page": 8,
                    "paragraph_y_threshold": 25
                },
                confidence=0.85
            )
            
            manager.add_template(template)
            
            # 테스트 텍스트
            sample_text = """1강 | 시의 표현과 형식
2강 | 시의 내용
01
02"""
            
            result = manager.match_template(
                pdf_text=sample_text,
                subject="literature",
                threshold=0.85
            )
            
            assert result is not None
            template_matched, confidence = result
            assert template_matched.name == "ebs_수능특강_문학_2026"
            assert confidence > 0.85
    
    def test_no_match_returns_none(self):
        """매칭 실패 시 None 반환 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / "templates"
            manager = TemplateManager(template_dir=template_dir)
            
            random_text = "완전히 다른 형식의 문서입니다."
            
            result = manager.match_template(
                pdf_text=random_text,
                subject="literature",
                threshold=0.85
            )
            
            assert result is None
    
    def test_template_caching(self):
        """템플릿 매칭 캐싱 테스트"""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_dir = Path(tmpdir) / "templates"
            manager = TemplateManager(template_dir=template_dir, enable_cache=True)
            
            # 템플릿 추가
            template = ParsingTemplate(
                name="test_template",
                subject="literature",
                patterns={
                    "lecture_title_patterns": [r'^\d+강']
                },
                confidence=0.9
            )
            manager.add_template(template)
            
            sample_text = "1강 테스트"
            book_id = "test_book_123"
            
            # 첫 번째 매칭
            result1 = manager.match_template(
                pdf_text=sample_text,
                subject="literature",
                book_id=book_id
            )
            
            # 두 번째 매칭 (캐시에서 가져와야 함)
            result2 = manager.match_template(
                pdf_text=sample_text,
                subject="literature",
                book_id=book_id
            )
            
            assert result1 is not None
            assert result2 is not None
            assert result1[0].name == result2[0].name
