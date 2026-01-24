"""
AI 강의 생성 모듈
LLM을 이용한 설명형 강의 생성

원칙:
- 교재 내용을 "설명"하는 역할만 한다
- 새로운 지식 추가 금지
- 정답 단정 금지
- 교재의 의미를 훼손하지 않는다
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class AILectureGenerator:
    """
    AI 강의 생성 클래스
    
    LLM 프롬프트 기본 구조:
    "너는 고등학생을 가르치는 교사다.
    아래 교재 내용을 바탕으로,
    더 쉽게 풀어서 말로 설명하라.
    교재에 없는 정보는 추가하지 마라."
    """
    
    def __init__(self, subject: str):
        """
        Args:
            subject: 과목명 ('literature', 'math1', 'english')
        """
        self.subject = subject
        self.data_dir = Path(__file__).parent.parent.parent / "data" / subject
        self.lectures_dir = self.data_dir / "lectures"
    
    def generate_lecture_explanation(
        self,
        lecture_id: int,
        llm_client: Any  # LLM 클라이언트 (OpenAI, Anthropic 등)
    ) -> str:
        """
        강의 설명 생성
        
        Args:
            lecture_id: 강의 ID
            llm_client: LLM 클라이언트
        
        Returns:
            생성된 설명 텍스트
        """
        lecture_path = self.lectures_dir / f"lecture_{lecture_id:02d}.json"
        
        if not lecture_path.exists():
            raise FileNotFoundError(f"강의 파일을 찾을 수 없습니다: {lecture_path}")
        
        with open(lecture_path, 'r', encoding='utf-8') as f:
            lecture_data = json.load(f)
        
        # 교재 내용 추출
        textbook_content = []
        for section in lecture_data.get('sections', []):
            for content_text in section.get('content', []):
                if content_text.strip():
                    textbook_content.append(content_text)
        
        # 프롬프트 생성
        prompt = self._create_prompt(textbook_content)
        
        # LLM 호출
        explanation = llm_client.generate(prompt)
        
        return explanation
    
    def generate_section_explanation(
        self,
        lecture_id: int,
        section_title: str,
        llm_client: Any
    ) -> str:
        """
        특정 섹션 설명 생성
        
        Args:
            lecture_id: 강의 ID
            section_title: 섹션 제목
            llm_client: LLM 클라이언트
        
        Returns:
            생성된 설명 텍스트
        """
        lecture_path = self.lectures_dir / f"lecture_{lecture_id:02d}.json"
        
        if not lecture_path.exists():
            raise FileNotFoundError(f"강의 파일을 찾을 수 없습니다: {lecture_path}")
        
        with open(lecture_path, 'r', encoding='utf-8') as f:
            lecture_data = json.load(f)
        
        # 해당 섹션 내용 추출
        section_content = []
        for section in lecture_data.get('sections', []):
            if section.get('title') == section_title:
                for content_text in section.get('content', []):
                    if content_text.strip():
                        section_content.append(content_text)
                break
        
        if not section_content:
            return "(해당 섹션의 내용이 없습니다)"
        
        # 프롬프트 생성
        prompt = self._create_prompt(section_content)
        
        # LLM 호출
        explanation = llm_client.generate(prompt)
        
        return explanation
    
    def _create_prompt(self, textbook_content: List[str]) -> str:
        """프롬프트 생성"""
        content_text = "\n".join(textbook_content)
        
        prompt = f"""너는 고등학생을 가르치는 교사다.
아래 교재 내용을 바탕으로,
더 쉽게 풀어서 말로 설명하라.
교재에 없는 정보는 추가하지 마라.
정답을 단정하지 마라.
교재의 의미를 훼손하지 마라.

[교재 내용]
{content_text}

[설명]
"""
        return prompt
