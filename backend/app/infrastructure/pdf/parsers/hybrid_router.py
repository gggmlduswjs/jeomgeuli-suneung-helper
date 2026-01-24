"""
하이브리드 파서 라우터
템플릿 매칭과 AI 파싱을 신뢰도 기반으로 자동 선택
"""
import logging
import time
from typing import Optional, Tuple, List, Dict
from pathlib import Path

from .template_manager import TemplateManager
from .template import ParsingTemplate
from .unified_parser import UnifiedTemplateParser
from .base import BaseParser
from app.core.config import settings
from app.infrastructure.pdf.types import OCRPageData, JSONDict

logger = logging.getLogger(__name__)


class HybridRouter:
    """하이브리드 파서 라우터
    
    파싱 전략:
    1. 템플릿 매칭 시도 (빠른 경로, 2-5초)
    2. 매칭 실패 또는 신뢰도 낮으면 AI 파싱 (정확한 경로, 60-120초)
    3. AI 파싱 실패 시 기존 config.json 기반 파서로 폴백
    """
    
    def __init__(
        self,
        template_threshold: float = 0.85,
        enable_ai_parsing: bool = True,
        enable_cache: bool = True
    ):
        """
        Args:
            template_threshold: 템플릿 매칭 최소 신뢰도 (0.0-1.0)
            enable_ai_parsing: AI 파싱 활성화 여부
            enable_cache: 캐싱 활성화 여부
        """
        self.template_manager = TemplateManager(enable_cache=enable_cache)
        self.template_threshold = template_threshold
        self.enable_ai_parsing = enable_ai_parsing
        self.enable_cache = enable_cache
        
        # AI 파싱 결과 캐시 (book_id -> parser)
        self._ai_parser_cache: Dict[str, BaseParser] = {}
        
        # 성능 메트릭
        self.metrics = {
            'template_matches': 0,
            'ai_parsing_used': 0,
            'fallback_used': 0,
            'total_requests': 0,
            'template_avg_time': 0.0,
            'ai_avg_time': 0.0,
            'cache_hits': 0
        }
    
    def select_parser(
        self,
        subject: str,
        ocr_data: List[OCRPageData],
        config_path: Optional[Path] = None,
        book_id: Optional[str] = None,
        pdf_path: Optional[Path] = None
    ) -> Tuple[BaseParser, str, JSONDict]:
        """적합한 파서 선택 및 반환

        Args:
            subject: 과목명 ('literature', 'math1', 'english')
            ocr_data: 페이지별 OCR 결과 리스트
            config_path: config.json 경로 (폴백용)
            book_id: 책 ID (섹션 이미지 크롭용)
            pdf_path: PDF 파일 경로 (섹션 이미지 크롭용)

        Returns:
            (파서 인스턴스, 사용된 전략, 메타데이터) 튜플
            전략: 'template', 'ai', 'fallback'
        """
        self.metrics['total_requests'] += 1
        start_time = time.time()
        
        try:
            # 1단계: 템플릿 매칭 시도
            logger.info(f"[HybridRouter] 템플릿 매칭 시도 (과목: {subject}, book_id: {book_id})")
            logger.info(f"[HybridRouter] 로드된 템플릿 수: {len(self.template_manager.templates)}")
            logger.info(f"[HybridRouter] 템플릿 디렉토리: {self.template_manager.template_dir}")

            # 디버깅: 템플릿이 없으면 다시 로드 시도
            if len(self.template_manager.templates) == 0:
                logger.warning("[HybridRouter] 템플릿이 로드되지 않음 - 재로드 시도")
                self.template_manager._load_templates()
                logger.info(f"[HybridRouter] 재로드 후 템플릿 수: {len(self.template_manager.templates)}")

            if self.template_manager.templates:
                for key, template in self.template_manager.templates.items():
                    logger.info(f"  - {key}: {template.name} (subject: {template.subject})")
            else:
                logger.error("[HybridRouter] ⚠️ 템플릿이 전혀 로드되지 않음! 템플릿 파일 위치 확인 필요")
            
            template_match = self._try_template_matching(subject, ocr_data, book_id)
            
            if template_match:
                template, confidence = template_match
                parser = self._create_parser_with_template(subject, template, config_path, pdf_path, book_id)
                elapsed = time.time() - start_time
                
                self.metrics['template_matches'] += 1
                self._update_avg_time('template_avg_time', elapsed)
                
                logger.info(
                    f"[HybridRouter] 템플릿 매칭 성공: {template.name} "
                    f"(신뢰도: {confidence:.2f}, 시간: {elapsed:.2f}초)"
                )
                
                return (
                    parser,
                    'template',
                    {
                        'template_name': template.name,
                        'confidence': confidence,
                        'processing_time': elapsed,
                        'strategy': 'template'
                    }
                )
            
            # 템플릿 매칭 실패 시에도 해당 과목의 템플릿이 있으면 강제로 사용 (영역 정보 활용)
            if not template_match:
                logger.warning(f"[HybridRouter] 템플릿 매칭 실패 - 대체 방법 시도")
                # 해당 과목의 템플릿이 있으면 가장 최신 템플릿 사용 (영역 정보 활용을 위해)
                subject_templates = self.template_manager.get_templates_by_subject(subject)
                if subject_templates:
                    # 가장 최신 템플릿 선택 (updated_at 기준, 없으면 created_at)
                    template = max(
                        subject_templates,
                        key=lambda t: (
                            t.updated_at if t.updated_at else t.created_at or "",
                            t.confidence
                        )
                    )
                    logger.info(
                        f"[HybridRouter] 과목별 템플릿 {len(subject_templates)}개 발견 - "
                        f"최신 템플릿 강제 사용: {template.name} (영역 정보 활용)"
                    )
                    parser = self._create_parser_with_template(subject, template, config_path, pdf_path, book_id)
                    elapsed = time.time() - start_time
                    
                    self.metrics['template_matches'] += 1
                    self._update_avg_time('template_avg_time', elapsed)
                    
                    return (
                        parser,
                        'template',
                        {
                            'template_name': template.name,
                            'confidence': 0.5,  # 강제 사용이므로 낮은 신뢰도
                            'processing_time': elapsed,
                            'strategy': 'template_forced'
                        }
                    )
                else:
                    logger.warning(f"[HybridRouter] 템플릿 매칭 실패 - 해당 과목 템플릿 없음, 폴백 파서 사용")
            
            # 2단계: AI 파싱 시도 (활성화된 경우)
            if self.enable_ai_parsing:
                try:
                    # 캐시 확인
                    ai_parser = None
                    cache_key = None
                    is_cached = False
                    
                    if self.enable_cache and book_id:
                        cache_key = f"{subject}_{book_id}"
                        if cache_key in self._ai_parser_cache:
                            ai_parser = self._ai_parser_cache[cache_key]
                            is_cached = True
                            self.metrics['cache_hits'] += 1
                            logger.info(f"[HybridRouter] AI 파서 캐시 히트: {book_id}")
                    
                    if not ai_parser:
                        ai_parser = self._try_ai_parsing(subject, ocr_data, config_path, book_id, pdf_path)
                        # 캐시 저장
                        if ai_parser and self.enable_cache and book_id:
                            if cache_key is None:
                                cache_key = f"{subject}_{book_id}"
                            self._ai_parser_cache[cache_key] = ai_parser
                    
                    if ai_parser:
                        elapsed = time.time() - start_time
                        
                        self.metrics['ai_parsing_used'] += 1
                        self._update_avg_time('ai_avg_time', elapsed)
                        
                        logger.info(
                            f"[HybridRouter] AI 파싱 사용 (시간: {elapsed:.2f}초, 캐시: {is_cached})"
                        )
                        
                        return (
                            ai_parser,
                            'ai',
                            {
                                'processing_time': elapsed,
                                'strategy': 'ai',
                                'cached': is_cached
                            }
                        )
                except Exception as e:
                    logger.warning(f"[HybridRouter] AI 파싱 실패, 폴백으로 전환: {e}")
            
            # 3단계: 폴백 - 기존 config.json 기반 파서
            parser = self._create_fallback_parser(subject, config_path, pdf_path, book_id)
            elapsed = time.time() - start_time
            
            self.metrics['fallback_used'] += 1
            
            logger.info(
                f"[HybridRouter] 폴백 파서 사용 (config.json, 시간: {elapsed:.2f}초)"
            )
            
            return (
                parser,
                'fallback',
                {
                    'processing_time': elapsed,
                    'strategy': 'fallback'
                }
            )
            
        except Exception as e:
            logger.error(f"[HybridRouter] 파서 선택 중 오류: {e}", exc_info=True)
            # 최종 폴백
            parser = self._create_fallback_parser(subject, config_path, pdf_path, book_id)
            return parser, 'fallback', {'error': str(e), 'strategy': 'fallback'}
    
    def _try_template_matching(
        self,
        subject: str,
        ocr_data: List[OCRPageData],
        book_id: Optional[str] = None
    ) -> Optional[Tuple[ParsingTemplate, float]]:
        """템플릿 매칭 시도

        Returns:
            (템플릿, 신뢰도) 튜플 또는 None
        """
        if not ocr_data:
            return None

        # 첫 3-5페이지의 텍스트 추출
        sample_pages = ocr_data[:5]
        sample_texts = []

        for page_data in sample_pages:
            texts = page_data.get('text', [])
            if texts:
                # 영역 마킹 활용을 위해 텍스트 개수 증가 (50 → 200)
                page_text = ' '.join(str(t) for t in texts[:200])
                sample_texts.append(page_text)

        pdf_text = '\n'.join(sample_texts)

        if not pdf_text or len(pdf_text) < 100:
            return None

        # 템플릿 매칭 (OCR 데이터도 함께 전달하여 영역 유사도 계산)
        return self.template_manager.match_template(
            pdf_text=pdf_text,
            subject=subject,
            threshold=self.template_threshold,
            book_id=book_id,
            pdf_ocr_data=sample_pages  # ← OCR 데이터 전달 (영역 유사도 계산용)
        )
    
    def _create_parser_with_template(
        self,
        subject: str,
        template: ParsingTemplate,
        config_path: Optional[Path] = None,
        pdf_path: Optional[Path] = None,
        book_id: Optional[str] = None
    ) -> BaseParser:
        """템플릿을 사용하는 통합 파서 생성 (모든 과목 공통)"""
        # 통합 파서 사용 (모든 과목에서 동일한 프로세스)
        return UnifiedTemplateParser(
            subject=subject,
            config_path=config_path,
            template=template,
            enable_ai_parsing=self.enable_ai_parsing,
            pdf_path=pdf_path,
            book_id=book_id
        )
    
    def _try_ai_parsing(
        self,
        subject: str,
        ocr_data: List[OCRPageData],
        config_path: Optional[Path] = None,
        book_id: Optional[str] = None,
        pdf_path: Optional[Path] = None
    ) -> Optional[BaseParser]:
        """AI 파싱 시도 (통합 파서 사용)

        Args:
            subject: 과목명
            ocr_data: OCR 데이터
            config_path: config.json 경로 (폴백용)
            book_id: 책 ID (섹션 이미지 크롭용)
            pdf_path: PDF 파일 경로 (섹션 이미지 크롭용)

        Returns:
            UnifiedTemplateParser 인스턴스 (AI 파싱 활성화) 또는 None
        """
        try:
            # OpenAI API 키 확인
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                logger.warning("[HybridRouter] OpenAI API 키가 설정되지 않아 AI 파싱을 건너뜁니다")
                return None

            logger.info(f"[HybridRouter] AI 파싱 시도 (과목: {subject}, 통합 파서 사용)")
            # 통합 파서 사용 (AI 파싱 활성화)
            return UnifiedTemplateParser(
                subject=subject,
                config_path=config_path,
                template=None,  # AI 파싱은 템플릿 없이도 가능
                enable_ai_parsing=True,
                pdf_path=pdf_path,
                book_id=book_id
            )
            
        except Exception as e:
            logger.warning(f"[HybridRouter] AI 파싱 초기화 실패: {e}")
            return None
    
    def _create_fallback_parser(
        self,
        subject: str,
        config_path: Optional[Path] = None,
        pdf_path: Optional[Path] = None,
        book_id: Optional[str] = None
    ) -> BaseParser:
        """폴백 파서 생성 (config.json 기반, 통합 파서 사용)

        IMPROVED: config.json이 없어도 템플릿 파일의 region_hints를 사용
        """
        # 개선: config.json이 없을 때 템플릿 파일 사용 시도
        template_to_use = None

        # config.json이 없거나 존재하지 않으면 템플릿 파일에서 region_hints 가져오기
        if not config_path or not config_path.exists():
            logger.warning(
                f"[HybridRouter] config.json 없음 ({config_path}) - "
                f"템플릿 파일에서 region_hints 로드 시도"
            )
            # 과목별 템플릿 검색
            subject_templates = self.template_manager.get_templates_by_subject(subject)
            if subject_templates:
                # 가장 최신 템플릿 선택
                template_to_use = max(
                    subject_templates,
                    key=lambda t: (
                        t.updated_at if t.updated_at else t.created_at or "",
                        t.confidence
                    )
                )
                logger.info(
                    f"[HybridRouter] 폴백용 템플릿 발견: {template_to_use.name} "
                    f"(region_hints 활용)"
                )

        # 폴백도 통합 파서 사용 (템플릿 또는 config.json 사용)
        return UnifiedTemplateParser(
            subject=subject,
            config_path=config_path,
            template=template_to_use,  # 템플릿이 있으면 사용
            enable_ai_parsing=False,
            pdf_path=pdf_path,
            book_id=book_id
        )
    
    def _update_avg_time(self, metric_key: str, elapsed_time: float):
        """평균 시간 업데이트"""
        current_avg = self.metrics.get(metric_key, 0.0)
        count = self.metrics['template_matches'] if 'template' in metric_key else self.metrics['ai_parsing_used']
        
        if count > 0:
            # 이동 평균 계산
            self.metrics[metric_key] = (current_avg * (count - 1) + elapsed_time) / count
        else:
            self.metrics[metric_key] = elapsed_time
    
    def get_metrics(self) -> JSONDict:
        """성능 메트릭 반환"""
        total = self.metrics['total_requests']
        if total == 0:
            return self.metrics.copy()
        
        return {
            **self.metrics,
            'template_match_rate': self.metrics['template_matches'] / total,
            'ai_parsing_rate': self.metrics['ai_parsing_used'] / total,
            'fallback_rate': self.metrics['fallback_used'] / total
        }
    
    def clear_cache(self):
        """캐시 초기화"""
        self.template_manager.clear_cache()
        self._ai_parser_cache.clear()
        logger.info("[HybridRouter] 모든 캐시 초기화 완료")
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = {
            'template_matches': 0,
            'ai_parsing_used': 0,
            'fallback_used': 0,
            'total_requests': 0,
            'template_avg_time': 0.0,
            'ai_avg_time': 0.0,
            'cache_hits': 0
        }
