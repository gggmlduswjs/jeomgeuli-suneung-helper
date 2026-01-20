# 사용자가 AI/ML을 확실히 느끼게 하는 기능

## 🎯 핵심 질문: 사용자가 "AI가 동작한다"는 걸 어떻게 느낄까?

**답**: **실시간 상호작용** + **개인화** + **지능적 응답**

---

## 🔥 가장 임팩트 큰 기능 (우선순위)

### 1️⃣ 실시간 AI 학습 도우미 (음성 질문 → AI 답변) ⭐⭐⭐⭐⭐

**사용자가 느끼는 것**:
> "음성으로 질문하면 AI가 바로 답변해줘!"

**구현 위치**:
```
apps/web/src/hooks/useAILearningAssistant.ts (새로 생성)
apps/web/src/services/ai/learningAssistant.ts (새로 생성)
```

**기능**:
- 사용자가 학습 중 음성으로 질문: "이 문장이 무슨 뜻이야?"
- AI가 실시간으로 답변 (LLM)
- TTS로 음성으로 답변 재생
- 점자 디바이스에도 답변 표시

**예시 시나리오**:
```
[학습 중]
사용자: "이 시의 주제가 뭐야?"
  ↓
[AI 처리 중...] (0.5초)
  ↓
AI: "이 시는 자연의 아름다움을 노래한 작품입니다. 
     시인은 봄날의 풍경을 통해 삶의 순환을 표현하고 있습니다."
  ↓
[TTS 재생] + [점자 출력]
```

**기술 스택**:
- STT (음성 인식) - 이미 있음
- LLM (OpenAI/Gemini) - 실시간 답변
- TTS (음성 합성) - 이미 있음
- 점자 출력 - 이미 있음

**구현 난이도**: ⭐⭐⭐ (중간)
**임팩트**: ⭐⭐⭐⭐⭐ (매우 높음)

---

### 2️⃣ AI 학습 내용 요약 (레슨 시작 전) ⭐⭐⭐⭐

**사용자가 느끼는 것**:
> "AI가 이 레슨의 핵심을 미리 알려줘!"

**구현 위치**:
```
apps/web/src/pages/Lesson.tsx (수정)
api/app/routers/lessons.py (새 엔드포인트)
```

**기능**:
- 레슨 시작 전: "이 레슨의 핵심 내용을 요약해드릴까요?"
- AI가 레슨 내용 분석 → 핵심 요약 생성
- TTS로 요약 내용 음성 재생
- 점자로도 요약 표시

**예시 시나리오**:
```
[레슨 선택]
사용자: "1강 시작"
  ↓
[AI 분석 중...] (1초)
  ↓
AI: "이 레슨은 고전 시가의 이해를 다룹니다. 
     주요 학습 내용은 시의 운율과 표현 기법입니다.
     예상 소요 시간은 15분입니다."
  ↓
[TTS 재생] + [점자 출력]
```

**기술 스택**:
- LLM (레슨 내용 요약)
- TTS
- 점자 출력

**구현 난이도**: ⭐⭐ (쉬움)
**임팩트**: ⭐⭐⭐⭐ (높음)

---

### 3️⃣ AI 개인화 학습 추천 (학습 패턴 분석) ⭐⭐⭐⭐

**사용자가 느끼는 것**:
> "AI가 내 학습 패턴을 분석해서 추천해줘!"

**구현 위치**:
```
apps/web/src/hooks/useAILearningRecommendation.ts (새로 생성)
api/app/routers/progress.py (새 엔드포인트)
api/app/services/learning_analyzer.py (새로 생성)
```

**기능**:
- 학습 진행 데이터 수집 (어디서 멈추는지, 얼마나 걸리는지)
- AI가 패턴 분석: "이 사용자는 문학에서 어려워하는 구간이 있네"
- 개인화된 추천: "다음에는 이 레슨을 추천합니다"
- 음성으로 추천 알림

