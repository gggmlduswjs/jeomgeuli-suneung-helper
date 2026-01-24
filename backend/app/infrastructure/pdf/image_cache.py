"""
이미지 캐시
페이지별 이미지 재사용으로 성능 최적화
"""
import logging
from typing import Dict, Optional, Callable
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


class ImageCache:
    """페이지별 이미지 캐시
    
    동일한 페이지를 여러 번 렌더링하지 않도록 캐싱
    """
    
    def __init__(
        self,
        render_page_fn: Optional[Callable[[Path, int], Optional[Image.Image]]] = None
    ):
        """
        Args:
            render_page_fn: PDF 페이지 렌더링 함수 (pdf_path, page_num) -> Image
        """
        self.render_page_fn = render_page_fn
        self._cache: Dict[int, Image.Image] = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_page_image(
        self,
        pdf_path: Path,
        page_num: int,
        ocr_data: list,
        fallback_to_ocr: bool = True
    ) -> Optional[Image.Image]:
        """페이지 이미지 가져오기 (캐싱 지원)
        
        Args:
            pdf_path: PDF 파일 경로
            page_num: 페이지 번호
            ocr_data: OCR 데이터 (페이지 경로 정보 포함)
            fallback_to_ocr: OCR 이미지 경로를 먼저 확인할지 여부
            
        Returns:
            PIL.Image 또는 None
        """
        # 캐시 확인
        if page_num in self._cache:
            self._cache_hits += 1
            logger.debug(f"[ImageCache] 캐시 히트: 페이지 {page_num}")
            return self._cache[page_num]
        
        # OCR 데이터에서 페이지 이미지 경로 찾기
        if fallback_to_ocr:
            page_image_path = None
            for ocr_page in ocr_data:
                if ocr_page.get('page_num') == page_num:
                    page_image_path = ocr_page.get('page_path')
                    break
            
            # OCR 이미지가 있으면 사용
            if page_image_path and Path(page_image_path).exists():
                try:
                    image = Image.open(page_image_path)
                    # 캐시에 저장
                    self._cache[page_num] = image
                    self._cache_misses += 1
                    logger.debug(f"[ImageCache] OCR 이미지 로드 및 캐시: 페이지 {page_num}")
                    return image
                except Exception as e:
                    logger.warning(f"[ImageCache] OCR 이미지 로드 실패: {e}")
        
        # OCR 이미지가 없으면 PDF에서 렌더링
        if self.render_page_fn:
            self._cache_misses += 1
            logger.debug(f"[ImageCache] PDF 렌더링 및 캐시: 페이지 {page_num}")
            page_image = self.render_page_fn(pdf_path, int(page_num))
            if page_image:
                # 캐시에 저장
                self._cache[page_num] = page_image
                return page_image
            else:
                logger.warning(f"[ImageCache] 페이지 {page_num} 렌더링 실패")
                return None
        
        logger.warning(f"[ImageCache] 페이지 {page_num} 이미지를 가져올 수 없음 (렌더링 함수 없음)")
        return None
    
    def clear(self):
        """캐시 초기화"""
        cache_size = len(self._cache)
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.debug(f"[ImageCache] 캐시 초기화: {cache_size}개 이미지 제거")
    
    def get_stats(self) -> Dict[str, int]:
        """캐시 통계 반환
        
        Returns:
            {
                'cache_size': 캐시된 이미지 수,
                'cache_hits': 캐시 히트 수,
                'cache_misses': 캐시 미스 수,
                'hit_rate': 히트율 (0.0-1.0)
            }
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests) if total_requests > 0 else 0.0
        
        return {
            'cache_size': len(self._cache),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': hit_rate
        }
