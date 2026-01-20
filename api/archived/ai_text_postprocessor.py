"""
AI Text Postprocessor: LLM 기반 텍스트 후처리

OCR 오류 수정, 텍스트 정리, 구조 정규화
"""
from typing import Dict, Any, Optional
import re

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AITextPostProcessor:
    """
    LLM 기반 텍스트 후처리기
    
    기능:
    - OCR 오류 자동 수정
    - 문장 구조 정리
    - 한글/영어 혼합 텍스트 정규화
    - 수능특강 교재 형식 유지
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        use_langchain: bool = True
    ):
        """
        Args:
            model: OpenAI 모델명 ('gpt-4', 'gpt-4o-mini', 'gpt-3.5-turbo' 등)
            temperature: 생성 온도 (0.0 = 일관성 최우선)
            use_langchain: LangChain 사용 여부
        """
        self.model = model
        self.temperature = temperature
        self.use_langchain = use_langchain and LANGCHAIN_AVAILABLE
        
        # 프롬프트 텍스트 (LangChain 사용 여부와 관계없이 필요)
        self.clean_prompt_text = """당신은 수능특강 교재 텍스트 정리 전문가입니다.

다음 작업을 수행해주세요:
1. OCR 오류 수정 (예: "0" → "O", "rn" → "m", "1" → "l")
2. 문장 구조 정리 (불필요한 줄바꿈, 공백 정규화)
3. 한글/영어 혼합 텍스트 정규화
4. 수능특강 교재 형식 유지 (문제 번호, 보기 기호 등)

중요:
- 원본 구조를 최대한 보존
- 수식이나 특수 기호는 그대로 유지
- 문제 번호(1., 2.)와 보기 기호(①②③④⑤)는 반드시 유지
- 지문과 문제의 구분은 명확히 유지"""
        
        self.ocr_fix_prompt_text = """당신은 OCR 오류 수정 전문가입니다.

다음 텍스트의 OCR 오류를 수정해주세요:
- 숫자와 문자 혼동 (0/O, 1/l/I, 5/S 등)
- 문자 인접 오류 (rn → m, cl → d 등)
- 공백 오류 (단어 분리/병합)

