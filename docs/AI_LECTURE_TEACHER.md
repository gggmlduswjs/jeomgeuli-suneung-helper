# AI 강의 선생님 (강의 대본 기반 수업)

## 🎯 핵심 아이디어

**강의 대본(HWP)을 프롬프트 컨텍스트로 사용해서 AI가 각 레슨마다 수업을 진행**

---

## 💡 왜 이 방법이 좋은가?

### 기존 방식의 문제
- ❌ AI가 일반적인 답변만 제공 (컨텍스트 부족)
- ❌ 레슨별 맞춤 설명 불가
- ❌ 강의 대본 내용과 연결 안 됨

### 새로운 방식의 장점
- ✅ 강의 대본을 프롬프트로 사용 → **정확한 컨텍스트**
- ✅ 각 레슨마다 해당 강의 대본 기반 수업
- ✅ 사용자 질문 → 강의 대본 컨텍스트 포함 답변
- ✅ **AI 선생님이 실제로 수업하는 것처럼** 느껴짐

---

## 🔥 구현 방법

### 1️⃣ 데이터 구조

**강의 대본 저장**:
```python
# api/app/db/models.py
class Lesson:
    lesson_id: str
    title: str
    lecture_script_text: str  # 강의 대본 전체 텍스트
    lecture_script_path: str  # HWP 파일 경로 (선택)
    # ...
```

**레슨별 강의 대본 매핑**:
- 1강 → `data/lecture_scripts/수능특강_문학_2026/1강.hwp` → 텍스트 추출
- 2강 → `data/lecture_scripts/수능특강_문학_2026/2강.hwp` → 텍스트 추출

---

### 2️⃣ AI 수업 진행 방식

#### 방식 A: 순차적 수업 진행 (추천)

```
[레슨 시작]
  ↓
[강의 대본 로드] (1강.hwp → 텍스트)
  ↓
[AI 프롬프트 구성]
  - 시스템: "당신은 수능 문학 선생님입니다"
  - 컨텍스트: 강의 대본 전체 텍스트
  - 지시: "이 강의 대본을 기반으로 수업을 진행하세요"
  ↓
[AI가 강의 대본 순서대로 설명]
  - "오늘은 고전 시가의 이해를 배워봅시다"
  - "먼저 운율에 대해 알아볼게요"
  - ...
  ↓
[TTS 재생] + [점자 출력]
```

#### 방식 B: 사용자 질문 기반 (대화형)

```
[사용자 질문]
사용자: "이 시의 주제가 뭐야?"
  ↓
[AI 프롬프트 구성]
  - 시스템: "당신은 수능 문학 선생님입니다"
  - 컨텍스트: 현재 레슨의 강의 대본 텍스트
  - 질문: "이 시의 주제가 뭐야?"
  - 지시: "강의 대본 내용을 참고해서 답변하세요"
  ↓
[AI 답변]
AI: "강의 대본에 따르면, 이 시는..."
  ↓
[TTS 재생] + [점자 출력]
```

---

## 📋 레슨 단위 구조화

**핵심**: 긴 강의 대본을 레슨 단위로 분할 → 각 레슨마다 AI 수업 진행

**구현 서비스**:
- `api/app/services/lecture_lesson_splitter.py`: 강의 대본을 레슨 단위로 분할
- 레슨 제목 기반 분할 또는 자동 분할 지원

**레슨 구조 예시** (2026 수능특강 문학 1강):
- 레슨 1: 강의 오리엔테이션 (5분)
- 레슨 2: 핵심 개념 안내 (3분)
- 레슨 3: 시의 표현 개념 정리 (4분)
- ...
- 레슨 16: 한 판에 담판 정리 (4분)

자세한 내용은 `docs/LECTURE_LESSON_STRUCTURE.md` 참고.

---

## 🔧 구현 위치

### 백엔드

**1. 강의 대본 저장/조회**:
```python
# api/app/routers/lessons.py
@router.get("/lessons/{lesson_id}/script")
async def get_lesson_script(lesson_id: str, db: Session = Depends(get_db)):
    """레슨의 강의 대본 조회"""
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="레슨을 찾을 수 없습니다.")
    
    # 강의 대본 텍스트 반환
    return {
        "lesson_id": lesson_id,
        "script_text": lesson.lecture_script_text,
        "script_path": lesson.lecture_script_path
    }
```

