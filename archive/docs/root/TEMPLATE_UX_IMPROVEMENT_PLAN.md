# 템플릿 생성 UI/UX 개선 계획

**날짜:** 2026-01-24
**목표:** 관리자가 5분 안에 완벽한 템플릿을 생성할 수 있도록

---

## 🎯 핵심 문제 (Current Pain Points)

### 1. **region_text_examples 입력이 어려움** 🔴 (Critical)
- **현재:** 수동으로 JSON 편집해야 함
- **문제:**
  - 어떤 텍스트를 입력해야 할지 모름
  - PDF를 보면서 복사/붙여넣기 반복
  - 오타/형식 오류 가능성
- **영향:** 섹션 추출 실패 → 이미지 저장 안 됨

### 2. **region_hints (좌표) 입력이 수동**
- **현재:** Y좌표 비율을 수동 입력 (0.0-1.0)
- **문제:**
  - PDF 좌표를 계산해야 함
  - 직관적이지 않음

### 3. **실시간 검증 부족**
- **현재:** 저장 후에야 오류 확인
- **문제:**
  - 여러 번 시도해야 함
  - 피드백 루프가 느림

### 4. **템플릿 재사용 어려움**
- **현재:** 처음부터 다시 생성
- **문제:**
  - 비슷한 교재도 처음부터 입력
  - 시간 낭비

---

## ✨ 개선 방안 (Improvements)

### 🎨 Phase 1: 즉시 적용 가능 (Quick Wins)

#### 1.1 **자동 텍스트 예시 추출** ⭐⭐⭐ (Most Important)

**기능:**
```
PDF 업로드
  ↓
자동으로 각 영역(concept, passage, problem)에서
텍스트 샘플 추출
  ↓
관리자 확인/수정
  ↓
저장
```

**구현:**
```typescript
// 새로운 API: /api/templates/extract-text-examples
POST /api/templates/extract-text-examples
Body: {
  pdf_file: File,
  subject: "literature",
  region_hints: {
    concept: {y_min: 0.11, y_max: 0.84},
    passage: {y_min: 0.12, y_max: 0.54},
    problem: {y_min: 0.10, y_max: 0.81}
  },
  sample_pages: [9, 15, 20]  // 대표 페이지
}

Response: {
  concept: ["갈래 고전 시가", "주제 아름다운", ...],
  passage: ["해(박두진)", "작품 이해", ...],
  problem: ["01 ~ 03", "다음 글을", ...]
}
```

**UI 변경:**
```
[TOC Wizard 단계 추가]

Step 1: 목차 붙여넣기 (기존)
Step 2: PDF 업로드 (새로운)
  → "텍스트 예시 자동 추출" 버튼
  → 로딩 3-5초
  → 추출된 예시 표시 (편집 가능)
Step 3: region_hints 설정 (기존, PDFBboxMarker 사용)
Step 4: 미리보기 및 저장
```

---

#### 1.2 **시각적 영역 선택 도구 개선**

**현재:** PDFBboxMarker 있음 ✅
**개선:**
```typescript
// PDFBboxMarker 개선 사항
<PDFBboxMarker
  mode="region_selection"  // 새로운 모드
  onRegionSelected={(region) => {
    // concept, passage, problem 영역을 드래그로 선택
    setRegionHints({
      ...regionHints,
      [region.type]: {
        y_min: region.y_min,
        y_max: region.y_max
      }
    });
  }}
  showGuidelines={true}  // 가이드라인 표시
  showTextOverlay={true}  // 텍스트 오버레이
/>
```

**UX:**
1. PDF 페이지 표시
2. "개념 영역 선택" 버튼 클릭
3. PDF에서 드래그하여 영역 선택
4. 자동으로 Y좌표 계산 및 저장
5. 선택한 영역 하이라이트 표시

---

#### 1.3 **실시간 검증 및 미리보기**

