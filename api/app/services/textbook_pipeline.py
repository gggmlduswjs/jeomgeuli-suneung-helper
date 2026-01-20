"""
교재 PDF 기반 AI 학습 콘텐츠 자동 생성 파이프라인 (최적화 버전)

핵심 원칙:
1. PDF만 존재, 강의 대본 없음
2. 교재 원문이 유일한 Source of Truth
3. JSON 중심 설계
4. 단일 파이프라인, config.json으로 과목 분기
5. 규칙 기반 + AI 기반 문서 파싱 (OCR + y좌표 + LLM)

성능 최적화:
- 병렬 OCR 처리 (multiprocessing, 최대 8 워커)
- OCR 결과 캐싱
- 최적 DPI (180-200, 기본값 180)
- 이미지 전처리
- AI 후처리 통합 (선택적)
"""
import re
import json
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    from pytesseract import Output
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont

from app.core.config import settings
from app.services.text_extractors import PdfplumberExtractor, OCRExtractor, TextExtractor

# AI 후처리기 import (선택적)
try:
    from app.services.pdf_extract.ai_text_postprocessor import (
        get_text_postprocessor,
        AITextPostProcessor,
        BasicTextPostProcessor
    )
    AI_POSTPROCESSOR_AVAILABLE = True
except ImportError:
    AI_POSTPROCESSOR_AVAILABLE = False
    AITextPostProcessor = None
    BasicTextPostProcessor = None


logger = logging.getLogger(__name__)


# 전역 변수: 프로세스 풀에서 사용할 설정
_ocr_config = None


def _init_worker(tesseract_cmd: Optional[str], lang: str):
    """워커 프로세스 초기화"""
    global _ocr_config
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    _ocr_config = {"lang": lang}


def _ocr_page_worker(args: Tuple[Image.Image, int, str, Optional[str]]) -> Dict[str, Any]:
    """병렬 OCR 워커 함수"""
    page_image, page_num, lang, tesseract_cmd = args
    
    # Tesseract 경로 설정
    if tesseract_cmd:
        if tesseract_cmd != 'tesseract':  # PATH에 있으면 이름만 사용
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    try:
        # OCR 설정 개선 (PSM 모드)
        ocr_config = r'--psm 6'  # 단일 균일한 텍스트 블록 가정
        
        ocr_data = pytesseract.image_to_data(
            page_image,
            lang=lang,
            output_type=Output.DICT,
            config=ocr_config
        )
        ocr_data['page_num'] = page_num
        return ocr_data
    except Exception as e:
        error_msg = str(e)
        # 중요한 에러만 로깅 (중복 방지)
        if "tesseract is not installed" in error_msg.lower() or "not in your path" in error_msg.lower():
            # 이 에러는 메인 프로세스에서 이미 처리됨
            pass
        else:
            logger.error(f"OCR 오류 (페이지 {page_num}): {e}")
        return {"page_num": page_num, "text": [], "left": [], "top": [], "width": [], "height": []}