**2. AI 수업 진행 API**:
```python
# api/app/routers/ai.py (새로 생성)
from app.services.ai_lecture_teacher import AILectureTeacher

router = APIRouter()

@router.post("/ai/teach/{lesson_id}")
async def ai_teach_lesson(
    lesson_id: str,
    mode: str = "sequential",  # "sequential" or "interactive"
    question: Optional[str] = None,  # 대화형 모드일 때
    db: Session = Depends(get_db)
):
    """
    AI가 강의 대본을 기반으로 수업 진행
    
    Args:
        lesson_id: 레슨 ID
        mode: "sequential" (순차적) 또는 "interactive" (대화형)
        question: 대화형 모드일 때 사용자 질문
    """
    lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="레슨을 찾을 수 없습니다.")
    
    # AI 강의 선생님 초기화
    teacher = AILectureTeacher(lesson.lecture_script_text)
    
    if mode == "sequential":
        # 순차적 수업 진행
        response = await teacher.teach_sequentially()
    else:
        # 대화형 수업 (질문 기반)
        if not question:
            raise HTTPException(status_code=400, detail="질문이 필요합니다.")
        response = await teacher.answer_question(question)
    
    return {
        "lesson_id": lesson_id,
        "response": response,
        "mode": mode
    }
```

**3. AI 강의 선생님 서비스**:
```python
# api/app/services/ai_lecture_teacher.py (새로 생성)
from typing import Optional
import openai  # 또는 Gemini

class AILectureTeacher:
    """강의 대본 기반 AI 수업 진행"""
    
    def __init__(self, lecture_script: str, subject: str = "literature"):
        self.lecture_script = lecture_script
        self.subject = subject
        self.client = openai.OpenAI()  # 또는 Gemini
    
    async def teach_sequentially(self) -> str:
        """순차적으로 강의 대본 기반 수업 진행"""
        prompt = f"""당신은 수능 {self.subject} 선생님입니다.

다음은 오늘 수업할 강의 대본입니다:
{self.lecture_script}

이 강의 대본을 기반으로 학생에게 수업을 진행하세요.
- 친절하고 이해하기 쉽게 설명하세요
- 강의 대본의 순서를 따라가세요
- 핵심 내용을 강조하세요
- 예시를 들어 설명하세요

수업 시작 인사와 함께 첫 번째 주제를 설명해주세요.
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"당신은 수능 {self.subject} 선생님입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    async def answer_question(self, question: str) -> str:
        """강의 대본 컨텍스트를 포함해서 질문에 답변"""
        prompt = f"""당신은 수능 {self.subject} 선생님입니다.

다음은 오늘 수업한 강의 대본입니다:
{self.lecture_script}

학생이 다음과 같이 질문했습니다:
{question}

강의 대본 내용을 참고해서 정확하고 친절하게 답변해주세요.
- 강의 대본에 나온 내용을 인용하세요
- 이해하기 쉽게 설명하세요
- 필요하면 추가 예시를 들어주세요
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"당신은 수능 {self.subject} 선생님입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    async def get_next_topic(self, current_position: int = 0) -> str:
        """강의 대본에서 다음 주제 가져오기"""
        # 강의 대본을 청크로 나눔
        chunks = self._split_script_into_chunks()
        
        if current_position < len(chunks):
            next_chunk = chunks[current_position]
            
            prompt = f"""다음 강의 대본 부분을 학생에게 설명해주세요:

{next_chunk}

친절하고 이해하기 쉽게 설명하세요.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"당신은 수능 {self.subject} 선생님입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        return "수업이 끝났습니다."
    
    def _split_script_into_chunks(self, chunk_size: int = 1000) -> list[str]:
        """강의 대본을 청크로 나누기"""
        # 간단한 구현: 문단 단위로 나누기
        paragraphs = self.lecture_script.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
```

---

### 프론트엔드

**1. AI 수업 진행 훅**:
```typescript
// apps/web/src/hooks/useAILectureTeacher.ts (새로 생성)
import { useState } from 'react';
import { aiAPI } from '../services/ai';

export function useAILectureTeacher(lessonId: string) {
  const [isTeaching, setIsTeaching] = useState(false);
  const [currentTopic, setCurrentTopic] = useState<string | null>(null);
  const [position, setPosition] = useState(0);

  const startLesson = async () => {
    setIsTeaching(true);
    try {
      // 순차적 수업 시작
      const response = await aiAPI.teachLesson(lessonId, 'sequential');
      setCurrentTopic(response.response);
      // TTS로 재생
      speak(response.response);
    } catch (error) {
      console.error('[AI Lecture] 수업 시작 실패:', error);
    } finally {
      setIsTeaching(false);
    }
  };

  const askQuestion = async (question: string) => {
    try {
      // 대화형 모드로 질문
      const response = await aiAPI.teachLesson(lessonId, 'interactive', question);
      // TTS로 재생
      speak(response.response);
      return response.response;
    } catch (error) {
      console.error('[AI Lecture] 질문 실패:', error);
    }
  };

  const nextTopic = async () => {
    setPosition(prev => prev + 1);
    try {
      const response = await aiAPI.getNextTopic(lessonId, position + 1);
      setCurrentTopic(response.response);
      speak(response.response);
    } catch (error) {
      console.error('[AI Lecture] 다음 주제 실패:', error);
    }
  };

  return {
    startLesson,
    askQuestion,
    nextTopic,
    isTeaching,
    currentTopic,
    position
  };
}
```

