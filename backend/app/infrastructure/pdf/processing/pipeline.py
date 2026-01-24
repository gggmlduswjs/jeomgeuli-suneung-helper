"""
통합 PDF 처리 파이프라인
extraction + parsing을 단일 플로우로 처리
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.processing.extractors import PdfplumberExtractor, OCRExtractor, PyMuPDFExtractor
from app.processing.parsers.literature import LiteratureParser
from app.processing.lecture_contents_extractor import LectureContentsExtractor
from app.processing.result_saver import ResultSaver
from app.core.config import settings

logger = logging.getLogger(__name__)


class UnifiedPipeline:
    """
    통합 PDF 처리 파이프라인

    플로우:
    1. 추출 (pdfplumber 또는 OCR)
    2. 파싱 (과목별)
    3. 후처리 (선택적 ML)
    """

    def __init__(
        self,
        subject: str,
        use_ocr: bool = False,
        use_ml_postprocess: bool = False,
        config_path: Optional[Path] = None,
        save_results: bool = True,
        **extractor_kwargs
    ):
        """
        Args:
            subject: 과목명 ('literature', 'math1', 'english')
            use_ocr: OCR 사용 여부 (False면 pdfplumber 사용)
            use_ml_postprocess: ML 후처리 사용 여부
            config_path: config.json 경로 (파서용)
            save_results: 결과를 JSON 파일로 저장할지 여부
            **extractor_kwargs: 추출기 추가 옵션
        """
        self.subject = subject
        self.use_ml = use_ml_postprocess
        self.config_path = config_path
        self.save_results = save_results

        # 1. 추출기 선택
        if use_ocr:
            self.extractor = OCRExtractor(**extractor_kwargs)
        else:
            # pdfplumber 사용 (PyMuPDF 한글 추출 문제로 인해 변경)
            self.extractor = PdfplumberExtractor(**extractor_kwargs)

        # 2. 파서 선택
        self.parser = self._get_parser(subject, config_path)
        
        # 3. 강의 콘텐츠 추출기
        config = self._load_config() if config_path else {}
        self.lecture_extractor = LectureContentsExtractor(subject, config)
        
        # textbook_pipeline 인스턴스 저장 (나중에 메서드 호출용)
        self._textbook_pipeline_ref = None
        
        # 4. 결과 저장기
        if save_results:
            data_dir = settings.API_DIR / "data" / subject
            self.result_saver = ResultSaver(subject, data_dir)
        else:
            self.result_saver = None

        logger.info(f"UnifiedPipeline 초기화 완료: {subject}, OCR={use_ocr}, ML={use_ml_postprocess}, Save={save_results}")

    def _get_parser(self, subject: str, config_path: Optional[Path] = None):
        """과목별 파서 반환"""
        from app.processing.parsers.literature import LiteratureParser
        from app.processing.parsers.math1 import Math1Parser
        from app.processing.parsers.english import EnglishParser

        parsers = {
            'literature': LiteratureParser,
            'math1': Math1Parser,
            'english': EnglishParser
        }

        parser_cls = parsers.get(subject)
        if not parser_cls:
            raise ValueError(f"지원하지 않는 과목: {subject}")

        # config_path가 있으면 전달
        if config_path:
            return parser_cls(config_path=config_path)
        else:
            return parser_cls()

    def process(self, pdf_path: Path) -> Dict[str, Any]:
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
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        if not pdf_path.is_file():
            raise ValueError(f"PDF 경로가 파일이 아닙니다: {pdf_path}")

        try:
            # 1. 텍스트 추출
            logger.info("1. 텍스트 추출 중...")
            logger.info(f"   추출기 타입: {type(self.extractor).__name__}")
            logger.info(f"   PDF 경로: {pdf_path}")
            
            if isinstance(self.extractor, OCRExtractor):
                # OCR 사용 시: PDF를 이미지로 변환 후 추출
                logger.info("   OCR 모드: PDF를 이미지로 변환 중...")
                from pdf2image import convert_from_path
                try:
                    page_images = convert_from_path(pdf_path, dpi=self.extractor.dpi)
                    if self.extractor.max_pages:
                        page_images = page_images[:self.extractor.max_pages]
                    logger.info(f"   이미지 변환 완료: {len(page_images)}개 페이지")
                    ocr_data = self.extractor.extract(page_images)
                except Exception as e:
                    logger.error(f"   PDF→이미지 변환 실패: {e}")
                    raise
            else:
                # PdfplumberExtractor 사용 시: PDF 경로 직접 전달
                logger.info("   pdfplumber 모드: 텍스트 추출 중...")
                try:
                    ocr_data = self.extractor.extract(pdf_path)
                except Exception as e:
                    logger.error(f"   pdfplumber 추출 실패: {e}")
                    logger.exception(e)
                    raise
            
            if not ocr_data:
                raise ValueError("텍스트 추출 실패: OCR 데이터가 비어있습니다.")
            
            logger.info(f"   추출 완료: {len(ocr_data)}개 페이지")

            # 2. 파싱
            logger.info("2. 파싱 중...")
            logger.info(f"   파서 타입: {type(self.parser).__name__}")
            try:
                result = self.parser.parse(ocr_data)
                lectures = result.get('lectures', [])
                problems = result.get('problems', [])
                logger.info(f"   파싱 완료: {len(lectures)}개 강의, {len(problems)}개 문제")
            except Exception as e:
                logger.error(f"   파싱 실패: {e}")
                logger.exception(e)
                raise

            # 3. 강의 콘텐츠 추출
            logger.info("3. 강의 콘텐츠 추출 중...")
            try:
                # parser를 직접 전달 (processing 모듈의 파서 사용)
                lecture_contents = self.lecture_extractor.extract(ocr_data, lectures, self.parser)
                logger.info(f"   강의 콘텐츠 추출 완료: {len(lecture_contents)}개")
            except Exception as e:
                logger.error(f"   강의 콘텐츠 추출 실패: {e}")
                logger.exception(e)
                raise

            # 4. ML 후처리 (선택적)
            if self.use_ml:
                logger.info("4. ML 후처리 중...")
                result = self._apply_ml_postprocessing(result)
                logger.info("   후처리 완료")

            # 5. 결과 저장 (선택적)
            if self.result_saver:
                logger.info("5. 결과 저장 중...")
                # lecture_contents에 이미 섹션별 content가 매칭되어 있음
                self.result_saver.save(lectures, lecture_contents, problems)
                logger.info("   저장 완료")

            # 결과 반환
            result['lecture_contents'] = lecture_contents
            return result
            
        except Exception as e:
            logger.error(f"UnifiedPipeline 실행 중 오류 발생: {e}")
            logger.exception(e)
            raise
    
    def _load_config(self) -> Dict[str, Any]:
        """config.json 로드"""
        if not self.config_path or not self.config_path.exists():
            return {}
        
        import json
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"config.json 로드 실패: {e}")
            return {}

    def _apply_ml_postprocessing(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        ML 후처리 적용

        Args:
            result: 파싱 결과

        Returns:
            후처리된 결과
        """
        from app.processing.postprocessors.classifier import BlockClassifier
        from app.processing.postprocessors.deduplicator import Deduplicator

        # 1. 블록 분류
        classifier = BlockClassifier()
        if classifier.available:
            lectures = result.get('lectures', [])
            problems = result.get('problems', [])

            if lectures:
                result['lectures'] = classifier.classify(lectures)
            if problems:
                result['problems'] = classifier.classify(problems)

        # 2. 중복 제거
        deduplicator = Deduplicator()
        if deduplicator.available:
            lectures = result.get('lectures', [])
            problems = result.get('problems', [])

            if lectures:
                result['lectures'] = deduplicator.deduplicate(lectures)
            if problems:
                result['problems'] = deduplicator.deduplicate(problems)

        return result
