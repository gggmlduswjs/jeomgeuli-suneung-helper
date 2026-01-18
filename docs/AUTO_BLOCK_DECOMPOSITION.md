# 강의대본 → 레슨 블록 자동 분해 시스템

## 개요

강의대본(txt/srt/stt)을 입력받아 레슨 블록 JSON을 자동 생성하는 시스템입니다.

**핵심 철학**: 점자는 신호등, 강의는 경험 문서, 블록은 학습 위치 고정 장치

---

## 시스템 아키텍처

```
강의대본 (txt/srt/stt)
    ↓
[규칙 기반 분해] ← 기본 분해
    ↓
[AI 기반 미세 조정] ← 선택적 (LLM 사용 시)
    ↓
[검증 및 정제]
    ↓
레슨 블록 JSON
```

---

## 사용 방법

### 1. 규칙 기반 분해 (기본)

```python
from app.services.lesson_block_decomposer import decompose_lecture_script

result = decompose_lecture_script(
    script_text="강의 대본 텍스트...",
    subject="korean",  # "korean", "math", "english"
    lesson_number=1
)

# 결과
# {
#   "lesson_title": "1강 시의 표현과 형식",
#   "subject": "korean",
#   "lesson_number": 1,
#   "blocks": [...]
# }
```

### 2. AI 기반 분해 (LangChain)

```python
from langchain_openai import ChatOpenAI
from app.services.langchain_block_decomposer import create_decomposition_chain

llm = ChatOpenAI(model="gpt-4", temperature=0)
chain = create_decomposition_chain(llm)

result = chain.invoke({
    "script_text": "강의 대본...",
    "subject": "korean",
    "lesson_number": 1
})
```

### 3. 하이브리드 분해

```python
from app.services.langchain_block_decomposer import HybridBlockDecomposer
from app.services.lesson_block_decomposer import Subject

decomposer = HybridBlockDecomposer(
    subject=Subject.KOREAN,
    llm=llm,  # 선택적
    use_ai=True  # AI 사용 여부
)

result = decomposer.decompose(script_text, lesson_number=1)
```

---

## 출력 형식

```json
{
  "lesson_title": "1강 시의 표현과 형식",
  "subject": "korean",
  "lesson_number": 1,
  "blocks": [
    {
      "block_id": "B1",
      "block_type": "orientation",
      "braille_signal": "●○○",
      "audio_focus": "강의 소개 및 목표",
      "state_meaning": "강의가 시작되었습니다",
      "source_range": "문단 1부터"
    },
    {
      "block_id": "B2",
      "block_type": "concept_frame",
      "braille_signal": "○●○",
      "audio_focus": "감상 프레임 및 분석 방법",
      "state_meaning": "감상 프레임을 학습합니다",
      "source_range": "문단 6부터"
    }
  ]
}
```

---

## 블록 분해 기준

### 국어 (Korean)

**분해 지점**:
- 오리엔테이션: "여러분, 안녕하세요", "시작됐습니다"
- 감상 프레임: "화자가 무엇을 어떻게", "감상 프레임", "사고 틀"
- 작품 분석: "작품", "지문", "본문", "고전", "현대"
- 문제: "1번 문제", "문제 1", "마지막 문제"
- 해설: "해설", "정답", "선택지"
- 정리: "정리", "요약", "한 판에 담판"

**점자 신호**:
- `●○○`: 강의 시작
- `○●○`: 감상 공식
- `○●●`: 작품 시작
- `○○●`: 문제
- `●●○`: 해설
- `●○●`: 정리

### 수학 (Math)

**분해 지점**:
- 문제: "문제 1", "예제 1", "유제 1"
- 조건: "조건", "전제", "가정"
- 정의: "정의", "개념", "약속"
- 핵심: "핵심", "중요", "포인트"
- 풀이: "풀이", "해결", "접근"
- 결론: "정리", "결론", "마무리"

**점자 신호**:
- `●○○`: 문제
- `●●○`: 조건
- `○●○`: 정의
- `●●●`: 핵심
- `○○●`: 전환
- `●○●`: 결론

### 영어 (English)

**분해 지점**:
- 강의 시작: "여러분, 안녕", "시작"
- 구조: "독해 구조", "문장 기능", "글의 목적"
- 표현: "표현", "기법", "어법"
- 논리 코드: "논리 코드", "전환어", "연결어"
- 문제 접근: "문제", "접근"
- 해설: "해설", "설명"
- 출제 포인트: "출제 포인트", "정리"

---

## 검증 규칙

### 자동 검증 항목

1. **블록 순서 검증**
   - 블록 ID가 순차적인지 확인
   - 블록 순서가 논리적인지 확인

2. **점자 신호 일관성**
   - 블록 타입과 점자 신호가 일치하는지 확인
   - 과목별 점자 신호 규칙 준수 확인

3. **상태 의미 메시지**
   - 각 블록에 상태 의미가 있는지 확인
   - 메시지가 명확하고 이해하기 쉬운지 확인

4. **소스 범위**
   - 각 블록의 소스 범위가 명시되어 있는지 확인
   - 범위가 중복되지 않는지 확인

### 수동 검증 가이드

생성된 블록을 검토할 때 다음을 확인:

1. **블록 경계가 적절한가?**
   - 학습자가 인지적으로 위치를 바꿔야 하는 지점에서 분리되었는가?

2. **점자 신호가 의미 있는가?**
   - 점자 패턴만 보고도 현재 상태를 파악할 수 있는가?

3. **상태 의미가 명확한가?**
   - 시각장애 학습자가 "지금 어디인지" 즉시 인지할 수 있는가?

---

## 프롬프트 (고정본)

핵심 프롬프트는 `api/app/services/ai_block_decomposer.py`의 `DECOMPOSITION_PROMPT`에 정의되어 있습니다.

이 프롬프트는:
- Cursor / GPT / LangChain 어디에 넣어도 동작
- 과목별 분해 기준 포함
- 점자 신호 규칙 포함
- 출력 형식 고정

---

## 구현 상태

✅ 규칙 기반 분해: 완료
✅ 과목별 분해 규칙: 완료
✅ 점자 신호 매핑: 완료
✅ LangChain 통합: 준비 완료
⏳ AI 기반 미세 조정: LLM 클라이언트 필요
⏳ 검증 규칙 자동화: 구현 중

---

## 다음 단계

1. **LangChain Flow 완성**: 실제 LLM과 통합 테스트
2. **검증 규칙 자동화**: 블록 품질 자동 검증
3. **수동 미세조정 UI**: 생성된 블록을 수정할 수 있는 인터페이스