**기능:**
```typescript
// 템플릿 입력 시 실시간 검증
function TemplateRealtimeValidator() {
  const [validationResult, setValidationResult] = useState(null);

  useEffect(() => {
    // 디바운스 500ms
    const timer = setTimeout(async () => {
      const result = await templatesAPI.validate(editedTemplate);
      setValidationResult(result);
    }, 500);
    return () => clearTimeout(timer);
  }, [editedTemplate]);

  return (
    <div className="validation-panel">
      {validationResult?.warnings.map(w => (
        <div key={w.field} className="warning">
          ⚠️ {w.message}
        </div>
      ))}
      {validationResult?.errors.map(e => (
        <div key={e.field} className="error">
          ❌ {e.message}
        </div>
      ))}
    </div>
  );
}
```

**검증 항목:**
- ✅ region_text_examples 비어있지 않음
- ✅ region_hints 범위 유효성 (0.0-1.0)
- ✅ 패턴 정규식 유효성
- ✅ TOC 강의 목록 일관성
- ⚠️ 예상 섹션 수 (너무 적거나 많으면 경고)

---

#### 1.4 **템플릿 복사 및 수정**

**UI:**
```typescript
<TemplateManager>
  <TemplateList>
    {templates.map(t => (
      <TemplateCard key={t.name}>
        <h3>{t.name}</h3>
        <p>{t.description}</p>
        <Actions>
          <Button onClick={() => editTemplate(t)}>수정</Button>
          <Button onClick={() => duplicateTemplate(t)}>
            복사 📋
          </Button>
          <Button onClick={() => deleteTemplate(t)}>삭제</Button>
        </Actions>
      </TemplateCard>
    ))}
  </TemplateList>
</TemplateManager>
```

**복사 기능:**
- 기존 템플릿 선택 → "복사" 클릭
- 자동으로 이름 변경 (e.g., "...\_2026" → "...\_2027")
- 수정 후 저장

---

### 🚀 Phase 2: 중기 개선 (Advanced Features)

#### 2.1 **AI 기반 자동 완성**

**기능:**
```typescript
// GPT로 부족한 정보 자동 생성
POST /api/templates/autocomplete
Body: {
  template: {...},  // 기존 템플릿 (일부만 입력됨)
  pdf_sample: "...",  // 샘플 텍스트
  autocomplete_fields: ["region_text_examples", "patterns"]
}

Response: {
  suggested_region_text_examples: {...},
  suggested_patterns: [...],
  confidence: 0.85
}
```

**UX:**
- "AI 자동 완성" 버튼
- 로딩 10-15초
- 제안된 내용 표시
- 수락/거절/수정 가능

---

#### 2.2 **배치 페이지 분석**

**기능:**
```typescript
// 여러 페이지를 한 번에 분석
POST /api/templates/analyze-pages
Body: {
  pdf_file: File,
  page_numbers: [9, 15, 20, 25, 30],
  region_hints: {...}
}

Response: {
  pages: [
    {
      page_num: 9,
      detected_sections: [
        {type: "concept", title: "...", bbox: [...]},
        {type: "passage", title: "...", bbox: [...]}
      ]
    },
    ...
  ],
  statistics: {
    avg_concept_count: 2.5,
    avg_passage_count: 1.8,
    consistency_score: 0.92
  }
}
```

**UX:**
- "페이지 분석" 탭
- 여러 페이지 선택
- 자동 분석 실행
- 결과 비교 (일관성 확인)

---

#### 2.3 **인터랙티브 튜토리얼**

**기능:**
```typescript
<TemplateCreationTutorial>
  <Step1>
    <Title>목차 붙여넣기</Title>
    <Description>
      PDF에서 목차를 복사하여 붙여넣으세요.
      강의 번호가 포함된 라인이 자동으로 추출됩니다.
    </Description>
    <Example>
      1강 | 시의 표현과 형식
      2강 | 시의 내용
      ...
    </Example>
  </Step1>

  <Step2>
    <Title>영역 선택</Title>
    <GIF src="/tutorial/region-selection.gif" />
    <Description>
      개념, 본문, 문제 영역을 드래그하여 선택하세요.
    </Description>
  </Step2>

  <Step3>...</Step3>
</TemplateCreationTutorial>
```