class TextbookPipeline:
    """
    교재 PDF 기반 자동 파이프라인 (최적화 버전)
    
    프로세스:
    1. PDF → 페이지 이미지 (최적 DPI)
    2. OCR (병렬 처리 + 캐싱)
    3. AI 후처리 (선택적)
    4. 문서 구조 분석 (config.json + LLM)
    5. JSON 생성 (lectures.json, lecture_XX.json, problem_XX.json)
    """
    
    def __init__(
        self,
        subject: str,
        dpi: int = 180,  # 최적화: 200 → 180 (속도 향상, 품질 유사)
        poppler_path: Optional[str] = None,
        lang: str = 'kor+eng',
        use_parallel: bool = True,  # 병렬 처리 활성화
        max_workers: Optional[int] = None,  # None이면 CPU 코어 수
        use_ai_postprocess: bool = False,  # AI 후처리 (선택적)
        use_cache: bool = True,  # OCR 캐싱
        ai_model: str = "gpt-4o-mini",  # AI 모델
        max_pages: Optional[int] = None,  # 처리할 최대 페이지 수 (None = 전체)
        use_pdfplumber: bool = True  # pdfplumber 사용 (텍스트 레이어가 있는 PDF에 권장)
    ):
        """
        Args:
            subject: 과목명 ('literature', 'math1', 'english')
            dpi: PDF → 이미지 변환 해상도 (180-200 권장, 기본값 180)
            poppler_path: Poppler bin 디렉토리 경로
            lang: Tesseract 언어 코드
            use_parallel: 병렬 OCR 처리 사용 여부
            max_workers: 병렬 처리 워커 수 (None = CPU 코어 수)
            use_ai_postprocess: AI 후처리 사용 여부
            use_cache: OCR 결과 캐싱
            ai_model: AI 모델명
            max_pages: 처리할 최대 페이지 수 (None = 전체, 예: 20 = 첫 20페이지만)
            use_pdfplumber: pdfplumber 사용 여부 (텍스트 레이어가 있는 PDF에 권장, OCR보다 정확하고 빠름)
        """
        self.subject = subject
        self.dpi = dpi
        self.poppler_path = poppler_path
        self.lang = lang
        self.use_parallel = use_parallel
        self.max_workers = max_workers or mp.cpu_count()
        self.use_ai_postprocess = use_ai_postprocess and AI_POSTPROCESSOR_AVAILABLE
        self.use_cache = use_cache
        self.max_pages = max_pages
        self.use_pdfplumber = use_pdfplumber and PDFPLUMBER_AVAILABLE
        
        if self.use_pdfplumber:
            print(f"    ✓ pdfplumber 사용 (텍스트 레이어 추출, OCR보다 정확하고 빠름)")
        elif PDFPLUMBER_AVAILABLE == False:
            print(f"    ⚠️ pdfplumber가 설치되지 않았습니다. OCR을 사용합니다.")
            print(f"    💡 더 정확한 추출을 위해: pip install pdfplumber")
        
        # 폴더 구조
        self.data_dir = settings.API_DIR / "data" / subject
        self.pdf_dir = self.data_dir / "pdf"
        self.pages_dir = self.data_dir / "pages"
        self.lectures_dir = self.data_dir / "lectures"
        self.problems_dir = self.data_dir / "problems"
        self.content_dir = self.data_dir / "content"  # 본문 JSON (지문, 설명)
        self.cache_dir = self.data_dir / "cache"  # OCR 캐시
        self.visualizations_dir = self.data_dir / "visualizations"  # 영역 시각화
        self.concepts_images_dir = self.data_dir / "concepts_images"  # 개념 이미지 (소단원)
        self.content_images_dir = self.data_dir / "content_images"  # 본문 이미지 (지문, 설명)
        self.problems_images_dir = self.data_dir / "problems_images"  # 문제 이미지
        self.config_path = self.data_dir / "config.json"
        
        # 디렉토리 생성 (모든 필요한 폴더 미리 생성)
        for dir_path in [
            self.pdf_dir,
            self.pages_dir,
            self.lectures_dir,
            self.problems_dir,
            self.content_dir,
            self.cache_dir,
            self.visualizations_dir,
            self.concepts_images_dir,
            self.content_images_dir,
            self.problems_images_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"폴더 확인/생성: {dir_path}")
        
        # config.json 로드
        self.config = self._load_config()
        
        # 텍스트 추출기 초기화 (pdfplumber / OCR 완전 분리)
        self.text_extractor: Optional[TextExtractor] = None
        if self.use_pdfplumber:
            try:
                self.text_extractor = PdfplumberExtractor(
                    dpi=self.dpi,
                    max_pages=self.max_pages
                )
                logger.info("pdfplumber 추출기 초기화 완료")
            except ImportError:
                logger.warning("pdfplumber 사용 불가, OCR로 대체")
                self.use_pdfplumber = False
                self.text_extractor = OCRExtractor(
                    dpi=self.dpi,
                    lang=self.lang,
                    tesseract_cmd=None,  # 나중에 설정
                    use_parallel=self.use_parallel,
                    max_workers=self.max_workers,
                    max_pages=self.max_pages
                )
        else:
            self.text_extractor = OCRExtractor(
                dpi=self.dpi,
                lang=self.lang,
                tesseract_cmd=None,  # 나중에 설정
                use_parallel=self.use_parallel,
                max_workers=self.max_workers,
                max_pages=self.max_pages
            )
        
        # Tesseract 경로 설정 (OCR 추출기용)
        self.tesseract_cmd = None
        if TESSERACT_AVAILABLE and isinstance(self.text_extractor, OCRExtractor):
            self.tesseract_cmd = self._setup_tesseract()
            if self.tesseract_cmd:
                # OCR 추출기에도 경로 설정
                self.text_extractor.tesseract_cmd = self.tesseract_cmd
            else:
                print(f"    ⚠️ Tesseract가 설정되지 않았습니다. OCR이 작동하지 않을 수 있습니다.")
                print(f"    설치 방법: https://github.com/UB-Mannheim/tesseract/wiki")
        elif not TESSERACT_AVAILABLE and isinstance(self.text_extractor, OCRExtractor):
            print(f"    ⚠️ pytesseract가 설치되지 않았습니다.")
        
        # AI 후처리기 초기화 (선택적)
        self.ai_postprocessor = None
        if self.use_ai_postprocess:
            try:
                self.ai_postprocessor = get_text_postprocessor(
                    use_ai=True,
                    model=ai_model,
                    temperature=0.0
                )
                logger.info(f"AI 후처리기 초기화 완료: {ai_model}")
            except Exception as e:
                logger.warning(f"AI 후처리기 초기화 실패, 기본 후처리기 사용: {e}")
                self.ai_postprocessor = BasicTextPostProcessor() if BasicTextPostProcessor else None
                self.use_ai_postprocess = False
        
        # 성능 통계
        self.stats = {
            "ocr_time": 0,
            "ai_postprocess_time": 0,
            "total_time": 0,
            "pages_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """config.json 로드 (없으면 기본값 생성)"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 기본 config 생성
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """과목별 기본 config"""
        if self.subject == 'literature':
            return {
                "subject": "literature",
                "lecture_title_patterns": [
                    # 큰 주제 단위만 추출 (엄격한 패턴)
                    r'^\d+강\s*[|]\s*[가-힣]+',  # "1강 | 시의 표현과 형식"
                    r'^\d+강\s+[가-힣]+',  # "1강 시의 표현과 형식"
                    r'^\d+\s+[가-힣]{2,}\s+[가-힣]{2,}',  # "1 시의 표현과 형식" (숫자 + 여러 한글 단어, 최소 2글자씩)
                ],
                "concept_title_patterns": [
                    # 개념 블록 제목 패턴 (일반적인 패턴 - 모든 단원에 적용 가능)
                    # OCR 오인식 대응: 공백 누락, 점 누락, 괄호 형태 등을 고려
                    r'^\(\d+\)\s+[가-힣]{2,}',  # "(1) 시적 표현", "(2) 소재" 등
                    r'^\d+\s*[\.]\s+[가-힣]{2,}',  # "1. 시적 표현", "2. 소재" 등
                    r'^\d+\s+[가-힣]{2,}',  # "1 시적 표현", "2 소재" 등
                    r'^\d+\s*[가-힣]{2,}',  # "1시적표현" (공백/점 없이 인식된 경우)
                    r'^[가-힣]{2,}\s+[가-힣]{2,}$',  # "시적 표현" (숫자 없이 2단어)
                ],
                "content_header_patterns": [
                    # 본문 헤더 패턴 (OCR 오인식 대응, 여러 줄 분리 대응)
                    r'작품으로\s*이해하기\s*\d+',  # "작품으로 이해하기 1"
                    r'작품으로\s*이해하기',  # "작품으로 이해하기" (끝 표시 없이도 매칭)
                    r'작품\s*이해',  # "작품 이해" (OCR에서 "으로" 누락된 경우)
                    r'작품.*이해',  # "작품"과 "이해" 사이에 다른 텍스트가 있어도 매칭
                    r'이해하기',  # "이해하기"만 있어도 매칭 (앞부분 누락 대응)
                ],
                "section_title_patterns": [
                    r'^\(\d+\)',  # "(1)", "(2)"
                    r'^\d+[\.\s]+[가-힣]',  # "1 시적 표현"
                    r'^\d+\s+[가-힣]',  # "1 시적 표현"
                ],
                "problem_number_pattern": r'^\d{2}$',  # "01", "02"
                "paragraph_y_threshold": 25,  # y좌표 차이 < 25 → 같은 문단
                "start_content_page": 8  # 실제 콘텐츠 시작 페이지 (표지/목차 제외)
            }
        elif self.subject == 'math1':
            return {
                "subject": "math1",
                "lecture_title_patterns": [
                    r'^\d+단원\s+[가-힣]+',  # "1단원 지수함수와 로그함수"
                    r'^\d+\s+단원\s+[가-힣]+',  # "1 단원 지수함수와 로그함수"
                    r'^\d+\.\s+[가-힣]+',  # "1. 지수함수와 로그함수"
                    r'^\d+\s+[가-힣]{2,}',  # "1 지수함수와 로그함수"
                ],
                "concept_title_patterns": [
                    r'^\d+\.\s+[가-힣]+',  # "1. 지수함수"
                    r'^\([가-힣]\)\s+[가-힣]+',  # "(가) 지수함수"
                    r'^[가-힣]\.\s+[가-힣]+',  # "가. 지수함수"
                ],
                "example_title_patterns": [
                    r'^예제\s*\d+',  # "예제 1"
                    r'^예\s*\d+',  # "예 1"
                    r'^Example\s*\d+',  # "Example 1"
                ],
                "exercise_title_patterns": [
                    r'^유제\s*\d+',  # "유제 1"
                    r'^연습\s*\d+',  # "연습 1"
                    r'^Exercise\s*\d+',  # "Exercise 1"
                ],
                "section_title_patterns": [
                    r'^\d+\.\s+[가-힣]+',  # "1. 지수함수"
                    r'^\([가-힣]\)\s+[가-힣]+',  # "(가) 지수함수"
                    r'^[가-힣]\.\s+[가-힣]+',  # "가. 지수함수"
                ],
                "problem_number_pattern": r'^\d+\.',  # "1.", "2."
                "paragraph_y_threshold": 25,
                "start_content_page": 5  # 수학은 보통 5페이지부터 시작
            }
        elif self.subject == 'english':
            return {
                "subject": "english",
                "lecture_title_patterns": [
                    r'Unit\s+\d+',  # "Unit 1"
                    r'^\d+\.\s+Unit\s+\d+',  # "1. Unit 1"
                    r'^\d+단원',  # "1단원"
                    r'^\d+\s+단원',  # "1 단원"
                ],
                "passage_title_patterns": [
                    r'지문\s*\d+',  # "지문 1"
                    r'Passage\s+\d+',  # "Passage 1"
                    r'Text\s+\d+',  # "Text 1"
                    r'Reading\s+\d+',  # "Reading 1"
                ],
                "section_title_patterns": [
                    r'^\d+\.',  # "1."
                    r'^[A-Z]\.',  # "A."
                    r'^[가-힣]\.',  # "가."
                ],
                "problem_number_pattern": r'^\d+\.',  # "1.", "2."
                "paragraph_y_threshold": 25,
                "start_content_page": 5  # 영어도 보통 5페이지부터 시작
            }
        else:
            # 기본값
            return {
                "subject": self.subject,
                "lecture_title_patterns": [r'^\d+\s+.+'],
                "section_title_patterns": [r'^\d+\.'],
                "problem_number_pattern": r'^\d+',
                "paragraph_y_threshold": 25
            }
    
    def _save_config(self, config: Dict[str, Any]):
        """config.json 저장"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def _setup_tesseract(self) -> Optional[str]:
        """Tesseract 경로 자동 설정"""
        try:
            # 이미 설정되어 있으면 확인
            if hasattr(pytesseract.pytesseract, 'tesseract_cmd') and pytesseract.pytesseract.tesseract_cmd:
                test_path = Path(pytesseract.pytesseract.tesseract_cmd)
                if test_path.exists():
                    return str(test_path)
            
            # Windows 기본 경로들 확인
            default_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            
            # 환경변수에서 찾기
            import shutil
            tesseract_from_path = shutil.which('tesseract')
            if tesseract_from_path:
                default_paths.insert(0, tesseract_from_path)
            
            for path in default_paths:
                if path and Path(path).exists():
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"    ✓ Tesseract 경로 설정: {path}")
                    return path
            
            # Tesseract 버전 확인 시도 (PATH에 있을 때)
            try:
                import subprocess
                result = subprocess.run(['tesseract', '--version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    print(f"    ✓ Tesseract를 PATH에서 찾았습니다")
                    return 'tesseract'  # PATH에 있으면 이름만으로 가능
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
                
            print(f"    ⚠️ Tesseract를 찾을 수 없습니다!")
            print(f"    다음 경로를 확인해주세요:")
            for path in default_paths[:2]:
                print(f"      - {path}")
            print(f"    또는 Tesseract를 설치하고 PATH에 추가하세요.")
            return None
        except Exception as e:
            print(f"    ⚠️ Tesseract 경로 설정 실패: {e}")
            return None
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """이미지 전처리 (OCR 정확도 향상)"""
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
    
    def _get_cache_key(self, pdf_path: Path, page_num: int) -> str:
        """캐시 키 생성"""
        pdf_hash = hashlib.md5(pdf_path.read_bytes()).hexdigest()[:8]
        return f"{pdf_hash}_page_{page_num:03d}.json"
    
    def _load_ocr_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """OCR 캐시 로드 (빈 데이터 검증 포함)"""
        if not self.use_cache:
            return None
        
        cache_path = self.cache_dir / cache_key
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # 빈 OCR 데이터 검증
                texts = cached_data.get('text', [])
                if not texts or len([t for t in texts if t and t.strip()]) == 0:
                    # 빈 캐시는 무효로 간주하고 삭제
                    logger.warning(f"빈 OCR 캐시 감지: {cache_key}, 삭제합니다")
                    cache_path.unlink()
                    return None
                
                return cached_data
            except Exception as e:
                logger.warning(f"캐시 로드 실패: {e}")
                # 손상된 캐시 파일 삭제
                try:
                    cache_path.unlink()
                except:
                    pass
        return None
    
    def _save_ocr_cache(self, cache_key: str, ocr_data: Dict[str, Any]):
        """OCR 캐시 저장"""
        if not self.use_cache:
            return
        
        cache_path = self.cache_dir / cache_key
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(ocr_data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {e}")
    
    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        PDF 전체 파이프라인 실행 (최적화 버전)
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            {
                "lectures": [...],
                "problems": [...],
                "pages_processed": 10,
                "stats": {...}
            }
        """
        start_time = time.time()
        logger.info(f"교재 파이프라인 시작: {pdf_path} (과목: {self.subject})")
        
        # 1. 텍스트 추출 (pdfplumber 사용 시 이미지 변환을 지연)
        page_images = None
        if isinstance(self.text_extractor, PdfplumberExtractor):
            # pdfplumber 사용 시: 텍스트 추출 먼저 (이미지 변환은 나중에 크롭할 때)
            print(f"[1/5] pdfplumber로 텍스트 추출 중... (텍스트 레이어 직접 추출, 매우 빠름)")
            print(f"    💡 텍스트 레이어가 있는 PDF에 최적화됨 (OCR보다 정확하고 빠름)")
            print(f"    ✅ pdfplumber 사용 중 - 텍스트 추출 우선, 이미지 변환은 나중에")
            ocr_start = time.time()
            all_ocr_data = self.text_extractor.extract(pdf_path)
            self.stats["ocr_time"] = time.time() - ocr_start
            print(f"    📊 pdfplumber 추출 완료: {len(all_ocr_data)}개 페이지 ({self.stats['ocr_time']:.1f}초)")
            print(f"    ⚡ 텍스트 추출 완료! (이미지 변환은 크롭 단계에서 수행)")
        elif isinstance(self.text_extractor, OCRExtractor):
            # OCR 사용 시: 이미지 변환 필요
            print(f"[1/5] PDF → 페이지 이미지 변환 중... (DPI: {self.dpi})")
            page_images = self._pdf_to_images(pdf_path)
            print(f"[1/5] 완료: {len(page_images)}개 페이지")
            
            print(f"[2/5] OCR 수행 중... (총 {len(page_images)}개 페이지, 병렬: {self.use_parallel})")
            ocr_start = time.time()
            # OCR은 캐시 지원 (기존 로직 유지)
            all_ocr_data = self._ocr_with_cache(page_images, pdf_path)
            self.stats["ocr_time"] = time.time() - ocr_start
        else:
            raise ValueError("텍스트 추출기가 초기화되지 않았습니다")
        
        # OCR 결과 검증
        total_text_count = 0
        empty_pages = []
        total_lines = 0
        for ocr_data in all_ocr_data:
            texts = [t.strip() for t in ocr_data.get('text', []) if t.strip()]
            if texts:
                total_text_count += len(texts)
                # 줄 단위 그룹화해서 줄 수도 계산
                tops = ocr_data.get('top', [])
                lefts = ocr_data.get('left', [])
                widths = ocr_data.get('width', [])
                heights = ocr_data.get('height', [])
                if tops:
                    lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
                    total_lines += len(lines)
            else:
                empty_pages.append(ocr_data.get('page_num', 0))
        
        print(f"[2/5] 완료: {len(all_ocr_data)}개 페이지 OCR ({self.stats['ocr_time']:.1f}초)")
        print(f"    캐시 히트: {self.stats['cache_hits']}, 미스: {self.stats['cache_misses']}")
        print(f"    추출된 텍스트: {total_text_count}개 단어, {total_lines}개 줄")
        if empty_pages:
            print(f"    ⚠️ 빈 OCR 페이지: {empty_pages[:5]}{'...' if len(empty_pages) > 5 else ''}")
            print(f"    캐시를 삭제하고 다시 시도하세요: data/{self.subject}/cache/ 폴더 삭제")
        elif total_text_count == 0:
            print(f"    ⚠️ 모든 페이지에서 텍스트를 추출하지 못했습니다!")
            print(f"    Tesseract 설치 및 한국어 언어팩 설치를 확인하세요.")
            print(f"    캐시를 삭제하고 다시 시도하세요: data/{self.subject}/cache/ 폴더 삭제")
        
        # 3. 강의 목록 생성 (AI 후처리 전에 구조 파싱)
        print(f"[3/5] 강의 목록 생성 중...")
        lectures = self._extract_lectures(all_ocr_data)
        print(f"[3/5] 완료: {len(lectures)}개 강의")
        
        # 4. 강의 콘텐츠 추출
        print(f"[4/5] 강의 콘텐츠 추출 중...")
        lecture_contents = self._extract_lecture_contents(all_ocr_data, lectures)
        print(f"[4/5] 완료: {len(lecture_contents)}개 강의 콘텐츠")
        
        # 5. 문제 추출
        print(f"[5/5] 문제 추출 중...")
        problems = self._extract_problems(all_ocr_data)
        print(f"[5/5] 완료: {len(problems)}개 문제")
        
        # 6. 개념/본문/문제 이미지 추출 (크롭을 위해 이미지 변환 필수)
        if lectures or problems or lecture_contents:
            # pdfplumber 사용 시: 이미지가 필요할 때만 변환 (지연 로딩)
            # 주의: 이미지 크롭을 위해 페이지 이미지가 반드시 필요함!
            if page_images is None and isinstance(self.text_extractor, PdfplumberExtractor):
                print(f"[이미지] PDF → 페이지 이미지 변환 중... (크롭을 위해 필수)")
                print(f"    💡 pdfplumber로 텍스트는 이미 추출 완료")
                print(f"    📸 개념/본문/문제 영역 크롭을 위해 페이지 이미지 변환 필요")
                page_images = self._pdf_to_images(pdf_path)
                print(f"[이미지] 완료: {len(page_images)}개 페이지 (크롭 준비 완료)")
            
            if page_images:
                print(f"[이미지] 개념, 본문, 문제 영역 이미지 크롭 중...")
                try:
                    self._extract_concept_content_and_problem_images(all_ocr_data, lectures, lecture_contents, problems)
                except Exception as e:
                    logger.warning(f"이미지 추출 실패: {e}")
                    print(f"    ⚠️ 이미지 추출 실패: {e}")
            else:
                print(f"[이미지] ⚠️ 페이지 이미지가 없어 이미지 추출을 건너뜁니다.")
        
        # 7. JSON 저장 (구조 파싱 완료 후)
        print(f"[저장] JSON 파일 저장 중...")
        self._save_results(lectures, lecture_contents, problems)
        print(f"[저장] 완료")
        
        # 8. AI 후처리 (구조 파싱 이후, 선택적 - 텍스트 정제만)
        if self.use_ai_postprocess:
            print(f"[후처리] AI 텍스트 정제 중... (⚠️ LLM API 호출로 시간이 오래 걸릴 수 있습니다)")
            print(f"    💡 빠른 처리를 원하면 다음 실행 시 'AI 후처리 사용? (y/N)'에 'n' 입력")
            ai_start = time.time()
            lecture_contents, problems = self._ai_postprocess_structured_data(lecture_contents, problems)
            self.stats["ai_postprocess_time"] = time.time() - ai_start
            print(f"[후처리] 완료: AI 텍스트 정제 ({self.stats['ai_postprocess_time']:.1f}초)")
            
            # 정제된 데이터 다시 저장
            print(f"[저장] 정제된 JSON 파일 저장 중...")
            self._save_results(lectures, lecture_contents, problems)
            print(f"[저장] 완료")
        else:
            print(f"[후처리] AI 후처리 건너뜀 (빠른 처리 모드)")
        
        self.stats["total_time"] = time.time() - start_time
        pages_count = len(page_images) if page_images is not None else len(all_ocr_data)
        self.stats["pages_processed"] = pages_count

        print(f"\n[성능 통계]")
        print(f"  총 처리 시간: {self.stats['total_time']:.1f}초")
        print(f"  OCR 시간: {self.stats['ocr_time']:.1f}초")
        if self.use_ai_postprocess:
            print(f"  AI 후처리 시간: {self.stats['ai_postprocess_time']:.1f}초")
        if pages_count > 0:
            print(f"  페이지당 평균: {self.stats['total_time']/pages_count:.2f}초")

        return {
            "lectures": lectures,
            "problems": problems,
            "pages_processed": pages_count,
            "stats": self.stats
        }
    
    def _pdf_to_images(self, pdf_path: Path) -> List[Image.Image]:
        """PDF → 페이지 이미지 변환 (최적화)"""
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image가 설치되지 않았습니다. pip install pdf2image")
        
        # PDF 파일 크기 확인
        pdf_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if pdf_size_mb > 50:
            print(f"    ⚠️ 큰 파일 감지 ({pdf_size_mb:.1f}MB). 변환에 시간이 걸릴 수 있습니다...")
        
        convert_kwargs = {"dpi": self.dpi}
        if self.poppler_path:
            convert_kwargs["poppler_path"] = self.poppler_path
        
        logger.info(f"PDF 이미지 변환 시작: {pdf_path} (DPI: {self.dpi})")
        
        # 첫 페이지 변환 테스트 (빠른 피드백)
        try:
            print(f"    첫 페이지 변환 테스트 중...")
            first_page = convert_from_path(pdf_path, first_page=1, last_page=1, **convert_kwargs)
            if first_page:
                print(f"    ✓ PDF 읽기 성공! 전체 변환 시작...")
        except Exception as e:
            print(f"    ⚠️ 첫 페이지 테스트 실패: {e}")
        
        # PDF 페이지 수 미리 확인 (진행 상황 파악)
        total_pages = None
        try:
            import fitz  # PyMuPDF
            pdf_doc = fitz.open(pdf_path)
            total_pages = len(pdf_doc)
            pdf_doc.close()
            print(f"    📄 총 {total_pages}개 페이지 감지됨")
        except ImportError:
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    total_pages = len(pdf_reader.pages)
                    print(f"    📄 총 {total_pages}개 페이지 감지됨")
            except:
                # pdfplumber로 시도
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        total_pages = len(pdf.pages)
                        print(f"    📄 총 {total_pages}개 페이지 감지됨 (pdfplumber)")
                except:
                    total_pages = None
                    print(f"    ⚠️ 페이지 수를 미리 확인할 수 없습니다")
        
        # 전체 PDF 변환 (페이지 제한 적용)
        start_time = time.time()
        if self.max_pages:
            print(f"    PDF 변환 중... (첫 {self.max_pages}페이지만 처리)")
            convert_kwargs["first_page"] = 1
            convert_kwargs["last_page"] = self.max_pages
            expected_pages = min(self.max_pages, total_pages if total_pages else self.max_pages)
        else:
            expected_pages = total_pages if total_pages else None
            if expected_pages:
                # DPI에 따른 예상 시간 계산 (DPI가 낮을수록 빠름)
                time_per_page = 0.4 if self.dpi <= 180 else (0.5 if self.dpi <= 200 else 0.6)
                estimated_time = expected_pages * time_per_page
                print(f"    PDF 전체 변환 중... ({expected_pages}개 페이지, 예상 시간: {estimated_time:.1f}초)")
            else:
                print(f"    PDF 전체 변환 중... (진행 중입니다, 잠시만 기다려주세요)")
        
        try:
            # 변환 시작 전 시간 로그
            start_time_str = time.strftime('%H:%M:%S')
            print(f"    ⏳ 변환 시작: {start_time_str} (잠시만 기다려주세요...)")
            if expected_pages:
                # DPI에 따른 예상 시간 계산
                time_per_page = 0.25 if self.dpi <= 180 else (0.3 if self.dpi <= 200 else 0.4)
                estimated_time = expected_pages * time_per_page
                print(f"    💡 팁: 대용량 PDF는 변환에 시간이 걸릴 수 있습니다 (예상: {estimated_time:.0f}초)")
            
            images = convert_from_path(pdf_path, **convert_kwargs)
            elapsed = time.time() - start_time
            logger.info(f"PDF 이미지 변환 완료: {len(images)}개 페이지 ({elapsed:.1f}초)")
            
            elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            if len(images) > 0:
                avg_time = elapsed / len(images)
                print(f"    ✓ 변환 완료: {len(images)}개 페이지 ({elapsed:.1f}초 소요, 평균 {avg_time:.2f}초/페이지)")
            else:
                print(f"    ✓ 변환 완료: {len(images)}개 페이지 ({elapsed:.1f}초 소요)")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"    ❌ [오류] PDF 변환 실패 (소요 시간: {elapsed:.1f}초): {e}")
            raise
        
        # 이미지 전처리 및 저장 (병렬)
        print(f"    페이지 이미지 전처리 및 저장 중... (총 {len(images)}개)")
        processed_images = []
        
        if self.use_parallel and len(images) > 1:
            # 병렬 이미지 처리 (워커 수 증가: 4 → 8 또는 CPU 코어 수)
            worker_count = min(8, self.max_workers) if self.max_workers else min(8, mp.cpu_count())
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = []
                for i, image in enumerate(images, 1):
                    future = executor.submit(self._process_and_save_image, image, i)
                    futures.append((future, i))
                
                completed = 0
                for future, i in futures:
                    processed_image = future.result()
                    processed_images.append(processed_image)
                    completed += 1
                    if completed % 5 == 0 or completed == len(images) or completed == 1:
                        print(f"    저장 완료: {completed}/{len(images)} 페이지")
        else:
            # 순차 처리
            for i, image in enumerate(images, 1):
                processed_image = self._process_and_save_image(image, i)
                processed_images.append(processed_image)
                if i % 5 == 0 or i == len(images) or i == 1:
                    print(f"    저장 완료: {i}/{len(images)} 페이지")
        
        return processed_images
    
    def _process_and_save_image(self, image: Image.Image, page_num: int) -> Image.Image:
        """이미지 전처리 및 저장"""
        # pages 폴더가 없으면 생성
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        
        # 전처리
        processed_image = self._preprocess_image(image)
        
        # 저장
        image_path = self.pages_dir / f"page_{page_num:03d}.png"
        processed_image.save(image_path)
        
        return processed_image
    
    def _ocr_with_cache(self, page_images: List[Image.Image], pdf_path: Path) -> List[Dict[str, Any]]:
        """
        OCR 수행 (캐시 지원)
        
        새로운 OCRExtractor를 사용하되, 캐시 기능은 유지
        """
        all_ocr_data = [None] * len(page_images)
        
        for page_num, page_image in enumerate(page_images, 1):
            # 캐시 확인
            cache_key = self._get_cache_key(pdf_path, page_num)
            cached_data = self._load_ocr_cache(cache_key)
            
            if cached_data:
                all_ocr_data[page_num - 1] = cached_data
                self.stats["cache_hits"] += 1
            else:
                # OCR 추출기 사용
                ocr_data = self.text_extractor._ocr_page(page_image, page_num)
                all_ocr_data[page_num - 1] = ocr_data
                self._save_ocr_cache(cache_key, ocr_data)
                self.stats["cache_misses"] += 1
            
            if page_num % 10 == 0 or page_num == 1:
                print(f"    OCR 진행 중: {page_num}/{len(page_images)} 페이지")
        
        return all_ocr_data
    
    def _ocr_pages_parallel(self, page_images: List[Image.Image], pdf_path: Path) -> List[Dict[str, Any]]:
        """
        [레거시] 병렬 OCR 처리 (OCRExtractor로 대체됨)
        
        호환성을 위해 유지하지만, 새로운 코드는 OCRExtractor 사용
        """
        """병렬 OCR 처리 (캐싱 포함)"""
        if not TESSERACT_AVAILABLE:
            raise ImportError("pytesseract가 설치되지 않았습니다. pip install pytesseract")
        
        all_ocr_data = [None] * len(page_images)
        
        # Tesseract 확인
        if not self.tesseract_cmd:
            print(f"    ⚠️ Tesseract가 설정되지 않아 OCR을 건너뜁니다.")
            print(f"    빈 OCR 데이터를 반환합니다.")
            return all_ocr_data
        
        if self.use_parallel and len(page_images) > 1:
            # 병렬 처리
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                
                for page_num, page_image in enumerate(page_images, 1):
                    # 캐시 확인
                    cache_key = self._get_cache_key(pdf_path, page_num)
                    cached_data = self._load_ocr_cache(cache_key)
                    
                    # 캐시 데이터 검증 (빈 데이터인지 확인)
                    if cached_data:
                        texts = cached_data.get('text', [])
                        valid_texts = [t for t in texts if t and t.strip()]
                        if valid_texts:
                            all_ocr_data[page_num - 1] = cached_data
                            self.stats["cache_hits"] += 1
                        else:
                            # 빈 캐시는 무효로 간주하고 OCR 수행
                            logger.debug(f"빈 캐시 무효화: 페이지 {page_num}, OCR 재수행")
                            future = executor.submit(
                                _ocr_page_worker,
                                (page_image, page_num, self.lang, self.tesseract_cmd)
                            )
                            futures[future] = (page_num, cache_key)
                            self.stats["cache_misses"] += 1
                    else:
                        # OCR 작업 제출
                        future = executor.submit(
                            _ocr_page_worker,
                            (page_image, page_num, self.lang, self.tesseract_cmd)
                        )
                        futures[future] = (page_num, cache_key)
                        self.stats["cache_misses"] += 1
                
                # 결과 수집
                completed = 0
                ocr_errors = []
                for future in as_completed(futures):
                    page_num, cache_key = futures[future]
                    try:
                        ocr_data = future.result()
                        # OCR 실패 확인 (텍스트가 비어있으면)
                        if not ocr_data.get('text') or len([t for t in ocr_data.get('text', []) if t.strip()]) == 0:
                            ocr_errors.append(page_num)
                        all_ocr_data[page_num - 1] = ocr_data
                        self._save_ocr_cache(cache_key, ocr_data)
                        completed += 1
                        if completed % 10 == 0 or completed == len(futures):
                            print(f"    OCR 진행 중: {completed}/{len(futures)} 페이지")
                    except Exception as e:
                        logger.error(f"OCR 오류 (페이지 {page_num}): {e}")
                        ocr_errors.append(page_num)
                
                # OCR 에러 요약
                if ocr_errors:
                    print(f"    ⚠️ OCR 실패한 페이지: {len(ocr_errors)}개")
                    if len(ocr_errors) == len(futures):
                        print(f"    모든 페이지에서 OCR 실패. Tesseract 설치를 확인하세요.")
        else:
            # 순차 처리
            for page_num, page_image in enumerate(page_images, 1):
                # 캐시 확인
                cache_key = self._get_cache_key(pdf_path, page_num)
                cached_data = self._load_ocr_cache(cache_key)
                
                # 캐시 데이터 검증 (빈 데이터인지 확인)
                if cached_data:
                    texts = cached_data.get('text', [])
                    valid_texts = [t for t in texts if t and t.strip()]
                    if valid_texts:
                        all_ocr_data[page_num - 1] = cached_data
                        self.stats["cache_hits"] += 1
                    else:
                        # 빈 캐시는 무효로 간주하고 OCR 수행
                        logger.debug(f"빈 캐시 무효화: 페이지 {page_num}, OCR 재수행")
                        ocr_data = self._ocr_page(page_image, page_num)
                        all_ocr_data[page_num - 1] = ocr_data
                        self._save_ocr_cache(cache_key, ocr_data)
                        self.stats["cache_misses"] += 1
                else:
                    ocr_data = self._ocr_page(page_image, page_num)
                    all_ocr_data[page_num - 1] = ocr_data
                    self._save_ocr_cache(cache_key, ocr_data)
                    self.stats["cache_misses"] += 1
                
                if page_num % 10 == 0 or page_num == 1:
                    print(f"    OCR 진행 중: {page_num}/{len(page_images)} 페이지")
        
        return all_ocr_data
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        pdfplumber를 사용하여 텍스트와 좌표 추출
        
        OCR보다 훨씬 정확하고 빠름 (텍스트 레이어가 있는 PDF의 경우)
        """
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber가 설치되지 않았습니다. pip install pdfplumber")
        
        all_ocr_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                if self.max_pages:
                    total_pages = min(total_pages, self.max_pages)
                
                for page_num in range(1, total_pages + 1):
                    page = pdf.pages[page_num - 1]
                    
                    # 페이지 크기 확인 (좌표 변환용)
                    page_width = page.width
                    page_height = page.height
                    
                    # 단어 단위로 추출 (좌표 정보 포함)
                    words = page.extract_words(
                        x_tolerance=3,
                        y_tolerance=3,
                        keep_blank_chars=False
                    )
                    
                    if not words:
                        # 빈 페이지
                        all_ocr_data.append({
                            'page_num': page_num,
                            'text': [],
                            'left': [],
                            'top': [],
                            'width': [],
                            'height': []
                        })
                        continue
                    
                    # OCR 형식과 호환되도록 변환
                    # pdfplumber는 PDF 좌표계 사용, 이미지는 픽셀 좌표계
                    # DPI를 고려한 스케일링 필요
                    texts = []
                    lefts = []
                    tops = []
                    widths = []
                    heights = []
                    
                    # 스케일 팩터 계산 (PDF 포인트 → 픽셀)
                    # 일반적으로 PDF는 72 DPI, 이미지는 설정된 DPI 사용
                    scale_x = self.dpi / 72.0
                    scale_y = self.dpi / 72.0
                    
                    for word in words:
                        text = word.get('text', '').strip()
                        if text:
                            texts.append(text)
                            # PDF 좌표를 픽셀 좌표로 변환
                            x0 = int(word.get('x0', 0) * scale_x)
                            y0 = int(word.get('top', 0) * scale_y)  # pdfplumber는 top 사용
                            x1 = int(word.get('x1', 0) * scale_x)
                            y1 = int(word.get('bottom', 0) * scale_y)
                            
                            lefts.append(x0)
                            tops.append(y0)
                            widths.append(x1 - x0)
                            heights.append(y1 - y0)
                    
                    all_ocr_data.append({
                        'page_num': page_num,
                        'text': texts,
                        'left': lefts,
                        'top': tops,
                        'width': widths,
                        'height': heights
                    })
                    
                    if page_num % 10 == 0 or page_num == 1:
                        word_count = len(texts)
                        print(f"    텍스트 추출 진행 중: {page_num}/{total_pages} 페이지 ({word_count}개 단어)")
        
        except Exception as e:
            logger.error(f"pdfplumber 추출 실패: {e}")
            print(f"    ⚠️ pdfplumber 추출 실패: {e}")
            print(f"    OCR로 대체합니다...")
            # OCR로 대체
            if not hasattr(self, '_page_images_cache'):
                self._page_images_cache = self._pdf_to_images(pdf_path)
            return self._ocr_pages_parallel(self._page_images_cache, pdf_path)
        
        total_words = sum(len(data.get('text', [])) for data in all_ocr_data)
        print(f"[2/5] 완료: {len(all_ocr_data)}개 페이지 텍스트 추출 ({self.stats['ocr_time']:.1f}초)")
        print(f"    추출된 텍스트: {total_words}개 단어")
        
        return all_ocr_data
    
    def _ocr_page(self, page_image: Image.Image, page_num: int) -> Dict[str, Any]:
        """단일 페이지 OCR 수행"""
        if not TESSERACT_AVAILABLE:
            raise ImportError("pytesseract가 설치되지 않았습니다. pip install pytesseract")
        
        # OCR 설정 개선 (PSM 모드로 레이아웃 분석 향상)
        ocr_config = r'--psm 6'  # PSM 6: 단일 균일한 텍스트 블록 가정
        # PSM 모드 설명:
        # 3 = 완전 자동 페이지 분할, OCR 없음
        # 6 = 단일 균일한 텍스트 블록 가정 (기본)
        # 11 = 희박한 텍스트, OSD 없음
        # 12 = OSD만 (레이아웃 분석)
        
        ocr_data = pytesseract.image_to_data(
            page_image,
            lang=self.lang,
            output_type=Output.DICT,
            config=ocr_config
        )
        
        ocr_data['page_num'] = page_num
        return ocr_data
    
    def _ai_postprocess_structured_data(
        self,
        lecture_contents: List[Dict[str, Any]],
        problems: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        구조 파싱 이후 AI 후처리 (텍스트 정제만) - 최적화 버전
        
        최적화:
        - 병렬 처리로 여러 API 호출 동시 실행 (5-10배 빠름)
        - 배치 처리로 여러 텍스트를 한 번에 처리
        - 진행률 표시
        """
        if not self.ai_postprocessor:
            return lecture_contents, problems
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        # 모든 텍스트 항목 수집 (병렬 처리용)
        text_items = []  # (type, content_ref, text) 튜플 리스트
        
        # 강의 콘텐츠 텍스트 수집
        for content_idx, content in enumerate(lecture_contents):
            # 섹션 텍스트
            if 'sections' in content:
                for section_idx, section in enumerate(content['sections']):
                    if 'content' in section:
                        for item_idx, item in enumerate(section['content']):
                            if isinstance(item, str) and item.strip():
                                text_items.append(('lecture_section', (content_idx, section_idx, item_idx), item))
            
            # 본문 문단 텍스트
            if 'content' in content:
                for para_idx, para in enumerate(content['content']):
                    if isinstance(para, str) and para.strip():
                        text_items.append(('lecture_content', (content_idx, para_idx), para))
        
        # 문제 텍스트 수집
        for problem_idx, problem in enumerate(problems):
            if 'content' in problem:
                for item_idx, item in enumerate(problem['content']):
                    if isinstance(item, str) and item.strip():
                        text_items.append(('problem', (problem_idx, item_idx), item))
        
        if not text_items:
            return lecture_contents, problems
        
        print(f"    📊 총 {len(text_items)}개 텍스트 항목 처리 중... (병렬 처리)")
        
        # 병렬 처리로 텍스트 정제
        cleaned_texts = {}
        max_workers = min(10, len(text_items))  # 최대 10개 동시 요청 (API rate limit 고려)
        
        def process_text(item_info):
            """단일 텍스트 처리"""
            item_type, ref, text = item_info
            try:
                cleaned = self.ai_postprocessor.clean_extracted_text(text, subject=self.subject)
                return (item_type, ref, cleaned)
            except Exception as e:
                logger.warning(f"AI 후처리 실패 ({item_type}): {e}")
                return (item_type, ref, text)  # 실패 시 원본 반환
        
        start_time = time.time()
        completed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_text, item): item for item in text_items}
            
            for future in as_completed(futures):
                try:
                    item_type, ref, cleaned = future.result()
                    cleaned_texts[(item_type, ref)] = cleaned
                    completed += 1
                    
                    # 진행률 표시 (10개마다 또는 완료 시)
                    if completed % 10 == 0 or completed == len(text_items):
                        elapsed = time.time() - start_time
                        avg_time = elapsed / completed if completed > 0 else 0
                        remaining = (len(text_items) - completed) * avg_time
                        print(f"    진행: {completed}/{len(text_items)} ({completed*100//len(text_items)}%) | "
                              f"예상 남은 시간: {remaining:.1f}초")
                except Exception as e:
                    logger.error(f"병렬 처리 중 오류: {e}")
        
        # 정제된 텍스트를 원본 구조에 반영
        processed_lectures = []
        for content_idx, content in enumerate(lecture_contents):
            processed_content = content.copy()
            
            # 섹션 텍스트 반영
            if 'sections' in processed_content:
                for section_idx, section in enumerate(processed_content['sections']):
                    if 'content' in section:
                        for item_idx, item in enumerate(section['content']):
                            if isinstance(item, str):
                                key = ('lecture_section', (content_idx, section_idx, item_idx))
                                if key in cleaned_texts:
                                    section['content'][item_idx] = cleaned_texts[key]
            
            # 본문 문단 텍스트 반영
            if 'content' in processed_content:
                for para_idx, para in enumerate(processed_content['content']):
                    if isinstance(para, str):
                        key = ('lecture_content', (content_idx, para_idx))
                        if key in cleaned_texts:
                            processed_content['content'][para_idx] = cleaned_texts[key]
            
            processed_lectures.append(processed_content)
        
        # 문제 텍스트 반영
        processed_problems = []
        for problem_idx, problem in enumerate(problems):
            processed_problem = problem.copy()
            
            if 'content' in processed_problem:
                for item_idx, item in enumerate(processed_problem['content']):
                    if isinstance(item, str):
                        key = ('problem', (problem_idx, item_idx))
                        if key in cleaned_texts:
                            processed_problem['content'][item_idx] = cleaned_texts[key]
            
            processed_problems.append(processed_problem)
        
        total_time = time.time() - start_time
        print(f"    ✓ 병렬 처리 완료: {len(text_items)}개 항목 ({total_time:.1f}초, 평균 {total_time/len(text_items):.2f}초/항목)")
        
        return processed_lectures, processed_problems
    
    def _extract_lectures(self, all_ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        강의/단원 목록 자동 생성 (과목별 분기)
        """
        if self.subject == 'literature':
            return self._extract_lectures_literature(all_ocr_data)
        elif self.subject == 'math1':
            return self._extract_lectures_math1(all_ocr_data)
        elif self.subject == 'english':
            return self._extract_lectures_english(all_ocr_data)
        else:
            # 기본값 (문학과 동일)
            return self._extract_lectures_literature(all_ocr_data)
    
    def _extract_lectures_literature(self, all_ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        문학 강의 목록 자동 생성 (config 기반)
        
        개선사항:
        - 단어 단위가 아닌 문장 단위 매칭
        - y좌표 기반으로 같은 줄의 단어 결합
        - 페이지 상단의 큰 텍스트 우선 인식
        """
        lectures = []
        lecture_id = 1
        patterns = self.config.get('lecture_title_patterns', [])
        
        # OCR 데이터 디버깅
        if all_ocr_data and len(all_ocr_data) > 0:
            first_page_ocr = all_ocr_data[0]
            first_page_texts = [t.strip() for t in first_page_ocr.get('text', []) if t.strip()]
            if first_page_texts:
                print(f"    [디버그] 첫 페이지 OCR 단어 샘플 (상위 20개):")
                for i, text in enumerate(first_page_texts[:20], 1):
                    print(f"      {i}. {text[:60]}")
                
                # 줄 단위로 그룹화된 텍스트도 출력
                texts = first_page_ocr.get('text', [])
                tops = first_page_ocr.get('top', [])
                lefts = first_page_ocr.get('left', [])
                widths = first_page_ocr.get('width', [])
                heights = first_page_ocr.get('height', [])
                
                if texts and tops:
                    lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
                    print(f"    [디버그] 첫 페이지 줄 단위 텍스트 (상위 20줄):")
                    for i, line in enumerate(lines[:20], 1):
                        line_text = " ".join([word['text'] for word in line])
                        if line_text.strip():
                            print(f"      {i}. {line_text[:80]}")
            else:
                print(f"    ⚠️ 첫 페이지에서 OCR 텍스트를 찾을 수 없습니다!")
                print(f"    캐시를 삭제하고 다시 시도하세요: data/{self.subject}/cache/ 폴더 삭제")
                return []
        
        # 각 페이지에서 강의 제목 찾기
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts or len([t for t in texts if t.strip()]) == 0:
                continue
            
            # y좌표 기준으로 같은 줄의 단어들을 그룹화
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 각 줄을 문장으로 결합하고 패턴 매칭
            # 페이지 상단의 큰 텍스트만 강의 제목으로 인식 (상위 40% 영역, 큰 폰트)
            page_top_threshold = None
            if lines and len(lines) > 0 and len(lines[0]) > 0:
                # 첫 번째 줄의 y좌표를 기준으로 상단 영역 계산
                first_line_y = lines[0][0]['top']
                # 이미지 높이 추정 (마지막 줄의 y좌표 + 높이)
                if lines and len(lines[-1]) > 0:
                    last_line = lines[-1]
                    estimated_page_height = last_line[-1]['top'] + last_line[-1]['height']
                    page_top_threshold = first_line_y + (estimated_page_height * 0.4)  # 상단 40%
            
            # 평균 폰트 크기 계산 (높이 기준) - 조건 완화
            if lines:
                total_height = sum(word['height'] for line in lines[:10] for word in line[:3])
                total_words = sum(len(line[:3]) for line in lines[:10])
                if total_words > 0:
                    avg_height = total_height / min(30, total_words)
                    min_title_height = avg_height * 1.0  # 평균 이상이면 OK (1.2배 → 1.0배로 완화)
                else:
                    min_title_height = 0
            else:
                min_title_height = 0
            
            for line in lines:
                # 같은 줄의 단어들을 공백으로 결합
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                if not line_text or len(line_text) < 5:  # 최소 길이 5자 이상
                    continue
                
                # 목차 형식 제외 (페이지 번호 포함된 것들)
                # 예: "01 모 죽지랑가 (득오) / 화왕가 (이익) 044"
                if re.search(r'\d{3,}', line_text) and len(line_text) < 50:
                    # 3자리 이상 숫자가 있고 텍스트가 짧으면 목차로 간주
                    continue
                
                # 작품 제목 형식 제외 (괄호 안에 작가명이 있는 짧은 텍스트)
                # 예: "03 귀 거래 귀거래 말뿐이오 ~ (이현보)"
                if re.search(r'\([가-힣]+\)', line_text) and len(line_text) < 40:
                    # 괄호 안에 한글이 있고 텍스트가 짧으면 작품 제목으로 간주
                    continue
                
                # 문제 번호/지문 제외 (숫자로 시작하지만 "N강" 형식이 아닌 경우)
                # 예: "01 간을 옮긴 이유도...", "03 주제 슬픔의 승화를..."
                if re.match(r'^\d{2,}\s+[가-힣]', line_text) and not re.search(r'^\d+강', line_text):
                    # 2자리 이상 숫자로 시작하고 "N강" 형식이 아니면 문제 번호/지문일 가능성
                    continue
                
                # 문제 지문 형식 제외 (긴 문장으로 시작하는 경우)
                # 예: "01 간을 옮긴 이유도 겉으로는 가족에 대한 미안한 마음을 언급했지"
                if len(line_text) > 30 and re.match(r'^\d{2,}\s+[가-힣]{5,}', line_text) and not re.search(r'^\d+강', line_text):
                    # 2자리 이상 숫자로 시작하고 한글이 5자 이상이고 "N강" 형식이 아니면 문제 지문일 가능성
                    continue
                
                # 페이지 상단 영역 체크 (상단 40%로 제한)
                line_y = line[0]['top']
                if page_top_threshold and line_y > page_top_threshold * 0.8:  # 상단 40%로 제한
                    continue  # 페이지 상단이 아니면 스킵
                
                # 큰 폰트 체크 (조건 강화)
                line_height = max(word['height'] for word in line)
                if min_title_height > 0 and line_height < min_title_height * 0.9:  # 0.9배 이상이어야 함
                    continue  # 너무 작은 폰트는 스킵
                
                # 패턴 매칭
                if self._matches_patterns(line_text, patterns):
                    # 강의 제목 검증: 반드시 "N강" 형식이어야 함 (문제 번호/지문 제외)
                    # "1강", "2강", "3강" 등으로 시작하거나 "N강 |" 형식이어야 함
                    lecture_title_match = re.search(r'^(\d+)강', line_text)
                    if not lecture_title_match:
                        # "N강" 형식이 아니면 스킵 (문제 번호나 지문일 가능성)
                        continue
                    
                    # 문제/해설 페이지 제외 (페이지 번호가 매우 높은 경우, 또는 "정답과 해설" 텍스트가 있는 경우)
                    # 문학 교재는 보통 1-2강이 8-40페이지 정도, 3강 이상은 더 뒤쪽
                    # 하지만 문제/해설 페이지는 보통 300페이지 이후
                    if page_num > 200:
                        # 200페이지 이후는 문제/해설 페이지일 가능성이 높음
                        # "정답과 해설", "답", "해설" 등의 키워드가 있으면 제외
                        if any(keyword in line_text for keyword in ["정답", "해설", "답", "문제", "보기"]):
                            continue
                        # "N강" 형식이지만 페이지가 너무 높으면 추가 검증
                        # 실제 강의 제목은 보통 "N강 |" 또는 "N강" 다음에 주제가 나옴
                        if not re.search(r'^\d+강\s*[|]', line_text) and len(line_text) < 20:
                            # "N강 |" 형식이 아니고 짧으면 문제 번호일 가능성
                            continue
                    
                    # bbox 계산 (줄의 첫 단어와 마지막 단어 기준)
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    lectures.append({
                        "lecture_id": lecture_id,
                        "title": line_text,
                        "page": page_num,
                        "bbox": [left, top, right, bottom]
                    })
                    lecture_id += 1
                    print(f"    ✓ 강의 발견: {line_text[:50]} (페이지 {page_num})")
                else:
                    # 디버깅: 패턴 매칭 실패한 경우 로그 (짧은 텍스트만)
                    if len(line_text) < 30 and re.match(r'^\d+', line_text):
                        print(f"    [디버그] 패턴 미매칭: '{line_text[:40]}' (페이지 {page_num})")
        
        if not lectures:
            print(f"    ⚠️ 강의를 찾을 수 없습니다.")
            print(f"    사용된 패턴: {patterns}")
            print(f"    캐시를 삭제하고 OCR을 다시 수행하세요.")
            # 모든 페이지의 상위 텍스트 출력 (디버깅)
            print(f"    [디버그] 각 페이지 상위 텍스트 (줄 단위):")
            for ocr_data in all_ocr_data[:5]:  # 처음 5페이지만
                page_num = ocr_data.get('page_num', 0)
                texts = ocr_data.get('text', [])
                tops = ocr_data.get('top', [])
                lefts = ocr_data.get('left', [])
                widths = ocr_data.get('width', [])
                heights = ocr_data.get('height', [])
                
                if texts and tops:
                    lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
                    print(f"      페이지 {page_num} (상위 10줄):")
                    for i, line in enumerate(lines[:10], 1):
                        line_text = " ".join([word['text'] for word in line])
                        if line_text.strip():
                            print(f"        {i}. {line_text[:70]}")
        
        return lectures
    
    def _extract_lectures_math1(self, all_ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        수학Ⅰ 단원 목록 자동 생성
        
        수학 구조:
        - 단원(Unit): "1단원 지수함수와 로그함수"
        - 개념(Concept): "1. 지수함수", "(가) 지수함수"
        - 예제(Example): "예제 1"
        - 유제(Exercise): "유제 1"
        - 문제(Problem): "1.", "2."
        """
        units = []
        unit_id = 1
        patterns = self.config.get('lecture_title_patterns', [])
        
        # OCR 데이터 디버깅
        if all_ocr_data and len(all_ocr_data) > 0:
            first_page_ocr = all_ocr_data[0]
            first_page_texts = [t.strip() for t in first_page_ocr.get('text', []) if t.strip()]
            if first_page_texts:
                print(f"    [디버그] 첫 페이지 OCR 단어 샘플 (상위 20개):")
                for i, text in enumerate(first_page_texts[:20], 1):
                    print(f"      {i}. {text[:60]}")
        
        # 각 페이지에서 단원 제목 찾기
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts or len([t for t in texts if t.strip()]) == 0:
                continue
            
            # y좌표 기준으로 같은 줄의 단어들을 그룹화
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 페이지 상단 영역 체크 (상단 30%)
            page_top_threshold = None
            if lines and len(lines) > 0 and len(lines[0]) > 0:
                first_line_y = lines[0][0]['top']
                if lines and len(lines[-1]) > 0:
                    last_line = lines[-1]
                    estimated_page_height = last_line[-1]['top'] + last_line[-1]['height']
                    page_top_threshold = first_line_y + (estimated_page_height * 0.3)
            
            # 평균 폰트 크기 계산
            if lines:
                total_height = sum(word['height'] for line in lines[:10] for word in line[:3])
                total_words = sum(len(line[:3]) for line in lines[:10])
                if total_words > 0:
                    avg_height = total_height / min(30, total_words)
                    min_title_height = avg_height * 1.0
                else:
                    min_title_height = 0
            else:
                min_title_height = 0
            
            for line in lines:
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                if not line_text or len(line_text) < 5:
                    continue
                
                # 페이지 상단 영역 체크
                line_y = line[0]['top']
                if page_top_threshold and line_y > page_top_threshold:
                    continue
                
                # 큰 폰트 체크
                line_height = max(word['height'] for word in line)
                if min_title_height > 0 and line_height < min_title_height * 0.9:
                    continue
                
                # 패턴 매칭
                if self._matches_patterns(line_text, patterns):
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    units.append({
                        "lecture_id": unit_id,
                        "title": line_text,
                        "page": page_num,
                        "bbox": [left, top, right, bottom]
                    })
                    unit_id += 1
                    print(f"    ✓ 단원 발견: {line_text[:50]} (페이지 {page_num})")
        
        if not units:
            print(f"    ⚠️ 단원을 찾을 수 없습니다.")
            print(f"    사용된 패턴: {patterns}")
        
        return units
    
    def _extract_lectures_english(self, all_ocr_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        영어 Unit 목록 자동 생성
        
        영어 구조:
        - Unit: "Unit 1", "1단원"
        - 지문(Passage): "지문 1", "Passage 1"
        - 문제(Problem): "1.", "2."
        """
        units = []
        unit_id = 1
        patterns = self.config.get('lecture_title_patterns', [])
        
        # OCR 데이터 디버깅
        if all_ocr_data and len(all_ocr_data) > 0:
            first_page_ocr = all_ocr_data[0]
            first_page_texts = [t.strip() for t in first_page_ocr.get('text', []) if t.strip()]
            if first_page_texts:
                print(f"    [디버그] 첫 페이지 OCR 단어 샘플 (상위 20개):")
                for i, text in enumerate(first_page_texts[:20], 1):
                    print(f"      {i}. {text[:60]}")
        
        # 각 페이지에서 Unit 제목 찾기
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts or len([t for t in texts if t.strip()]) == 0:
                continue
            
            # y좌표 기준으로 같은 줄의 단어들을 그룹화
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 페이지 상단 영역 체크 (상단 30%)
            page_top_threshold = None
            if lines and len(lines) > 0 and len(lines[0]) > 0:
                first_line_y = lines[0][0]['top']
                if lines and len(lines[-1]) > 0:
                    last_line = lines[-1]
                    estimated_page_height = last_line[-1]['top'] + last_line[-1]['height']
                    page_top_threshold = first_line_y + (estimated_page_height * 0.3)
            
            # 평균 폰트 크기 계산
            if lines:
                total_height = sum(word['height'] for line in lines[:10] for word in line[:3])
                total_words = sum(len(line[:3]) for line in lines[:10])
                if total_words > 0:
                    avg_height = total_height / min(30, total_words)
                    min_title_height = avg_height * 1.0
                else:
                    min_title_height = 0
            else:
                min_title_height = 0
            
            for line in lines:
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                if not line_text or len(line_text) < 3:
                    continue
                
                # 페이지 상단 영역 체크
                line_y = line[0]['top']
                if page_top_threshold and line_y > page_top_threshold:
                    continue
                
                # 큰 폰트 체크
                line_height = max(word['height'] for word in line)
                if min_title_height > 0 and line_height < min_title_height * 0.9:
                    continue
                
                # 패턴 매칭 (대소문자 무시)
                line_text_lower = line_text.lower()
                matched = False
                for pattern in patterns:
                    if re.search(pattern, line_text_lower, re.IGNORECASE):
                        matched = True
                        break
                
                if matched:
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    units.append({
                        "lecture_id": unit_id,
                        "title": line_text,
                        "page": page_num,
                        "bbox": [left, top, right, bottom]
                    })
                    unit_id += 1
                    print(f"    ✓ Unit 발견: {line_text[:50]} (페이지 {page_num})")
        
        if not units:
            print(f"    ⚠️ Unit을 찾을 수 없습니다.")
            print(f"    사용된 패턴: {patterns}")
        
        return units
    
    def _group_texts_by_line(
        self,
        texts: List[str],
        tops: List[int],
        lefts: List[int],
        widths: List[int],
        heights: List[int],
        y_threshold: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        y좌표 기준으로 같은 줄의 단어들을 그룹화
        
        Args:
            texts: 텍스트 리스트
            tops: y좌표 리스트
            lefts: x좌표 리스트
            widths: 너비 리스트
            heights: 높이 리스트
            y_threshold: 같은 줄으로 판단할 y좌표 차이 임계값
        
        Returns:
            줄별로 그룹화된 단어 리스트
        """
        # 단어 정보 수집
        words = []
        for i in range(len(texts)):
            text = texts[i].strip()
            if not text:
                continue
            words.append({
                'text': text,
                'top': tops[i] if i < len(tops) else 0,
                'left': lefts[i] if i < len(lefts) else 0,
                'width': widths[i] if i < len(widths) else 0,
                'height': heights[i] if i < len(heights) else 0,
                'index': i
            })
        
        if not words:
            return []
        
        # y좌표 기준으로 정렬
        words.sort(key=lambda w: (w['top'], w['left']))
        
        # 같은 줄로 그룹화
        lines = []
        current_line = [words[0]]
        current_y = words[0]['top']
        
        for word in words[1:]:
            # 같은 줄인지 확인 (y좌표 차이가 threshold 이하)
            if abs(word['top'] - current_y) <= y_threshold:
                current_line.append(word)
            else:
                # 새 줄 시작
                if current_line:
                    # x좌표 기준으로 정렬 (왼쪽부터)
                    current_line.sort(key=lambda w: w['left'])
                    lines.append(current_line)
                current_line = [word]
                current_y = word['top']
        
        # 마지막 줄 추가
        if current_line:
            current_line.sort(key=lambda w: w['left'])
            lines.append(current_line)
        
        return lines
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """텍스트가 패턴 중 하나와 매칭되는지 확인"""
        if not text or len(text.strip()) < 2:
            return False
        
        # 텍스트 정규화 (공백 정리)
        normalized_text = re.sub(r'\s+', ' ', text.strip())
        
        for pattern in patterns:
            try:
                # 정확한 매칭 시도
                if re.match(pattern, text) or re.match(pattern, normalized_text):
                    return True
                # 부분 매칭도 시도 (패턴이 텍스트 시작 부분과 일치하는지)
                if re.search(pattern, text) or re.search(pattern, normalized_text):
                    # 패턴이 텍스트의 앞부분과 일치하는지 확인
                    match = re.search(pattern, text) or re.search(pattern, normalized_text)
                    if match and match.start() == 0:
                        return True
            except re.error:
                # 잘못된 정규식 패턴은 스킵
                continue
        return False
    
    def _find_actual_lecture_start_page(
        self,
        lecture_id: int,
        lecture_title: str,
        all_ocr_data: List[Dict[str, Any]],
        START_CONTENT_PAGE: int = 8
    ) -> int:
        """목차 페이지에서 발견된 강의의 실제 시작 페이지 찾기
        
        예: "1강 | 시의 표현과 형식" -> 페이지 8에서 "1" 찾기
        
        Returns:
            int: 실제 시작 페이지 번호 (찾은 경우), -1 (찾지 못한 경우)
        """
        # 강의 번호 추출 (예: "1강" -> 1)
        lecture_num_match = re.search(r'^(\d+)강', lecture_title)
        if not lecture_num_match:
            # "1강" 형식이 아니면 숫자만 추출 시도
            lecture_num_match = re.search(r'^(\d+)', lecture_title)
        
        if not lecture_num_match:
            return -1  # 찾지 못함을 나타내는 sentinel 값
        
        lecture_num = int(lecture_num_match.group(1))
        
        # 실제 콘텐츠 페이지에서 해당 번호 찾기
        for ocr_data in all_ocr_data:
            page_num = ocr_data.get('page_num', 0)
            if page_num < START_CONTENT_PAGE:
                continue
            
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            # 페이지 상단의 큰 텍스트에서 강의 번호 찾기
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 상단 40% 영역의 큰 폰트만 체크
            if lines:
                first_line_y = lines[0][0]['top']
                last_line = lines[-1]
                estimated_height = last_line[-1]['top'] + last_line[-1]['height']
                top_threshold = first_line_y + (estimated_height * 0.4)
                
                avg_height = sum(word['height'] for line in lines[:5] for word in line[:2]) / min(10, sum(len(line[:2]) for line in lines[:5]))
                
                for line in lines[:10]:  # 상위 10줄만 확인
                    line_y = line[0]['top']
                    if line_y > top_threshold:
                        break
                    
                    line_text = " ".join([word['text'] for word in line]).strip()
                    line_height = max(word['height'] for word in line)
                    
                    # 큰 폰트이고, 숫자가 강의 번호와 일치하면
                    if line_height >= avg_height * 0.9:
                        cleaned_text = line_text.strip()
                        
                        # 정확히 강의 번호만 있는 경우 (예: "1", "2")
                        if cleaned_text == str(lecture_num):
                            print(f"    [강의 {lecture_id}] 실제 시작 페이지 발견: {page_num} (목차: {lecture_num}강, 텍스트: '{cleaned_text}')")
                            return page_num
                        
                        # 강의 번호로 시작하는 경우 (예: "1 ", "1강", "2 시의 내용")
                        if cleaned_text.startswith(f"{lecture_num} ") or cleaned_text.startswith(f"{lecture_num}강"):
                            print(f"    [강의 {lecture_id}] 실제 시작 페이지 발견: {page_num} (목차: {lecture_num}강, 텍스트: '{cleaned_text[:30]}')")
                            return page_num
                        
                        # 디버깅: 매칭 실패한 경우 (큰 폰트의 숫자지만 강의 번호와 다름)
                        if cleaned_text and cleaned_text[0].isdigit() and len(cleaned_text) <= 5:
                            print(f"    [강의 {lecture_id} 디버그] 페이지 {page_num}에서 '{cleaned_text}' 발견 (강의 번호: {lecture_num}, 폰트 높이: {line_height:.1f}, 평균: {avg_height:.1f})")
        
        # 찾지 못하면 -1 반환 (제외 표시)
        print(f"    ⚠️ [강의 {lecture_id}] 실제 시작 페이지를 찾지 못했습니다. 강의 번호 {lecture_num}을(를) 페이지 {START_CONTENT_PAGE} 이상에서 찾을 수 없습니다.")
        return -1  # 찾지 못함을 나타내는 sentinel 값
    
    def _load_existing_lectures(self) -> Dict[int, Dict[str, Any]]:
        """기존에 파싱된 강의 목록 로드 (증분 파싱용)"""
        existing_lectures = {}
        
        # lectures.json 파일 확인
        lectures_json_path = self.lectures_dir / "lectures.json"
        if not lectures_json_path.exists():
            return existing_lectures
        
        try:
            with open(lectures_json_path, 'r', encoding='utf-8') as f:
                lectures_list = json.load(f)
            
            # 각 강의 파일 로드
            for lecture_info in lectures_list:
                lecture_id = lecture_info.get('lecture_id', 0)
                lecture_file = self.lectures_dir / f"lecture_{lecture_id:02d}.json"
                
                if lecture_file.exists():
                    try:
                        with open(lecture_file, 'r', encoding='utf-8') as f:
                            lecture_data = json.load(f)
                            existing_lectures[lecture_id] = lecture_data
                    except Exception as e:
                        logger.warning(f"기존 강의 파일 로드 실패 (lecture_{lecture_id:02d}.json): {e}")
        except Exception as e:
            logger.warning(f"기존 강의 목록 로드 실패: {e}")
        
        return existing_lectures
    
    def _load_existing_problems(self) -> Dict[str, Dict[str, Any]]:
        """기존에 파싱된 문제 목록 로드 (증분 파싱용)"""
        existing_problems = {}
        
        if not self.problems_dir.exists():
            return existing_problems
        
        # problem_*.json 파일들 찾기
        problem_files = list(self.problems_dir.glob("problem_*.json"))
        
        for problem_file in problem_files:
            try:
                with open(problem_file, 'r', encoding='utf-8') as f:
                    problem_data = json.load(f)
                    problem_id = problem_data.get('problem_id', '')
                    page = problem_data.get('page', 0)
                    # 문제 ID는 페이지 번호와 함께 고유하게 식별
                    problem_key = f"{page:02d}_{problem_id}"
                    existing_problems[problem_key] = problem_data
            except Exception as e:
                logger.warning(f"기존 문제 파일 로드 실패 ({problem_file.name}): {e}")
        
        return existing_problems
    
    def _extract_lecture_contents(
        self,
        all_ocr_data: List[Dict[str, Any]],
        lectures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """강의별 목차 및 콘텐츠 추출 (증분 파싱 지원)"""
        lecture_contents = []
        START_CONTENT_PAGE = self.config.get('start_content_page', 8)
        
        # 기존에 파싱된 강의 로드
        existing_lectures = self._load_existing_lectures()
        skipped_count = 0
        
        for lecture in lectures:
            lecture_id = lecture['lecture_id']
            lecture_page = lecture['page']
            
            # 증분 파싱: 이미 파싱된 강의는 건너뛰기
            if lecture_id in existing_lectures:
                existing_lecture = existing_lectures[lecture_id]
                print(f"    ⏭️ [강의 {lecture_id}] 이미 파싱됨: '{existing_lecture.get('title', '')}' - 건너뜀")
                # 기존 데이터를 그대로 사용
                lecture_contents.append({
                    "lecture_id": lecture_id,
                    "title": existing_lecture.get('title', lecture['title']),
                    "sections": existing_lecture.get('sections', []),
                    "content": [],  # content는 재생성하지 않음 (이미 sections에 포함됨)
                    "page": existing_lecture.get('page', lecture_page),
                    "start_page": existing_lecture.get('start_page', lecture_page),
                    "end_page": existing_lecture.get('end_page', lecture_page)
                })
                skipped_count += 1
                continue
            
            # 목차 페이지에서 발견된 경우, 실제 시작 페이지 찾기
            actual_start_page = None
            if lecture_page < START_CONTENT_PAGE:
                print(f"    [강의 {lecture_id}] 목차 페이지({lecture_page})에서 발견. 실제 시작 페이지 검색 중...")
                actual_start_page = self._find_actual_lecture_start_page(
                    lecture_id, 
                    lecture['title'], 
                    all_ocr_data, 
                    START_CONTENT_PAGE
                )
                
                # 실제 시작 페이지를 찾지 못한 경우 이 강의는 제외
                # _find_actual_lecture_start_page가 -1을 반환했다는 것은
                # 강의 번호를 찾지 못했다는 의미이므로 제외
                if actual_start_page == -1:
                    print(f"    ⚠️ [강의 {lecture_id}] '{lecture['title']}'의 실제 시작 페이지를 찾지 못했습니다. 이 강의는 제외됩니다.")
                    continue  # 이 강의는 건너뛰기
                
                print(f"    ✓ [강의 {lecture_id}] 실제 시작 페이지: {actual_start_page} (목차: {lecture_page})")
                start_page = actual_start_page
            else:
                start_page = lecture_page
                actual_start_page = lecture_page
                print(f"    [강의 {lecture_id}] 실제 콘텐츠 페이지에서 발견: {lecture_page}")
            
            # 다음 강의의 실제 시작 페이지 확인 (같은 목차 페이지에서 발견된 경우)
            next_lecture = next((l for l in lectures if l['lecture_id'] == lecture_id + 1), None)
            
            # 강의 페이지 범위 찾기
            if next_lecture:
                if next_lecture['page'] < START_CONTENT_PAGE:
                    # 다음 강의도 목차 페이지에서 발견되었으면, 실제 시작 페이지 찾기
                    next_actual_start = self._find_actual_lecture_start_page(
                        next_lecture['lecture_id'],
                        next_lecture['title'],
                        all_ocr_data,
                        START_CONTENT_PAGE
                    )
                    # 다음 강의의 실제 시작 페이지를 찾지 못한 경우 (-1 반환)
                    # 이 경우 현재 강의가 마지막 강의가 되므로 전체 페이지까지 포함
                    if next_actual_start == -1:
                        print(f"    [강의 {lecture_id} 디버그] 다음 강의({next_lecture['lecture_id']})의 실제 시작 페이지를 찾지 못했습니다. 현재 강의가 마지막 강의로 처리됩니다.")
                        end_page = self._find_lecture_end_page(lectures, lecture_id, len(all_ocr_data), start_page)
                    elif next_actual_start > start_page:
                        end_page = next_actual_start - 1
                    else:
                        # 다음 강의의 실제 시작 페이지가 현재 강의 시작 페이지보다 작거나 같으면 기본 로직 사용
                        print(f"    [강의 {lecture_id} 디버그] 다음 강의의 실제 시작 페이지({next_actual_start})가 현재 강의 시작 페이지({start_page})보다 작거나 같습니다. 기본 로직 사용.")
                        end_page = self._find_lecture_end_page(lectures, lecture_id, len(all_ocr_data), start_page)
                else:
                    # 다음 강의가 실제 콘텐츠 페이지에 있으면 그 전까지
                    if next_lecture['page'] > start_page:
                        end_page = next_lecture['page'] - 1
                    else:
                        # 다음 강의의 페이지가 현재 강의 시작 페이지보다 작거나 같으면
                        # 다음 강의도 실제 시작 페이지를 찾아야 함 (목차 페이지일 수 있음)
                        next_actual_start = self._find_actual_lecture_start_page(
                            next_lecture['lecture_id'],
                            next_lecture['title'],
                            all_ocr_data,
                            START_CONTENT_PAGE
                        )
                        if next_actual_start != -1 and next_actual_start > start_page:
                            end_page = next_actual_start - 1
                        else:
                            end_page = self._find_lecture_end_page(lectures, lecture_id, len(all_ocr_data), start_page)
            else:
                # 마지막 강의면 기본 로직 사용
                end_page = self._find_lecture_end_page(lectures, lecture_id, len(all_ocr_data), start_page)
            
            # 디버깅: 페이지 범위 계산 과정 출력
            print(f"    [강의 {lecture_id} 디버그] 목차 페이지: {lecture_page}, 실제 시작: {start_page}, 끝: {end_page}")
            if next_lecture:
                print(f"    [강의 {lecture_id} 디버그] 다음 강의: ID={next_lecture['lecture_id']}, 목차 페이지={next_lecture['page']}")
            
            
            print(f"    [강의 {lecture_id}] 페이지 범위: {start_page} ~ {end_page}")
            
            # 해당 페이지들의 OCR 데이터 (페이지 번호 기준으로 필터링)
            lecture_ocr_data = [
                ocr_data for ocr_data in all_ocr_data
                if start_page <= ocr_data['page_num'] <= end_page
            ]
            
            if not lecture_ocr_data:
                print(f"    ⚠️ 강의 {lecture_id}에 해당하는 OCR 데이터가 없습니다.")
                lecture_contents.append({
                    "lecture_id": lecture_id,
                    "title": lecture['title'],
                    "sections": [],
                    "content": [],
                    "page": actual_start_page if lecture_page < START_CONTENT_PAGE else lecture_page,
                    "start_page": start_page,
                    "end_page": end_page
                })
                continue
            
            # 목차 및 콘텐츠 추출
            sections = self._extract_sections(lecture_ocr_data)
            content_paragraphs = self._extract_content_paragraphs(lecture_ocr_data, sections)
            
            print(f"    [강의 {lecture_id}] 섹션 {len(sections)}개 추출")
            
            # 새로 파싱한 강의 추가
            lecture_contents.append({
                "lecture_id": lecture_id,
                "title": lecture['title'],
                "sections": sections,
                "content": content_paragraphs,
                "page": actual_start_page if lecture_page < START_CONTENT_PAGE else lecture_page,
                "start_page": start_page,
                "end_page": end_page
            })
        
        if skipped_count > 0:
            print(f"    ⏭️ 증분 파싱: {skipped_count}개 강의 건너뜀 (이미 파싱됨)")
        
        return lecture_contents
    
    def _find_lecture_end_page(
        self,
        lectures: List[Dict[str, Any]],
        current_lecture_id: int,
        total_pages: int,
        current_start_page: int = None
    ) -> int:
        """강의의 끝 페이지 찾기 (다음 강의 시작 전까지)
        
        Args:
            lectures: 전체 강의 목록
            current_lecture_id: 현재 강의 ID
            total_pages: 전체 페이지 수
            current_start_page: 현재 강의의 실제 시작 페이지 (선택적)
        """
        current_lecture = None
        next_lecture = None
        
        # 현재 강의와 다음 강의 찾기
        for lecture in lectures:
            if lecture['lecture_id'] == current_lecture_id:
                current_lecture = lecture
            elif lecture['lecture_id'] == current_lecture_id + 1:
                next_lecture = lecture
                break
        
        if not current_lecture:
            print(f"    [디버그] 강의 {current_lecture_id}를 찾을 수 없습니다.")
            return total_pages
        
        # 다음 강의가 있고, 같은 페이지가 아니면 그 전 페이지까지
        if next_lecture:
            print(f"    [디버그] 강의 {current_lecture_id}의 다음 강의: ID={next_lecture['lecture_id']}, 목차 페이지={next_lecture['page']}")
            # 다음 강의의 목차 페이지가 현재 강의 실제 시작 페이지보다 크면
            if current_start_page and next_lecture['page'] > current_start_page:
                end_page = next_lecture['page'] - 1
                print(f"    [디버그] 강의 {current_lecture_id} 끝 페이지: {end_page} (다음 강의 목차 페이지 전)")
                return end_page
            elif next_lecture['page'] > current_lecture['page']:
                end_page = next_lecture['page'] - 1
                print(f"    [디버그] 강의 {current_lecture_id} 끝 페이지: {end_page} (다음 강의 전)")
                return end_page
            else:
                print(f"    [디버그] 강의 {current_lecture_id}와 다음 강의가 같은 목차 페이지({current_lecture['page']})에 있습니다.")
        
        # 다음 강의가 없거나 같은 페이지면 전체 페이지까지
        print(f"    [디버그] 강의 {current_lecture_id} 끝 페이지: {total_pages} (마지막 강의 또는 다음 강의와 같은 페이지)")
        return total_pages
    
    def _extract_sections(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        소단원/섹션 목차 추출 (과목별 분기)
        """
        if self.subject == 'literature':
            return self._extract_sections_literature(lecture_ocr_data)
        elif self.subject == 'math1':
            return self._extract_sections_math1(lecture_ocr_data)
        elif self.subject == 'english':
            return self._extract_sections_english(lecture_ocr_data)
        else:
            return self._extract_sections_literature(lecture_ocr_data)
    
    def _extract_sections_literature(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        문학 소단원 목차 추출 (config 기반 + 레이아웃 분석)
        
        개선: 줄 단위로 결합하여 "(1) 시적 표현의 개념" 같은 제목 인식
        실제 강의 내용의 소단원만 추출 (목차 페이지 제외)
        """
        sections = []
        patterns = self.config.get('section_title_patterns', [])
        START_PAGE = self.config.get('start_content_page', 8)
        
        for ocr_data in lecture_ocr_data:
            page_num = ocr_data['page_num']
            
            # 시작 페이지 이전은 목차이므로 제외
            if page_num < START_PAGE:
                continue
            
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            # y좌표 기준으로 같은 줄의 단어들을 그룹화
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 각 줄을 문장으로 결합하고 패턴 매칭
            for line in lines:
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                # 특수 문자 제거 후 패턴 매칭
                cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                
                # 목차 형식 제외 (페이지 번호 포함된 것들)
                if re.search(r'\d{3}', cleaned_line) and len(cleaned_line) < 30:
                    # "01 무정 (이광수) 155" 같은 목차 형식 제외
                    continue
                
                # 패턴 매칭
                if self._matches_patterns(cleaned_line, patterns):
                    # bbox 계산
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    sections.append({
                        "title": cleaned_line,
                        "page": page_num,
                        "bbox": [left, top, right, bottom]
                    })
        
        return sections
    
    def _extract_sections_math1(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        수학Ⅰ 섹션 추출 (개념/예제/유제)
        
        섹션 타입:
        - concept: "1. 지수함수", "(가) 지수함수"
        - example: "예제 1", "예 1"
        - exercise: "유제 1", "연습 1"
        """
        sections = []
        concept_patterns = self.config.get('concept_title_patterns', [])
        example_patterns = self.config.get('example_title_patterns', [])
        exercise_patterns = self.config.get('exercise_title_patterns', [])
        START_PAGE = self.config.get('start_content_page', 5)
        
        for ocr_data in lecture_ocr_data:
            page_num = ocr_data['page_num']
            
            if page_num < START_PAGE:
                continue
            
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            for line_idx, line in enumerate(lines):
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                
                # 섹션 타입 판별 (ML 기반 우선, Fallback: 정규식)
                section_type = None
                matched_patterns = []
                
                # 섹션 타입 판별
                if section_type is None:
                    if self._matches_patterns(cleaned_line, concept_patterns):
                        section_type = 'concept'
                        matched_patterns = concept_patterns
                    elif self._matches_patterns(cleaned_line, example_patterns):
                        section_type = 'example'
                        matched_patterns = example_patterns
                    elif self._matches_patterns(cleaned_line, exercise_patterns):
                        section_type = 'exercise'
                        matched_patterns = exercise_patterns
                
                if section_type:
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    sections.append({
                        "title": cleaned_line,
                        "page": page_num,
                        "bbox": [left, top, right, bottom],
                        "type": section_type  # concept, example, exercise
                    })
        
        return sections
    
    def _extract_sections_english(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        영어 섹션 추출 (지문)
        
        섹션 타입:
        - passage: "지문 1", "Passage 1"
        """
        sections = []
        passage_patterns = self.config.get('passage_title_patterns', [])
        section_patterns = self.config.get('section_title_patterns', [])
        START_PAGE = self.config.get('start_content_page', 5)
        
        for ocr_data in lecture_ocr_data:
            page_num = ocr_data['page_num']
            
            if page_num < START_PAGE:
                continue
            
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            for line_idx, line in enumerate(lines):
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                line_text_lower = cleaned_line.lower()
                
                # 지문 패턴 매칭 (대소문자 무시)
                matched = False
                section_type = None
                for pattern in passage_patterns:
                    if re.search(pattern, line_text_lower, re.IGNORECASE):
                        matched = True
                        section_type = 'passage'
                        break
                
                # 일반 섹션 패턴도 체크
                if not matched:
                    for pattern in section_patterns:
                        if re.match(pattern, cleaned_line):
                            matched = True
                            section_type = 'section'
                            break
                
                if matched:
                    first_word = line[0]
                    last_word = line[-1]
                    
                    left = first_word['left']
                    top = first_word['top']
                    right = last_word['left'] + last_word['width']
                    bottom = max(w['top'] + w['height'] for w in line)
                    
                    sections.append({
                        "title": cleaned_line,
                        "page": page_num,
                        "bbox": [left, top, right, bottom],
                        "type": section_type  # passage, section
                    })
        
        return sections
    
    def _extract_content_paragraphs(
        self,
        lecture_ocr_data: List[Dict[str, Any]],
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        문단 묶기 (y좌표 기반 + 레이아웃 분석)
        
        개선:
        - 줄 단위로 그룹화 후 문단으로 결합
        - 섹션 제목과 본문 구분
        - 개념 영역 자동 감지
        """
        all_paragraphs = []
        threshold = self.config.get('paragraph_y_threshold', 25)
        section_patterns = self.config.get('section_title_patterns', [])
        
        # 섹션 위치 정보 (페이지별)
        section_positions = {}
        for section in sections:
            page = section['page']
            if page not in section_positions:
                section_positions[page] = []
            section_positions[page].append({
                'y': section['bbox'][1],
                'title': section['title']
            })
        
        for ocr_data in lecture_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            # y좌표 기준으로 줄 그룹화
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 줄들을 문단으로 결합
            paragraphs = []
            current_paragraph = {
                "text": "",
                "y_start": None,
                "y_end": None,
                "page": page_num,
                "bbox": None
            }
            
            prev_line_y = None
            
            for line in lines:
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                # 섹션 제목이면 스킵 (하지만 특수 문자 제거 후 확인)
                cleaned_line = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                if self._matches_patterns(cleaned_line, section_patterns):
                    continue
                
                # 개념 제목 패턴도 제외 (개념은 별도로 처리)
                concept_patterns = self.config.get('concept_title_patterns', [])
                if self._matches_patterns(cleaned_line, concept_patterns):
                    continue
                
                # 문제 번호 패턴도 제외
                problem_pattern = self.config.get('problem_number_pattern', r'^\d{2}$')
                if re.match(problem_pattern, cleaned_line):
                    continue
                
                # 제외 패턴들
                exclude_patterns = [
                    r'정답과 해설',
                    r'다음 글을 읽고',
                    r'물음에 답하시오',
                ]
                if any(re.search(p, cleaned_line) for p in exclude_patterns):
                    continue
                
                line_y = line[0]['top']
                
                # 같은 문단인지 확인 (y좌표 차이)
                if prev_line_y is not None and abs(line_y - prev_line_y) < threshold:
                    # 같은 문단에 추가
                    if current_paragraph['text']:
                        current_paragraph['text'] += " " + line_text
                    else:
                        current_paragraph['text'] = line_text
                        current_paragraph['y_start'] = line_y
                        # bbox 초기화
                        first_word = line[0]
                        current_paragraph['bbox'] = [
                            first_word['left'],
                            first_word['top'],
                            first_word['left'] + first_word['width'],
                            first_word['top'] + first_word['height']
                        ]
                    
                    # bbox 확장
                    if current_paragraph['bbox']:
                        last_word = line[-1]
                        current_paragraph['bbox'][0] = min(current_paragraph['bbox'][0], line[0]['left'])
                        current_paragraph['bbox'][1] = min(current_paragraph['bbox'][1], line_y)
                        current_paragraph['bbox'][2] = max(current_paragraph['bbox'][2], last_word['left'] + last_word['width'])
                        current_paragraph['bbox'][3] = max(current_paragraph['bbox'][3], line[-1]['top'] + line[-1]['height'])
                    
                    current_paragraph['y_end'] = line_y
                else:
                    # 새 문단 시작
                    if current_paragraph['text']:
                        paragraphs.append(current_paragraph.copy())
                    
                    # 새 문단 초기화
                    first_word = line[0]
                    last_word = line[-1]
                    current_paragraph = {
                        "text": line_text,
                        "y_start": line_y,
                        "y_end": line_y,
                        "page": page_num,
                        "bbox": [
                            first_word['left'],
                            first_word['top'],
                            last_word['left'] + last_word['width'],
                            last_word['top'] + last_word['height']
                        ]
                    }
                
                prev_line_y = line_y
            
            # 마지막 문단 추가
            if current_paragraph['text']:
                paragraphs.append(current_paragraph)
            
            all_paragraphs.extend(paragraphs)
        
        return all_paragraphs
    
    def _extract_problems(
        self,
        all_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        문제 추출 (과목별 분기, 증분 파싱 지원)
        """
        # 기존에 파싱된 문제 로드
        existing_problems = self._load_existing_problems()
        existing_problem_keys = set(existing_problems.keys())
        
        if self.subject == 'literature':
            problems = self._extract_problems_literature(all_ocr_data, existing_problem_keys)
        elif self.subject == 'math1':
            problems = self._extract_problems_math1(all_ocr_data, existing_problem_keys)
        elif self.subject == 'english':
            problems = self._extract_problems_english(all_ocr_data, existing_problem_keys)
        else:
            problems = self._extract_problems_literature(all_ocr_data, existing_problem_keys)
        
        # 기존 문제와 새 문제 병합
        all_problems = list(existing_problems.values())
        all_problems.extend(problems)
        
        if existing_problems:
            print(f"    ⏭️ 증분 파싱: {len(existing_problems)}개 문제 건너뜀 (이미 파싱됨)")
        
        return all_problems
    
    def _extract_problems_literature(
        self,
        all_ocr_data: List[Dict[str, Any]],
        existing_problem_keys: set = None
    ) -> List[Dict[str, Any]]:
        """
        문학 문제 추출 (config 기반 + 레이아웃 분석)
        
        설계 문서 v1.1 기준:
        - 문제 영역: 문제 번호 + 지문 + 선택지 전체를 하나의 블록으로 캡처
        - 이미지 단계에서는 세분화 안 함 (JSON 단계에서 세분화)
        
        개선:
        - 줄 단위로 그룹화하여 문제 영역 정확히 감지
        - 문제 번호부터 다음 문제까지 영역 자동 감지
        """
        problems = []
        problem_id = 1
        pattern = self.config.get('problem_number_pattern', r'^\d{2}$')
        
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            # y좌표 기준으로 줄 그룹화
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 문제 번호가 있는 줄 찾기
            problem_starts = []
            for line_idx, line in enumerate(lines):
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                # 문제 번호 패턴 매칭
                if re.match(pattern, line_text):
                    problem_starts.append({
                        "number": line_text,
                        "line_idx": line_idx,
                        "y": line[0]['top']
                    })
            
            # 각 문제 영역 추출
            for j, problem_start in enumerate(problem_starts):
                start_line_idx = problem_start['line_idx']
                end_line_idx = problem_starts[j + 1]['line_idx'] if j + 1 < len(problem_starts) else len(lines)
                
                # 문제 영역의 모든 줄 수집
                problem_lines = lines[start_line_idx:end_line_idx]
                problem_texts = []
                problem_bbox = None
                
                for line in problem_lines:
                    line_text = " ".join([word['text'] for word in line])
                    if line_text.strip():
                        problem_texts.append(line_text.strip())
                        
                        # bbox 계산
                        first_word = line[0]
                        last_word = line[-1]
                        line_bbox = [
                            first_word['left'],
                            first_word['top'],
                            last_word['left'] + last_word['width'],
                            last_word['top'] + last_word['height']
                        ]
                        
                        if problem_bbox is None:
                            problem_bbox = line_bbox
                        else:
                            problem_bbox[0] = min(problem_bbox[0], line_bbox[0])
                            problem_bbox[1] = min(problem_bbox[1], line_bbox[1])
                            problem_bbox[2] = max(problem_bbox[2], line_bbox[2])
                            problem_bbox[3] = max(problem_bbox[3], line_bbox[3])
                
                problem = self._parse_problem_structure(problem_texts, problem_id, page_num)
                if problem:
                    problem['bbox'] = problem_bbox  # 영역 정보 추가
                    
                    # 증분 파싱: 이미 파싱된 문제는 건너뛰기
                    problem_key = f"{page_num:02d}_{problem_id}"
                    if existing_problem_keys and problem_key in existing_problem_keys:
                        print(f"    ⏭️ [문제 {problem_id}] 이미 파싱됨 (페이지 {page_num}) - 건너뜀")
                        problem_id += 1
                        continue
                    
                    problems.append(problem)
                    problem_id += 1
        
        return problems
    
    def _parse_problem_structure(
        self,
        problem_texts: List[str],
        problem_id: int,
        page: int
    ) -> Optional[Dict[str, Any]]:
        """
        문제 구조 파싱 (JSON 단계에서 세분화)
        
        설계 문서 v1.1 기준:
        - 이미지 크롭 단계: 문제 전체를 하나의 블록으로 캡처
        - JSON 생성 단계: 문제 번호, 지문, 선택지를 분리하여 구조화
        """
        full_text = " ".join(problem_texts)
        
        # 보기 패턴 찾기
        choices = {}
        choice_pattern = re.compile(r'[①②③④⑤]\s*(.+?)(?=[①②③④⑤]|$)')
        choice_matches = choice_pattern.findall(full_text)
        
        for i, choice_text in enumerate(choice_matches[:5], 1):
            choices[str(i)] = choice_text.strip()
        
        # 전체 텍스트 정제
        full_text_clean = " ".join(problem_texts).strip()
        
        # 불필요한 텍스트 제거
        full_text_clean = re.sub(r'^\d{2}\s*', '', full_text_clean).strip()
        full_text_clean = re.sub(r'다음 글을 읽고.*?물음에 답하시오\.?\s*', '', full_text_clean, flags=re.DOTALL)
        # 페이지 번호 및 메타 정보 제거
        full_text_clean = re.sub(r'\[.*?교과서.*?\].*', '', full_text_clean)
        full_text_clean = re.sub(r'\d{4}학년도.*', '', full_text_clean)
        full_text_clean = re.sub(r'오후 \d{1,2}:\d{2}.*', '', full_text_clean)
        full_text_clean = re.sub(r'\d{2,3}\.indd.*', '', full_text_clean)
        full_text_clean = re.sub(r'\d{2,3}\s+\d{1,2}\.\s+\d{1,2}\.', '', full_text_clean)
        full_text_clean = full_text_clean.strip()
        
        # 문제 번호 제거된 텍스트로 passage와 question 구분
        problem_text_clean = full_text_clean
        
        # passage와 question 구분
        question_match = re.search(r'(.+\?)', problem_text_clean)
        if question_match:
            question = question_match.group(1).strip()
            passage_text = problem_text_clean[:question_match.start()].strip()
        else:
            question = ""
            passage_text = problem_text_clean
        
        # passage를 문장 단위로 분리 (더 많은 문장 포함)
        if passage_text and passage_text.strip():
            passage = [s.strip() for s in re.split(r'[.!?]\s+', passage_text) if s.strip() and len(s.strip()) > 5]
            # 최대 20개 문장까지 포함
            passage = passage[:20]
        else:
            passage = []
        
        # passage가 없으면 전체 텍스트를 문장 단위로 분리
        if not passage and full_text_clean:
            # 선택지 번호 이전까지만 본문으로 간주
            passage_part = re.split(r'[①②③④⑤]', full_text_clean)[0].strip()
            if passage_part:
                passage = [s.strip() for s in re.split(r'[.!?]\s+', passage_part) if s.strip() and len(s.strip()) > 5]
                passage = passage[:20]
            if not passage:
                # 문장 단위 분리가 안 되면 전체를 하나로 (최대 500자)
                passage_text_for_display = full_text_clean[:500]
                if passage_text_for_display:
                    passage = [passage_text_for_display]
        
        # choices 정제
        clean_choices = {}
        for key, value in choices.items():
            clean_choice = re.sub(r'\[.*?교과서.*?\].*', '', value).strip()
            clean_choice = re.sub(r'\d{4}학년도.*', '', clean_choice).strip()
            clean_choice = re.sub(r'오후 \d{1,2}:\d{2}.*', '', clean_choice).strip()
            if clean_choice:
                clean_choices[key] = clean_choice
        
        return {
            "problem_id": f"{problem_id:02d}",
            "page": page,
            "content": passage if passage else [""],
            "choices": clean_choices if clean_choices else choices,
            "question_text": question if 'question' in locals() else "",
            "full_text": full_text_clean  # 정제된 전체 텍스트
        }
    
    def _extract_problems_math1(
        self,
        all_ocr_data: List[Dict[str, Any]],
        existing_problem_keys: set = None
    ) -> List[Dict[str, Any]]:
        """
        수학Ⅰ 문제 추출
        
        수학 문제 특징:
        - 문제 번호: "1.", "2." 형식
        - 수식이 많음 (이미지로 처리 필요)
        - 선택지: "①", "②", "③", "④", "⑤" 또는 "1)", "2)", "3)", "4)", "5)"
        """
        problems = []
        problem_id = 1
        pattern = self.config.get('problem_number_pattern', r'^\d+\.')
        
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 문제 번호가 있는 줄 찾기
            problem_starts = []
            for line_idx, line in enumerate(lines):
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                # 문제 번호 패턴 매칭 ("1.", "2." 등)
                if re.match(pattern, line_text):
                    problem_starts.append({
                        "number": line_text,
                        "line_idx": line_idx,
                        "y": line[0]['top']
                    })
            
            # 각 문제 영역 추출
            for j, problem_start in enumerate(problem_starts):
                start_line_idx = problem_start['line_idx']
                end_line_idx = problem_starts[j + 1]['line_idx'] if j + 1 < len(problem_starts) else len(lines)
                
                # 문제 영역의 모든 줄 추출
                problem_lines = lines[start_line_idx:end_line_idx]
                
                # 전체 텍스트 추출
                full_text = " ".join([" ".join([word['text'] for word in line]) for line in problem_lines])
                
                # 선택지 추출 (①~⑤ 또는 1)~5) 형식)
                choices = {}
                choice_patterns = [
                    r'[①②③④⑤]\s*(.+?)(?=[①②③④⑤]|$)',
                    r'(\d+)\)\s*(.+?)(?=\d+\)|$)',
                ]
                
                for pattern in choice_patterns:
                    matches = re.finditer(pattern, full_text)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            choice_num = match.group(1) if match.group(1) else str(len(choices) + 1)
                            choice_text = match.group(2).strip()
                            if choice_text:
                                choices[choice_num] = choice_text
                
                # 문제 질문 추출 (문제 번호 다음부터 선택지 전까지)
                question_match = re.search(r'^\d+\.\s*(.+?)(?=[①②③④⑤]|\d+\)|$)', full_text, re.DOTALL)
                question_text = question_match.group(1).strip() if question_match else ""
                
                # bbox 계산
                all_words = [word for line in problem_lines for word in line]
                if all_words:
                    left = min(w['left'] for w in all_words)
                    top = min(w['top'] for w in all_words)
                    right = max(w['left'] + w['width'] for w in all_words)
                    bottom = max(w['top'] + w['height'] for w in all_words)
                    
                    problem = {
                        "problem_id": f"{problem_id:02d}",
                        "page": page_num,
                        "content": [full_text],  # 수학은 전체를 하나의 텍스트로
                        "choices": choices if choices else {},
                        "question_text": question_text,
                        "full_text": full_text
                    }
                    
                    # 증분 파싱: 이미 파싱된 문제는 건너뛰기
                    problem_key = f"{page_num:02d}_{problem_id:02d}"
                    if existing_problem_keys and problem_key in existing_problem_keys:
                        print(f"    ⏭️ [문제 {problem_id}] 이미 파싱됨 (페이지 {page_num}) - 건너뜀")
                        problem_id += 1
                        continue
                    
                    problems.append(problem)
                    problem_id += 1
        
        return problems
    
    def _extract_problems_english(
        self,
        all_ocr_data: List[Dict[str, Any]],
        existing_problem_keys: set = None
    ) -> List[Dict[str, Any]]:
        """
        영어 문제 추출
        
        영어 문제 특징:
        - 문제 번호: "1.", "2." 형식
        - 지문(Passage)과 문제가 분리되어 있음
        - 선택지: "①", "②", "③", "④", "⑤" 또는 "1)", "2)", "3)", "4)", "5)"
        """
        problems = []
        problem_id = 1
        pattern = self.config.get('problem_number_pattern', r'^\d+\.')
        
        for ocr_data in all_ocr_data:
            page_num = ocr_data['page_num']
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 문제 번호가 있는 줄 찾기
            problem_starts = []
            for line_idx, line in enumerate(lines):
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                # 문제 번호 패턴 매칭 ("1.", "2." 등)
                if re.match(pattern, line_text):
                    problem_starts.append({
                        "number": line_text,
                        "line_idx": line_idx,
                        "y": line[0]['top']
                    })
            
            # 각 문제 영역 추출
            for j, problem_start in enumerate(problem_starts):
                start_line_idx = problem_start['line_idx']
                end_line_idx = problem_starts[j + 1]['line_idx'] if j + 1 < len(problem_starts) else len(lines)
                
                # 문제 영역의 모든 줄 추출
                problem_lines = lines[start_line_idx:end_line_idx]
                
                # 전체 텍스트 추출
                full_text = " ".join([" ".join([word['text'] for word in line]) for line in problem_lines])
                
                # 선택지 추출 (①~⑤ 또는 1)~5) 형식)
                choices = {}
                choice_patterns = [
                    r'[①②③④⑤]\s*(.+?)(?=[①②③④⑤]|$)',
                    r'(\d+)\)\s*(.+?)(?=\d+\)|$)',
                ]
                
                for pattern in choice_patterns:
                    matches = re.finditer(pattern, full_text)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            choice_num = match.group(1) if match.group(1) else str(len(choices) + 1)
                            choice_text = match.group(2).strip()
                            if choice_text:
                                choices[choice_num] = choice_text
                
                # 문제 질문 추출 (문제 번호 다음부터 선택지 전까지)
                question_match = re.search(r'^\d+\.\s*(.+?)(?=[①②③④⑤]|\d+\)|$)', full_text, re.DOTALL)
                question_text = question_match.group(1).strip() if question_match else ""
                
                # bbox 계산
                all_words = [word for line in problem_lines for word in line]
                if all_words:
                    left = min(w['left'] for w in all_words)
                    top = min(w['top'] for w in all_words)
                    right = max(w['left'] + w['width'] for w in all_words)
                    bottom = max(w['top'] + w['height'] for w in all_words)
                    
                    problem = {
                        "problem_id": f"{problem_id:02d}",
                        "page": page_num,
                        "content": [full_text],  # 영어는 전체를 하나의 텍스트로 (지문은 별도 추출)
                        "choices": choices if choices else {},
                        "question_text": question_text,
                        "full_text": full_text
                    }
                    
                    # 증분 파싱: 이미 파싱된 문제는 건너뛰기
                    problem_key = f"{page_num:02d}_{problem_id:02d}"
                    if existing_problem_keys and problem_key in existing_problem_keys:
                        print(f"    ⏭️ [문제 {problem_id}] 이미 파싱됨 (페이지 {page_num}) - 건너뜀")
                        problem_id += 1
                        continue
                    
                    problems.append(problem)
                    problem_id += 1
        
        return problems
    
    def _save_results(
        self,
        lectures: List[Dict[str, Any]],
        lecture_contents: List[Dict[str, Any]],
        problems: List[Dict[str, Any]]
    ):
        """결과를 JSON 파일로 저장 (규격에 맞게, 증분 파싱 지원)
        
        구조:
        - 큰 단위(1강, 2강) = 강의 (lecture)
        - 그 안에 세부 목차 = 섹션 (sections)
        """
        # 1. lectures.json 생성 (큰 단위 강의 목록) - 기존 파일과 병합
        existing_lectures_list = []
        lectures_json_path = self.lectures_dir / "lectures.json"
        if lectures_json_path.exists():
            try:
                with open(lectures_json_path, 'r', encoding='utf-8') as f:
                    existing_lectures_list = json.load(f)
            except Exception as e:
                logger.warning(f"기존 강의 목록 로드 실패: {e}")
        
        # 기존 강의 ID 집합
        existing_lecture_ids = {l.get('lecture_id', 0) for l in existing_lectures_list}
        
        # 새 강의만 추가
        new_lectures_list = [
            {
                "lecture_id": l['lecture_id'],
                "title": l['title']
            }
            for l in lectures
            if l['lecture_id'] not in existing_lecture_ids
        ]
        
        # 기존 강의와 새 강의 병합 (lecture_id 순서대로 정렬)
        all_lectures_list = existing_lectures_list + new_lectures_list
        all_lectures_list.sort(key=lambda x: x.get('lecture_id', 0))
        
        with open(lectures_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_lectures_list, f, ensure_ascii=False, indent=2)
        print(f"    ✓ [저장] 강의 목록 저장: {len(all_lectures_list)}개 강의 (기존: {len(existing_lectures_list)}, 새: {len(new_lectures_list)})")
        
        # 2. lecture_XX.json 생성 (각 강의에 세부 목차 포함)
        saved_count = 0
        skipped_count = 0
        print(f"    [저장] 강의 파일 저장 시작: {len(lecture_contents)}개 강의 콘텐츠")
        print(f"    [저장] 기존 강의 ID: {existing_lecture_ids}")
        for content in lecture_contents:
            lecture_id = content['lecture_id']
            
            sections = []
            if content['sections']:
                for section_idx, section in enumerate(content['sections']):
                    section_content = []
                    next_section = content['sections'][section_idx + 1] if section_idx + 1 < len(content['sections']) else None
                    
                    # 작품 분석 문제 섹션인지 확인 (예: "(1) 1연의 '-아라'", "(2) 2연의 '-어'")
                    poem_analysis_patterns = [
                        r'\(?\d+\)?\s*\d+연',
                        r'\(?\d+\)?\s*[가-힣]+연',
                        r'\(?\d+\)?\s*[가-힣]*의\s*[\'\"-]',
                        r'\(?\d+\)?\s*\d+연의',
                    ]
                    is_poem_analysis_section = any(re.search(p, section['title']) for p in poem_analysis_patterns)
                    
                    # 작품 분석 문제 섹션이면 건너뛰기 (문제는 별도로 저장되므로)
                    if is_poem_analysis_section:
                        continue
                    
                    # 문제 형식 패턴
                    problem_patterns = [
                        r'시하시오\.?$',
                        r'^\(?\s*\)?\s*$',  # "( )" 또는 "(  )"
                        r'적절하지 않은',
                        r'설명으로 적절',
                        r'적절한 것',
                        r'고르고',
                        r'서술하시오',
                        r'^[①②③④⑤]',  # 선택지 번호
                        r'윗글에 대한',
                        r'다음.*?설명으로',
                        r'<보기>',
                        r'㉠|㉡|㉢|㉣|㉤',  # 보기 번호
                    ]
                    
                    # 작가 이름 패턴
                    author_pattern = r'-\s*[가-힣]+\s*,\s*「[^」]+」'
                    
                    # 작가 정보 발견 여부 (작가 정보 이후 문단은 모두 제외)
                    author_found = False
                    
                    # 섹션과 같은 페이지 또는 다음 섹션 전까지의 모든 문단 포함
                    for para in content['content']:
                        para_text = para.get('text', '').strip()
                        if not para_text:
                            continue
                        
                        # 특수 문자 제거
                        para_text = re.sub(r'\(cid:\d+\)', '', para_text).strip()
                        if not para_text or len(para_text) < 3:
                            continue
                        
                        # 불필요한 텍스트 제거
                        exclude_patterns = [
                            r'^>>>',
                            r'^\d{4}학년도',
                            r'^\d{2}:\d{2}',
                            r'오후 \d{1,2}:\d{2}',
                            r'\[.*?\]$',  # 페이지 번호 등
                            r'^\d{3} EBS',  # "008 EBS 수능특강..."
                            r'^\[1부\]',  # "[1부] 교과서 개념 학습..."
                        ]
                        if any(re.search(p, para_text) for p in exclude_patterns):
                            continue
                        
                        # 문제 형식 문단 제외
                        if any(re.search(p, para_text) for p in problem_patterns):
                        
                            continue
                        
                        # 작가 이름 패턴이 있으면 작가 정보까지만 포함 (이후는 문제이므로 제외)
                        is_work_para = False
                        if re.search(author_pattern, para_text):
                            is_work_para = True
                        
                        if is_work_para:
                            # 작가 패턴 매칭
                            author_match = re.search(author_pattern, para_text)
                            if author_match:
                                # 작가 정보까지만 포함
                                para_text = para_text[:author_match.end()].strip()
                                # 작가 정보 이후가 비어있으면 건너뛰기
                                if not para_text:
                                    author_found = True
                                    continue
                                # 작가 정보 포함 문단 추가 후 플래그 설정
                                author_found = True
                        elif author_found:
                            # 작가 정보 이후 문단은 모두 제외
                            continue
                        
                        # 같은 페이지이거나 다음 섹션 전까지
                        if para['page'] == section['page']:
                            section_y = section['bbox'][1]
                            para_y = para.get('y_start', 0)
                            
                            # 섹션 제목 아래에 있는 문단만 포함 (약간의 여유 공간 허용)
                            if para_y >= section_y - 100:  # 섹션 제목 위 100px까지 허용
                                if next_section and next_section['page'] == section['page']:
                                    next_y = next_section['bbox'][1]
                                    if para_y < next_y:
                                        section_content.append(para_text)
                                else:
                                    section_content.append(para_text)
                        elif next_section and para['page'] < next_section['page'] and para['page'] > section['page']:
                            # 다음 섹션 전 페이지의 모든 문단 포함
                            section_content.append(para_text)
                        elif not next_section and para['page'] >= section['page']:
                            # 마지막 섹션이면 이후 페이지의 모든 문단 포함
                            section_content.append(para_text)
                    
                    # 섹션이 있으면 저장 (콘텐츠가 없어도 섹션은 유지) - 세부 목차
                    sections.append({
                        "title": section['title'],
                        "content": section_content if section_content else [],
                        "page": section.get('page', 0)  # 페이지 정보 추가
                    })
            else:
                # 섹션이 없으면 모든 문단을 하나의 본문으로
                all_content = []
                for para in content['content']:
                    para_text = para.get('text', '').strip()
                    if para_text:
                        para_text = re.sub(r'\(cid:\d+\)', '', para_text).strip()
                        if para_text and len(para_text) >= 3:
                            exclude_patterns = [
                                r'^>>>',
                                r'^\d{4}학년도',
                                r'^\d{2}:\d{2}',
                            ]
                            if not any(re.search(p, para_text) for p in exclude_patterns):
                                all_content.append(para_text)
                
                sections = [{
                    "title": "본문",
                    "content": all_content if all_content else [],
                    "page": content.get('page', 0)
                }]
            
            # 강의에 속한 문제 찾기 (페이지 범위 기반)
            lecture_problems = []
            start_page = content.get('start_page', 0)
            end_page = content.get('end_page', 0)
            
            if start_page > 0 and end_page > 0:
                for problem in problems:
                    problem_page = problem.get('page', 0)
                    if start_page <= problem_page <= end_page:
                        problem_id = problem.get('problem_id', '')
                        lecture_problems.append(problem_id)
            
            # 큰 단위 강의 JSON 생성 (세부 목차 포함)
            lecture_json = {
                "subject": self.subject,
                "lecture_id": lecture_id,
                "title": content['title'],  # "1 시의 표현과 형식" 같은 큰 단위 제목
                "sections": sections,  # 세부 목차들
                "problems": lecture_problems if lecture_problems else []  # 해당 강의의 문제 ID 목록
            }
            
            lecture_json_path = self.lectures_dir / f"lecture_{lecture_id:02d}.json"
            # 증분 파싱: 기존 파일이 있고 기존 강의 목록에 있으면 건너뛰기
            if lecture_json_path.exists() and lecture_id in existing_lecture_ids:
                # 기존 파일은 그대로 유지 (이미 파싱된 강의)
                print(f"    ⏭️ [저장] 강의 {lecture_id}는 이미 저장됨 - 건너뜀")
                skipped_count += 1
                continue
            
            # 새로 파싱한 강의 저장
            with open(lecture_json_path, 'w', encoding='utf-8') as f:
                json.dump(lecture_json, f, ensure_ascii=False, indent=2)
            print(f"    ✓ [저장] 강의 {lecture_id} 저장: {lecture_json_path.name} (섹션 {len(sections)}개)")
            saved_count += 1
        
        if skipped_count > 0:
            print(f"    ⏭️ [저장] {skipped_count}개 강의 건너뜀 (이미 저장됨)")
        if saved_count > 0:
            print(f"    ✓ [저장] {saved_count}개 새 강의 저장 완료")
        
        # 3. problem_p{page}_{problem_id}.json (페이지 번호 포함) - 증분 파싱 지원
        if problems:
            # problems 폴더가 없으면 생성
            self.problems_dir.mkdir(parents=True, exist_ok=True)
            new_problem_count = 0
            for problem in problems:
                problem_id = problem['problem_id']
                page = problem.get('page', 0)
                # 파일명에 페이지 번호 포함: problem_p09_01.json
                problem_json_path = self.problems_dir / f"problem_p{page:02d}_{problem_id}.json"
                
                # 증분 파싱: 기존 파일이 있으면 건너뛰기 (이미 파싱된 문제)
                if problem_json_path.exists():
                    continue
                
                with open(problem_json_path, 'w', encoding='utf-8') as f:
                    json.dump(problem, f, ensure_ascii=False, indent=2)
                new_problem_count += 1
            
            if new_problem_count > 0:
                print(f"    ✓ {new_problem_count}개 새 문제 저장: {self.problems_dir}")
            else:
                print(f"    ⏭️ 새로 파싱된 문제 없음 (모두 이미 파싱됨)")
        else:
            print(f"    ⚠️ 추출된 문제가 없습니다. 문제 패턴을 확인하세요.")
        
        # 5. 영역 시각화 (선택적) - YOLO 없이 OCR 좌표 기반
        if lectures or problems:
            print(f"    [시각화] 추출된 영역을 이미지에 표시 중...")
            try:
                self._visualize_regions(lectures, lecture_contents, problems)
            except Exception as e:
                logger.warning(f"영역 시각화 실패: {e}")
    
    def _visualize_regions(
        self,
        lectures: List[Dict[str, Any]],
        lecture_contents: List[Dict[str, Any]],
        problems: List[Dict[str, Any]]
    ):
        """
        추출된 영역을 페이지 이미지에 시각화 (OCR 좌표 기반)
        
        색상:
        - 빨강: 강의 제목
        - 파랑: 소단원
        - 초록: 본문 문단
        - 주황: 문제 영역
        """
        # visualizations_dir는 이미 __init__에서 생성됨
        
        # 페이지별로 그룹화
        page_lectures = {}
        page_problems = {}
        page_sections = {}
        
        for lecture in lectures:
            page = lecture['page']
            if page not in page_lectures:
                page_lectures[page] = []
            page_lectures[page].append(lecture)
        
        for problem in problems:
            page = problem.get('page', 0)
            if page > 0:
                if page not in page_problems:
                    page_problems[page] = []
                page_problems[page].append(problem)
        
        for content in lecture_contents:
            for section in content.get('sections', []):
                page = section.get('page', 0)
                if page > 0:
                    if page not in page_sections:
                        page_sections[page] = []
                    page_sections[page].append(section)
        
        # 각 페이지 이미지에 영역 그리기
        page_files = list(self.pages_dir.glob("page_*.png"))
        for page_num in range(1, len(page_files) + 1):
            page_image_path = self.pages_dir / f"page_{page_num:03d}.png"
            if not page_image_path.exists():
                continue
            
            try:
                # 이미지 로드
                img = Image.open(page_image_path)
                draw = ImageDraw.Draw(img)
                
                # 폰트 설정 (기본 폰트 사용)
                try:
                    font = ImageFont.truetype("arial.ttf", 16)
                except:
                    try:
                        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
                    except:
                        font = ImageFont.load_default()
                
                # 강의 제목 그리기 (빨강)
                if page_num in page_lectures:
                    for lecture in page_lectures[page_num]:
                        bbox = lecture.get('bbox', [])
                        if len(bbox) == 4:
                            x1, y1, x2, y2 = bbox
                            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
                            draw.text((x1, y1 - 20), f"강의: {lecture['title'][:30]}", fill="red", font=font)
                
                # 소단원 그리기 (파랑)
                if page_num in page_sections:
                    for section in page_sections[page_num]:
                        bbox = section.get('bbox', [])
                        if len(bbox) == 4:
                            x1, y1, x2, y2 = bbox
                            draw.rectangle([x1, y1, x2, y2], outline="blue", width=2)
                            draw.text((x1, y1 - 18), f"소단원: {section['title'][:25]}", fill="blue", font=font)
                
                # 문제 영역 그리기 (주황)
                if page_num in page_problems:
                    for problem in page_problems[page_num]:
                        bbox = problem.get('bbox', [])
                        if len(bbox) == 4:
                            x1, y1, x2, y2 = bbox
                            draw.rectangle([x1, y1, x2, y2], outline="orange", width=3)
                            problem_id = problem.get('problem_id', '?')
                            draw.text((x1, y1 - 20), f"문제 {problem_id}", fill="orange", font=font)
                
                # 저장
                output_path = self.visualizations_dir / f"page_{page_num:03d}_visualized.png"
                img.save(output_path)
                
            except Exception as e:
                logger.warning(f"페이지 {page_num} 시각화 실패: {e}")
        
        print(f"    ✓ 시각화 완료: {self.visualizations_dir}")
    
    def _extract_concept_content_and_problem_images(
        self,
        all_ocr_data: List[Dict[str, Any]],
        lectures: List[Dict[str, Any]],
        lecture_contents: List[Dict[str, Any]],
        problems: List[Dict[str, Any]]
    ):
        """
        개념, 본문, 문제 영역 이미지 추출 및 저장 (오케스트레이터)
        
        - concepts_images/: 각 개념(소단원) 영역 이미지
        - content_images/: 본문(지문, 설명) 영역 이미지
        - problems_images/: 각 문제 영역 이미지
        
        주의: 페이지 이미지가 먼저 생성되어 있어야 함 (process_pdf의 1단계)
        """
        # 페이지 이미지 존재 확인
        page_files = list(self.pages_dir.glob("page_*.png"))
        if not page_files:
            print(f"    ⚠️ 페이지 이미지가 없습니다. 이미지 추출을 건너뜁니다.")
            logger.warning(f"페이지 이미지 디렉토리: {self.pages_dir}, 파일 수: 0")
            return
        
        print(f"    페이지 이미지 {len(page_files)}개 발견, 이미지 추출 시작...")
        
        # OCR 데이터에서 직접 논리적 블록 추출 (헤더 기반)
        concept_blocks = self._extract_concept_blocks_from_ocr(all_ocr_data)
        content_blocks = self._extract_content_blocks_from_ocr(all_ocr_data)
        
        # 본문 블록이 없으면 fallback: 문제 번호 직전의 작품 텍스트를 본문으로 인식
        if len(content_blocks) == 0:
            print(f"    ⚠️ 본문 헤더 매칭 실패, fallback 로직 시도...")
            content_blocks = self._extract_content_blocks_fallback(all_ocr_data)
        
        # 각 타입별 이미지 크롭 (책임 분리)
        print(f"\n[개념 블록 추출 결과] 총 {len(concept_blocks)}개 발견")
        for block in concept_blocks:
            print(f"  - 페이지 {block['page']}: '{block['title']}'")
        
        concept_count = self._crop_concept_images(concept_blocks, lecture_contents)
        print(f"\n[본문 블록 추출 결과] 총 {len(content_blocks)}개 발견")
        for block in content_blocks:
            print(f"  - 페이지 {block['page']}: '{block['title']}'")
        
        content_count, content_metadata = self._crop_content_images(content_blocks, lecture_contents)
        problem_count = self._crop_problem_images(problems)
        
        # 본문 이미지 JSON 메타데이터 저장
        if content_metadata:
            self._save_content_metadata(content_metadata)
        
        # 결과 출력
        if concept_count > 0:
            print(f"    ✓ 개념 이미지 {concept_count}개 저장: {self.concepts_images_dir}")
        else:
            print(f"    ⚠️ 개념 이미지 0개 (블록 추출 실패 또는 bbox 없음)")
        
        if content_count > 0:
            print(f"    ✓ 본문 이미지 {content_count}개 저장: {self.content_images_dir}")
            print(f"    ✓ 본문 메타데이터 {len(content_metadata)}개 저장: {self.content_dir}")
        else:
            print(f"    ⚠️ 본문 이미지 0개 (블록 추출 실패 또는 bbox 없음)")
        
        if problem_count > 0:
            print(f"    ✓ 문제 이미지 {problem_count}개 저장: {self.problems_images_dir}")
        else:
            print(f"    ⚠️ 문제 이미지 0개 (문제 추출 실패 또는 bbox 없음)")
    
    def _crop_concept_images(
        self,
        concept_blocks: List[Dict[str, Any]],
        lecture_contents: List[Dict[str, Any]]
    ) -> int:
        """
        개념 이미지 크롭 및 저장
        
        Args:
            concept_blocks: 헤더 기반으로 추출된 개념 블록 리스트
            lecture_contents: 강의 콘텐츠 (백업용)
        
        Returns:
            저장된 개념 이미지 개수
        """
        concept_count = 0
        
        # 페이지별로 그룹화하여 순서 매기기
        from collections import defaultdict
        blocks_by_page = defaultdict(list)
        for block in concept_blocks:
            blocks_by_page[block['page']].append(block)
        
        # 각 페이지 내에서 y좌표 순서로 정렬
        for page_num in blocks_by_page:
            blocks_by_page[page_num].sort(key=lambda b: b['bbox'][1] if len(b.get('bbox', [])) >= 2 else 0)
        
        # 1. 헤더 기반 개념 블록 크롭 (우선)
        for page_num in sorted(blocks_by_page.keys()):
            page_blocks = blocks_by_page[page_num]
            for block_idx, block in enumerate(page_blocks, 1):
                page = block['page']
                bbox = block['bbox']
                title = block['title']
                
                if len(bbox) != 4 or page <= 0:
                    continue
                
                try:
                    page_image_path = self.pages_dir / f"page_{page:03d}.png"
                    if not page_image_path.exists():
                        continue
                    
                    img = Image.open(page_image_path)
                    x1, y1, x2, y2 = bbox
                    
                    # bbox 조정
                    x1 = max(0, min(x1, img.width))
                    y1 = max(0, min(y1, img.height))
                    x2 = max(x1, min(x2, img.width))
                    y2 = max(y1, min(y2, img.height))
                    
                    if x2 <= x1 or y2 <= y1:
                        continue
                    
                    concept_img = img.crop((x1, y1, x2, y2))
                    
                    if concept_img.width < 10 or concept_img.height < 10:
                        continue
                    
                    concept_count += 1
                    # 파일명: concept_p{페이지번호}_{순서}.png (예: concept_p08_01.png)
                    concept_filename = f"concept_p{page:02d}_{block_idx:02d}.png"
                    concept_path = self.concepts_images_dir / concept_filename
                    concept_img.save(concept_path)
                except Exception as e:
                    logger.warning(f"개념 이미지 추출 실패 ({title}): {e}")
        
        # 2. 백업 방식: 강의 단위 개념 이미지 (헤더 기반이 실패한 경우)
        if concept_count == 0 and lecture_contents:
            concept_count += self._crop_concept_images_fallback(lecture_contents)
        
        return concept_count
    
    def _crop_content_images(
        self,
        content_blocks: List[Dict[str, Any]],
        lecture_contents: List[Dict[str, Any]] = None
    ) -> tuple[int, List[Dict[str, Any]]]:
        """
        본문 이미지 크롭 및 저장
        
        Args:
            content_blocks: 헤더 기반으로 추출된 본문 블록 리스트
            lecture_contents: 강의 콘텐츠 (강의 ID 매핑용)
        
        Returns:
            (저장된 본문 이미지 개수, 메타데이터 리스트)
        """
        content_count = 0
        content_metadata = []
        
        # 강의 페이지 범위 매핑 생성 (본문이 속한 강의 찾기)
        lecture_page_ranges = {}
        if lecture_contents:
            for lecture in lecture_contents:
                start_page = lecture.get('start_page', 0)
                end_page = lecture.get('end_page', 0)
                if start_page > 0 and end_page > 0:
                    lecture_page_ranges[lecture['lecture_id']] = (start_page, end_page)
        
        for block in content_blocks:
            page = block['page']
            bbox = block['bbox']
            title = block.get('title', '작품 텍스트')
            text_lines = block.get('text_lines', [])
            
            if len(bbox) != 4 or page <= 0:
                continue
            
            try:
                page_image_path = self.pages_dir / f"page_{page:03d}.png"
                if not page_image_path.exists():
                    continue
                
                img = Image.open(page_image_path)
                x1, y1, x2, y2 = bbox
                
                # bbox 조정
                x1 = max(0, min(x1, img.width))
                y1 = max(0, min(y1, img.height))
                x2 = max(x1, min(x2, img.width))
                y2 = max(y1, min(y2, img.height))
                
                if x2 <= x1 or y2 <= y1:
                    continue
                
                content_img = img.crop((x1, y1, x2, y2))
                
                if content_img.width < 10 or content_img.height < 10:
                    continue
                
                content_count += 1
                # 파일명: content_p{페이지번호}_{순서}.png (예: content_p09_01.png)
                # 페이지별로 그룹화하여 순서 매기기
                if not hasattr(self, '_content_count_by_page'):
                    self._content_count_by_page = {}
                if page not in self._content_count_by_page:
                    self._content_count_by_page[page] = 0
                self._content_count_by_page[page] += 1
                content_id = f"{self._content_count_by_page[page]:02d}"
                content_filename = f"content_p{page:02d}_{content_id}.png"
                content_path = self.content_images_dir / content_filename
                content_img.save(content_path)
                
                # 본문이 속한 강의 찾기
                lecture_id = None
                for lid, (start, end) in lecture_page_ranges.items():
                    if start <= page <= end:
                        lecture_id = lid
                        break
                
                # 메타데이터 생성
                metadata = {
                    "content_id": content_id,
                    "page": page,
                    "title": title,
                    "image_path": f"/api/data/literature/content_images/{content_filename}",
                    "text": text_lines,  # 원본 텍스트 (TTS용)
                    "bbox": [x1, y1, x2, y2],
                    "lecture_id": lecture_id  # 속한 강의 ID
                }
                content_metadata.append(metadata)
            except Exception as e:
                logger.warning(f"본문 이미지 추출 실패 ({title}): {e}")
        
        return content_count, content_metadata
    
    def _save_content_metadata(
        self,
        content_metadata: List[Dict[str, Any]]
    ):
        """
        본문 이미지 메타데이터를 JSON 파일로 저장
        
        Args:
            content_metadata: 본문 이미지 메타데이터 리스트
        """
        if not content_metadata:
            return
        
        # content 디렉토리에 JSON 파일 저장 (이미지와 분리)
        for metadata in content_metadata:
            page = metadata['page']
            content_id = metadata['content_id']
            # 파일명: content_p{page}_{id}.json
            json_filename = f"content_p{page:02d}_{content_id}.json"
            json_path = self.content_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _crop_problem_images(
        self,
        problems: List[Dict[str, Any]]
    ) -> int:
        """
        문제 이미지 크롭 및 저장
        
        설계 문서 v1.1 기준:
        - 문제 영역: 문제 번호 + 지문 + 선택지 전체를 하나의 블록으로 캡처
        - 이미지 단계에서는 세분화 안 함 (JSON 단계에서 세분화)
        
        Args:
            problems: 추출된 문제 리스트
        
        Returns:
            저장된 문제 이미지 개수
        """
        problem_count = 0
        START_PAGE = self.config.get('start_content_page', 8)
        
        for problem in problems:
            bbox = problem.get('bbox', [])
            page = problem.get('page', 0)
            
            # 시작 페이지 미만은 건너뛰기
            if page < START_PAGE:
                continue
            
            if len(bbox) == 4 and page > 0:
                try:
                    page_image_path = self.pages_dir / f"page_{page:03d}.png"
                    if not page_image_path.exists():
                        logger.debug(f"페이지 이미지 없음: {page_image_path}")
                        continue
                    
                    img = Image.open(page_image_path)
                    x1, y1, x2, y2 = bbox
                    
                    # bbox가 이미지 범위를 벗어나지 않도록 조정
                    x1 = max(0, min(x1, img.width))
                    y1 = max(0, min(y1, img.height))
                    x2 = max(x1, min(x2, img.width))
                    y2 = max(y1, min(y2, img.height))
                    
                    # 유효한 bbox인지 확인
                    if x2 <= x1 or y2 <= y1:
                        logger.warning(f"잘못된 bbox: [{x1}, {y1}, {x2}, {y2}]")
                        continue
                    
                    # 영역 크롭
                    problem_img = img.crop((x1, y1, x2, y2))
                    
                    # 최소 크기 확인 (너무 작은 영역은 건너뛰기)
                    if problem_img.width < 10 or problem_img.height < 10:
                        logger.debug(f"문제 이미지 너무 작음: {problem_img.width}x{problem_img.height}")
                        continue
                    
                    # 저장 (파일명에 페이지 번호 포함)
                    problem_count += 1
                    problem_id = problem.get('problem_id', f'{problem_count:03d}')
                    page = problem.get('page', 0)
                    # 파일명에 페이지 번호 포함: problem_p09_01.png
                    problem_path = self.problems_images_dir / f"problem_p{page:02d}_{problem_id}.png"
                    problem_img.save(problem_path)
                except Exception as e:
                    logger.warning(f"문제 이미지 추출 실패 (문제 ID: {problem.get('problem_id', '?')}, 페이지: {page}): {e}")
        
        return problem_count
    
    def _crop_concept_images_fallback(
        self,
        lecture_contents: List[Dict[str, Any]]
    ) -> int:
        """
        개념 이미지 크롭 (백업 방식: 강의 단위)
        
        헤더 기반 추출이 실패한 경우 강의 단위로 크롭
        
        Args:
            lecture_contents: 강의 콘텐츠 리스트
        
        Returns:
            저장된 개념 이미지 개수
        """
        concept_count = 0
        
        for content in lecture_contents:
            lecture_id = content.get('lecture_id', 0)
            sections = content.get('sections', [])
            
            if not sections:
                continue
            
            # 강의 내 모든 섹션의 bbox를 통합하여 하나의 개념 이미지로
            try:
                # 페이지별로 섹션 그룹화
                page_sections = {}
                for section in sections:
                    page = section.get('page', 0)
                    if page > 0:
                        if page not in page_sections:
                            page_sections[page] = []
                        page_sections[page].append(section)
                
                # 각 페이지별로 개념 블록 생성
                for page, page_section_list in page_sections.items():
                    if not page_section_list:
                        continue
                    
                    page_image_path = self.pages_dir / f"page_{page:03d}.png"
                    if not page_image_path.exists():
                        continue
                    
                    img = Image.open(page_image_path)
                    
                    # 모든 섹션의 bbox를 통합
                    min_x = min(s.get('bbox', [0, 0, 0, 0])[0] for s in page_section_list if len(s.get('bbox', [])) == 4)
                    min_y = min(s.get('bbox', [0, 0, 0, 0])[1] for s in page_section_list if len(s.get('bbox', [])) == 4)
                    max_x = max(s.get('bbox', [0, 0, 0, 0])[2] for s in page_section_list if len(s.get('bbox', [])) == 4)
                    max_y = max(s.get('bbox', [0, 0, 0, 0])[3] for s in page_section_list if len(s.get('bbox', [])) == 4)
                    
                    # bbox 조정
                    x1 = max(0, min(min_x, img.width))
                    y1 = max(0, min(min_y, img.height))
                    x2 = max(x1, min(max_x, img.width))
                    y2 = max(y1, min(max_y, img.height))
                    
                    # 유효한 bbox 확인
                    if x2 <= x1 or y2 <= y1:
                        continue
                    
                    # 영역 크롭
                    concept_img = img.crop((x1, y1, x2, y2))
                    
                    # 최소 크기 확인
                    if concept_img.width < 10 or concept_img.height < 10:
                        continue
                    
                    # 저장 (강의 단위로 하나의 파일)
                    concept_count += 1
                    lecture_title = content.get('title', 'concept')[:30] if content.get('title') else 'concept'
                    concept_filename = f"concept_{lecture_id:02d}_{lecture_title}.png"
                    concept_filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', concept_filename)
                    if len(concept_filename) > 200:
                        concept_filename = concept_filename[:200] + ".png"
                    concept_path = self.concepts_images_dir / concept_filename
                    concept_img.save(concept_path)
            except Exception as e:
                logger.warning(f"개념 이미지 추출 실패 (강의 {lecture_id}): {e}")
        
        return concept_count
    
    def _extract_concept_blocks_from_ocr(
        self,
        all_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        OCR 데이터에서 개념 블록 추출 (헤더 기반)
        
        설계 문서 v1.1 기준:
        - 개념 영역: 좌측 보조 박스 포함, 좌/우 컬럼 전체를 하나의 개념 블록으로
        - 시작: 개념 제목 패턴 인식
        - 종료: 다음 개념 제목 / "작품으로 이해하기" / 문제 번호
        
        예: "시적 표현", "시의 형식" 같은 메인 제목부터 다음 메인 제목 전까지
        """
        blocks = []
        concept_patterns = self.config.get('concept_title_patterns', [
            r'^[가-힣]{2,}\s+[가-힣]{2,}',  # "시적 표현", "시의 형식"
            r'^\d+\s+[가-힣]{2,}\s+[가-힣]{2,}',  # "1 시적 표현"
        ])
        
        # config에서 시작 페이지 가져오기
        START_PAGE = self.config.get('start_content_page', 8)
        
        for page_idx, ocr_data in enumerate(all_ocr_data):
            page_num = ocr_data['page_num']
            
            # 8페이지 미만은 건너뛰기
            if page_num < START_PAGE:
                continue
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            # 색상 정보 가져오기 (pdfplumber 사용 시)
            colors = ocr_data.get('color', [])
            has_color_info = len(colors) == len(texts)
            
            # 단어별 색상 매핑 생성 (텍스트+좌표로 고유하게 식별)
            word_color_map = {}
            if has_color_info:
                for i, (text, left, top) in enumerate(zip(texts, lefts, tops)):
                    key = (text, left, top)  # 텍스트+좌표로 고유 식별
                    if i < len(colors):
                        word_color_map[key] = colors[i]
            
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 디버깅: 페이지별 텍스트 샘플 출력 (처음 5줄만)
            if page_num <= 12:  # 8-12페이지만
                print(f"\n[페이지 {page_num} OCR 텍스트 샘플]")
                for i, line in enumerate(lines[:10]):  # 처음 10줄만
                    line_text = " ".join([word['text'] for word in line]).strip()
                    if line_text:
                        # 색상 정보도 함께 출력
                        if has_color_info:
                            line_colors = []
                            for word in line:
                                key = (word['text'], word['left'], word['top'])
                                color = word_color_map.get(key)
                                if color:
                                    line_colors.append(color)
                            if line_colors:
                                from collections import Counter
                                main_color = Counter(line_colors).most_common(1)[0][0]
                                print(f"  줄 {i}: '{line_text}' [색상: RGB{main_color}]")
                            else:
                                print(f"  줄 {i}: '{line_text}' [색상: None]")
                        else:
                            print(f"  줄 {i}: '{line_text}'")
            
            # 개념 제목 찾기
            for line_idx, line in enumerate(lines):
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                # 색상 기반 필터링 (pdfplumber 사용 시)
                if has_color_info:
                    # 줄의 단어들의 색상 정보 수집
                    line_colors = []
                    for word in line:
                        key = (word['text'], word['left'], word['top'])
                        color = word_color_map.get(key)
                        if color:
                            line_colors.append(color)
                    
                    # 색상이 있는 경우, 주요 색상 확인
                    if line_colors:
                        # 가장 많이 나타나는 색상 찾기
                        from collections import Counter
                        color_counter = Counter(line_colors)
                        main_color = color_counter.most_common(1)[0][0]
                        
                        # 디버깅: 색상 정보 출력
                        if page_num <= 12 and line_idx < 5:
                            print(f"  줄 {line_idx} 색상: '{line_text}' → RGB{main_color}")
                        
                        # 색상 기반 필터링: 검은색(0,0,0) 또는 진한 색상만 개념 제목으로 간주
                        r, g, b = main_color if isinstance(main_color, tuple) and len(main_color) >= 3 else (0, 0, 0)
                        # 검은색 또는 매우 어두운 색상 (RGB 합이 100 이하)
                        is_dark = (r + g + b) < 100
                        # 또는 특정 색상 범위 (예: 파란색 계열)
                        is_blue = b > max(r, g) + 30  # 파란색이 다른 색보다 30 이상 큼
                        
                        # 색상 필터링: 너무 밝은 색상은 제외 (회색 본문 텍스트)
                        if not is_dark and not is_blue and (r + g + b) > 200:
                            # 너무 밝은 색상은 본문일 가능성이 높음
                            continue
                
                # 특수 문자 제거 (cid: 같은 pdfplumber 특수 문자 제거)
                # cid: 패턴과 괄호 제거 후 매칭
                cleaned_line_text = re.sub(r'\(cid:\d+\)', '', line_text)
                cleaned_line_text = cleaned_line_text.strip()
                
                # 개념 제목 패턴 매칭 (엄격하게)
                # 제외할 패턴들 (문제 지시문, 정답과 해설 등)
                exclude_patterns = [
                    r'다음 글을 읽고',
                    r'물음에 답하시오',
                    r'정답과 해설',
                    r'문제\s*\d+',
                    r'^\d{2}$',  # 문제 번호
                    r'[①②③④⑤]',  # 선택지 번호
                    r'cid:',  # pdfplumber 특수 문자
                ]
                
                # 제외 패턴에 해당하면 스킵
                if any(re.search(exclude_pat, line_text) for exclude_pat in exclude_patterns):
                    continue
                
                # 개념 제목 패턴 매칭 (cleaned 텍스트 사용)
                matched = False
                matched_pattern = None
                for pattern in concept_patterns:
                    match = re.search(pattern, cleaned_line_text)
                    if match:
                        # 매칭된 부분이 줄의 시작 부분에 있어야 함 (전체 텍스트가 아닌 경우 제외)
                        if match.start() == 0 or len(cleaned_line_text) < 30:  # 짧은 텍스트는 허용
                            matched = True
                            matched_pattern = pattern
                            break
                
                if not matched:
                    continue
                
                # 너무 긴 텍스트는 개념 제목이 아님 (본문 내용일 가능성)
                if len(cleaned_line_text) > 50:
                    continue
                
                # 매칭된 텍스트를 cleaned 버전으로 교체
                line_text = cleaned_line_text
                
                # 디버깅: 매칭된 개념 제목 출력
                print(f"[개념 제목 매칭] 페이지 {page_num}, 줄 {line_idx}: '{line_text}' (패턴: {matched_pattern})")
                
                # 다음 개념 제목이나 "작품으로 이해하기" 또는 문제가 나올 때까지의 영역 찾기
                start_y = line[0]['top']
                end_y = None
                
                # 다음 페이지나 다음 개념 제목 찾기
                for next_page_idx in range(page_idx, min(page_idx + 5, len(all_ocr_data))):
                    next_ocr = all_ocr_data[next_page_idx]
                    next_texts = next_ocr.get('text', [])
                    next_tops = next_ocr.get('top', [])
                    next_lefts = next_ocr.get('left', [])
                    next_widths = next_ocr.get('width', [])
                    next_heights = next_ocr.get('height', [])
                    
                    if not next_texts:
                        continue
                    
                    next_lines = self._group_texts_by_line(next_texts, next_tops, next_lefts, next_widths, next_heights)
                    
                    for next_line_idx, next_line in enumerate(next_lines):
                        next_line_text = " ".join([w['text'] for w in next_line]).strip()
                        next_cleaned = re.sub(r'\(cid:\d+\)', '', next_line_text).strip()
                        
                        # 다음 개념 제목인지 확인
                        next_is_concept = False
                        for pattern in concept_patterns:
                            if re.search(pattern, next_cleaned):
                                next_is_concept = True
                                break
                        
                        # 다음 개념 제목, 본문 헤더, 문제 번호 발견 시 종료
                        if (next_page_idx > page_idx or (next_page_idx == page_idx and next_line_idx > line_idx)) and (
                            next_is_concept or
                            any(re.search(p, next_cleaned) for p in self.config.get('content_header_patterns', [])) or
                            re.match(self.config.get('problem_number_pattern', r'^\d{2}$'), next_line_text)
                        ):
                            if next_page_idx == page_idx:
                                end_y = next_line[0]['top']
                            else:
                                # 다음 페이지면 현재 페이지 끝
                                end_y = None
                            break
                    
                    if end_y is not None:
                        break
                
                # bbox 계산 (v1.1 설계: 좌측 보조 박스 포함, 좌/우 컬럼 전체)
                first_word = line[0]
                
                # 개념 영역의 줄 범위 결정 (end_y 직전까지)
                concept_lines = []
                for line_group in lines[line_idx:]:
                    # end_y가 설정되어 있으면 그 직전까지만 포함
                    if end_y is not None and line_group[0]['top'] >= end_y:
                        break
                    concept_lines.append(line_group)
                
                # end_y가 None이면 페이지 끝까지
                if end_y is None:
                    if concept_lines:
                        last_line = concept_lines[-1]
                        end_y = last_line[-1]['top'] + last_line[-1]['height']
                    else:
                        end_y = first_word['top'] + first_word['height'] * 20  # 기본값
                
                # v1.1 설계: 좌/우 컬럼 전체 포함
                # left: 모든 단어의 최소 left (좌측 보조 박스 포함)
                # right: 모든 단어의 최대 right
                if concept_lines:
                    # 모든 줄의 단어들에서 최소 left, 최대 right 찾기
                    all_words_in_concept = [w for line_group in concept_lines for w in line_group]
                    if all_words_in_concept:
                        left = min(w['left'] for w in all_words_in_concept)
                        right = max(w['left'] + w['width'] for w in all_words_in_concept)
                    else:
                        left = first_word['left']
                        right = first_word['left'] + first_word['width']
                else:
                    left = first_word['left']
                    right = first_word['left'] + first_word['width']
                
                blocks.append({
                    'title': line_text,
                    'page': page_num,
                    'bbox': [left, start_y, right, end_y],
                    'line_idx': line_idx  # 병합을 위해 저장
                })
                # break 제거: 한 페이지에 여러 개념 블록이 있을 수 있음
        
        # 같은 페이지에서 연속된 번호 개념 병합 (예: (1), (2) -> 하나로)
        merged_blocks = []
        from collections import defaultdict
        blocks_by_page = defaultdict(list)
        for block in blocks:
            blocks_by_page[block['page']].append(block)
        
        for page_num in sorted(blocks_by_page.keys()):
            page_blocks = blocks_by_page[page_num]
            # line_idx 순서로 정렬
            page_blocks.sort(key=lambda b: b.get('line_idx', 0))
            
            i = 0
            while i < len(page_blocks):
                current_block = page_blocks[i]
                current_title = current_block['title']
                
                # 현재 블록의 번호 추출
                current_match = re.search(r'^\((\d+)\)', current_title)
                
                # 연속된 번호의 블록들을 병합
                merged_block = current_block.copy()
                j = i + 1
                
                while j < len(page_blocks):
                    next_block = page_blocks[j]
                    next_title = next_block['title']
                    next_match = re.search(r'^\((\d+)\)', next_title)
                    
                    # 둘 다 번호가 있고 연속된 번호면 병합
                    if current_match and next_match:
                        current_num = int(current_match.group(1))
                        next_num = int(next_match.group(1))
                        
                        # 연속된 번호이고 같은 주제 계열이면 병합
                        if next_num == current_num + 1:
                            # bbox 병합 (더 넓은 영역으로)
                            merged_bbox = [
                                min(merged_block['bbox'][0], next_block['bbox'][0]),  # left
                                min(merged_block['bbox'][1], next_block['bbox'][1]),  # top
                                max(merged_block['bbox'][2], next_block['bbox'][2]),  # right
                                max(merged_block['bbox'][3], next_block['bbox'][3])   # bottom
                            ]
                            merged_block['bbox'] = merged_bbox
                            # 제목은 첫 번째 블록의 제목 유지 (병합 표시는 하지 않음)
                            # 예: "(1) 시적 표현의 개념" + "(2) 시의 형식" -> "(1) 시적 표현의 개념" 유지
                            # 병합된 블록임을 표시하려면 주석 처리된 코드 사용
                            # merged_block['title'] = f"{current_title} + {next_title}"
                            j += 1
                            continue
                    
                    break
                
                merged_blocks.append(merged_block)
                i = j
        
        return merged_blocks
    
    def _extract_content_blocks_from_ocr(
        self,
        all_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        OCR 데이터에서 본문 블록 추출 (헤더 기반)
        
        설계 문서 v1.1 기준:
        - 본문 영역: "작품으로 이해하기" 헤더부터 문제 번호 직전까지
        - 시 전문은 하나의 연속 본문으로 처리
        
        예: "작품으로 이해하기" 헤더부터 다음 메인 제목이나 문제 전까지
        """
        blocks = []
        content_header_patterns = self.config.get('content_header_patterns', [
            r'작품으로\s*이해하기',
            r'작품\s*이해',
        ])
        
        # config에서 시작 페이지 가져오기
        START_PAGE = self.config.get('start_content_page', 8)
        
        for page_idx, ocr_data in enumerate(all_ocr_data):
            page_num = ocr_data['page_num']
            
            # 8페이지 미만은 건너뛰기
            if page_num < START_PAGE:
                continue
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 디버깅: 본문 헤더 찾기 전 텍스트 샘플 출력
            if page_num <= 12:
                print(f"\n[페이지 {page_num} 본문 헤더 검색]")
                for i, line in enumerate(lines[:15]):  # 처음 15줄 확인
                    line_text = " ".join([word['text'] for word in line]).strip()
                    if line_text:
                        # "작품" 또는 "이해" 키워드가 포함된 줄 강조
                        if '작품' in line_text or '이해' in line_text:
                            print(f"  ⭐ 줄 {i}: '{line_text}' [본문 헤더 후보]")
                        else:
                            print(f"  줄 {i}: '{line_text}'")
            
            # 본문 헤더 찾기
            for line_idx, line in enumerate(lines):
                line_text = " ".join([word['text'] for word in line])
                line_text = line_text.strip()
                
                if not line_text:
                    continue
                
                # 특수 문자 제거 (cid: 같은 pdfplumber 특수 문자 제거)
                cleaned_line_text = re.sub(r'\(cid:\d+\)', '', line_text)
                cleaned_line_text = cleaned_line_text.strip()
                
                # 본문 헤더 패턴 매칭 (엄격하게)
                # 제외할 패턴들
                exclude_patterns = [
                    r'정답과 해설',
                    r'문제\s*\d+',
                    r'^\d{2}$',  # 문제 번호
                    r'cid:',  # pdfplumber 특수 문자
                ]
                
                # 제외 패턴에 해당하면 스킵
                if any(re.search(exclude_pat, line_text) for exclude_pat in exclude_patterns):
                    continue
                
                # 본문 헤더 패턴 매칭 (cleaned 텍스트 사용)
                # 여러 줄에 걸쳐 있을 수 있으므로 이전/다음 줄도 확인
                matched = False
                matched_pattern = None
                matched_text = cleaned_line_text
                
                # 현재 줄에서 매칭 시도
                for pattern in content_header_patterns:
                    match = re.search(pattern, cleaned_line_text, re.IGNORECASE)
                    if match:
                        matched = True
                        matched_pattern = pattern
                        matched_text = cleaned_line_text
                        break
                
                # 현재 줄에서 매칭 실패 시, 이전 줄과 합쳐서 확인 (2줄에 걸쳐 있을 수 있음)
                if not matched and line_idx > 0:
                    prev_line = lines[line_idx - 1]
                    prev_text = " ".join([word['text'] for word in prev_line]).strip()
                    prev_cleaned = re.sub(r'\(cid:\d+\)', '', prev_text).strip()
                    combined_text = f"{prev_cleaned} {cleaned_line_text}"
                    
                    for pattern in content_header_patterns:
                        match = re.search(pattern, combined_text, re.IGNORECASE)
                        if match:
                            matched = True
                            matched_pattern = pattern
                            matched_text = combined_text
                            # 이전 줄부터 시작하도록 조정
                            line_idx = line_idx - 1
                            line = prev_line
                            start_y = prev_line[0]['top']
                            break
                
                if not matched:
                    continue
                
                # 매칭된 텍스트 사용
                line_text = matched_text
                
                # 디버깅: 매칭된 본문 헤더 출력
                print(f"[본문 헤더 매칭] 페이지 {page_num}, 줄 {line_idx}: '{line_text}' (패턴: {matched_pattern})")
                
                # 다음 개념 제목이나 문제가 나올 때까지의 영역 찾기
                start_y = line[0]['top']
                end_y = None
                
                # 다음 페이지나 다음 헤더 찾기
                for next_page_idx in range(page_idx, min(page_idx + 3, len(all_ocr_data))):
                    next_ocr = all_ocr_data[next_page_idx]
                    next_texts = next_ocr.get('text', [])
                    next_tops = next_ocr.get('top', [])
                    next_lefts = next_ocr.get('left', [])
                    next_widths = next_ocr.get('width', [])
                    next_heights = next_ocr.get('height', [])
                    
                    if not next_texts:
                        continue
                    
                    next_lines = self._group_texts_by_line(next_texts, next_tops, next_lefts, next_widths, next_heights)
                    
                    for next_line_idx, next_line in enumerate(next_lines):
                        next_line_text = " ".join([w['text'] for w in next_line]).strip()
                        
                        # 다음 개념 제목, 본문 헤더, 문제 번호 발견 시 종료
                        if (next_page_idx > page_idx or (next_page_idx == page_idx and next_line_idx > line_idx)) and (
                            any(re.search(p, next_line_text) for p in self.config.get('concept_title_patterns', [])) or
                            (any(re.search(p, next_line_text) for p in content_header_patterns) and next_line_text != line_text) or
                            re.match(self.config.get('problem_number_pattern', r'^\d{2}$'), next_line_text)
                        ):
                            if next_page_idx == page_idx:
                                end_y = next_line[0]['top']
                            else:
                                end_y = None
                            break
                    
                    if end_y is not None:
                        break
                
                # bbox 계산 (v1.1 설계: 본문 영역 전체 포함)
                first_word = line[0]
                
                # 본문 영역의 줄 범위 결정 (end_y 직전까지)
                content_lines = []
                for line_group in lines[line_idx:]:
                    # end_y가 설정되어 있으면 그 직전까지만 포함
                    if end_y is not None and line_group[0]['top'] >= end_y:
                        break
                    content_lines.append(line_group)
                
                # end_y가 None이면 페이지 끝까지
                if end_y is None:
                    if content_lines:
                        last_line = content_lines[-1]
                        end_y = last_line[-1]['top'] + last_line[-1]['height']
                    else:
                        end_y = first_word['top'] + first_word['height'] * 30  # 기본값
                
                # v1.1 설계: 본문 영역 내 모든 텍스트 포함
                if content_lines:
                    all_words_in_content = [w for line_group in content_lines for w in line_group]
                    if all_words_in_content:
                        left = min(w['left'] for w in all_words_in_content)
                        right = max(w['left'] + w['width'] for w in all_words_in_content)
                    else:
                        left = first_word['left']
                        right = first_word['left'] + first_word['width']
                else:
                    left = first_word['left']
                    right = first_word['left'] + first_word['width']
                
                # 본문 텍스트 라인 추출 (TTS용)
                text_lines = []
                for line_group in content_lines:
                    line_text_content = " ".join([w['text'] for w in line_group]).strip()
                    if line_text_content:
                        text_lines.append(line_text_content)
                
                blocks.append({
                    'title': line_text,
                    'page': page_num,
                    'bbox': [left, start_y, right, end_y],
                    'text_lines': text_lines  # 원본 텍스트 (TTS용)
                })
                # break 제거: 한 페이지에 여러 본문 블록이 있을 수 있음
        
        return blocks
    
    def _extract_content_blocks_fallback(
        self,
        all_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        본문 블록 추출 fallback: "작품으로 이해하기" 헤더가 없는 경우
        문제 번호 직전의 작품 텍스트를 본문으로 인식
        """
        blocks = []
        START_PAGE = self.config.get('start_content_page', 8)
        problem_pattern = self.config.get('problem_number_pattern', r'^\d{2}$')
        
        for page_idx, ocr_data in enumerate(all_ocr_data):
            page_num = ocr_data['page_num']
            
            if page_num < START_PAGE:
                continue
            
            texts = ocr_data.get('text', [])
            tops = ocr_data.get('top', [])
            lefts = ocr_data.get('left', [])
            widths = ocr_data.get('width', [])
            heights = ocr_data.get('height', [])
            
            if not texts:
                continue
            
            lines = self._group_texts_by_line(texts, tops, lefts, widths, heights)
            
            # 문제 번호 위치 찾기
            problem_line_indices = []
            for line_idx, line in enumerate(lines):
                line_text = " ".join([word['text'] for word in line]).strip()
                if re.match(problem_pattern, line_text):
                    problem_line_indices.append(line_idx)
            
            # 문제 번호가 있으면, 그 직전의 작품 텍스트를 본문으로 간주
            if problem_line_indices:
                first_problem_idx = problem_line_indices[0]
                
                # "정답과 해설", "다음 글을 읽고", "[01~03]" 같은 지시문 건너뛰기
                content_start_idx = None
                
                # 문제 번호 앞에서부터 역순으로 탐색
                for line_idx in range(first_problem_idx - 1, -1, -1):
                    line_text = " ".join([word['text'] for word in lines[line_idx]]).strip()
                    cleaned = re.sub(r'\(cid:\d+\)', '', line_text).strip()
                    
                    # 제외할 패턴
                    exclude_patterns = [
                        r'정답과 해설',
                        r'다음 글을 읽고',
                        r'물음에 답하시오',
                        r'^\d{2}$',  # 문제 번호
                        r'^\[.*\]$',  # [01~03], [25001-0001] 같은 번호
                        r'cid:',  # 특수 문자
                    ]
                    
                    if any(re.search(p, cleaned) for p in exclude_patterns):
                        continue
                    
                    # 작품 텍스트로 보이는 줄 찾기 (시 전문, 작가명 등)
                    # 길이가 있고, 특수 패턴이 아닌 경우
                    if len(cleaned) > 5:
                        content_start_idx = line_idx
                        # 더 위쪽에 작품 텍스트가 있을 수 있으므로 계속 탐색
                        # 하지만 너무 위로 올라가지 않도록 제한
                        if line_idx < max(0, first_problem_idx - 50):  # 최대 50줄 위까지만
                            break
                
                if content_start_idx is not None:
                    # 본문 영역 추출: content_start_idx부터 첫 번째 문제 번호 직전까지
                    content_lines = lines[content_start_idx:first_problem_idx]
                    if content_lines and len(content_lines) > 3 and len(content_lines[0]) > 0 and len(content_lines[-1]) > 0:  # 최소 3줄 이상
                        first_word = content_lines[0][0]
                        last_word = content_lines[-1][-1]
                        
                        all_words = [w for line_group in content_lines for w in line_group]
                        if all_words:
                            left = min(w['left'] for w in all_words)
                            right = max(w['left'] + w['width'] for w in all_words)
                            top = first_word['top']
                            bottom = last_word['top'] + last_word['height']
                            
                            # 첫 몇 줄의 텍스트를 제목으로 사용
                            title_lines = content_lines[:3]
                            title_text = " ".join([" ".join([w['text'] for w in line]) for line in title_lines]).strip()
                            title_text = re.sub(r'\(cid:\d+\)', '', title_text).strip()
                            if len(title_text) > 80:
                                title_text = title_text[:80] + "..."
                            
                            # 본문 텍스트 라인 추출 (TTS용)
                            text_lines = []
                            for line_group in content_lines:
                                line_text_content = " ".join([w['text'] for w in line_group]).strip()
                                if line_text_content:
                                    text_lines.append(line_text_content)
                            
                            blocks.append({
                                'title': f"작품 텍스트",
                                'page': page_num,
                                'bbox': [left, top, right, bottom],
                                'text_lines': text_lines  # 원본 텍스트 (TTS용)
                            })
                            print(f"[본문 블록 fallback] 페이지 {page_num}: 줄 {content_start_idx}~{first_problem_idx-1} ({len(content_lines)}줄)")
        
        return blocks