맥락 정보를 활용하여 정확한 단어로 수정해주세요."""
        
        if self.use_langchain:
            self.llm = ChatOpenAI(model=model, temperature=temperature)
            self._setup_prompts()
        elif OPENAI_AVAILABLE:
            self.client = openai.OpenAI()
        else:
            raise ImportError(
                "OpenAI 또는 LangChain이 설치되지 않았습니다. "
                "pip install openai langchain 또는 pip install openai"
            )
    
    def _setup_prompts(self):
        """LangChain 프롬프트 설정"""
        self.clean_prompt = ChatPromptTemplate.from_messages([
            ("system", self.clean_prompt_text),
            ("human", "다음 텍스트를 정리해주세요:\n\n{text}")
        ])
        
        self.ocr_fix_prompt = ChatPromptTemplate.from_messages([
            ("system", self.ocr_fix_prompt_text),
            ("human", "맥락: {context}\n\n텍스트: {text}\n\n수정된 텍스트:")
        ])
    
    def clean_extracted_text(self, raw_text: str, subject: str = "korean") -> str:
        """
        LLM으로 텍스트 정리
        
        Args:
            raw_text: 원본 추출 텍스트
            subject: 과목 ('korean', 'english', 'math' 등)
        
        Returns:
            정리된 텍스트
        """
        if not raw_text or not raw_text.strip():
            return raw_text
        
        # 너무 긴 텍스트는 청크 단위로 처리
        max_chunk_size = 3000  # 토큰 제한 고려
        if len(raw_text) <= max_chunk_size:
            return self._clean_chunk(raw_text, subject)
        
        # 청크 단위로 분할 및 처리
        chunks = self._split_text_chunks(raw_text, max_chunk_size)
        cleaned_chunks = []
        
        for chunk in chunks:
            cleaned = self._clean_chunk(chunk, subject)
            cleaned_chunks.append(cleaned)
        
        return "\n\n".join(cleaned_chunks)
    
    def _clean_chunk(self, text: str, subject: str) -> str:
        """단일 청크 정리"""
        if self.use_langchain:
            chain = self.clean_prompt | self.llm
            result = chain.invoke({"text": text})
            return result.content
        elif OPENAI_AVAILABLE:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.clean_prompt_text},
                    {"role": "user", "content": f"다음 텍스트를 정리해주세요:\n\n{text}"}
                ],
                temperature=self.temperature
            )
            return response.choices[0].message.content
        else:
            # Fallback: 기본 정리만 수행
            return self._basic_clean(text)
    
    def fix_ocr_errors(self, text: str, context: str = "") -> str:
        """
        OCR 오류 자동 수정
        
        Args:
            text: 오류가 포함된 텍스트
            context: 주변 맥락 (선택)
        
        Returns:
            수정된 텍스트
        """
        if not text or not text.strip():
            return text
        
        # 간단한 규칙 기반 오류 수정 (빠른 처리)
        fixed = self._rule_based_fix(text)
        
        # LLM 기반 수정 (선택적, 정확도 향상)
        if self.use_langchain:
            chain = self.ocr_fix_prompt | self.llm
            result = chain.invoke({"text": fixed, "context": context})
            return result.content
        elif OPENAI_AVAILABLE:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.ocr_fix_prompt_text},
                    {"role": "user", "content": f"맥락: {context}\n\n텍스트: {text}\n\n수정된 텍스트:"}
                ],
                temperature=self.temperature
            )
            return response.choices[0].message.content
        else:
            return fixed
    
    def _rule_based_fix(self, text: str) -> str:
        """규칙 기반 기본 오류 수정"""
        # 일반적인 OCR 오류 패턴
        fixes = {
            # 공백 정규화
            r'\s+': ' ',  # 여러 공백 → 하나
            r'\n\s*\n\s*\n+': '\n\n',  # 여러 줄바꿈 → 두 개
        }
        
        fixed = text
        for pattern, replacement in fixes.items():
            fixed = re.sub(pattern, replacement, fixed)
        
        return fixed.strip()
    
    def _basic_clean(self, text: str) -> str:
        """기본 텍스트 정리 (LLM 없이)"""
        # 공백 정규화
        text = re.sub(r'\s+', ' ', text)
        # 줄바꿈 정리
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text.strip()
    
    def _split_text_chunks(self, text: str, max_size: int) -> list:
        """텍스트를 청크로 분할 (문장/문단 경계 고려)"""
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # 문단 단위로 분할 시도
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [text]


# Fallback: LLM 없이 사용할 수 있는 기본 후처리기
class BasicTextPostProcessor:
    """LLM 없이 사용할 수 있는 기본 텍스트 후처리기"""
    
    @staticmethod
    def clean_extracted_text(raw_text: str, subject: str = "korean") -> str:
        """기본 텍스트 정리"""
        if not raw_text:
            return raw_text
        
        # 공백 정규화
        text = re.sub(r' +', ' ', raw_text)
        # 줄바꿈 정리 (3개 이상 → 2개)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    @staticmethod
    def fix_ocr_errors(text: str, context: str = "") -> str:
        """규칙 기반 OCR 오류 수정"""
        if not text:
            return text
        
        # 일반적인 OCR 오류 패턴
        fixes = {
            r'\s+': ' ',  # 공백 정규화
        }
        
        fixed = text
        for pattern, replacement in fixes.items():
            fixed = re.sub(pattern, replacement, fixed)
        
        return fixed.strip()


def get_text_postprocessor(use_ai: bool = True, **kwargs) -> Any:
    """
    텍스트 후처리기 인스턴스 반환
    
    Args:
        use_ai: AI 사용 여부 (False면 BasicTextPostProcessor 반환)
        **kwargs: AITextPostProcessor 생성자 인자
    
    Returns:
        AITextPostProcessor 또는 BasicTextPostProcessor 인스턴스
    """
    if use_ai:
        try:
            return AITextPostProcessor(**kwargs)
        except (ImportError, Exception) as e:
            print(f"⚠️ AI 텍스트 후처리기 사용 불가, 기본 후처리기 사용: {e}")
            return BasicTextPostProcessor()
    else:
        return BasicTextPostProcessor()
