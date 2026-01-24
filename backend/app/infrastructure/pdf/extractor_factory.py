"""
추출기 팩토리
OCR 추출기 생성 및 전환 로직 분리
"""
import logging
import multiprocessing as mp
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.infrastructure.pdf.extractors import PdfplumberExtractor, OCRExtractor
from app.core.config import settings

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """추출기 팩토리
    
    OCR 추출기 생성 및 pdfplumber → OCR 전환 판단 로직
    """
    
    @staticmethod
    def create_ocr_extractor(
        extractor_kwargs: Dict[str, Any],
        dpi: int = 300
    ) -> OCRExtractor:
        """OCRExtractor 생성
        
        Args:
            extractor_kwargs: 추출기 추가 옵션
            dpi: DPI 설정 (기본값: 300)
            
        Returns:
            OCRExtractor 인스턴스
        """
        ocr_kwargs = dict(extractor_kwargs)
        ocr_kwargs.setdefault('use_parallel', True)
        ocr_kwargs.setdefault('dpi', dpi)

        # 워커 수는 명시되면 그대로 사용, 없으면 CPU-1
        if ocr_kwargs.get('use_parallel') and ocr_kwargs.get('max_workers') is None:
            ocr_kwargs['max_workers'] = max(1, mp.cpu_count() - 1)

        # Tesseract 경로 자동 감지값이 있으면 기본 적용
        if ocr_kwargs.get('tesseract_cmd') is None and settings.TESSERACT_CMD:
            ocr_kwargs['tesseract_cmd'] = settings.TESSERACT_CMD

        max_workers = ocr_kwargs.get('max_workers')
        if ocr_kwargs.get('use_parallel') and max_workers:
            logger.info(f"[ExtractorFactory] 병렬 처리: {max_workers}개 워커로 OCR 실행")

        return OCRExtractor(**ocr_kwargs)
    
    @staticmethod
    def should_switch_to_ocr(sample_ocr_data: List[Dict[str, Any]]) -> bool:
        """pdfplumber 결과가 빈약/깨졌으면 OCR로 전환
        
        Args:
            sample_ocr_data: pdfplumber 샘플 추출 결과
            
        Returns:
            True면 OCR로 전환, False면 pdfplumber 유지
        """
        if not sample_ocr_data:
            return True

        pages = len(sample_ocr_data)
        nonempty_pages = 0
        word_count = 0
        cid_tokens = 0

        for page in sample_ocr_data:
            texts = page.get('text', []) or []
            if texts:
                nonempty_pages += 1
            word_count += len(texts)
            cid_tokens += sum(1 for t in texts if "(cid:" in str(t))

        # 텍스트 레이어가 사실상 없으면 OCR로
        if nonempty_pages == 0:
            return True

        # 샘플 대비 텍스트가 거의 없으면 OCR로 (스캔본 가능성)
        if pages >= 3 and word_count < 30:
            return True

        # CID 쓰레기 비율이 높으면 OCR로 (텍스트 추출 깨짐)
        if word_count > 0 and (cid_tokens / max(word_count, 1)) > 0.35:
            return True

        return False
