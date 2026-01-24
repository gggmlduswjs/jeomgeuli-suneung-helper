"""
LLM 기반 PDF 구조 분석기
PDF 텍스트 샘플을 분석하여 파싱 규칙을 자동으로 생성
"""
import logging
from typing import Dict, Any, List, Optional
import json

# BaseModel은 항상 import (pydantic은 필수)
try:
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError("pydantic이 설치되지 않았습니다. pip install pydantic")

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.output_parsers import PydanticOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("[StructureAnalyzer] langchain not available. Install with: pip install langchain openai")


logger = logging.getLogger(__name__)


class PDFStructure(BaseModel):
    """PDF 구조 분석 결과 스키마"""
    subject: str = Field(description="과목명 (literature, math1, english)")
    lecture_title_patterns: List[str] = Field(description="강의 제목 정규식 패턴 리스트")
    toc_lecture_patterns: List[str] = Field(default_factory=list, description="목차 강의 패턴 리스트")
    concept_title_patterns: List[str] = Field(default_factory=list, description="개념 제목 패턴 리스트")
    content_header_patterns: List[str] = Field(default_factory=list, description="본문 헤더 패턴 리스트")
    section_title_patterns: List[str] = Field(default_factory=list, description="섹션 제목 패턴 리스트")
    problem_number_pattern: str = Field(description="문제 번호 정규식 패턴")
    toc_end_page: int = Field(default=7, description="목차 종료 페이지")
    start_content_page: int = Field(default=8, description="본문 시작 페이지")
    paragraph_y_threshold: int = Field(default=25, description="문단 Y 좌표 임계값")
    confidence: float = Field(default=0.0, description="분석 신뢰도 (0.0-1.0)")


class StructureAnalyzer:
    """LLM 기반 PDF 구조 분석기
    
    PDF 텍스트 샘플(첫 3-5페이지)을 분석하여:
    - 강의 제목 패턴
    - 문제 번호 패턴
    - 섹션 구조
    등을 자동으로 추출하고 파싱 규칙을 생성
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.3
    ):
        """
        Args:
            model_name: OpenAI 모델 이름 (기본값: gpt-4o-mini, 빠르고 저렴)
            api_key: OpenAI API 키 (None이면 환경변수 사용)
            temperature: 생성 온도 (낮을수록 일관성 높음)
        """
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError(
                "langchain not available. "
                "Install with: pip install langchain openai"
            )
        
        self.model_name = model_name
        self.temperature = temperature
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=api_key
        )
        
        # Output Parser
        self.parser = PydanticOutputParser(pydantic_object=PDFStructure)
        
        # 프롬프트 템플릿
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """당신은 EBS 수능 교재 PDF 구조 분석 전문가입니다.
주어진 PDF 텍스트 샘플을 분석하여 파싱 규칙을 생성해야 합니다.

분석 항목:
1. 강의 제목 패턴: "1강 시의 표현과 형식", "Unit 1", "1단원" 등
2. 목차 강의 패턴: 목차 페이지에서 사용되는 강의 제목 형식
3. 개념 제목 패턴: "1. 시적 표현", "2. 시의 형식" 등
4. 본문 헤더 패턴: "작품으로 이해하기", "Passage 1" 등
5. 섹션 제목 패턴: "(1)", "1.", "①" 등
6. 문제 번호 패턴: "01", "02", "1.", "2." 등

출력 형식:
- 정규식 패턴을 JSON 형식으로 제공
- 각 패턴은 실제 텍스트에서 확인된 형식을 기반으로 작성
- 패턴은 가능한 한 구체적이면서도 일반화되어야 함

{format_instructions}"""),
            ("human", """다음은 PDF의 첫 3-5페이지에서 추출한 텍스트 샘플입니다:

{text_sample}

이 텍스트를 분석하여 파싱 규칙을 생성해주세요.
과목: {subject}
""")
        ])
    
    def analyze(
        self,
        text_sample: str,
        subject: str = "literature"
    ) -> PDFStructure:
        """PDF 텍스트 샘플을 분석하여 구조 추출
        
        Args:
            text_sample: PDF에서 추출한 텍스트 (첫 3-5페이지 권장)
            subject: 과목명 (literature, math1, english)
            
        Returns:
            PDFStructure 인스턴스 (파싱 규칙 포함)
        """
        if not text_sample or len(text_sample) < 100:
            raise ValueError("텍스트 샘플이 너무 짧습니다 (최소 100자 필요)")
        
        logger.info(f"[StructureAnalyzer] PDF 구조 분석 시작 (과목: {subject}, 텍스트 길이: {len(text_sample)}자)")
        
        try:
            # 프롬프트 생성
            prompt = self.prompt_template.format_messages(
                text_sample=text_sample[:5000],  # 최대 5000자 (토큰 절약)
                subject=subject,
                format_instructions=self.parser.get_format_instructions()
            )
            
            # LLM 호출
            response = self.llm(prompt)
            
            # 결과 파싱
            structure = self.parser.parse(response.content)
            
            # 신뢰도 계산 (기본값, 실제로는 패턴 매칭률 기반으로 계산 가능)
            structure.confidence = 0.75  # AI 분석 기본 신뢰도
            
            logger.info(
                f"[StructureAnalyzer] 분석 완료: "
                f"강의 패턴 {len(structure.lecture_title_patterns)}개, "
                f"문제 패턴: {structure.problem_number_pattern}"
            )
            
            return structure
            
        except Exception as e:
            logger.error(f"[StructureAnalyzer] 분석 실패: {e}", exc_info=True)
            raise
    
    def analyze_from_ocr_data(
        self,
        ocr_data: List[Dict[str, Any]],
        subject: str = "literature",
        max_pages: int = 5
    ) -> PDFStructure:
        """OCR 데이터에서 텍스트 샘플 추출 후 분석
        
        Args:
            ocr_data: 페이지별 OCR 결과 리스트
            subject: 과목명
            max_pages: 분석할 최대 페이지 수
            
        Returns:
            PDFStructure 인스턴스
        """
        # 첫 N페이지의 텍스트 추출
        sample_pages = ocr_data[:max_pages]
        text_lines = []
        
        for page_data in sample_pages:
            texts = page_data.get('text', [])
            if texts:
                # 텍스트를 줄 단위로 결합
                page_text = '\n'.join(str(t) for t in texts[:100])  # 페이지당 최대 100개
                text_lines.append(f"=== Page {page_data.get('page_num', 0)} ===\n{page_text}")
        
        text_sample = '\n\n'.join(text_lines)
        
        if not text_sample:
            raise ValueError("OCR 데이터에서 텍스트를 추출할 수 없습니다")
        
        return self.analyze(text_sample, subject)