---

#### 2.4 **템플릿 품질 점수**

**기능:**
```typescript
interface TemplateQualityScore {
  overall_score: number;  // 0-100
  completeness: number;  // 필수 필드 완성도
  accuracy: number;  // 테스트 결과 정확도
  coverage: number;  // region_text_examples 커버리지
  suggestions: string[];  // 개선 제안
}
```

**UI:**
```
템플릿 품질: 85/100 ⭐⭐⭐⭐

✅ 완성도: 95% (필수 필드 모두 입력)
⚠️ 정확도: 78% (테스트 권장)
✅ 커버리지: 90% (예시 충분)

개선 제안:
- passage 영역의 텍스트 예시를 3개 더 추가하세요
- 패턴 테스트를 실행하여 정확도를 확인하세요
```

---

### 🎨 Phase 3: 장기 개선 (Future Vision)

#### 3.1 **비주얼 템플릿 빌더**

**컨셉:**
```
┌─────────────────────────────────────┐
│ PDF Preview (좌측)                  │
│ ┌───────────────────────────────┐   │
│ │                               │   │
│ │  [개념 영역 - 하이라이트]    │   │
│ │                               │   │
│ │  [본문 영역 - 하이라이트]    │   │
│ │                               │   │
│ │  [문제 영역 - 하이라이트]    │   │
│ │                               │   │
│ └───────────────────────────────┘   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 설정 패널 (우측)                    │
│ ┌───────────────────────────────┐   │
│ │ 개념 영역 ✅                  │   │
│ │ Y좌표: 0.11 - 0.84           │   │
│ │ 텍스트 예시 (3개):            │   │
│ │ - 갈래 고전 시가              │   │
│ │ - 주제 아름다운               │   │
│ │ - 특징 화자의                 │   │
│ │ [+ 예시 추가]                 │   │
│ └───────────────────────────────┘   │
└─────────────────────────────────────┘
```

**기능:**
- 드래그 앤 드롭으로 영역 선택
- 클릭으로 텍스트 선택
- 실시간 미리보기

---

#### 3.2 **머신러닝 기반 제안**

**기능:**
```python
# 백엔드: 기존 템플릿 학습
from sklearn.ensemble import RandomForestClassifier

model = TemplateRecommender()
model.train(existing_templates)  # 기존 템플릿 학습

# 새 PDF 분석
suggestions = model.recommend(new_pdf_sample)
# → region_hints, 예상 강의 수, 패턴 등 자동 제안
```

---

#### 3.3 **협업 기능**

**기능:**
- 템플릿 댓글/리뷰
- 버전 관리 (Git 스타일)
- 변경 이력 추적
- 템플릿 공유 (커뮤니티)

---

## 📋 우선순위 (Priority)

### 🔥 즉시 구현 (이번 주)

1. **자동 텍스트 예시 추출** (1-2일)
   - API: `/api/templates/extract-text-examples`
   - UI: TOC Wizard에 단계 추가

2. **실시간 검증** (1일)
   - API: `/api/templates/validate`
   - UI: TemplateEditor에 검증 패널 추가

3. **템플릿 복사 기능** (0.5일)
   - UI: TemplateManager에 "복사" 버튼

### ⭐ 단기 구현 (다음 주)

4. **시각적 영역 선택 개선** (2일)
   - PDFBboxMarker 개선
   - 가이드라인 및 오버레이

5. **배치 페이지 분석** (2-3일)
   - API: `/api/templates/analyze-pages`
   - UI: 새 탭 추가

### 🚀 중기 구현 (다음 달)

6. **AI 자동 완성** (5-7일)
7. **템플릿 품질 점수** (3-4일)
8. **인터랙티브 튜토리얼** (2-3일)

---

## 🎯 구현 가이드

