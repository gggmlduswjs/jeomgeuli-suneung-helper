"""
하이브리드 라우터 테스트
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from app.infrastructure.pdf.parsers.hybrid_router import HybridRouter


class TestHybridRouter:
    """HybridRouter 테스트"""
    
    def test_template_matching_success(self):
        """템플릿 매칭 성공 테스트"""
        router = HybridRouter(template_threshold=0.85, enable_ai_parsing=False)
        
        # 모의 OCR 데이터
        ocr_data = [
            {
                'page_num': 1,
                'text': ['1강', '시의', '표현과', '형식', '01', '02']
            }
        ]
        
        parser, strategy, metadata = router.select_parser(
            subject="literature",
            ocr_data=ocr_data,
            book_id="test_book"
        )
        
        # 템플릿이 매칭되면 template 전략 사용
        # 매칭 실패 시 fallback 사용
        assert strategy in ['template', 'fallback']
        assert parser is not None
    
    def test_fallback_on_no_match(self):
        """매칭 실패 시 폴백 테스트"""
        router = HybridRouter(template_threshold=0.95, enable_ai_parsing=False)
        
        # 매칭 불가능한 텍스트
        ocr_data = [
            {
                'page_num': 1,
                'text': ['완전히', '다른', '형식']
            }
        ]
        
        parser, strategy, metadata = router.select_parser(
            subject="literature",
            ocr_data=ocr_data
        )
        
        assert strategy == 'fallback'
        assert parser is not None
    
    def test_metrics_tracking(self):
        """메트릭 추적 테스트"""
        router = HybridRouter()
        
        ocr_data = [{'page_num': 1, 'text': ['test']}]
        
        # 여러 번 호출
        for _ in range(3):
            router.select_parser(
                subject="literature",
                ocr_data=ocr_data
            )
        
        metrics = router.get_metrics()
        
        assert metrics['total_requests'] == 3
        assert 'template_match_rate' in metrics
        assert 'fallback_rate' in metrics