**예시 시나리오**:
```
[학습 완료 후]
AI: "학습 패턴을 분석한 결과, 
     문학 레슨에서 시 해석 부분에서 시간이 오래 걸리셨습니다.
     다음에는 비유법에 대한 보충 학습을 추천합니다."
  ↓
[TTS 재생] + [점자 출력]
```

**기술 스택**:
- 간단한 ML (scikit-learn) - 패턴 분석
- LLM - 추천 이유 설명
- TTS
- 점자 출력

**구현 난이도**: ⭐⭐⭐⭐ (어려움)
**임팩트**: ⭐⭐⭐⭐ (높음)

---

### 4️⃣ AI 실시간 점자 변환 개선 (문맥 이해) ⭐⭐⭐

**사용자가 느끼는 것**:
> "AI가 문맥을 이해해서 더 정확한 점자로 변환해줘!"

**구현 위치**:
```
apps/web/src/services/braille/aiBrailleConverter.ts (새로 생성)
api/app/services/braille_convert.py (수정)
```

**기능**:
- 기존: 규칙 기반 점자 변환
- 개선: AI가 문맥 이해 → 더 정확한 점자 변환
- 예: "수학" vs "수업" → 문맥에 따라 다른 점자

**예시 시나리오**:
```
[학습 중]
텍스트: "수학 문제를 풀었다"
  ↓
[AI 문맥 분석]
  ↓
점자: [수학] (올바른 점자)
  ↓
텍스트: "수업 시간이 되었다"
  ↓
[AI 문맥 분석]
  ↓
점자: [수업] (올바른 점자)
```

**기술 스택**:
- LLM - 문맥 이해
- 점자 변환 규칙

**구현 난이도**: ⭐⭐⭐ (중간)
**임팩트**: ⭐⭐⭐ (보통)

---

### 5️⃣ AI 학습 난이도 자동 조절 ⭐⭐⭐

**사용자가 느끼는 것**:
> "AI가 내 수준에 맞춰서 학습 난이도를 조절해줘!"

**구현 위치**:
```
api/app/services/learning_difficulty_adjuster.py (새로 생성)
apps/web/src/store/learningStore.ts (수정)
```

**기능**:
- 학습 진행 데이터 분석 (정답률, 소요 시간)
- AI가 난이도 판단: "이 사용자는 중급 수준"
- 자동으로 적절한 레슨 추천
- 음성으로 난이도 안내

**예시 시나리오**:
```
[문제 풀이 완료]
정답률: 80%
  ↓
[AI 분석]
  ↓
AI: "현재 수준은 중급입니다. 
     다음 레슨은 조금 더 어려운 내용을 추천합니다."
  ↓
[TTS 재생]
```

**기술 스택**:
- 간단한 ML (정답률 기반 분류)
- LLM - 난이도 설명
- TTS

**구현 난이도**: ⭐⭐⭐ (중간)
**임팩트**: ⭐⭐⭐ (보통)

---

## 🎯 MVP 우선순위 (시간 없을 때)

### ✅ 반드시 구현 (최고 임팩트)

1. **실시간 AI 학습 도우미** (음성 질문 → AI 답변)
   - 구현 시간: 2-3일
   - 임팩트: ⭐⭐⭐⭐⭐
   - 사용자 체감: 매우 높음

2. **AI 학습 내용 요약** (레슨 시작 전)
   - 구현 시간: 1일
   - 임팩트: ⭐⭐⭐⭐
   - 사용자 체감: 높음

### ⚠️ 선택적 구현

3. **AI 개인화 학습 추천**
   - 구현 시간: 3-4일
   - 임팩트: ⭐⭐⭐⭐
   - 사용자 체감: 높음 (하지만 데이터 수집 필요)

4. **AI 실시간 점자 변환 개선**
   - 구현 시간: 2일
   - 임팩트: ⭐⭐⭐
   - 사용자 체감: 보통

5. **AI 학습 난이도 자동 조절**
   - 구현 시간: 2-3일
   - 임팩트: ⭐⭐⭐
   - 사용자 체감: 보통