### Step 1: 자동 텍스트 예시 추출 API

**백엔드 (`backend/app/routers/templates.py`):**

```python
@router.post("/templates/extract-text-examples")
async def extract_text_examples(
    pdf_file: UploadFile = File(...),
    subject: str = Form(...),
    region_hints: str = Form(...),  # JSON string
    sample_pages: str = Form("9,15,20")  # comma-separated
):
    """PDF에서 영역별 텍스트 예시 자동 추출"""
    import json
    from app.infrastructure.pdf.extractors import PdfplumberExtractor

    # 임시 저장
    temp_pdf = Path(f"/tmp/{pdf_file.filename}")
    with open(temp_pdf, "wb") as f:
        f.write(await pdf_file.read())

    # OCR 추출
    extractor = PdfplumberExtractor()
    ocr_data = extractor.extract(temp_pdf)

    # 영역별 텍스트 수집
    region_hints_dict = json.loads(region_hints)
    sample_page_nums = [int(p) for p in sample_pages.split(",")]

    region_texts = {
        "concept": [],
        "passage": [],
        "problem": []
    }

    for page_data in ocr_data:
        if page_data['page_num'] not in sample_page_nums:
            continue

        page_height = page_data.get('page_height', 1400.0)
        texts = page_data.get('text', [])
        tops = page_data.get('top', [])

        for text, top in zip(texts, tops):
            y_ratio = top / page_height

            # 각 영역에 속하는지 확인
            for region_type, hints in region_hints_dict.items():
                if hints['y_min'] <= y_ratio <= hints['y_max']:
                    if len(text) >= 5:  # 최소 5자
                        region_texts[region_type].append(text)

    # 중복 제거 및 상위 10개 선택
    for region_type in region_texts:
        unique_texts = list(set(region_texts[region_type]))
        region_texts[region_type] = unique_texts[:10]

    return {
        "region_text_examples": region_texts,
        "sample_pages": sample_page_nums,
        "message": "텍스트 예시가 추출되었습니다."
    }
```

---

### Step 2: 프론트엔드 통합

**TOCTemplateWizard 수정:**

```typescript
// Step 추가: PDF 업로드 및 텍스트 예시 추출
const [step, setStep] = useState(1);  // 1: TOC, 2: PDF, 3: Region, 4: Review
const [extractedExamples, setExtractedExamples] = useState(null);

const handleExtractTextExamples = async () => {
  if (!pdfFile || !parsingGuideRegions.length) {
    onSpeak?.('PDF와 영역 정보를 먼저 입력해주세요.');
    return;
  }

  setExtracting(true);
  try {
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    formData.append('subject', subject);
    formData.append('region_hints', JSON.stringify({
      concept: parsingGuideRegions.find(r => r.label === 'concept')?.bbox,
      passage: parsingGuideRegions.find(r => r.label === 'passage')?.bbox,
      problem: parsingGuideRegions.find(r => r.label === 'problem')?.bbox
    }));
    formData.append('sample_pages', '9,15,20');

    const result = await templatesAPI.extractTextExamples(formData);
    setExtractedExamples(result.region_text_examples);
    onSpeak?.('텍스트 예시가 자동으로 추출되었습니다.');
    setStep(3);  // 다음 단계로
  } catch (err: any) {
    onSpeak?.(err.message || '텍스트 예시 추출 실패');
  } finally {
    setExtracting(false);
  }
};

// UI 렌더링
{step === 2 && (
  <div className="step step-2">
    <h3>Step 2: PDF 업로드 및 텍스트 예시 추출</h3>

    <input
      type="file"
      accept=".pdf"
      onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
    />

    <button
      onClick={handleExtractTextExamples}
      disabled={!pdfFile || extracting}
    >
      {extracting ? '추출 중...' : '텍스트 예시 자동 추출 ✨'}
    </button>

    {extractedExamples && (
      <div className="extracted-examples">
        <h4>추출된 텍스트 예시 (편집 가능)</h4>
        {Object.entries(extractedExamples).map(([type, examples]) => (
          <div key={type} className="region-examples">
            <h5>{type}</h5>
            <ul>
              {examples.map((ex, i) => (
                <li key={i}>
                  <input
                    value={ex}
                    onChange={(e) => {
                      const newExamples = {...extractedExamples};
                      newExamples[type][i] = e.target.value;
                      setExtractedExamples(newExamples);
                    }}
                  />
                  <button onClick={() => {
                    const newExamples = {...extractedExamples};
                    newExamples[type].splice(i, 1);
                    setExtractedExamples(newExamples);
                  }}>
                    ❌
                  </button>
                </li>
              ))}
            </ul>
            <button onClick={() => {
              const newExamples = {...extractedExamples};
              newExamples[type].push('');
              setExtractedExamples(newExamples);
            }}>
              + 예시 추가
            </button>
          </div>
        ))}
      </div>
    )}
  </div>
)}
```

