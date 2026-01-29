"""
파싱 규칙 생성기
LLM 분석 결과를 config.json 형식으로 변환하고 검증
"""
import logging
import json
from typing import TYPE_CHECKING, Optional
from pathlib import Path

from app.infrastructure.pdf.types import JSONDict

if TYPE_CHECKING:
    from app.infrastructure.ai.genai.structure_analyzer import PDFStructure

logger = logging.getLogger(__name__)


class RuleGenerator:
    """파싱 규칙 생성기
    
    LLM 분석 결과를 config.json 형식으로 변환하고:
    - 규칙 검증
    - 최적화
    - 템플릿 저장
    """
    
    def __init__(self):
        """RuleGenerator 초기화"""
        pass
    
    def structure_to_config(
        self,
        structure: "PDFStructure",
        validate: bool = True
    ) -> JSONDict:
        """PDFStructure를 config.json 형식으로 변환

        Args:
            structure: LLM 분석 결과
            validate: 규칙 검증 여부

        Returns:
            config.json 형식의 딕셔너리
        """
        config = {
            "subject": structure.subject,
            "lecture_title_patterns": structure.lecture_title_patterns,
            "toc_lecture_patterns": structure.toc_lecture_patterns or structure.lecture_title_patterns,
            "concept_title_patterns": structure.concept_title_patterns,
            "content_header_patterns": structure.content_header_patterns,
            "section_title_patterns": structure.section_title_patterns,
            "problem_number_pattern": structure.problem_number_pattern,
            "toc_end_page": structure.toc_end_page,
            "start_content_page": structure.start_content_page,
            "paragraph_y_threshold": structure.paragraph_y_threshold
        }
        
        if validate:
            self._validate_config(config)
        
        return config
    
    def _validate_config(self, config: JSONDict):
        """생성된 config 검증

        Args:
            config: 검증할 config 딕셔너리

        Raises:
            ValueError: 검증 실패 시
        """
        # 필수 필드 확인
        required_fields = [
            "subject",
            "lecture_title_patterns",
            "problem_number_pattern"
        ]
        
        for field in required_fields:
            if field not in config or not config[field]:
                raise ValueError(f"필수 필드 누락 또는 비어있음: {field}")
        
        # 패턴 형식 검증
        if not isinstance(config["lecture_title_patterns"], list):
            raise ValueError("lecture_title_patterns는 리스트여야 합니다")
        
        if len(config["lecture_title_patterns"]) == 0:
            raise ValueError("lecture_title_patterns가 비어있습니다")
        
        # 정규식 패턴 유효성 검증 (기본적인 검증)
        import re
        for pattern in config["lecture_title_patterns"]:
            try:
                re.compile(pattern)
            except re.error as e:
                logger.warning(f"잘못된 정규식 패턴: {pattern}, 오류: {e}")
        
        if config.get("problem_number_pattern"):
            try:
                re.compile(config["problem_number_pattern"])
            except re.error as e:
                logger.warning(f"잘못된 문제 번호 패턴: {config['problem_number_pattern']}, 오류: {e}")
    
    def optimize_config(self, config: JSONDict) -> JSONDict:
        """생성된 config 최적화

        - 중복 패턴 제거
        - 유사 패턴 통합
        - 불필요한 패턴 제거

        Args:
            config: 최적화할 config 딕셔너리

        Returns:
            최적화된 config 딕셔너리
        """
        optimized = config.copy()
        
        # 중복 패턴 제거
        if "lecture_title_patterns" in optimized:
            optimized["lecture_title_patterns"] = list(set(optimized["lecture_title_patterns"]))
        
        if "toc_lecture_patterns" in optimized:
            optimized["toc_lecture_patterns"] = list(set(optimized["toc_lecture_patterns"]))
        
        if "concept_title_patterns" in optimized:
            optimized["concept_title_patterns"] = list(set(optimized["concept_title_patterns"]))
        
        # 빈 리스트 제거
        for key in ["toc_lecture_patterns", "concept_title_patterns", 
                    "content_header_patterns", "section_title_patterns"]:
            if key in optimized and not optimized[key]:
                # 기본값으로 대체
                if key == "toc_lecture_patterns":
                    optimized[key] = optimized.get("lecture_title_patterns", [])
        
        return optimized
    
    def save_config(
        self,
        config: JSONDict,
        output_path: Path
    ) -> Path:
        """config를 JSON 파일로 저장

        Args:
            config: 저장할 config 딕셔너리
            output_path: 저장 경로

        Returns:
            저장된 파일 경로
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Config 저장 완료: {output_path}")
        return output_path
    
    def structure_to_template(
        self,
        structure: "PDFStructure",
        template_name: str,
        version: str = "",
        description: str = ""
    ) -> JSONDict:
        """PDFStructure를 템플릿 형식으로 변환

        Args:
            structure: LLM 분석 결과
            template_name: 템플릿 이름
            version: 버전
            description: 설명

        Returns:
            템플릿 딕셔너리 (ParsingTemplate.to_dict() 형식)
        """
        from app.infrastructure.pdf.parsers.template import ParsingTemplate
        
        # config로 변환
        config = self.structure_to_config(structure, validate=True)
        config = self.optimize_config(config)
        
        # 템플릿 생성
        template = ParsingTemplate(
            name=template_name,
            subject=structure.subject,
            version=version,
            description=description or f"AI 자동 생성 템플릿: {template_name}",
            patterns={
                "lecture_title_patterns": config.get("lecture_title_patterns", []),
                "toc_lecture_patterns": config.get("toc_lecture_patterns", []),
                "concept_title_patterns": config.get("concept_title_patterns", []),
                "content_header_patterns": config.get("content_header_patterns", []),
                "section_title_patterns": config.get("section_title_patterns", []),
                "problem_number_pattern": config.get("problem_number_pattern", "")
            },
            config={
                "toc_end_page": config.get("toc_end_page", 7),
                "start_content_page": config.get("start_content_page", 8),
                "paragraph_y_threshold": config.get("paragraph_y_threshold", 25)
            },
            confidence=structure.confidence
        )
        
        return template.to_dict()