---

## 💡 발표용 데모 시나리오

### 시나리오 1: 실시간 AI 학습 도우미

```
[데모 시작]
1. 사용자가 레슨 학습 중
2. "이 문장이 무슨 뜻이야?" (음성 질문)
3. [AI 처리 중...] (0.5초)
4. AI: "이 문장은..." (음성 답변)
5. 점자 디바이스에도 답변 표시

→ "AI가 실시간으로 학습을 도와줍니다!"
```

### 시나리오 2: AI 학습 내용 요약

```
[데모 시작]
1. 사용자가 레슨 선택
2. "1강 시작"
3. [AI 분석 중...] (1초)
4. AI: "이 레슨은..." (핵심 요약)
5. TTS로 요약 재생

→ "AI가 레슨 내용을 미리 요약해줍니다!"
```

---

## 🔧 구현 가이드

### 1. 실시간 AI 학습 도우미 구현

**프론트엔드** (`apps/web/src/hooks/useAILearningAssistant.ts`):
```typescript
export function useAILearningAssistant() {
  const { transcript } = useSTT();
  const { speak } = useTTS();
  
  const askAI = async (question: string, context: string) => {
    // AI API 호출
    const response = await aiAPI.askQuestion(question, context);
    
    // TTS로 답변 재생
    speak(response.answer);
    
    // 점자로도 표시
    displayBraille(response.answer);
  };
  
  return { askAI };
}
```

**백엔드** (`api/app/routers/ai.py`):
```python
@router.post("/ai/ask")
async def ask_ai_question(
    question: str,
    context: str,
    db: Session = Depends(get_db)
):
    """AI 학습 도우미"""
    # LLM 호출
    response = llm_client.chat(
        messages=[
            {"role": "system", "content": "당신은 수능 학습 도우미입니다."},
            {"role": "user", "content": f"질문: {question}\n\n맥락: {context}"}
        ]
    )
    
    return {"answer": response.content}
```

### 2. AI 학습 내용 요약 구현

**백엔드** (`api/app/routers/lessons.py`):
```python
@router.get("/lessons/{lesson_id}/summary")
async def get_lesson_summary(
    lesson_id: str,
    db: Session = Depends(get_db)
):
    """레슨 내용 AI 요약"""
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    
    # 레슨 내용 수집
    content = collect_lesson_content(lesson)
    
    # LLM으로 요약
    summary = llm_client.summarize(content)
    
    return {"summary": summary}
```

**프론트엔드** (`apps/web/src/pages/Lesson.tsx`):
```typescript
useEffect(() => {
  // 레슨 시작 시 AI 요약 가져오기
  const loadSummary = async () => {
    const summary = await lessonsAPI.getSummary(lessonId);
    speak(`이 레슨의 핵심 내용: ${summary.summary}`);
  };
  
  loadSummary();
}, [lessonId]);
```

---

## 📊 최종 추천

### MVP 구현 (시간 없을 때)

1. **실시간 AI 학습 도우미** (필수)
   - 가장 임팩트 큼
   - 사용자가 바로 체감 가능
   - 구현 시간: 2-3일

2. **AI 학습 내용 요약** (필수)
   - 구현 간단
   - 사용자 체감 높음
   - 구현 시간: 1일

### 추가 구현 (시간 있을 때)

3. **AI 개인화 학습 추천**
   - 구현 시간: 3-4일
   - 데이터 수집 필요

---

## 🎓 발표용 한 줄 요약

> **"사용자가 음성으로 질문하면 AI가 실시간으로 답변하고, 
> 레슨 시작 전 AI가 핵심 내용을 요약해주는 지능형 학습 시스템"**

**핵심 포인트**:
- ✅ 실시간 상호작용 (음성 질문 → AI 답변)
- ✅ 개인화 (학습 내용 요약)
- ✅ 접근성 (점자 + 음성)

---

*작성일: 2024년 12월*
