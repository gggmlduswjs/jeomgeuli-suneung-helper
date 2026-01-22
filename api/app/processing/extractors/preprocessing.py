"""
통합 이미지 전처리 모듈
OCR 정확도 향상을 위한 이미지 전처리 기능 (image_processor.py + ocr_extractor.py 통합)
"""
import logging
from pathlib import Path
from typing import Optional
from PIL import Image, ImageEnhance
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """통합 이미지 전처리 클래스"""

    @staticmethod
    def preprocess_for_ocr(
        image: Image.Image,
        method: str = 'balanced'
    ) -> Image.Image:
        """
        OCR 정확도 향상을 위한 통합 이미지 전처리

        Args:
            image: 원본 이미지
            method: 전처리 강도
                - 'fast': 기본 전처리 (RGB 처리 + 그레이스케일 + 대비/선명도)
                - 'balanced': fast + 이진화 (기본값, 권장)
                - 'aggressive': balanced + 형태학 연산 + 기울기 보정

        Returns:
            전처리된 이미지
        """
        # 1. RGBA → RGB 변환 (투명 배경 처리)
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3] if len(image.split()) == 4 else None)
            image = background
        elif image.mode != 'RGB' and image.mode != 'L':
            image = image.convert('RGB')

        # 2. 크기 확인 (너무 작으면 확대)
        min_size = 1000
        if image.width < min_size or image.height < min_size:
            scale = max(min_size / image.width, min_size / image.height)
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 3. Grayscale 변환
        gray = image.convert('L') if image.mode != 'L' else image

        # 4. 대비 향상
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(1.3)

        # 5. 선명도 향상
        enhancer = ImageEnhance.Sharpness(gray)
        gray = enhancer.enhance(1.2)

        if method == 'fast':
            return gray

        # 6. 이진화 (Otsu thresholding) - balanced 이상
        img_array = np.array(gray)
        _, binary = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        if method == 'balanced':
            return Image.fromarray(binary)

        # 7. 노이즈 제거 (morphological operations) - aggressive
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

        # 8. 스캔 기울기 보정 (deskew) - aggressive
        try:
            edges = cv2.Canny(cleaned, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

            if lines is not None:
                angles = []
                for rho, theta in lines[:10]:  # 상위 10개 선만
                    angle = np.degrees(theta) - 90
                    if -45 < angle < 45:  # 기울기 범위 제한
                        angles.append(angle)

                if angles:
                    angle = np.median(angles)
                    center = (cleaned.shape[1] // 2, cleaned.shape[0] // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                    cleaned = cv2.warpAffine(
                        cleaned, rotation_matrix,
                        (cleaned.shape[1], cleaned.shape[0]),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )
        except Exception as e:
            logger.debug(f"기울기 보정 실패 (무시): {e}")

        return Image.fromarray(cleaned)

    @staticmethod
    def process_and_save_image(
        image: Image.Image,
        page_num: int,
        output_dir: Path,
        method: str = 'balanced'
    ) -> Image.Image:
        """
        이미지 전처리 및 저장

        Args:
            image: 원본 이미지
            page_num: 페이지 번호
            output_dir: 저장 디렉토리
            method: 전처리 강도 ('fast', 'balanced', 'aggressive')

        Returns:
            전처리된 이미지
        """
        # 디렉토리 생성 (병렬 처리 안전)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, FileExistsError):
            pass

        # 전처리
        processed_image = ImagePreprocessor.preprocess_for_ocr(image, method=method)

        # 저장 (재시도 로직)
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
                import time
                time.sleep(0.1 * (attempt + 1))

        return processed_image
