"""
통합 텍스트 추출기
extraction/extractors.py를 processing/으로 이동 및 통합
"""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image

logger = logging.getLogger(__name__)

# PDF 추출 라이브러리 import
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pytesseract
    from pytesseract import Output
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class TextExtractor(ABC):
    """
    텍스트 추출기 기본 인터페이스

    모든 추출기는 동일한 OCR 형식의 데이터를 반환해야 함:
    {
        'page_num': int,
        'text': List[str],
        'left': List[int],
        'top': List[int],
        'width': List[int],
        'height': List[int],
        'color': List[tuple]  # Optional
    }
    """

    @abstractmethod
    def extract(self, source: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        텍스트 추출

        Args:
            source: PDF 경로 또는 이미지 리스트
            **kwargs: 추가 옵션

        Returns:
            OCR 형식의 데이터 리스트 (페이지별)
        """
        pass


class PdfplumberExtractor(TextExtractor):
    """
    pdfplumber 기반 텍스트 추출기

    텍스트 레이어가 있는 PDF에 최적화
    - 빠름
    - 정확함
    - 좌표계: PDF 포인트 (72 DPI) → 이미지 픽셀 (DPI) 변환
    """

    def __init__(self, dpi: int = 200, max_pages: Optional[int] = None):
        """
        Args:
            dpi: 이미지 DPI (좌표 변환용)
            max_pages: 최대 처리 페이지 수
        """
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber가 설치되지 않았습니다. pip install pdfplumber")

        self.dpi = dpi
        self.max_pages = max_pages

    def extract(self, pdf_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """
        pdfplumber로 텍스트 추출

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            OCR 형식의 데이터 리스트
        """
        all_ocr_data = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                if self.max_pages:
                    total_pages = min(total_pages, self.max_pages)

                print(f"    pdfplumber: {total_pages}개 페이지 처리 중...")
                for page_num in range(1, total_pages + 1):
                    page = pdf.pages[page_num - 1]

                    # 단어 단위로 추출
                    words = page.extract_words(
                        x_tolerance=3,
                        y_tolerance=3,
                        keep_blank_chars=False
                    )

                    # 문자 단위로 추출 (색상 정보용)
                    chars = page.chars

                    if not words:
                        all_ocr_data.append({
                            'page_num': page_num,
                            'text': [],
                            'left': [],
                            'top': [],
                            'width': [],
                            'height': [],
                            'color': []
                        })
                        continue

                    # OCR 형식으로 변환
                    texts = []
                    lefts = []
                    tops = []
                    widths = []
                    heights = []
                    colors = []

                    # PDF 포인트 (72 DPI) → 이미지 픽셀 (DPI) 변환
                    scale_x = self.dpi / 72.0
                    scale_y = self.dpi / 72.0

                    # 문자-단어 매핑 생성
                    char_to_word_map = {}
                    for word_idx, word in enumerate(words):
                        word_x0 = word.get('x0', 0)
                        word_y0 = word.get('top', 0)
                        word_x1 = word.get('x1', 0)
                        word_y1 = word.get('bottom', 0)

                        for char in chars:
                            char_x = char.get('x0', 0)
                            char_y = char.get('top', 0)

                            if (word_x0 - 2 <= char_x <= word_x1 + 2 and
                                word_y0 - 2 <= char_y <= word_y1 + 2):
                                char_key = (char_x, char_y, char.get('text', ''))
                                char_to_word_map[char_key] = word_idx

                    # 단어별 색상 정보 수집
                    word_colors = {}
                    for char in chars:
                        char_key = (char.get('x0', 0), char.get('top', 0), char.get('text', ''))
                        word_idx = char_to_word_map.get(char_key)

                        if word_idx is not None:
                            color = char.get('non_stroking_color')
                            if color is not None:
                                if word_idx not in word_colors:
                                    word_colors[word_idx] = []
                                word_colors[word_idx].append(color)

                    for word in words:
                        text = word.get('text', '').strip()
                        if text:
                            texts.append(text)

                            # PDF 좌표를 픽셀 좌표로 변환
                            x0 = int(word.get('x0', 0) * scale_x)
                            y0 = int(word.get('top', 0) * scale_y)
                            x1 = int(word.get('x1', 0) * scale_x)
                            y1 = int(word.get('bottom', 0) * scale_y)

                            lefts.append(x0)
                            tops.append(y0)
                            widths.append(max(1, x1 - x0))
                            heights.append(max(1, y1 - y0))

                            # 색상 정보 추출
                            word_idx = len(texts) - 1
                            char_colors = word_colors.get(word_idx, [])

                            if char_colors:
                                from collections import Counter
                                color_counter = Counter(tuple(c) if isinstance(c, (list, tuple)) else c for c in char_colors)
                                main_color = color_counter.most_common(1)[0][0]

                                if isinstance(main_color, (list, tuple)):
                                    if len(main_color) >= 3:
                                        rgb = tuple(int(c * 255) if c <= 1.0 else int(c) for c in main_color[:3])
                                        colors.append(rgb)
                                    else:
                                        colors.append(None)
                                else:
                                    colors.append(None)
                            else:
                                colors.append(None)

                    all_ocr_data.append({
                        'page_num': page_num,
                        'text': texts,
                        'left': lefts,
                        'top': tops,
                        'width': widths,
                        'height': heights,
                        'color': colors
                    })

                    if page_num % 10 == 0 or page_num == 1:
                        word_count = len(texts)
                        logger.debug(f"pdfplumber 추출: {page_num}/{total_pages} 페이지 ({word_count}개 단어)")

        except Exception as e:
            logger.error(f"pdfplumber 추출 실패: {e}")
            raise

        return all_ocr_data


class OCRExtractor(TextExtractor):
    """
    Tesseract OCR 기반 텍스트 추출기

    이미지 기반 PDF 또는 스캔본에 최적화
    - 느림 (병렬 처리 가능)
    - 좌표계: 이미지 픽셀 (DPI) 직접 사용
    """

    def __init__(
        self,
        dpi: int = 200,
        lang: str = 'kor+eng',
        tesseract_cmd: Optional[str] = None,
        use_parallel: bool = True,
        max_workers: Optional[int] = None,
        max_pages: Optional[int] = None,
        preprocessing_method: str = 'balanced'
    ):
        """
        Args:
            dpi: 이미지 DPI
            lang: Tesseract 언어 코드
            tesseract_cmd: Tesseract 실행 파일 경로
            use_parallel: 병렬 처리 사용 여부
            max_workers: 최대 워커 수
            max_pages: 최대 처리 페이지 수
            preprocessing_method: 전처리 강도 ('fast', 'balanced', 'aggressive')
        """
        if not TESSERACT_AVAILABLE:
            raise ImportError("pytesseract가 설치되지 않았습니다. pip install pytesseract")

        self.dpi = dpi
        self.lang = lang
        self.tesseract_cmd = tesseract_cmd
        self.use_parallel = use_parallel
        self.max_workers = max_workers
        self.max_pages = max_pages
        self.preprocessing_method = preprocessing_method

    def extract(self, page_images: List[Image.Image], **kwargs) -> List[Dict[str, Any]]:
        """
        OCR로 텍스트 추출

        Args:
            page_images: 페이지 이미지 리스트

        Returns:
            OCR 형식의 데이터 리스트
        """
        # 전처리 적용
        from app.processing.extractors.preprocessing import ImagePreprocessor
        preprocessed_images = [
            ImagePreprocessor.preprocess_for_ocr(img, method=self.preprocessing_method)
            for img in page_images
        ]

        if self.max_pages:
            preprocessed_images = preprocessed_images[:self.max_pages]

        if self.use_parallel and len(preprocessed_images) > 1:
            return self._ocr_pages_parallel(preprocessed_images)
        else:
            return self._ocr_pages_sequential(preprocessed_images)

    def _ocr_pages_parallel(self, page_images: List[Image.Image]) -> List[Dict[str, Any]]:
        """병렬 OCR 처리"""
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor

        max_workers = self.max_workers or mp.cpu_count()

        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        all_ocr_data = [None] * len(page_images)

        with ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_init_ocr_worker,
            initargs=(self.tesseract_cmd, self.lang)
        ) as executor:
            futures = {
                executor.submit(_ocr_page_worker, (img, i + 1, self.lang, self.tesseract_cmd)): i
                for i, img in enumerate(page_images)
            }

            for future in futures:
                idx = futures[future]
                try:
                    ocr_data = future.result()
                    all_ocr_data[idx] = ocr_data
                except Exception as e:
                    logger.error(f"OCR 실패 (페이지 {idx + 1}): {e}")
                    all_ocr_data[idx] = {
                        'page_num': idx + 1,
                        'text': [],
                        'left': [],
                        'top': [],
                        'width': [],
                        'height': []
                    }

        return all_ocr_data

    def _ocr_pages_sequential(self, page_images: List[Image.Image]) -> List[Dict[str, Any]]:
        """순차 OCR 처리"""
        # Tesseract 경로 설정
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        all_ocr_data = []

        for i, page_image in enumerate(page_images, 1):
            try:
                ocr_data = self._ocr_page(page_image, i)
                all_ocr_data.append(ocr_data)
            except Exception as e:
                logger.error(f"OCR 실패 (페이지 {i}): {e}")
                all_ocr_data.append({
                    'page_num': i,
                    'text': [],
                    'left': [],
                    'top': [],
                    'width': [],
                    'height': []
                })

        return all_ocr_data

    def _ocr_page(self, page_image: Image.Image, page_num: int) -> Dict[str, Any]:
        """단일 페이지 OCR"""
        # Tesseract 경로 설정 (병렬이 아닐 때)
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        ocr_config = r'--psm 6'

        ocr_data = pytesseract.image_to_data(
            page_image,
            lang=self.lang,
            output_type=Output.DICT,
            config=ocr_config
        )
        ocr_data['page_num'] = page_num
        return ocr_data


# 병렬 OCR 워커 함수들
def _init_ocr_worker(tesseract_cmd: Optional[str], lang: str):
    """OCR 워커 초기화"""
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def _ocr_page_worker(args: tuple) -> Dict[str, Any]:
    """OCR 워커 함수"""
    page_image, page_num, lang, tesseract_cmd = args

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    ocr_config = r'--psm 6'
    ocr_data = pytesseract.image_to_data(
        page_image,
        lang=lang,
        output_type=Output.DICT,
        config=ocr_config
    )
    ocr_data['page_num'] = page_num
    return ocr_data


class PyMuPDFExtractor(TextExtractor):
    """
    PyMuPDF (fitz) 기반 텍스트 추출기

    pdfplumber의 CID 문제를 해결하기 위한 대안
    - 한글 폰트를 더 잘 처리
    - 좌표계: PDF 포인트 (72 DPI) → 이미지 픽셀 (DPI) 변환
    """

    def __init__(self, dpi: int = 200, max_pages: Optional[int] = None):
        """
        Args:
            dpi: 이미지 DPI (좌표 변환용)
            max_pages: 최대 처리 페이지 수
        """
        try:
            import fitz
            self.fitz = fitz
        except ImportError:
            raise ImportError("PyMuPDF가 설치되지 않았습니다. pip install pymupdf")

        self.dpi = dpi
        self.max_pages = max_pages

    def extract(self, pdf_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """
        PyMuPDF로 텍스트 추출

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            OCR 형식의 데이터 리스트
        """
        all_ocr_data = []

        try:
            pdf = self.fitz.open(pdf_path)
            total_pages = len(pdf)
            if self.max_pages:
                total_pages = min(total_pages, self.max_pages)

            print(f"    PyMuPDF: {total_pages}개 페이지 처리 중...")

            # PDF 포인트 (72 DPI) → 이미지 픽셀 (DPI) 변환
            scale_x = self.dpi / 72.0
            scale_y = self.dpi / 72.0

            for page_num in range(1, total_pages + 1):
                page = pdf[page_num - 1]

                # 단어 단위로 추출
                words = page.get_text("words")  # (x0, y0, x1, y1, word, block_no, line_no, word_no)

                if not words:
                    all_ocr_data.append({
                        'page_num': page_num,
                        'text': [],
                        'left': [],
                        'top': [],
                        'width': [],
                        'height': [],
                        'color': []
                    })
                    continue

                # OCR 형식으로 변환
                texts = []
                lefts = []
                tops = []
                widths = []
                heights = []
                colors = []

                for word_data in words:
                    x0, y0, x1, y1, text, block_no, line_no, word_no = word_data

                    text = text.strip()
                    if not text:
                        continue

                    texts.append(text)

                    # PDF 좌표를 픽셀 좌표로 변환
                    left = int(x0 * scale_x)
                    top = int(y0 * scale_y)
                    right = int(x1 * scale_x)
                    bottom = int(y1 * scale_y)

                    lefts.append(left)
                    tops.append(top)
                    widths.append(max(1, right - left))
                    heights.append(max(1, bottom - top))
                    colors.append(None)  # PyMuPDF의 색상 추출은 복잡하므로 생략

                all_ocr_data.append({
                    'page_num': page_num,
                    'text': texts,
                    'left': lefts,
                    'top': tops,
                    'width': widths,
                    'height': heights,
                    'color': colors
                })

                if page_num % 10 == 0 or page_num == 1:
                    word_count = len(texts)
                    logger.debug(f"PyMuPDF 추출: {page_num}/{total_pages} 페이지 ({word_count}개 단어)")

            pdf.close()

        except Exception as e:
            logger.error(f"PyMuPDF 추출 실패: {e}")
            raise

        return all_ocr_data
