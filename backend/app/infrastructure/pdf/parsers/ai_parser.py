"""
AI 기반 파서
LLM을 사용하여 PDF 구조를 자동 분석하고 파싱
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseParser
from app.infrastructure.ai.genai.structure_analyzer import StructureAnalyzer
from .rule_generator import RuleGenerator
from .unified_parser import UnifiedTemplateParser

logger = logging.getLogger(__name__)


class AIParser(BaseParser):
    """AI 기반 파서
    
    LLM을 사용하여:
    1. PDF 구조 자동 분석
    2. 파싱 규칙 생성
    3. 생성된 규칙으로 파싱 실행
    """
    
    def __init__(
        self,
        subject: str,
        ocr_data: List[Dict[str, Any]],
        config_path: Optional[Path] = None,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini"
    ):
        """
        Args:
            subject: 과목명
            ocr_data: OCR 데이터 (구조 분석용)
            config_path: config.json 경로 (폴백용)
            api_key: OpenAI API 키
            model_name: 사용할 LLM 모델
        """
        self.subject = subject
        self.ocr_data = ocr_data
        self.config_path = config_path
        
        # LLM 구조 분석기
        try:
            self.structure_analyzer = StructureAnalyzer(
                model_name=model_name,
                api_key=api_key,
                temperature=0.3
            )
        except Exception as e:
            logger.error(f"StructureAnalyzer 초기화 실패: {e}")
            raise
        
        # 규칙 생성기
        self.rule_generator = RuleGenerator()
        
        # 파싱 규칙 (구조 분석 후 생성됨)
        self.config: Optional[Dict[str, Any]] = None
        self.parser: Optional[BaseParser] = None
        
        # 구조 분석 및 파서 초기화
        self._initialize_parser()
    
    def _initialize_parser(self):
        """구조 분석 및 파서 초기화"""
        try:
            logger.info(f"[AIParser] PDF 구조 분석 시작 (과목: {self.subject})")
            
            # 1. 구조 분석
            structure = self.structure_analyzer.analyze_from_ocr_data(
                ocr_data=self.ocr_data,
                subject=self.subject,
                max_pages=5
            )
            
            logger.info(
                f"[AIParser] 구조 분석 완료: "
                f"강의 패턴 {len(structure.lecture_title_patterns)}개, "
                f"신뢰도: {structure.confidence:.2f}"
            )
            
            # 2. 규칙 생성
            self.config = self.rule_generator.structure_to_config(structure, validate=True)
            self.config = self.rule_generator.optimize_config(self.config)
            
            logger.info(f"[AIParser] 파싱 규칙 생성 완료")
            
            # 3. 파서 생성 (템플릿 사용)
            from app.infrastructure.pdf.parsers.template import ParsingTemplate
            
            template = ParsingTemplate(
                name=f"ai_generated_{self.subject}",
                subject=self.subject,
                version="",
                description=f"AI 자동 생성 파싱 규칙 ({self.subject})",
                patterns={
                    "lecture_title_patterns": self.config.get("lecture_title_patterns", []),
                    "toc_lecture_patterns": self.config.get("toc_lecture_patterns", []),
                    "concept_title_patterns": self.config.get("concept_title_patterns", []),
                    "content_header_patterns": self.config.get("content_header_patterns", []),
                    "section_title_patterns": self.config.get("section_title_patterns", []),
                    "problem_number_pattern": self.config.get("problem_number_pattern", "")
                },
                config={
                    "toc_end_page": self.config.get("toc_end_page", 7),
                    "start_content_page": self.config.get("start_content_page", 8),
                    "paragraph_y_threshold": self.config.get("paragraph_y_threshold", 25)
                },
                confidence=structure.confidence
            )
            
            # 통합 파서 생성 (템플릿 사용)
            self.parser = UnifiedTemplateParser(
                subject=self.subject,
                config_path=self.config_path,
                template=template,
                enable_ai_parsing=False  # 이미 AI로 구조 분석했으므로 추가 AI 파싱 불필요
            )
            
            logger.info(f"[AIParser] 통합 파서 초기화 완료")
            
        except Exception as e:
            logger.error(f"[AIParser] 초기화 실패: {e}", exc_info=True)
            # 폴백: 통합 파서 사용 (템플릿 없이)
            self.parser = UnifiedTemplateParser(
                subject=self.subject,
                config_path=self.config_path,
                template=None,
                enable_ai_parsing=False
            )
            logger.warning(f"[AIParser] 폴백 통합 파서 사용")
    
    def parse(self, ocr_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """OCR 데이터 파싱
        
        Args:
            ocr_data: 페이지별 OCR 결과 리스트
            
        Returns:
            파싱 결과 딕셔너리
        """
        if not self.parser:
            raise RuntimeError("파서가 초기화되지 않았습니다")
        
        try:
            result = self.parser.parse(ocr_data)
            
            # 메타데이터에 AI 파싱 정보 추가
            if 'metadata' not in result:
                result['metadata'] = {}
            result['metadata']['parsing_method'] = 'ai'
            result['metadata']['ai_confidence'] = self.config.get('confidence', 0.0) if self.config else 0.0
            
            logger.info(f"[AIParser] 파싱 완료: {len(result.get('lectures', []))}개 강의")
            
            return result
            
        except Exception as e:
            logger.error(f"[AIParser] 파싱 실패: {e}", exc_info=True)
            raise
    
    def extract_sections(
        self,
        lecture_ocr_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """섹션 추출 (BaseParser 구현)"""
        if not self.parser:
            raise RuntimeError("파서가 초기화되지 않았습니다")
        return self.parser.extract_sections(lecture_ocr_data)
    
    def extract_content_paragraphs(
        self,
        lecture_ocr_data: List[Dict[str, Any]],
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """문단 추출 (BaseParser 구현)"""
        if not self.parser:
            raise RuntimeError("파서가 초기화되지 않았습니다")
        return self.parser.extract_content_paragraphs(lecture_ocr_data, sections)
