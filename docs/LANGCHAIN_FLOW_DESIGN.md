# LangChain 기반 레슨 블록 자동 생성 Flow 설계

## 시스템 개요

본 시스템은 강의 대본을 입력으로 받아 LLM 기반 구조 분석 체인을 통해 강의 흐름을 레슨 블록 단위로 분해한다.

생성된 레슨 블록은 시각장애 학습자를 위한 점자 출력 및 학습 UI 제어를 목적으로 설계된 JSON 스키마로 고정되며, MongoDB에 저장되어 이후 학습 인터페이스에서 재사용된다.

---

## 전체 Flow 아키텍처

```
[강의대본 입력]
    ↓
[전처리 체인]
(불필요한 기호 / 공백 / 타임스탬프 정리)
    ↓
[레슨 블록 분해 LLM 체인]
(자동 레슨 블록 분해 프롬프트)
    ↓
[JSON 파싱 체인]
(정규식 기반 JSON 추출)
    ↓
[Pydantic 검증 체인]
(스키마 검증 및 타입 안전성 보장)
    ↓
[MongoDB 저장] (선택)
    ↓
[UI 전달]
```

---

## 설계 철학

### 1. "LLM을 한 번만 쓰지 않는다"

전체 파이프라인을 체인으로 구성하여:
- 전처리 → 분해 → 검증 → 저장이 하나의 흐름
- 각 단계가 독립적으로 테스트 가능
- 단계별 오류 처리 용이

### 2. "AI가 함부로 말 못 하게 하는 안전장치"

Pydantic 스키마로:
- LLM 출력을 강제 검증
- 타입 안전성 보장
- 잘못된 형식 자동 거부

### 3. "일관성 > 창의성"

LLM 설정:
- `temperature=0`: 구조 흔들림 방지
- 창의성 ❌ / 일관성 ⭕

---

## 기술 스택

- **LangChain**: LLM 체인 구성
- **ChatOpenAI**: GPT-4o-mini / GPT-4.1
- **Pydantic v2**: 스키마 검증
- **MongoDB**: 문서 저장
- **Python 3.11+**

---

## 핵심 컴포넌트

### 1. 전처리 체인

```python
def preprocess_script(script_text: str) -> str:
    """강의대본 전처리"""
    # SRT 타임스탬프 제거
    # 연속된 공백 정리
    # 연속된 줄바꿈 정리
    return script_text.strip()
```

**설계 이유**: 다양한 형식의 입력을 일관된 형식으로 정규화

### 2. LLM 분해 체인

```python
prompt = create_decomposition_prompt(subject)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
chain = prompt | llm | StrOutputParser()
```

**설계 이유**: 
- 과목별 특화 프롬프트로 정확도 향상
- temperature=0으로 일관된 출력 보장

### 3. JSON 파싱 체인

```python
def parse_and_validate_json(response: str) -> Dict:
    """LLM 응답에서 JSON 추출"""
    json_match = re.search(r'\{[\s\S]*\}', response)
    return json.loads(json_match.group(0))
```

**설계 이유**: LLM이 JSON 외에 설명을 추가해도 자동 추출

### 4. Pydantic 검증 체인

```python
def validate_lesson_schema(data: Dict) -> LessonSchema:
    """스키마 검증"""
    return LessonSchema(**data)
```

**설계 이유**:
- 점자 신호 형식 강제 검증 (3셀, ●○만)
- 블록 타입 검증
- 필수 필드 누락 방지

### 5. MongoDB 저장 체인

```python
def save_to_mongodb(lesson: LessonSchema) -> str:
    """MongoDB 저장"""
    collection.insert_one(lesson.model_dump())
```

**설계 이유**: 
- Pydantic 모델을 딕셔너리로 자동 변환
- 타입 안전성 유지

---

## 사용 예시

### 기본 사용

```python
from app.services.langchain_lesson_flow import generate_lesson_blocks

# 강의대본 → 레슨 블록
lesson = generate_lesson_blocks(
    script_text="강의 대본...",
    subject="korean",
    lesson_number=1
)

# 결과 사용
for block in lesson.blocks:
    print(f"{block.block_id}: {block.braille_signal} - {block.state_meaning}")
```

### MongoDB 저장 포함

