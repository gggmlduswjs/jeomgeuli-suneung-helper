"""
통합 PDF 처리 파이프라인
extraction + parsing을 단일 플로우로 처리
"""
import logging
from pathlib import Path
from typing import Optional, List, Union, Tuple
from PIL import Image

from app.infrastructure.pdf.extractors import PdfplumberExtractor, OCRExtractor, PyMuPDFExtractor
from app.infrastructure.pdf.types import OCRPageData, ParsingResult, JSONDict
# 통합 파서 사용으로 변경됨 (UnifiedTemplateParser)
from app.infrastructure.pdf.parsers.hybrid_router import HybridRouter
from app.infrastructure.pdf.lecture_contents_extractor import LectureContentsExtractor
from app.infrastructure.pdf.result_saver import ResultSaver
from app.infrastructure.pdf.image_saver import ImageSaver
from app.infrastructure.pdf.image_cache import ImageCache
from app.infrastructure.pdf.page_range_calculator import PageRangeCalculator
from app.infrastructure.pdf.extractor_factory import ExtractorFactory
from app.infrastructure.pdf.exceptions import (
    ParsingError,
    ExtractionError,
    TemplateNotFoundError,
    ImageProcessingError,
    ConfigurationError,
    PageRangeError
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class UnifiedPipeline:
    """
    통합 PDF 처리 파이프라인

    플로우:
    1. 추출 (pdfplumber 또는 OCR)
    2. 파싱 (과목별)
    3. 강의 콘텐츠 추출
    4. 결과 저장
    """

    def __init__(
        self,
        subject: str,
        use_ocr: Union[bool, str] = False,
        config_path: Optional[Path] = None,
        save_results: bool = True,
        save_images: bool = False,
        book_id: Optional[str] = None,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
        auto_sample_pages: int = 5,
        **extractor_kwargs
    ):
        """
        Args:
            subject: 과목명 ('literature', 'math1', 'english')
            use_ocr: OCR 사용 여부 (False면 pdfplumber 사용)
            config_path: config.json 경로 (파서용)
            save_results: 결과를 JSON 파일로 저장할지 여부
            save_images: 개념/본문/문제 이미지를 크롭하여 저장할지 여부
            book_id: 교재 ID (None이면 과목별, 지정하면 교재별 분리)
            start_page: 시작 페이지 번호 (1부터 시작, None이면 처음부터)
            end_page: 종료 페이지 번호 (None이면 끝까지)
            **extractor_kwargs: 추출기 추가 옵션
        """
        self.subject = subject
        self.config_path = config_path
        self.save_results = save_results
        self.save_images = save_images
        self.book_id = book_id
        self.start_page = start_page
        self.end_page = end_page
        self.progress_callback = None  # OCR 진행률 업데이트 콜백
        self.auto_sample_pages = max(1, int(auto_sample_pages or 5))

        # 추출 모드 정규화: 'pdf' | 'ocr' | 'auto'
        normalized_mode = None
        if isinstance(use_ocr, str):
            normalized_mode = use_ocr.strip().lower()
        if normalized_mode in ("auto", "smart"):
            self.extraction_mode = "auto"
        elif bool(use_ocr):
            self.extraction_mode = "ocr"
        else:
            self.extraction_mode = "pdf"

        # 1. 추출기 선택
        # extractor가 받지 않는 인자 필터링
        extractor_only_kwargs = {k: v for k, v in extractor_kwargs.items() 
                                if k not in ['use_ml_postprocess']}
        self._extractor_only_kwargs = extractor_only_kwargs
        
        # pdfplumber 추출기 (항상 준비: auto 모드에서 먼저 사용)
        pdfplumber_kwargs = {k: v for k, v in extractor_only_kwargs.items()
                             if k in ['dpi', 'max_pages']}
        self._pdf_extractor = PdfplumberExtractor(**pdfplumber_kwargs)

        if self.extraction_mode == "ocr":
            self.extractor = self._create_ocr_extractor()
        else:
            # 'pdf' 또는 'auto'는 pdfplumber로 시작
            self.extractor = self._pdf_extractor

        # 2. 파서 선택 (HybridRouter 사용, OCR 데이터 추출 후 동적 선택)
        self.parser = None  # process 메서드에서 동적으로 선택
        self.config_path = config_path
        self.hybrid_router = HybridRouter(
            template_threshold=0.85,
            enable_ai_parsing=True  # Phase 2에서 활성화될 예정
        )
        
        # 페이지 범위 계산기
        self.page_range_calculator = PageRangeCalculator(self.hybrid_router.template_manager)
        
        # 3. 강의 콘텐츠 추출기
        config = self._load_config() if config_path else {}
        self.lecture_extractor = LectureContentsExtractor(subject, config)
        
        # textbook_pipeline 인스턴스 저장 (나중에 메서드 호출용)
        self._textbook_pipeline_ref = None
        
        # 4. 결과 저장기 (교재별 분리)
        if save_results:
            data_dir = settings.API_DIR / "data"
            self.result_saver = ResultSaver(subject, data_dir, book_id=book_id)
        else:
            self.result_saver = None

        logger.info(f"UnifiedPipeline 초기화 완료: {subject}, OCR={use_ocr}, Save={save_results}, BookID={book_id}")

    def set_progress_callback(self, callback):
        """OCR 진행률 업데이트 콜백 설정"""
        self.progress_callback = callback
    
    def _calculate_required_page_range_from_template(self) -> Optional[Tuple[int, Optional[int]]]:
        """템플릿의 강의 목록에서 필요한 페이지 범위 계산
        
        Returns:
            (시작 페이지, 종료 페이지) 튜플 또는 None (템플릿이 없거나 페이지 정보가 없으면)
        """
        return self.page_range_calculator.calculate_from_template(self.subject)

    def _create_ocr_extractor(self) -> OCRExtractor:
        """OCRExtractor 생성 (요청 파라미터를 존중하면서 기본값 보완)"""
        dpi = getattr(self.extractor, 'dpi', 300) if hasattr(self, 'extractor') else 300
        return ExtractorFactory.create_ocr_extractor(self._extractor_only_kwargs, dpi=dpi)

    def _should_switch_to_ocr(self, sample_ocr_data: List[OCRPageData]) -> bool:
        """pdfplumber 결과가 빈약/깨졌으면 OCR로 전환"""
        return ExtractorFactory.should_switch_to_ocr(sample_ocr_data)

    def _get_parser(self, subject: str, config_path: Optional[Path] = None):
        """통합 파서 반환 (모든 과목 공통)"""
        from app.infrastructure.pdf.parsers.unified_parser import UnifiedTemplateParser
        
        # 통합 파서 사용 (템플릿 자동 매칭)
        return UnifiedTemplateParser(
            subject=subject,
            config_path=config_path,
            template=None,  # 자동 매칭
            enable_ai_parsing=False
        )

    def process(self, pdf_path: Path) -> ParsingResult:
        """
        PDF 전체 파이프라인 실행

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            {
                'lectures': [...],
                'lecture_contents': [...],
                'problems': [...],
                'metadata': {...}
            }
        """
        logger.info(f"UnifiedPipeline 시작: {pdf_path}")
        
        # PDF 파일 존재 확인
        if not pdf_path.exists():
            raise ExtractionError(
                f"PDF 파일을 찾을 수 없습니다: {pdf_path}",
                details={"pdf_path": str(pdf_path)}
            )
        
        if not pdf_path.is_file():
            raise ExtractionError(
                f"PDF 경로가 파일이 아닙니다: {pdf_path}",
                details={"pdf_path": str(pdf_path)}
            )

        try:
            # 1. 텍스트 추출
            logger.info("="*50)
            logger.info("1. 텍스트 추출 시작")
            logger.info(f"   추출기: {type(self.extractor).__name__}")
            logger.info(f"   OCR 사용: {isinstance(self.extractor, OCRExtractor)}")
            logger.info(f"   PDF 경로: {pdf_path}")
            logger.info("="*50)

            # 템플릿 기반 페이지 범위 최적화 (템플릿이 있고 페이지 정보가 있으면)
            # 원래 값 보존을 위해 로컬 변수 사용
            effective_start_page = self.start_page
            effective_end_page = self.end_page
            
            if not effective_start_page and not effective_end_page:  # 사용자가 명시적으로 지정하지 않은 경우만
                template_page_range = self._calculate_required_page_range_from_template()
                if template_page_range:
                    template_start, template_end = template_page_range
                    effective_start_page = template_start
                    effective_end_page = template_end
                    logger.info(f"   📋 템플릿 기반 페이지 범위 적용: {effective_start_page}~{effective_end_page or '끝'}")

            # auto 모드: 먼저 pdfplumber로 샘플 검사 후 필요 시 OCR로 전환
            if self.extraction_mode == "auto":
                sample_first = effective_start_page or 1
                sample_last = sample_first + self.auto_sample_pages - 1
                if effective_end_page:
                    sample_last = min(sample_last, effective_end_page)

                logger.info(
                    f"[Pipeline] auto 모드: pdfplumber 샘플 추출로 텍스트 레이어 검사 "
                    f"(페이지 {sample_first}-{sample_last})"
                )

                sample_data = self._pdf_extractor.extract(
                    pdf_path,
                    first_page=sample_first,
                    last_page=sample_last
                )

                if self._should_switch_to_ocr(sample_data):
                    logger.info("[AUTO 모드] 텍스트 레이어 부족/깨짐 감지 → OCR로 자동 전환")
                    self.extractor = self._create_ocr_extractor()
                else:
                    logger.info("[AUTO 모드] 텍스트 레이어 양호 → pdfplumber 유지")
                    self.extractor = self._pdf_extractor
            
            if isinstance(self.extractor, OCRExtractor):
                # OCR 사용 시: PDF를 이미지로 변환 후 추출
                logger.info("   OCR 모드: PDF를 이미지로 변환 중...")
                from pdf2image import convert_from_path
                try:
                    # 페이지 범위 설정
                    convert_kwargs = {'dpi': self.extractor.dpi}

                    # Poppler 경로 (자동 감지 또는 환경 변수)
                    if settings.POPPLER_PATH:
                        convert_kwargs['poppler_path'] = settings.POPPLER_PATH
                        logger.debug(f"   Poppler 경로: {settings.POPPLER_PATH}")
                    else:
                        logger.warning("   Poppler 경로 없음 - 자동 감지 시도")

                    first_page = effective_start_page or 1
                    convert_kwargs['first_page'] = first_page
                    if effective_end_page:
                        convert_kwargs['last_page'] = effective_end_page

                    logger.info(f"   페이지 범위: {first_page} ~ {effective_end_page or '끝'}")
                    page_images = convert_from_path(pdf_path, **convert_kwargs)
                    logger.info(f"   이미지 변환 완료: {len(page_images)}개 페이지")
                    
                    # OCR 진행률 콜백 설정
                    if self.progress_callback and hasattr(self.extractor, 'set_progress_callback'):
                        self.extractor.set_progress_callback(self.progress_callback)
                    
                    ocr_data = self.extractor.extract(page_images)

                    # 페이지 번호 조정 (배치 처리 시)
                    if effective_start_page and effective_start_page > 1:
                        page_offset = effective_start_page - 1
                        for page_data in ocr_data:
                            page_data['page_num'] += page_offset
                        logger.info(f"   페이지 번호 조정: +{page_offset}")
                except Exception as e:
                    logger.error(f"   PDF→이미지 변환 실패: {e}")
                    raise
            else:
                # PdfplumberExtractor 사용 시: PDF 경로 직접 전달
                logger.info("   pdfplumber 모드: 텍스트 추출 중...")
                try:
                    first_page = effective_start_page or 1
                    ocr_data = self.extractor.extract(
                        pdf_path,
                        first_page=first_page,
                        last_page=effective_end_page
                    )
                    logger.info(f"   pdfplumber 추출 완료: {len(ocr_data)}개 페이지")
                except Exception as e:
                    logger.error(f"   pdfplumber 추출 실패: {e}")
                    logger.exception(e)
                    raise
            
            if not ocr_data:
                raise ExtractionError(
                    "텍스트 추출 실패: OCR 데이터가 비어있습니다.",
                    details={"pdf_path": str(pdf_path), "extraction_mode": extraction_mode_used}
                )
            
            logger.info(f"   추출 완료: {len(ocr_data)}개 페이지")

            # 추출 모드 기록
            extraction_mode_used = 'ocr' if isinstance(self.extractor, OCRExtractor) else 'pdfplumber'

            # 2. 하이브리드 라우터를 통한 파서 선택
            logger.info("2. 파서 선택 중...")
            # 템플릿 재로드 (새로 생성된 템플릿 감지)
            logger.info("   템플릿 재로드 중...")
            self.hybrid_router.template_manager.reload_templates()
            logger.info(f"   로드된 템플릿: {len(self.hybrid_router.template_manager.templates)}개")
            try:
                parser, strategy, metadata = self.hybrid_router.select_parser(
                    subject=self.subject,
                    ocr_data=ocr_data,
                    config_path=self.config_path,
                    book_id=self.book_id,
                    pdf_path=pdf_path
                )
                self.parser = parser
                logger.info(f"   선택된 전략: {strategy}")
                if metadata.get('template_name'):
                    logger.info(f"   사용된 템플릿: {metadata['template_name']} (신뢰도: {metadata.get('confidence', 0):.2f})")
                logger.info(f"   처리 시간: {metadata.get('processing_time', 0):.2f}초")
            except Exception as e:
                logger.warning(f"   하이브리드 라우터 실패, 기본 파서 사용: {e}")
                # 폴백: 기본 파서 사용
                self.parser = self._get_parser(self.subject, self.config_path)

            # 3. 파싱
            logger.info("3. 파싱 중...")
            logger.info(f"   파서 타입: {type(self.parser).__name__}")
            try:
                result = self.parser.parse(ocr_data)
                lectures = result.get('lectures', [])
                problems = result.get('problems', [])
                
                # 메타데이터에 파싱 전략 추가
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['parsing_strategy'] = strategy
                result['metadata']['extraction_mode'] = extraction_mode_used
                result['metadata']['requested_extraction_mode'] = self.extraction_mode
                result['metadata'].update(metadata)
                
                logger.info(f"   파싱 완료: {len(lectures)}개 강의, {len(problems)}개 문제")
            except ParsingError:
                raise  # 파싱 관련 예외는 그대로 전파
            except Exception as e:
                logger.error(f"   파싱 실패: {e}")
                logger.exception(e)
                raise ParsingError(
                    f"파싱 중 오류 발생: {e}",
                    details={"subject": self.subject, "strategy": strategy},
                    original_error=e
                ) from e

            # 4. 강의 콘텐츠 추출
            logger.info("4. 강의 콘텐츠 추출 중...")
            try:
                # parser를 직접 전달 (processing 모듈의 파서 사용)
                lecture_contents = self.lecture_extractor.extract(ocr_data, lectures, self.parser)
                logger.info(f"   강의 콘텐츠 추출 완료: {len(lecture_contents)}개")
            except ParsingError:
                raise  # 파싱 관련 예외는 그대로 전파
            except Exception as e:
                logger.error(f"   강의 콘텐츠 추출 실패: {e}")
                logger.exception(e)
                raise ParsingError(
                    f"강의 콘텐츠 추출 중 오류 발생: {e}",
                    details={"lecture_count": len(lectures)},
                    original_error=e
                ) from e

            # 5. 개념/본문/문제 이미지 크롭 및 저장 (옵션)
            # - 기존: OCR 모드에서만 저장
            # - 개선: pdfplumber 모드에서도 필요한 페이지를 렌더링하여 bbox 기반 크롭 가능
            if self.save_images:
                # 이미지 캐시 생성 (페이지별 재사용으로 성능 최적화)
                image_cache = ImageCache(render_page_fn=self._render_page_from_pdf)
                
                # ImageSaver 인스턴스 생성 (캐시 사용)
                image_saver = ImageSaver(
                    pdf_path=pdf_path,
                    subject=self.subject,
                    book_id=self.book_id,
                    render_page_fn=self._render_page_from_pdf,
                    image_cache=image_cache
                )
                
                # 5-1. 개념 이미지 저장
                if lecture_contents:
                    logger.info("5. 개념 이미지 크롭 및 저장 중...")
                    try:
                        concept_count = image_saver.save_concept_images(lecture_contents, ocr_data)
                        logger.info(f"   개념 이미지 저장 완료: {concept_count}개")
                    except Exception as e:
                        logger.warning(f"   개념 이미지 저장 실패 (계속 진행): {e}")
                        logger.exception(e)

                # 5-2. 본문 이미지 저장
                if lecture_contents:
                    logger.info("6. 본문 이미지 크롭 및 저장 중...")
                    try:
                        content_count = image_saver.save_content_images(lecture_contents, ocr_data)
                        logger.info(f"   본문 이미지 저장 완료: {content_count}개")
                    except Exception as e:
                        logger.warning(f"   본문 이미지 저장 실패 (계속 진행): {e}")
                        logger.exception(e)

                # 5-3. 문제 이미지 저장
                if problems:
                    logger.info("7. 문제 이미지 크롭 및 저장 중...")
                    try:
                        problem_count = image_saver.save_problem_images(problems, ocr_data)
                        logger.info(f"   문제 이미지 저장 완료: {problem_count}개")
                    except Exception as e:
                        logger.warning(f"   문제 이미지 저장 실패 (계속 진행): {e}")
                        logger.exception(e)
                
                # 이미지 캐시 통계 로깅
                cache_stats = image_cache.get_stats()
                logger.info(
                    f"[ImageCache] 캐시 통계: "
                    f"크기={cache_stats['cache_size']}, "
                    f"히트={cache_stats['cache_hits']}, "
                    f"미스={cache_stats['cache_misses']}, "
                    f"히트율={cache_stats['hit_rate']:.2%}"
                )

            # 6. 결과 저장 (선택적)
            if self.result_saver:
                logger.info("8. 기존 데이터 삭제 중...")
                self.result_saver.clear()
                logger.info("   기존 데이터 삭제 완료")

                logger.info("9. 결과 저장 중...")
                # lecture_contents에 이미 섹션별 content가 매칭되어 있음
                self.result_saver.save(lectures, lecture_contents, problems)
                logger.info("   저장 완료")

            # 결과 반환
            result['lecture_contents'] = lecture_contents
            return result
            
        except ParsingError:
            raise  # 파싱 관련 예외는 그대로 전파
        except Exception as e:
            logger.error(f"UnifiedPipeline 실행 중 예상치 못한 오류 발생: {e}")
            logger.exception(e)
            raise ParsingError(
                f"파이프라인 실행 중 오류 발생: {e}",
                details={"pdf_path": str(pdf_path), "subject": self.subject},
                original_error=e
            ) from e
    
    def _load_config(self) -> JSONDict:
        """config.json 로드"""
        if not self.config_path or not self.config_path.exists():
            return {}
        
        import json
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError as e:
            logger.warning(f"config.json 파일을 찾을 수 없음: {e}")
            return {}
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"config.json 파싱 실패: {e}",
                details={"config_path": str(self.config_path)},
                original_error=e
            )
        except Exception as e:
            raise ConfigurationError(
                f"config.json 로드 실패: {e}",
                details={"config_path": str(self.config_path)},
                original_error=e
            ) from e
    
    def _render_page_from_pdf(self, pdf_path: Path, page_num: int) -> Optional[Image.Image]:
        """PDF에서 특정 페이지만 렌더링하여 PIL.Image로 반환 (1-based page_num).
        
        공통 메서드: 문제/개념/본문 이미지 저장에서 재사용
        
        Args:
            pdf_path: PDF 파일 경로
            page_num: 페이지 번호 (1-based)
            
        Returns:
            PIL.Image 또는 None (실패 시)
        """
        if not page_num or int(page_num) < 1:
            logger.warning(f"   유효하지 않은 페이지 번호로 렌더링 건너뜀: {page_num}")
            return None
        
        from pdf2image import convert_from_path

        convert_kwargs: JSONDict = {
            "dpi": getattr(self.extractor, "dpi", 300),
            "first_page": int(page_num),
            "last_page": int(page_num),
        }
        
        # Windows 환경에서 poppler_path가 필요할 수 있음
        if settings.POPPLER_PATH:
            convert_kwargs["poppler_path"] = settings.POPPLER_PATH
        
        try:
            page_images = convert_from_path(pdf_path, **convert_kwargs)
            return page_images[0] if page_images else None
        except Exception as e:
            logger.error(f"   페이지 {page_num} 렌더링 실패: {e}")
            return None

    # 이미지 저장 로직은 ImageSaver 클래스로 이동됨
    # 기존 메서드들은 제거되었으며, process() 메서드에서 ImageSaver를 사용합니다.
