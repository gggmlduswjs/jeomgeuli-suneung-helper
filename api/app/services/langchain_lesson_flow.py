"""
LangChain 기반 레슨 블록 자동 생성 Flow

강의대본 → (LLM) → 레슨 블록 JSON → DB 저장 / UI 전달
"""
from typing import Dict, Any, Optional, List
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator
import json
import re
from datetime import datetime

from app.services.ai_block_decomposer import DECOMPOSITION_PROMPT


# ============================================================================
# Pydantic 스키마 (JSON 강제 검증)
# ============================================================================

class LessonBlock(BaseModel):
    """레슨 블록 스키마"""
    block_id: str = Field(..., description="블록 고유 ID (예: B1, B2)")
    block_type: str = Field(..., description="블록 타입 (orientation, concept_frame, work_analysis 등)")
    braille_signal: str = Field(..., pattern=r'^[●○]{3}$', description="3셀 점자 패턴")
    audio_focus: str = Field(..., description="강의자가 무엇을 설명 중인지")
    state_meaning: str = Field(..., description="학습자가 지금 인지해야 할 상태")
    source_range: str = Field(..., description="대본 기준 범위 설명")
    
    @field_validator('braille_signal')
    @classmethod
    def validate_braille_signal(cls, v: str) -> str:
        """점자 신호 검증 (3셀 이내)"""
        if len(v) != 3:
            raise ValueError("점자 신호는 정확히 3셀이어야 합니다")
        if not all(c in '●○' for c in v):
            raise ValueError("점자 신호는 ● 또는 ○만 사용할 수 있습니다")
        return v


class LessonSchema(BaseModel):
    """레슨 전체 스키마"""
    lesson_title: str = Field(..., description="레슨 제목")
    subject: str = Field(..., description="과목 (korean, math, english)")
    lesson_number: int = Field(..., description="강의 번호")
    blocks: List[LessonBlock] = Field(..., description="레슨 블록 목록")
    
    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """과목 검증"""
        valid_subjects = ['korean', 'math', 'english']
        if v not in valid_subjects:
            raise ValueError(f"과목은 {valid_subjects} 중 하나여야 합니다")
        return v


# ============================================================================
# 전처리 체인
# ============================================================================

def preprocess_script(script_text: str) -> str:
    """
    강의대본 전처리
    
    - 불필요한 기호 제거
    - 공백 정리
    - 타임스탬프 정리 (SRT 형식인 경우)
    """
    # SRT 타임스탬프 제거
    srt_pattern = r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n'
    script_text = re.sub(srt_pattern, '', script_text)
    
    # 연속된 공백 정리
    script_text = re.sub(r'\s+', ' ', script_text)
    
    # 연속된 줄바꿈 정리
    script_text = re.sub(r'\n{3,}', '\n\n', script_text)
    
    return script_text.strip()


# ============================================================================
# LangChain Prompt Template
# ============================================================================

