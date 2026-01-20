"""
PDF 영역 캡처 서비스
bbox 좌표를 사용하여 PDF의 특정 영역을 이미지로 캡처 (학습 없이)
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import logging
import os

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)


def find_poppler_path() -> Optional[str]:
    """
    Poppler 설치 경로 자동 감지
    
    Returns:
        Poppler bin 디렉토리 경로 또는 None
    """
    # 1. 환경 변수에서 확인
    poppler_path = os.getenv('POPPLER_PATH')
    if poppler_path and Path(poppler_path).exists():
        return poppler_path
    
    # 2. 일반적인 Windows 설치 경로 확인
    common_paths = [
        r"C:\poppler\Library\bin",
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files (x86)\poppler\Library\bin",
        r"D:\poppler\Library\bin",
    ]
    
    for path_str in common_paths:
        path = Path(path_str)
        if path.exists() and (path / "pdftoppm.exe").exists():
            return str(path)
    
    # 3. PATH에서 pdftoppm 찾기
    import shutil
    pdftoppm_path = shutil.which("pdftoppm")
    if pdftoppm_path:
        # pdftoppm.exe의 디렉토리 반환
        return str(Path(pdftoppm_path).parent)
    
    return None


class PDFRegionCapturer:
    """
    PDF의 특정 영역을 이미지로 캡처하는 클래스
    
    학습 없이 bbox 좌표만으로 영역을 크롭합니다.
    """
    
    def __init__(
        self, 
        dpi: int = 300, 
        base_output_dir: Optional[Path] = None,
        poppler_path: Optional[str] = None
    ):
        """
        Args:
            dpi: PDF → 이미지 변환 해상도 (기본값: 300)
            base_output_dir: 이미지 저장 기본 디렉토리 (None이면 자동 생성)
            poppler_path: Poppler bin 디렉토리 경로 (예: "C:\\poppler\\Library\\bin")
                          None이면 자동 감지 시도
        """
        self.dpi = dpi
        self.base_output_dir = base_output_dir or (settings.API_DIR / "data" / "pdfs" / "captures")
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Poppler 경로 설정 (지정되지 않았으면 자동 감지)
        if poppler_path:
            self.poppler_path = poppler_path
        else:
            self.poppler_path = find_poppler_path()
            if self.poppler_path:
                logger.info(f"Poppler 경로 자동 감지: {self.poppler_path}")
            else:
                logger.warning("Poppler 경로를 찾을 수 없습니다. PDF 영역 캡처가 작동하지 않을 수 있습니다.")
        
        if not PDF2IMAGE_AVAILABLE:
            logger.warning("pdf2image가 설치되지 않았습니다. pip install pdf2image")
    
    def capture_region(
        self,
        pdf_path: Path,
        page: int,
        bbox: List[float],
        output_path: Optional[Path] = None,
        padding: int = 5
    ) -> Optional[Path]:
        """
        PDF의 특정 페이지에서 bbox 좌표로 영역을 캡처하여 이미지로 저장
        
        Args:
            pdf_path: PDF 파일 경로
            page: 페이지 번호 (1-based)
            bbox: 바운딩 박스 좌표 [x0, y0, x1, y1] (PDF 좌표계)
            output_path: 출력 이미지 경로 (None이면 자동 생성)
            padding: 영역 주변 여백 (픽셀 단위)
        
        Returns:
            저장된 이미지 파일 경로 또는 None (실패 시)
        """
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image가 설치되지 않았습니다. pip install pdf2image")
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        try:
            # PDF → 이미지 변환 (특정 페이지만)
            convert_kwargs = {
                "dpi": self.dpi,
                "first_page": page,
                "last_page": page
            }
            # Poppler 경로가 지정되어 있으면 추가
            if self.poppler_path:
                convert_kwargs["poppler_path"] = self.poppler_path
            
            images = convert_from_path(pdf_path, **convert_kwargs)
            
            if not images:
                logger.error(f"페이지 {page}를 이미지로 변환할 수 없습니다.")
                return None
            
            page_image = images[0]  # 첫 번째 (유일한) 이미지
            
            # PDF 좌표계 → 이미지 좌표계 변환
            # pdf2image는 DPI에 따라 이미지 크기가 달라짐
            # pdfplumber의 bbox는 포인트 단위 (1 point = 1/72 inch)
            # 이미지는 DPI에 따라 픽셀 단위
            
            # PDF 페이지 크기 가져오기 (pdfplumber로)
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    if page > len(pdf.pages):
                        raise ValueError(f"페이지 {page}가 PDF 범위를 벗어났습니다. (총 {len(pdf.pages)}페이지)")
                    pdf_page = pdf.pages[page - 1]  # 0-based
                    pdf_width = pdf_page.width
                    pdf_height = pdf_page.height
            except ImportError:
                # pdfplumber가 없으면 이미지 크기로 추정
                logger.warning("pdfplumber가 없어 이미지 크기로 PDF 크기를 추정합니다.")
                pdf_width = page_image.width / (self.dpi / 72.0)
                pdf_height = page_image.height / (self.dpi / 72.0)
            
            # bbox 유효성 검사 및 자동 수정
            # x0와 x1이 같거나 x1이 0이면 페이지 전체 너비 사용
            if len(bbox) >= 4:
                if bbox[0] == bbox[2] or bbox[2] == 0:
                    logger.warning(f"bbox의 x 좌표가 유효하지 않습니다 ({bbox[0]}, {bbox[2]}). 페이지 전체 너비를 사용합니다.")
                    bbox = [0, bbox[1], pdf_width, bbox[3]]
            
            # 좌표 변환: PDF 포인트 → 이미지 픽셀
            # PDF 좌표계: 왼쪽 하단이 (0,0), Y축이 위로 증가
            # 이미지 좌표계: 왼쪽 상단이 (0,0), Y축이 아래로 증가
            scale_x = page_image.width / pdf_width
            scale_y = page_image.height / pdf_height
            
            # X축은 그대로 변환
            x0 = int(bbox[0] * scale_x) - padding
            x1 = int(bbox[2] * scale_x) + padding
            
            # Y축은 반전 필요: PDF의 y0(하단 기준) → 이미지의 y1(상단 기준)
            # PDF의 y1(하단 기준) → 이미지의 y0(상단 기준)
            pdf_y0 = bbox[1]  # PDF 좌표계에서 하단에서의 거리 (작은 값)
            pdf_y1 = bbox[3]  # PDF 좌표계에서 하단에서의 거리 (큰 값)
            
            # 이미지 좌표계로 변환 (상단 기준)
            img_y1 = int((pdf_height - pdf_y0) * scale_y) + padding  # PDF의 y0 → 이미지의 y1
            img_y0 = int((pdf_height - pdf_y1) * scale_y) - padding  # PDF의 y1 → 이미지의 y0
            
            y0 = img_y0
            y1 = img_y1
            
            # 경계 체크
            x0 = max(0, x0)
            y0 = max(0, y0)
            x1 = min(page_image.width, x1)
            y1 = min(page_image.height, y1)
            
            # 영역 크롭
            cropped_image = page_image.crop((x0, y0, x1, y1))
            
            # 출력 경로 결정
            if output_path is None:
                output_path = self._generate_output_path(pdf_path, page, bbox)
            
            # 디렉토리 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 이미지 저장
            cropped_image.save(output_path, "PNG")
            
            logger.info(f"PDF 영역 캡처 완료: {output_path} (크기: {cropped_image.size})")
            return output_path
            
        except Exception as e:
            # Poppler 미설치 등의 경우 경고만 표시하고 None 반환
            error_msg = str(e)
            if "poppler" in error_msg.lower() or "PDFInfoNotInstalledError" in str(type(e).__name__):
                # 첫 번째 에러만 경고 표시
                if not hasattr(self, '_poppler_warning_shown'):
                    logger.warning(f"PDF 영역 캡처 실패: Poppler가 설치되지 않았습니다.")
                    print(f"    [WARNING] Poppler 미설치 - PDF 영역 캡처 건너뜀 (이미지 없이 진행)")
                    self._poppler_warning_shown = True
                # 나머지는 조용히 처리 (에러 로그 없음)
            else:
                logger.error(f"PDF 영역 캡처 실패: {e}")
            return None
    
    def capture_block_regions(
        self,
        pdf_path: Path,
        blocks: List[Dict[str, Any]],
        subject: str,
        lesson_number: int,
        block_id_key: str = "block_id"
    ) -> Dict[str, Path]:
        """
        여러 블록의 영역을 일괄 캡처
        
        Args:
            pdf_path: PDF 파일 경로
            blocks: 블록 리스트 (각 블록에 page, bbox, block_id 포함)
            subject: 과목명
            lesson_number: 강 번호
            block_id_key: 블록 ID를 가진 키 이름 (기본값: "block_id")
        
        Returns:
            {block_id: image_path} 딕셔너리
        """
        captured = {}
        
        for block in blocks:
            block_id = block.get(block_id_key)
            if not block_id:
                logger.warning(f"블록에 {block_id_key}가 없습니다: {block}")
                continue
            
            page = block.get("page", 1)
            bbox = block.get("bbox")
            
            if not bbox or len(bbox) < 4:
                logger.warning(f"블록 {block_id}에 유효한 bbox가 없습니다.")
                continue
            
            # 출력 경로 생성
            output_path = self._generate_block_output_path(
                subject, lesson_number, block_id
            )
            
            # 영역 캡처
            image_path = self.capture_region(
                pdf_path=pdf_path,
                page=page,
                bbox=bbox,
                output_path=output_path
            )
            
            if image_path:
                captured[block_id] = image_path
        
        if captured:
            logger.info(f"총 {len(captured)}개 블록 영역 캡처 완료")
        elif len(blocks) > 0:
            # 모든 캡처 실패 시 (Poppler 미설치 등)
            logger.warning(f"PDF 영역 캡처 실패: {len(blocks)}개 블록 (Poppler 미설치 가능)")
        
        return captured
    
    def _generate_output_path(
        self,
        pdf_path: Path,
        page: int,
        bbox: List[float]
    ) -> Path:
        """
        출력 경로 자동 생성
        
        Args:
            pdf_path: PDF 파일 경로
            page: 페이지 번호
            bbox: 바운딩 박스 좌표
        
        Returns:
            출력 파일 경로
        """
        # 파일명: {pdf_name}_page{page}_x{x0}y{y0}x{x1}y{y1}.png
        pdf_name = pdf_path.stem
        bbox_str = f"x{int(bbox[0])}y{int(bbox[1])}x{int(bbox[2])}y{int(bbox[3])}"
        filename = f"{pdf_name}_page{page}_{bbox_str}.png"
        
        return self.base_output_dir / filename
    
    def _generate_block_output_path(
        self,
        subject: str,
        lesson_number: int,
        block_id: str
    ) -> Path:
        """
        블록별 출력 경로 생성
        
        Args:
            subject: 과목명
            lesson_number: 강 번호
            block_id: 블록 ID (예: "b0", "b1")
        
        Returns:
            출력 파일 경로: captures/{subject}/lesson_{n}/{block_id}.png
        """
        output_dir = self.base_output_dir / subject / f"lesson_{lesson_number:02d}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir / f"{block_id}.png"


def capture_pdf_region(
    pdf_path: Path,
    page: int,
    bbox: List[float],
    output_path: Optional[Path] = None,
    dpi: int = 300
) -> Optional[Path]:
    """
    편의 함수: PDF 영역 캡처
    
    Args:
        pdf_path: PDF 파일 경로
        page: 페이지 번호 (1-based)
        bbox: 바운딩 박스 좌표 [x0, y0, x1, y1]
        output_path: 출력 이미지 경로 (None이면 자동 생성)
        dpi: 이미지 해상도
    
    Returns:
        저장된 이미지 파일 경로 또는 None
    """
    capturer = PDFRegionCapturer(dpi=dpi)
    return capturer.capture_region(pdf_path, page, bbox, output_path)
