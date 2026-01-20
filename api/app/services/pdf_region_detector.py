"""
PDF 영역 자동 감지 서비스
규칙 기반으로 문제/지문/보기 영역을 자동 감지
"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pytesseract
from PIL import Image

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    from pytesseract import Output
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFRegionDetector:
    """
    PDF에서 문제 영역을 자동으로 감지하는 클래스
    
    규칙 기반 접근:
    1. 문제 번호 패턴 감지 (1., 2., ①, ② 등)
    2. 텍스트 블록 그룹화
    3. 레이아웃 구조 분석
    """
    
    # 문제 번호 패턴
    QUESTION_NUMBER_PATTERNS = [
        r'^\d+\.',  # 1., 2., 3.
        r'^\d+\s*번',  # 1번, 2번
        r'^[①②③④⑤⑥⑦⑧⑨⑩]',  # 원문자
        r'^\([0-9]+\)',  # (1), (2)
        r'^\[[0-9]+\]',  # [1], [2]
    ]
    
    # 보기 패턴
    OPTION_PATTERNS = [
        r'^[①②③④⑤]',  # 원문자 보기
        r'^\([가-나다라마]\)',  # (가), (나)
        r'^\d+\)',  # 1), 2)
    ]
    
    def __init__(self, dpi: int = 300, lang: str = 'kor+eng'):
        """
        Args:
            dpi: PDF → 이미지 변환 해상도
            lang: Tesseract 언어 코드
        """
        self.dpi = dpi
        self.lang = lang
        
        # Windows에서 Tesseract 경로 자동 감지
        try:
            default_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            for path in default_paths:
                if Path(path).exists():
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        except Exception:
            pass
    
    def detect_question_regions(
        self,
        pdf_path: Path,
        page: int,
        min_question_height: int = 100
    ) -> List[Dict[str, Any]]:
        """
        특정 페이지에서 문제 영역을 자동 감지
        
        Args:
            pdf_path: PDF 파일 경로
            page: 페이지 번호 (1-based)
            min_question_height: 최소 문제 높이 (픽셀)
        
        Returns:
            문제 영역 리스트
            [
                {
                    "question_number": 1,
                    "bbox": [x0, y0, x1, y1],
                    "type": "question",
                    "confidence": 0.9
                },
                ...
            ]
        """
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image가 설치되지 않았습니다.")
        
        if not TESSERACT_AVAILABLE:
            raise ImportError("pytesseract가 설치되지 않았습니다.")
        
        # PDF → 이미지 변환
        images = convert_from_path(
            pdf_path,
            dpi=self.dpi,
            first_page=page,
            last_page=page
        )
        
        if not images:
            return []
        
        page_image = images[0]
        
        # OCR로 텍스트 + 좌표 추출
        ocr_data = pytesseract.image_to_data(
            page_image,
            lang=self.lang,
            output_type=Output.DICT
        )
        
        # 문제 번호 찾기
        question_starts = self._find_question_numbers(ocr_data)
        
        # 문제 영역 계산
        regions = self._calculate_question_regions(
            question_starts,
            ocr_data,
            page_image.size,
            min_question_height
        )
        
        return regions
    
    def _find_question_numbers(
        self,
        ocr_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        OCR 결과에서 문제 번호 찾기
        
        Returns:
            [
                {
                    "number": 1,
                    "x": 100,
                    "y": 200,
                    "text": "1."
                },
                ...
            ]
        """
        question_starts = []
        
        num_words = len(ocr_data['text'])
        
        for i in range(num_words):
            text = ocr_data['text'][i].strip()
            conf = int(ocr_data['conf'][i])
            
            # 신뢰도가 너무 낮으면 스킵
            if conf < 30:
                continue
            
            # 문제 번호 패턴 확인
            for pattern in self.QUESTION_NUMBER_PATTERNS:
                match = re.match(pattern, text)
                if match:
                    # 숫자 추출
                    number_match = re.search(r'\d+', text)
                    if number_match:
                        question_starts.append({
                            "number": int(number_match.group()),
                            "x": ocr_data['left'][i],
                            "y": ocr_data['top'][i],
                            "width": ocr_data['width'][i],
                            "height": ocr_data['height'][i],
                            "text": text,
                            "confidence": conf / 100.0
                        })
                        break
        
        # y 좌표 기준으로 정렬
        question_starts.sort(key=lambda q: q['y'])
        
        return question_starts
    
    def _calculate_question_regions(
        self,
        question_starts: List[Dict[str, Any]],
        ocr_data: Dict[str, Any],
        image_size: Tuple[int, int],
        min_height: int
    ) -> List[Dict[str, Any]]:
        """
        문제 시작점으로부터 문제 영역 계산
        
        Args:
            question_starts: 문제 번호 위치 리스트
            ocr_data: 전체 OCR 데이터
            image_size: 이미지 크기 (width, height)
            min_height: 최소 문제 높이
        
        Returns:
            문제 영역 리스트
        """
        regions = []
        image_width, image_height = image_size
        
        for i, question_start in enumerate(question_starts):
            # 현재 문제 시작 y 좌표
            start_y = question_start['y']
            
            # 다음 문제 시작 y 좌표 (없으면 페이지 끝)
            if i + 1 < len(question_starts):
                end_y = question_starts[i + 1]['y']
            else:
                end_y = image_height
            
            # 문제 영역 높이
            height = end_y - start_y
            
            # 최소 높이 체크
            if height < min_height:
                continue
            
            # x 좌표는 페이지 전체 너비 사용 (또는 OCR 데이터 기반)
            x0 = 0
            x1 = image_width
            
            # bbox 생성 (이미지 좌표계)
            bbox = [x0, start_y, x1, end_y]
            
            regions.append({
                "question_number": question_start['number'],
                "bbox": bbox,
                "type": "question",
                "confidence": question_start['confidence'],
                "page": 1  # 현재 페이지
            })
        
        return regions
    
    def detect_by_text_matching(
        self,
        pdf_path: Path,
        page: int,
        target_text: str,
        context_lines: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        텍스트 매칭으로 영역 감지
        
        Args:
            pdf_path: PDF 파일 경로
            page: 페이지 번호
            target_text: 찾을 텍스트
            context_lines: 주변 줄 수
        
        Returns:
            {
                "bbox": [x0, y0, x1, y1],
                "matched_text": "...",
                "confidence": 0.9
            }
        """
        if not PDF2IMAGE_AVAILABLE or not TESSERACT_AVAILABLE:
            return None
        
        # PDF → 이미지
        images = convert_from_path(
            pdf_path,
            dpi=self.dpi,
            first_page=page,
            last_page=page
        )
        
        if not images:
            return None
        
        page_image = images[0]
        
        # OCR
        ocr_data = pytesseract.image_to_data(
            page_image,
            lang=self.lang,
            output_type=Output.DICT
        )
        
        # 텍스트 매칭
        matched_indices = []
        for i, text in enumerate(ocr_data['text']):
            if target_text in text:
                matched_indices.append(i)
        
        if not matched_indices:
            return None
        
        # 첫 번째 매칭 주변 영역 계산
        first_match = matched_indices[0]
        
        # 주변 줄 찾기
        start_idx = max(0, first_match - context_lines * 10)
        end_idx = min(len(ocr_data['text']), first_match + context_lines * 10)
        
        # bbox 계산
        x_coords = [ocr_data['left'][i] for i in range(start_idx, end_idx) if ocr_data['text'][i].strip()]
        y_coords = [ocr_data['top'][i] for i in range(start_idx, end_idx) if ocr_data['text'][i].strip()]
        
        if not x_coords or not y_coords:
            return None
        
        x0 = min(x_coords)
        y0 = min(y_coords)
        x1 = max(x_coords) + max([ocr_data['width'][i] for i in range(start_idx, end_idx) if ocr_data['text'][i].strip()] or [0])
        y1 = max(y_coords) + max([ocr_data['height'][i] for i in range(start_idx, end_idx) if ocr_data['text'][i].strip()] or [0])
        
        return {
            "bbox": [x0, y0, x1, y1],
            "matched_text": target_text,
            "confidence": 0.8,
            "page": page
        }
    
    def detect_paragraph_regions(
        self,
        pdf_path: Path,
        page: int,
        y_threshold: float = 20.0
    ) -> List[Dict[str, Any]]:
        """
        문단 단위로 영역 감지
        
        Args:
            pdf_path: PDF 파일 경로
            page: 페이지 번호
            y_threshold: 문단 구분 y 좌표 차이 임계값
        
        Returns:
            문단 영역 리스트
        """
        if not PDF2IMAGE_AVAILABLE or not TESSERACT_AVAILABLE:
            return []
        
        # PDF → 이미지
        images = convert_from_path(
            pdf_path,
            dpi=self.dpi,
            first_page=page,
            last_page=page
        )
        
        if not images:
            return []
        
        page_image = images[0]
        
        # OCR
        ocr_data = pytesseract.image_to_data(
            page_image,
            lang=self.lang,
            output_type=Output.DICT
        )
        
        # 줄 단위로 그룹화
        lines = []
        current_line = None
        
        num_words = len(ocr_data['text'])
        
        for i in range(num_words):
            text = ocr_data['text'][i].strip()
            if not text or int(ocr_data['conf'][i]) < 30:
                continue
            
            y = ocr_data['top'][i]
            
            if current_line is None:
                current_line = {
                    "y": y,
                    "words": [i],
                    "x0": ocr_data['left'][i],
                    "y0": y,
                    "x1": ocr_data['left'][i] + ocr_data['width'][i],
                    "y1": y + ocr_data['height'][i]
                }
            else:
                # 같은 줄인지 확인
                if abs(y - current_line['y']) < y_threshold:
                    current_line['words'].append(i)
                    current_line['x0'] = min(current_line['x0'], ocr_data['left'][i])
                    current_line['y0'] = min(current_line['y0'], y)
                    current_line['x1'] = max(current_line['x1'], ocr_data['left'][i] + ocr_data['width'][i])
                    current_line['y1'] = max(current_line['y1'], y + ocr_data['height'][i])
                else:
                    # 새 줄 시작
                    lines.append(current_line)
                    current_line = {
                        "y": y,
                        "words": [i],
                        "x0": ocr_data['left'][i],
                        "y0": y,
                        "x1": ocr_data['left'][i] + ocr_data['width'][i],
                        "y1": y + ocr_data['height'][i]
                    }
        
        if current_line:
            lines.append(current_line)
        
        # 문단으로 그룹화
        paragraphs = []
        current_paragraph = None
        
        for line in lines:
            if current_paragraph is None:
                current_paragraph = {
                    "lines": [line],
                    "bbox": [line['x0'], line['y0'], line['x1'], line['y1']]
                }
            else:
                # 문단 구분 확인
                last_line = current_paragraph['lines'][-1]
                if line['y0'] - last_line['y1'] > y_threshold * 2:
                    # 새 문단
                    paragraphs.append(current_paragraph)
                    current_paragraph = {
                        "lines": [line],
                        "bbox": [line['x0'], line['y0'], line['x1'], line['y1']]
                    }
                else:
                    # 같은 문단
                    current_paragraph['lines'].append(line)
                    bbox = current_paragraph['bbox']
                    current_paragraph['bbox'] = [
                        min(bbox[0], line['x0']),
                        min(bbox[1], line['y0']),
                        max(bbox[2], line['x1']),
                        max(bbox[3], line['y1'])
                    ]
        
        if current_paragraph:
            paragraphs.append(current_paragraph)
        
        # 결과 변환
        regions = []
        for i, para in enumerate(paragraphs):
            regions.append({
                "paragraph_number": i + 1,
                "bbox": para['bbox'],
                "type": "paragraph",
                "line_count": len(para['lines']),
                "page": page
            })
        
        return regions