def create_decomposition_prompt(subject: str) -> ChatPromptTemplate:
    """
    레슨 블록 분해 프롬프트 생성
    
    Args:
        subject: 과목 ('korean', 'math', 'english')
    """
    # 과목별 추가 지시사항
    subject_guidance = {
        'korean': """
### [국어]

- 지문 설명
- 감상 프레임 제시
- 화자/정서/표현 분석
- 문제 적용
- 시험 포인트 강조

점자 규칙:
- [강의 시작] → orientation
- [감상 공식] → concept_frame
- [작품 시작] → work_analysis
- [문제] → problem_application
- [해설] → explanation
- [정리] → summary

지문 문장 / 선지 텍스트는 절대 블록 기준이 아니다.
""",
        'math': """
### [수학]

- 문제 제시
- 조건 설명
- 개념 도입
- 풀이 아이디어
- 계산 단계
- 결론 도출

점자 규칙:
- [문제] → orientation
- [조건] → learning_goal
- [정의] → concept_frame
- [핵심] → exam_structure
- [전환] → problem_application
- [결론] → summary

수식, 숫자, 계산 과정은 점자로 출력하지 않는다.
"풀이의 국면"만 표시한다.
""",
        'english': """
### [영어]

- 지문 목적 제시
- 독해 구조 프레임
- 문장 기능 설명
- 전환어/논리 코드
- 문제 접근
- 해설
- 출제 포인트

점자 규칙:
- [강의 시작] → orientation
- [구조] → concept_frame
- [표현] → exam_structure
- [논리 코드] → learning_goal
- [문제 접근] → problem_application
- [해설] → explanation
- [출제 포인트] → summary

문장 내용이 아니라
'그 문장이 하는 역할'을 기준으로 블록을 나눈다.
"""
    }
    
    prompt_template = f"""
너는 시각장애 수험생을 위한 학습 시스템에서
'강의대본을 레슨 블록으로 구조화하는 전용 분석 AI'다.

이 작업의 목적은
강의 내용을 요약하거나 설명하는 것이 아니라,
강의의 흐름을 '학습 단위 블록'으로 정확히 분해하는 것이다.

⚠️ 중요:
- 문장 요약 ❌
- 내용 압축 ❌
- 설명 재작성 ❌
- 오직 "강의 흐름과 기능"만 분해한다.

---

📌 시스템 전제 (반드시 지킬 것)

1. 점자 출력은 6점자 셀 3칸만 가능하다.
2. 점자는 내용을 전달하지 않는다.
3. 점자의 역할은
   "지금 강의가 어떤 국면인지 알려주는 상태 신호"이다.

즉,
점자 = 신호등
음성 = 설명
레슨 블록 = 학습 위치 고정 장치

---

📦 레슨 블록이란?

레슨 블록은
강의 중 '학습자가 인지적으로 위치를 바꿔야 하는 지점'이다.

다음 중 하나라도 해당되면
반드시 새로운 블록으로 분리한다:

- 강의의 목적이 바뀔 때
- 설명 대상이 바뀔 때
- 시험 관점이 등장할 때
- 문제 → 해설로 전환될 때
- 개념 → 적용으로 넘어갈 때
- 정서적 메시지(동기/마무리)가 나올 때

---

📘 과목별 분해 기준

{subject_guidance.get(subject, subject_guidance['korean'])}

---

📤 출력 형식 (절대 고정)

출력은 반드시 아래 JSON 형식을 따른다.
JSON만 출력하고 다른 설명은 하지 마라.

```json
{{
  "lesson_title": "레슨 제목",
  "subject": "{subject}",
  "lesson_number": 강의번호,
  "blocks": [
    {{
      "block_id": "B1",
      "block_type": "orientation",
      "braille_signal": "●○○",
      "audio_focus": "강의 소개 및 목표",
      "state_meaning": "강의가 시작되었습니다",
      "source_range": "문단 1부터"
    }}
  ]
}}
```

---

📌 블록 작성 규칙

* block_type은 기능 중심으로 작성
  (orientation, concept_frame, problem_application 등)
* braille_signal은 반드시 3셀 이내의 짧은 신호어 (● 또는 ○만 사용)
* audio_focus는 "강의자가 무엇을 설명 중인지"
* state_meaning은 "학습자가 지금 인지해야 할 상태"
* source_range는 대본 위치 설명 (문단/타임스탬프 기준)

---

🎯 최종 목표

이 시스템의 목표는
"시각장애 학습자가
지금 강의의 어디에 있는지를
점자 신호 하나로 즉시 인지하게 만드는 것"이다.

항상 이 질문에 답하라:

> "이 지점에서 학습자는
> 지금 강의의 무엇을 인식해야 하는가?"

이 질문에 대한 답이 바뀌는 지점이
곧 새로운 레슨 블록이다.

---

[강의대본]
{{script_text}}

위 강의대본을 레슨 블록으로 분해하여 JSON 형식으로만 출력하라.
"""
    
    return ChatPromptTemplate.from_template(prompt_template)