**2. AI 서비스**:
```typescript
// apps/web/src/services/ai.ts (새로 생성)
import { api } from './api';

export const aiAPI = {
  async teachLesson(
    lessonId: string,
    mode: 'sequential' | 'interactive',
    question?: string
  ) {
    const params = new URLSearchParams({ mode });
    if (question) {
      params.append('question', question);
    }
    return api.post(`/ai/teach/${lessonId}?${params}`);
  },

  async getNextTopic(lessonId: string, position: number) {
    return api.post(`/ai/teach/${lessonId}/next`, { position });
  }
};
```

**3. 레슨 페이지 수정**:
```typescript
// apps/web/src/pages/Lesson.tsx (수정)
import { useAILectureTeacher } from '../hooks/useAILectureTeacher';

export default function Lesson() {
  const { lessonId } = useParams();
  const { speak } = useTTS();
  const { startLesson, askQuestion, isTeaching } = useAILectureTeacher(lessonId!);

  // 레슨 시작 시 AI 수업 시작
  useEffect(() => {
    if (lessonId) {
      startLesson();
    }
  }, [lessonId]);

  // 사용자 질문 처리
  const handleQuestion = async (question: string) => {
    const answer = await askQuestion(question);
    // 점자로도 표시
    displayBraille(answer);
  };

  return (
    <AppShellMobile>
      {/* AI 수업 진행 중 표시 */}
      {isTeaching && <div>AI가 수업을 진행하고 있습니다...</div>}
      
      {/* 사용자 질문 입력 */}
      <SpeechBar onQuestion={handleQuestion} />
    </AppShellMobile>
  );
}
```

---

## 🎯 사용자 경험

### 시나리오 1: 순차적 수업

```
[사용자: "1강 시작"]
  ↓
[AI: "안녕하세요. 오늘은 고전 시가의 이해를 배워봅시다.
      먼저 운율에 대해 알아볼게요. 운율이란..."]
  ↓
[TTS 재생] + [점자 출력]
  ↓
[사용자: "다음"]
  ↓
[AI: "이제 시의 표현 기법에 대해 배워봅시다..."]
  ↓
[TTS 재생] + [점자 출력]
```

### 시나리오 2: 대화형 수업

```
[사용자: "이 시의 주제가 뭐야?"]
  ↓
[AI: "강의 대본에 따르면, 이 시는 자연의 아름다움을 노래한 작품입니다.
      시인은 봄날의 풍경을 통해 삶의 순환을 표현하고 있습니다.
      특히 2절에서 '꽃이 피고 지는 것'을 통해..."]
  ↓
[TTS 재생] + [점자 출력]
```

---

## 📊 장점 정리

1. **정확한 컨텍스트**: 강의 대본을 프롬프트로 사용 → 정확한 답변
2. **레슨별 맞춤**: 각 레슨마다 해당 강의 대본 기반 수업
3. **자연스러운 학습**: AI 선생님이 실제로 수업하는 것처럼
4. **확장 가능**: 다른 과목도 동일한 방식으로 적용 가능

---

## 🔧 구현 우선순위

### MVP (1강만)

1. **강의 대본 저장/조회** (필수)
   - 레슨에 강의 대본 텍스트 저장
   - API로 조회 가능하게

2. **AI 대화형 수업** (필수)
   - 사용자 질문 → 강의 대본 컨텍스트 포함 답변
   - 구현 시간: 2일

3. **AI 순차적 수업** (선택)
   - 강의 대본 순서대로 수업 진행
   - 구현 시간: 3일

---

## 💡 최종 정리

**핵심 아이디어**:
> 강의 대본(HWP)을 프롬프트 컨텍스트로 사용해서 AI가 각 레슨마다 수업 진행

**구현 방법**:
1. 레슨에 강의 대본 텍스트 저장
2. AI API에 강의 대본을 컨텍스트로 전달
3. 사용자 질문/진행 → AI가 강의 대본 기반으로 답변/수업

**사용자 경험**:
- AI 선생님이 실제로 수업하는 것처럼 느껴짐
- 강의 대본 내용과 정확히 일치하는 답변
- 레슨별 맞춤 수업

---

*작성일: 2024년 12월*
