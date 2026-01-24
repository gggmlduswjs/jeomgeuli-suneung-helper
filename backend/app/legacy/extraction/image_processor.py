"""
이미지 전처리 모듈
OCR 정확도 향상을 위한 이미지 전처리 기능
"""
import logging
from pathlib import Path
from typing import Optional
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)


class ImageProcessor:
    """이미지 전처리 클래스"""
    
    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """
        이미지 전처리 (OCR 정확도 향상)
        
        Args:
            image: 원본 이미지
            
        Returns:
            전처리된 이미지
        """
        # 원본은 RGB로 유지 (한글 OCR에 더 좋을 수 있음)
        if image.mode == 'RGBA':
            # 투명 배경을 흰색으로 변환
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3] if len(image.split()) == 4 else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 크기 확인 (너무 작으면 확대)
        min_size = 1000
        if image.width < min_size or image.height < min_size:
            scale = max(min_size / image.width, min_size / image.height)
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Grayscale 변환 (한글 OCR은 RGB가 더 나을 수도 있지만, 전처리용으로는 grayscale도 좋음)
        gray = image.convert('L') if image.mode != 'L' else image
        
        # 대비 향상 (한글 텍스트 가독성 향상)
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(1.3)  # 1.2 → 1.3 (더 강하게)
        
        # 선명도 향상
        enhancer = ImageEnhance.Sharpness(gray)
        gray = enhancer.enhance(1.2)  # 1.1 → 1.2 (더 강하게)
        
        return gray
    
    @staticmethod
    def process_and_save_image(
        image: Image.Image,
        page_num: int,
        output_dir: Path
    ) -> Image.Image:
        """
        이미지 전처리 및 저장

        Args:
            image: 원본 이미지
            page_num: 페이지 번호
            output_dir: 저장 디렉토리

        Returns:
            전처리된 이미지
        """
        # 디렉토리는 이미 생성되어 있어야 함 (병렬 처리 시 중복 생성 방지)
        # 혹시 모를 경우를 대비해 한 번 더 확인
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, FileExistsError):
            # 이미 존재하거나 다른 스레드가 생성 중이면 무시
            pass

        # 전처리
        processed_image = ImageProcessor.preprocess_image(image)

        # 저장 (재시도 로직 추가)
        image_path = output_dir / f"page_{page_num:03d}.png"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                processed_image.save(image_path)
                break
            except OSError as e:
                if attempt == max_retries - 1:
                    logger.error(f"이미지 저장 실패 (페이지 {page_num}): {e}")
                    raise
                # 짧은 대기 후 재시도
                import time
                time.sleep(0.1 * (attempt + 1))

        return processed_image