---

## 📝 체크리스트

관리자가 템플릿 생성 시 확인할 사항:

- [ ] **목차 텍스트** 입력 (강의 제목 포함)
- [ ] **PDF 업로드** (대표 페이지 분석용)
- [ ] **텍스트 예시 자동 추출** ✨ (또는 수동 입력)
  - [ ] 개념(concept) 예시 5-10개
  - [ ] 본문(passage) 예시 5-10개
  - [ ] 문제(problem) 예시 5-10개
- [ ] **영역 좌표** (region_hints) 설정
  - [ ] 드래그로 선택 또는 수동 입력
- [ ] **실시간 검증** 통과
  - [ ] 경고 0개
  - [ ] 에러 0개
- [ ] **템플릿 테스트** 실행 (선택)
- [ ] **저장 및 적용**

---

## 🎨 UI 목업 (Mockup)

### Before (현재)
```
┌──────────────────────────────────┐
│ 템플릿 생성                       │
├──────────────────────────────────┤
│ 이름: [____________]             │
│ 과목: [literature ▼]             │
│ 목차: [____________]             │
│      [____________]             │
│      [____________]             │
│                                  │
│ region_hints (JSON):             │
│ {                                │
│   "concept": {                   │
│     "y_min": 0.11,              │
│     "y_max": 0.84               │
│   }                              │
│ }                                │
│                                  │
│ [생성]  [취소]                   │
└──────────────────────────────────┘
```

### After (개선)
```
┌──────────────────────────────────────────────────┐
│ 템플릿 마법사 🪄                Step 2/4          │
├──────────────────────────────────────────────────┤
│ ◉ 목차 입력  → ◉ PDF 분석 → ◯ 영역 설정 → ◯ 완료 │
├──────────────────────────────────────────────────┤
│                                                  │
│ PDF 업로드 및 자동 분석                          │
│ ┌────────────────────────────────────────┐      │
│ │ 📄 수능특강_문학_2026.pdf              │      │
│ │ ✅ 업로드 완료 (35.2 MB)               │      │
│ └────────────────────────────────────────┘      │
│                                                  │
│ [✨ 텍스트 예시 자동 추출]  (추천)              │
│                                                  │
│ 또는 수동 입력:                                  │
│ ┌────────────────────────────────────────┐      │
│ │ 개념 영역 예시 (5개 이상 권장)          │      │
│ │ • 갈래 고전 시가, 가사, 연시조          │      │
│ │ • 주제 아름다운 자연에 묻혀 사는        │      │
│ │ • 특징 화자의 정서가                    │      │
│ │ [+ 추가]                               │      │
│ └────────────────────────────────────────┘      │
│                                                  │
│ ✅ 검증 통과 (품질 점수: 92/100)                │
│                                                  │
│ [◀ 이전]  [다음 ▶]                             │
└──────────────────────────────────────────────────┘
```

---

**작성자:** Claude Sonnet 4.5
**버전:** 1.0
**날짜:** 2026-01-24