```python
from app.services.langchain_lesson_flow import generate_and_save_lesson_blocks

result = generate_and_save_lesson_blocks(
    script_text="강의 대본...",
    subject="korean",
    lesson_number=1,
    save_to_db=True,
    mongo_uri="mongodb://localhost:27017"
)

print(f"저장 완료: {result['mongodb_id']}")
```

### Flow 객체 직접 사용

```python
from app.services.langchain_lesson_flow import LessonBlockGenerationFlow

flow = LessonBlockGenerationFlow(
    subject="korean",
    llm_model="gpt-4o-mini",
    temperature=0
)

lesson = flow.generate(script_text, lesson_number=1)
```

---

## 오류 처리 전략

### 1. LLM 호출 실패
- 규칙 기반 분해로 자동 폴백
- 사용자에게 경고 메시지

### 2. JSON 파싱 실패
- 정규식으로 JSON 블록 재추출 시도
- 실패 시 규칙 기반 분해로 폴백

### 3. 스키마 검증 실패
- 오류 메시지 상세 출력
- 수동 수정 가이드 제공

### 4. MongoDB 저장 실패
- 로컬 JSON 파일로 자동 저장
- 나중에 수동 저장 가능

---

## 성능 최적화

### 1. 프롬프트 길이 제한
- 대본이 너무 길면 청크로 분할
- 각 청크를 독립적으로 처리 후 병합

### 2. 캐싱
- 동일한 대본은 캐시에서 조회
- MongoDB에 저장된 레슨은 재생성 불필요

### 3. 비동기 처리
- 대량 처리 시 asyncio 활용
- 여러 레슨을 병렬로 생성

---

## 논문/발표용 문장

### 시스템 개요

> 본 시스템은 강의 대본을 입력으로 받아 LLM 기반 구조 분석 체인을 통해 강의 흐름을 레슨 블록 단위로 분해한다. 생성된 레슨 블록은 시각장애 학습자를 위한 점자 출력 및 학습 UI 제어를 목적으로 설계된 JSON 스키마로 고정되며, MongoDB에 저장되어 이후 학습 인터페이스에서 재사용된다.

### 설계 철학

> 본 시스템은 "점자는 신호등, 강의는 경험 문서"라는 핵심 설계 철학을 기반으로, 6점자 셀 3칸이라는 하드웨어 제약을 인정하고 오히려 이를 "상태 신호 장치"로 활용한다. 레슨 블록은 학습자가 인지적으로 위치를 바꿔야 하는 지점에서 분리되며, 각 블록은 점자 신호, 오디오 포커스, 상태 의미를 포함하여 시각장애 학습자가 항상 "지금 어디인지" 인지할 수 있도록 보장한다.

### 기술적 접근

> LangChain을 활용한 체인 기반 파이프라인으로 전처리, LLM 분해, JSON 파싱, Pydantic 검증, MongoDB 저장을 하나의 흐름으로 구성하였다. Pydantic 스키마를 통해 LLM 출력의 타입 안전성을 보장하고, 규칙 기반 분해를 폴백 메커니즘으로 제공하여 LLM 호출 실패 시에도 시스템이 정상 동작하도록 설계하였다.

### 교육 도메인 규칙 고정

> 과목별 분해 기준과 점자 신호 매핑을 프롬프트에 명시적으로 포함하여, LLM이 교육 도메인의 특수성을 이해하고 일관된 블록 구조를 생성하도록 하였다. 이는 단순히 "GPT를 사용했다"가 아니라, 교육 도메인 규칙을 AI 파이프라인에 체계적으로 통합한 시스템 설계이다.

---

## 이 구조의 강점

### 1. 연구/논문 레벨
- AI 파이프라인을 설계한 구조
- 교육 도메인 규칙을 프롬프트 + 스키마로 고정
- 점자·UI·DB까지 하나의 시스템

### 2. 실용성
- LLM 없이도 동작 (규칙 기반 폴백)
- 타입 안전성 보장 (Pydantic)
- 확장 가능한 구조 (새로운 블록 타입 추가 용이)

### 3. 포트폴리오
- LangChain 전문성
- 시스템 설계 능력
- 접근성 기술 이해

---

## 다음 단계

1. **실제 LLM 테스트**: OpenAI API 키로 실제 생성 테스트
2. **검증 규칙 강화**: 블록 품질 자동 검증 시스템
3. **수동 미세조정 UI**: 생성된 블록을 수정할 수 있는 관리 화면
