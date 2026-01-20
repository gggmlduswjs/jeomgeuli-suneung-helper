# PDF 내용 구조화 및 UI/UX 표시

## 🎯 목적

수능특강 PDF의 내용(개념 설명, 작품, 문제)을 UI에 표시하고 AI가 읽어주도록 구조화

---

## 📋 PDF 내용 구조 (수능특강 문학 1강 예시)

### 1. 개념 설명 섹션

**예시: 시적 표현**
- 제목: "1 시적 표현"
- 하위 개념:
  - (1) 시적 표현의 개념
  - (2) 시적 표현의 여러 가지 효과

**예시: 시의 형식**
- 제목: "2 시의 형식"
- 하위 개념:
  - (1) 시의 형식의 개념과 특성
  - (2) 시의 형식의 여러 층위

### 2. 작품 섹션

**예시: 박두진 〈해〉**
- 작품 제목: "해"
- 작가: 박두진
- 작품 내용: 시 전문
- 분석 포인트: 표현 기법, 이미지 대립 등

### 3. 문제 섹션

**예시: 문제 01**
- 문제 유형: 다중 선택
- 문제 지문: "윗글에 대한 설명으로 적절하지 않은 것은?"
- 선택지: ①~⑤
- 정답: ②번

**예시: 문제 02**
- 문제 유형: O/X 판단
- 문제 지문: "종결 어미의 기능에 대한 이해"
- 하위 문제: (1)~(4)

**예시: 문제 03**
- 문제 유형: 빈칸 채우기
- 문제 지문: "㉠~㉤에 들어갈 적절한 말을 찾아 쓰시오"

---

## 🔧 구현 구조

### 1. 데이터 모델

**Unit 모델 확장** (이미 있음):
```python
# api/app/db/models.py
class Unit(Base):
    unit_id: str
    lesson_id: str
    type: UnitType  # CONCEPT_CORE, PASSAGE, QUESTION
    title: str
    content_text: str  # 개념 설명 또는 작품 내용
    question_stem: str  # 문제 지문 (문제인 경우)
    question_choices: str  # JSON: ["① ...", "② ..."]
    question_answer: int  # 정답 번호
    pdf_page_number: int  # PDF 페이지 번호
    pdf_section: str  # "concept", "work", "question"
```

### 2. PDF 구조 파싱

**PDF에서 구조 추출**:
```python
# api/app/services/pdf_extract/literature_extractor.py (수정)
class LiteraturePDFExtractor:
    def extract_structured_content(self, pdf_path: Path) -> Dict:
        """
        PDF에서 구조화된 내용 추출
        
        Returns:
            {
                'concepts': [
                    {
                        'title': '시적 표현',
                        'subsections': [...],
                        'content': '...',
                        'page': 8
                    }
                ],
                'works': [
                    {
                        'title': '해',
                        'author': '박두진',
                        'content': '시 전문...',
                        'page': 12
                    }
                ],
                'questions': [
                    {
                        'number': '01',
                        'type': 'multiple_choice',
                        'stem': '...',
                        'choices': [...],
                        'answer': 2,
                        'page': 13
                    }
                ]
            }
        """
```

### 3. UI 컴포넌트

**프론트엔드 표시**:
```typescript
// apps/web/src/components/unit/UnitViewer.tsx (수정)
export default function UnitViewer({ unit }: { unit: Unit }) {
  // 개념 설명 표시
  if (unit.type === 'CONCEPT_CORE') {
    return <ConceptViewer content={unit.content_text} />;
  }
  
  // 작품 표시
  if (unit.type === 'PASSAGE') {
    return <WorkViewer 
      title={unit.title}
      content={unit.content_text}
      author={unit.author}
    />;
  }
  
  // 문제 표시
  if (unit.type === 'QUESTION') {
    return <QuestionViewer
      stem={unit.question_stem}
      choices={unit.question_choices}
      answer={unit.question_answer}
    />;
  }
}
```

### 4. AI가 읽어주기