# ============================================================================
# JSON 파싱 및 검증
# ============================================================================

def parse_and_validate_json(response: str) -> Dict[str, Any]:
    """
    LLM 응답에서 JSON 추출 및 검증
    
    Args:
        response: LLM 응답 텍스트
        
    Returns:
        파싱된 JSON 딕셔너리
    """
    try:
        # JSON 블록 찾기
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            return parsed
    except json.JSONDecodeError as e:
        print(f"[JSON 파싱 오류] {e}")
        print(f"[응답 일부] {response[:500]}")
    
    raise ValueError("LLM 응답에서 유효한 JSON을 추출할 수 없습니다")


def validate_lesson_schema(data: Dict[str, Any]) -> LessonSchema:
    """
    Pydantic으로 스키마 검증
    
    Args:
        data: 파싱된 JSON 데이터
        
    Returns:
        검증된 LessonSchema 객체
    """
    try:
        return LessonSchema(**data)
    except Exception as e:
        print(f"[스키마 검증 오류] {e}")
        raise


# ============================================================================
# LangChain Flow 구성
# ============================================================================

class LessonBlockGenerationFlow:
    """
    레슨 블록 자동 생성 LangChain Flow
    
    전체 파이프라인:
    1. 전처리
    2. LLM 분해
    3. JSON 파싱
    4. 스키마 검증
    5. MongoDB 저장 (선택)
    """
    
    def __init__(
        self,
        subject: str,
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0,
        openai_api_key: Optional[str] = None
    ):
        """
        Args:
            subject: 과목 ('korean', 'math', 'english')
            llm_model: OpenAI 모델명
            temperature: LLM temperature (0 = 일관성 최대)
            openai_api_key: OpenAI API 키 (없으면 환경변수 사용)
        """
        self.subject = subject
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature,
            api_key=openai_api_key
        )
        
        # 프롬프트 생성
        self.prompt = create_decomposition_prompt(subject)
        
        # 체인 구성
        self.chain = self._build_chain()
    
    def _build_chain(self):
        """LangChain 체인 구성"""
        # 1. 전처리
        preprocess_step = RunnableLambda(preprocess_script)
        
        # 2. LLM 호출
        llm_step = self.prompt | self.llm | StrOutputParser()
        
        # 3. JSON 파싱
        parse_step = RunnableLambda(parse_and_validate_json)
        
        # 4. 스키마 검증
        validate_step = RunnableLambda(validate_lesson_schema)
        
        # 전체 체인
        chain = (
            {"script_text": preprocess_step}
            | llm_step
            | parse_step
            | validate_step
        )
        
        return chain
    
    def generate(
        self,
        script_text: str,
        lesson_number: Optional[int] = None
    ) -> LessonSchema:
        """
        강의대본을 레슨 블록으로 변환
        
        Args:
            script_text: 강의 대본 텍스트
            lesson_number: 강의 번호 (없으면 자동 추출)
            
        Returns:
            검증된 LessonSchema 객체
        """
        # 강의 번호가 없으면 프롬프트에 포함
        if lesson_number:
            # 프롬프트에 강의 번호 힌트 추가
            script_text = f"[강의 번호: {lesson_number}]\n\n{script_text}"
        
        # 체인 실행
        result = self.chain.invoke({"script_text": script_text})
        
        # 강의 번호 설정
        if lesson_number:
            result.lesson_number = lesson_number
        
        return result
    
    def generate_and_save(
        self,
        script_text: str,
        lesson_number: Optional[int] = None,
        save_to_db: bool = False,
        mongo_uri: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        생성 및 저장 (전체 파이프라인)
        
        Args:
            script_text: 강의 대본 텍스트
            lesson_number: 강의 번호
            save_to_db: MongoDB 저장 여부
            mongo_uri: MongoDB 연결 URI
            
        Returns:
            {
                "lesson": LessonSchema,
                "saved": bool,
                "mongodb_id": Optional[str]
            }
        """
        # 레슨 블록 생성
        lesson = self.generate(script_text, lesson_number)
        
        result = {
            "lesson": lesson,
            "saved": False,
            "mongodb_id": None
        }
        
        # MongoDB 저장
        if save_to_db:
            mongodb_id = self._save_to_mongodb(lesson, mongo_uri)
            result["saved"] = True
            result["mongodb_id"] = mongodb_id
        
        return result
    
    def _save_to_mongodb(
        self,
        lesson: LessonSchema,
        mongo_uri: Optional[str] = None
    ) -> Optional[str]:
        """
        MongoDB에 저장
        
        Args:
            lesson: LessonSchema 객체
            mongo_uri: MongoDB 연결 URI
            
        Returns:
            저장된 문서의 _id
        """
        try:
            from pymongo import MongoClient
            
            if mongo_uri:
                client = MongoClient(mongo_uri)
            else:
                # 기본 로컬 MongoDB
                client = MongoClient("mongodb://localhost:27017")
            
            db = client["jeomgeuli"]
            collection = db["lessons"]
            
            # Pydantic 모델을 딕셔너리로 변환
            lesson_dict = lesson.model_dump()
            lesson_dict["createdAt"] = datetime.utcnow()
            lesson_dict["updatedAt"] = datetime.utcnow()
            
            # 저장
            result = collection.insert_one(lesson_dict)
            return str(result.inserted_id)
            
        except ImportError:
            print("[경고] pymongo가 설치되지 않았습니다. MongoDB 저장을 건너뜁니다.")
            return None
        except Exception as e:
            print(f"[MongoDB 저장 오류] {e}")
            return None


# ============================================================================
# 편의 함수
# ============================================================================

def generate_lesson_blocks(
    script_text: str,
    subject: str = "korean",
    lesson_number: Optional[int] = None,
    llm_model: str = "gpt-4o-mini",
    temperature: float = 0,
    openai_api_key: Optional[str] = None
) -> LessonSchema:
    """
    강의대본을 레슨 블록으로 변환 (편의 함수)
    
    Args:
        script_text: 강의 대본 텍스트
        subject: 과목
        lesson_number: 강의 번호
        llm_model: LLM 모델명
        temperature: LLM temperature
        openai_api_key: OpenAI API 키
        
    Returns:
        LessonSchema 객체
    """
    flow = LessonBlockGenerationFlow(
        subject=subject,
        llm_model=llm_model,
        temperature=temperature,
        openai_api_key=openai_api_key
    )
    
    return flow.generate(script_text, lesson_number)


def generate_and_save_lesson_blocks(
    script_text: str,
    subject: str = "korean",
    lesson_number: Optional[int] = None,
    llm_model: str = "gpt-4o-mini",
    temperature: float = 0,
    openai_api_key: Optional[str] = None,
    save_to_db: bool = False,
    mongo_uri: Optional[str] = None
) -> Dict[str, Any]:
    """
    생성 및 저장 (편의 함수)
    
    Args:
        script_text: 강의 대본 텍스트
        subject: 과목
        lesson_number: 강의 번호
        llm_model: LLM 모델명
        temperature: LLM temperature
        openai_api_key: OpenAI API 키
        save_to_db: MongoDB 저장 여부
        mongo_uri: MongoDB 연결 URI
        
    Returns:
        {
            "lesson": LessonSchema,
            "saved": bool,
            "mongodb_id": Optional[str]
        }
    """
    flow = LessonBlockGenerationFlow(
        subject=subject,
        llm_model=llm_model,
        temperature=temperature,
        openai_api_key=openai_api_key
    )
    
    return flow.generate_and_save(
        script_text,
        lesson_number,
        save_to_db,
        mongo_uri
    )