**AI 강의 선생님이 PDF 내용도 읽어주기**:
```python
# api/app/services/ai_lecture_teacher.py (수정)
class AILectureTeacher:
    async def teach_unit(self, unit: Unit, lesson_script: str) -> str:
        """
        Unit 내용을 강의 대본과 함께 AI가 설명
        
        Args:
            unit: 학습 단위 (개념/작품/문제)
            lesson_script: 해당 레슨의 강의 대본
            
        Returns:
            AI 설명 텍스트
        """
        if unit.type == 'CONCEPT_CORE':
            prompt = f"""당신은 수능 문학 선생님입니다.

강의 대본:
{lesson_script}

다음은 교재의 개념 설명입니다:
{unit.content_text}

이 개념을 학생에게 설명해주세요.
강의 대본 내용을 참고해서 친절하게 설명하세요.
"""
        
        elif unit.type == 'PASSAGE':
            prompt = f"""당신은 수능 문학 선생님입니다.

강의 대본:
{lesson_script}

다음은 작품입니다:
제목: {unit.title}
작가: {unit.author}
내용: {unit.content_text}

이 작품을 분석해서 설명해주세요.
강의 대본의 분석 방법을 따라 설명하세요.
"""
        
        elif unit.type == 'QUESTION':
            prompt = f"""당신은 수능 문학 선생님입니다.

강의 대본:
{lesson_script}

다음은 문제입니다:
{unit.question_stem}
선택지:
{unit.question_choices}

이 문제를 풀이해주세요.
강의 대본의 풀이 방법을 따라 설명하세요.
"""
        
        response = self.client.chat.completions.create(...)
        return response.choices[0].message.content
```

---

## 💡 사용자 경험

### 시나리오 1: 개념 설명 학습

```
[사용자: "시적 표현 개념 보기"]
  ↓
[UI 표시]
  - 제목: "1 시적 표현"
  - (1) 시적 표현의 개념
  - (2) 시적 표현의 여러 가지 효과
  ↓
[AI 설명 시작]
AI: "시적 표현은 시의 주제나 화자의 정서를 형상화하는 데 기여하는 
     언어적 표현입니다. 비유, 상징, 역설 등의 표현 기법이 있습니다..."
  ↓
[TTS 재생] + [점자 출력]
```

### 시나리오 2: 작품 분석

```
[사용자: "박두진 '해' 작품 보기"]
  ↓
[UI 표시]
  - 작품 제목: "해"
  - 작가: 박두진
  - 작품 내용: 시 전문
  ↓
[AI 분석 시작]
AI: "이 작품은 해를 상징으로 사용하여 밝음과 어둠의 이미지 대립을 
     보여줍니다. 반복과 변주를 통해 화자의 소망을 강조하고 있습니다..."
  ↓
[TTS 재생] + [점자 출력]
```

### 시나리오 3: 문제 풀이

```
[사용자: "문제 01 풀기"]
  ↓
[UI 표시]
  - 문제 지문
  - 선택지 ①~⑤
  ↓
[AI 풀이 시작]
AI: "이 문제는 박두진의 '해' 작품에 대한 설명을 묻고 있습니다.
     각 선택지를 하나씩 살펴보겠습니다..."
  ↓
[사용자 답안 선택]
  ↓
[AI 정답 확인]
AI: "정답은 ②번입니다. 나열의 방식을 활용하여 반성적 태도를 
     드러낸다는 설명은 적절하지 않습니다..."
  ↓
[TTS 재생] + [점자 출력]
```

---

## 🔧 구현 위치

### 백엔드

1. **PDF 구조 파싱**:
   - `api/app/services/pdf_extract/literature_extractor.py` (수정)
   - 개념/작품/문제 구분 로직 추가

2. **Unit 생성**:
   - `api/app/services/curriculum_generator.py` (수정)
   - PDF 내용을 Unit으로 변환

3. **AI 강의 선생님**:
   - `api/app/services/ai_lecture_teacher.py` (수정)
   - Unit 타입별로 다른 프롬프트 사용

### 프론트엔드

1. **Unit 표시 컴포넌트**:
   - `apps/web/src/components/unit/ConceptViewer.tsx` (새로 생성)
   - `apps/web/src/components/unit/WorkViewer.tsx` (새로 생성)
   - `apps/web/src/components/unit/QuestionViewer.tsx` (수정)

2. **AI 수업 진행**:
   - `apps/web/src/hooks/useAILectureTeacher.ts` (수정)
   - Unit별 AI 설명 호출

---

## 📊 데이터 흐름

```
PDF 파일
  ↓
[PDF 구조 파싱]
  - 개념 설명 추출
  - 작품 추출
  - 문제 추출
  ↓
[Unit 생성]
  - CONCEPT_CORE: 개념 설명
  - PASSAGE: 작품
  - QUESTION: 문제
  ↓
[DB 저장]
  ↓
[사용자 학습]
  - Unit 선택
  - UI 표시
  - AI 설명 요청
  - TTS 재생 + 점자 출력
```

---

## 🎯 핵심 포인트

1. **PDF 구조 인식**: 개념/작품/문제 자동 구분
2. **Unit 기반 표시**: 각 타입별 맞춤 UI
3. **AI 통합 설명**: 강의 대본 + PDF 내용 함께 설명
4. **접근성**: TTS + 점자 출력

---

*작성일: 2024년 12월*
