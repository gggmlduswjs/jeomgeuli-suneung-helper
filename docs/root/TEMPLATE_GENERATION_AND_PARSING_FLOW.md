# 템플릿 생성 및 파싱 흐름 가이드

## 📋 전체 개요

이 시스템은 **사전 구조 가이드 기반 PDF 파싱 템플릿 생성**을 통해 고정밀도 자동 파싱을 가능하게 합니다.

핵심 원칙: **"파싱 정확도는 파싱 시작 전에 결정된다"**

---

## 🔄 전체 워크플로우

```
[관리자] → [템플릿 생성] → [템플릿 저장] → [PDF 업로드] → [파싱] → [결과]
   ↓            ↓              ↓              ↓           ↓        ↓
설문조사    GPT 생성      JSON 저장      템플릿 매칭   region_hints   구조화된
+ bbox      (TOC 기반)    (재사용)       + 파싱        활용         데이터
마킹
```

---

## 1️⃣ 템플릿 생성 흐름 (프론트엔드 → 백엔드)

### Step 1: 관리자 입력 (TOCTemplateWizard)

**위치**: `frontend/src/components/admin/TOCTemplateWizard.tsx`

관리자가 다음 정보를 입력합니다:

1. **기본 정보**
   - 과목 (literature, math1, english)
   - 연도 (2026)
   - 템플릿 이름
   - 설명

2. **커리큘럼 구조 설문** (선택)
   ```typescript
   {
     is_lecture_based: true,
     lecture_units: ["concept", "passage", "problem"],
     unit_order: ["concept", "passage", "problem"]
   }
   ```

3. **TOC 텍스트** (필수)
   - PDF 목차 페이지를 복사해서 붙여넣기
   - 예: `1강 | 시의 표현과 형식\n해 (박두진) 009\n...`

4. **TOC 예시** (필수)
   - 강의 라인 예시: `["1강 | 시의 표현과 형식", "2강 | 시의 내용"]`
   - 비강의 라인 예시 (선택): `["정답과 해설", "부록"]`

5. **파싱 가이드 영역** (선택, 권장)
   - PDF 파일 업로드
   - 3-5개 대표 페이지 선택
   - 각 페이지에서 드래그로 영역 마킹:
     - 개념 영역 (concept)
     - 본문 영역 (passage)
     - 문제 영역 (problem)

### Step 2: bbox 마킹 (PDFBboxMarker)

**위치**: `frontend/src/components/admin/PDFBboxMarker.tsx`

1. PDF 파일을 이미지로 렌더링
2. 사용자가 드래그로 영역 선택
3. 레이블 지정 (concept/passage/problem)
4. bbox 좌표 저장: `[x_min, y_min, x_max, y_max]` (픽셀 단위)

**예시**:
```typescript
{
  page: 12,
  label: "concept",
  bbox: [120, 90, 980, 320]  // 픽셀 좌표
}
```

### Step 3: API 요청 전송

**위치**: `frontend/src/services/templates.ts`

```typescript
const request: GenerateTemplateFromTOCRequest = {
  subject: "literature",
  name: "ebs_수능특강_literature_2026",
  version: "2026",
  year: 2026,
  book_name: "EBS 수능특강 문학",
  toc_text: "...",
  curriculum_survey: { ... },
  parsing_guide_regions: [
    { page: 12, label: "concept", bbox: [120, 90, 980, 320] },
    { page: 14, label: "passage", bbox: [110, 340, 980, 820] },
    { page: 16, label: "problem", bbox: [120, 600, 980, 980] }
  ],
  toc_lecture_line_examples: [...],
  expected_lecture_count: 73
};

await templatesAPI.generateFromToc(request);
```

---

## 2️⃣ 백엔드 템플릿 생성 (백엔드)

### Step 1: Region Hints 계산

**위치**: `backend/app/routers/templates.py` → `_compute_region_hints()`

bbox 좌표를 페이지 비율(0.0-1.0)로 정규화:

```python
# 입력: parsing_guide_regions
[
  { "page": 12, "label": "concept", "bbox": [120, 90, 980, 320] },
  { "page": 14, "label": "concept", "bbox": [110, 100, 970, 310] },
  { "page": 14, "label": "passage", "bbox": [110, 340, 980, 820] }
]

# 출력: region_hints
{
  "concept": { "y_min": 0.05, "y_max": 0.35 },  # 평균/범위 계산
  "passage": { "y_min": 0.3, "y_max": 0.7 }
}
```

**계산 로직**:
1. 각 레이블별로 bbox 그룹화
2. y_min, y_max를 페이지 높이로 나누어 비율 계산
3. 레이블별 최소/최대 범위 집계

### Step 2: 프롬프트 빌드

**위치**: `backend/app/routers/templates.py` → `_build_toc_prompt()`

마스터 프롬프트 구조로 LLM 요청 프롬프트 생성:

```
## [SYSTEM PROMPT]
You are an expert in educational PDF structure analysis...

## [USER INPUTS]
### 1️⃣ PDF METADATA
{ "subject": "literature", "year": 2026, ... }

### 2️⃣ CURRICULUM STRUCTURE SURVEY
{ "is_lecture_based": true, "unit_order": [...] }

### 3️⃣ TABLE OF CONTENTS (TOC TEXT)
1강 | 시의 표현과 형식
...

### 4️⃣ PARSING GUIDE REGIONS
Computed region_hints (normalized ratios):
{
  "concept": { "y_min": 0.05, "y_max": 0.35 },
  "passage": { "y_min": 0.3, "y_max": 0.7 }
}
```

### Step 3: LLM 호출 (OpenAI)

**위치**: `backend/app/routers/templates.py` → `_generate_template_from_toc_via_openai()`

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You output JSON only."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.2,
    response_format={"type": "json_object"}
)
```

**LLM 출력 예시**:
```json
{
  "patterns": {
    "toc_lecture_patterns": ["^\\d+강\\s*[|:]\\s*(.+)$"],
    "concept_title_patterns": ["^(개념|핵심 정리)"],
    "problem_number_pattern": "^(\\d+\\.|①|②|③)"
  },
  "config": {
    "unit_order": ["concept", "passage", "problem"],
    "region_hints": {
      "concept": { "y_min": 0.05, "y_max": 0.35 },
      "passage": { "y_min": 0.3, "y_max": 0.7 }
    },
    "toc_end_page": 7,
    "start_content_page": 8,
    "paragraph_y_threshold": 25
  }
}
```

### Step 4: 템플릿 저장

**위치**: `backend/app/infrastructure/pdf/parsers/template.py`

```python
template = ParsingTemplate(
    name="ebs_수능특강_literature_2026",
    subject="literature",
    version="2026",
    patterns={...},
    config={
        "toc_end_page": 7,
        "start_content_page": 8,
        "paragraph_y_threshold": 25,
        "unit_order": ["concept", "passage", "problem"],
        "region_hints": {
            "concept": { "y_min": 0.05, "y_max": 0.35 },
            "passage": { "y_min": 0.3, "y_max": 0.7 },
            "problem": { "y_min": 0.6, "y_max": 0.95 }
        }
    }
)

template.save(template_dir)  # → backend/data/templates/literature_ebs_수능특강_literature_2026.json
```

---

## 3️⃣ PDF 파싱 시 템플릿 활용 (백엔드)

### Step 1: 템플릿 매칭

**위치**: `backend/app/infrastructure/pdf/parsers/template_manager.py`

PDF 업로드 시:

1. OCR 데이터에서 첫 3-5페이지 텍스트 추출
2. 과목별 템플릿 목록 조회
3. 각 템플릿과 신뢰도 계산:
   - 강의 제목 패턴 매칭률 (40%)
   - 문제 번호 패턴 매칭률 (30%)
   - 개념/섹션 패턴 매칭률 (20%)
   - 템플릿 기본 신뢰도 (10%)
4. 신뢰도 >= 0.85인 템플릿 선택

### Step 2: 템플릿 → Config 변환

**위치**: `backend/app/infrastructure/pdf/parsers/literature.py` → `_template_to_config()`

```python
def _template_to_config(self, template: ParsingTemplate) -> Dict[str, Any]:
    config = {
        'lecture_title_patterns': template.patterns.get('lecture_title_patterns', []),
        'toc_lecture_patterns': template.patterns.get('toc_lecture_patterns', []),
        'concept_title_patterns': template.patterns.get('concept_title_patterns', []),
        'problem_number_pattern': template.patterns.get('problem_number_pattern', ''),
        'toc_end_page': template.config.get('toc_end_page', 7),
        'start_content_page': template.config.get('start_content_page', 8),
        'paragraph_y_threshold': template.config.get('paragraph_y_threshold', 25),
        # ✨ 새로 추가된 필드
        'unit_order': template.config.get('unit_order', ['concept', 'passage', 'problem']),
        'region_hints': template.config.get('region_hints', {})
    }
    return config
```

### Step 3: 섹션 추출 (region_hints 활용)

**위치**: `backend/app/infrastructure/pdf/parsers/section_extractor.py`

#### 3-1. 패턴 매칭으로 섹션 추출

```python
def _extract_by_pattern(self, lecture_ocr_data):
    sections = []
    
    for ocr_data in lecture_ocr_data:
        # 텍스트 라인 그룹화
        lines = BaseParser.group_lines(ocr_data, y_threshold=10)
        
        for line in lines:
            line_text = BaseParser.join_line_text(line)
            
            # 패턴 매칭으로 타입 결정
            if re.match(r'^(\d+)\s*[\.]\s*([가-힣]+)$', line_text):
                section_type = "concept"
            elif matches_content_pattern(line_text):
                section_type = "content"
            
            # bbox 계산
            bbox = BaseParser.get_line_bbox(line)
            
            # ✨ region_hints로 타입 보정
            if bbox and self.region_hints:
                page_height = ocr_data.get('page_height', 1400.0)
                y_center = (bbox[1] + bbox[3]) / 2.0  # y_min과 y_max의 중간
                y_ratio = y_center / page_height
                
                # region_hint로 분류
                hint_type = self._classify_by_region_hint(y_ratio, page_height)
                if hint_type:
                    # 패턴 매칭 결과와 충돌하지 않으면 타입 변경
                    if section_type == 'content' and hint_type == 'passage':
                        section_type = 'passage'  # content → passage
                    elif not section_type:
                        section_type = hint_type  # 타입이 없으면 힌트 사용
            
            sections.append({
                "title": line_text,
                "type": section_type,
                "page": page_num,
                "bbox": bbox
            })
    
    return sections
```

#### 3-2. Region Hints 분류 로직

```python
def _classify_by_region_hint(self, y_ratio: float, page_height: float) -> Optional[str]:
    """y 좌표 비율로 단위 타입 분류"""
    if not self.region_hints:
        return None
    
    # unit_order 순서대로 확인 (concept → passage → problem)
    for unit_type in self.unit_order:
        if unit_type not in self.region_hints:
            continue
        
        hint = self.region_hints[unit_type]
        y_min = hint.get('y_min', 0.0)  # 예: 0.05
        y_max = hint.get('y_max', 1.0)  # 예: 0.35
        
        # y_ratio가 힌트 범위 내에 있으면 해당 단위 타입 반환
        if y_min <= y_ratio <= y_max:
            return unit_type  # "concept"
    
    return None
```

**예시**:
- 텍스트가 페이지 상단 10% 위치 (y_ratio = 0.1)
- region_hints: `{"concept": {"y_min": 0.05, "y_max": 0.35}}`
- → `0.05 <= 0.1 <= 0.35` → `"concept"` 반환

### Step 4: 최종 결과

**위치**: `backend/app/infrastructure/pdf/parsers/literature.py` → `extract_sections()`

```python
def extract_sections(self, lecture_ocr_data):
    extractor = ImprovedSectionExtractor(
        config=self.config,  # region_hints 포함
        parser=self,
        enable_ai=False
    )
    
    result = extractor.extract(lecture_ocr_data)
    
    # 결과 예시:
    # [
    #   {"title": "1. 시적 표현", "type": "concept", "page": 12, "bbox": [...]},
    #   {"title": "작품으로 이해하기", "type": "passage", "page": 14, "bbox": [...]},
    #   {"title": "①", "type": "problem", "page": 16, "bbox": [...]}
    # ]
    
    return result.sections
```

---

## 📊 데이터 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 템플릿 생성 (관리자)                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ TOCTemplateWizard (프론트엔드)        │
    │ - TOC 텍스트 입력                     │
    │ - 커리큘럼 설문                       │
    │ - PDF 업로드 + bbox 마킹              │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ PDFBboxMarker (프론트엔드)            │
    │ - 드래그로 영역 선택                  │
    │ - 레이블 지정 (concept/passage/problem)│
    │ - bbox: [x_min, y_min, x_max, y_max] │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ POST /templates/generate-from-toc     │
    │ (백엔드 API)                          │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ _compute_region_hints()              │
    │ bbox → 페이지 비율 정규화            │
    │ [120, 90, 980, 320]                  │
    │ → {"y_min": 0.05, "y_max": 0.35}    │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ _build_toc_prompt()                  │
    │ 마스터 프롬프트 구조로 LLM 요청 생성   │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ OpenAI GPT-4o-mini                   │
    │ JSON 템플릿 생성                      │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ ParsingTemplate.save()               │
    │ → backend/data/templates/            │
    │   literature_ebs_수능특강_2026.json   │
    └──────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 2. PDF 파싱 (자동)                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ PDF 업로드                            │
    │ POST /books/upload                    │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ TemplateManager.match_template()     │
    │ - OCR 텍스트와 템플릿 신뢰도 계산     │
    │ - 신뢰도 >= 0.85인 템플릿 선택        │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ LiteratureParser._template_to_config()│
    │ 템플릿 → config 변환                  │
    │ (region_hints 포함)                   │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ ImprovedSectionExtractor.extract()   │
    │ - 패턴 매칭으로 섹션 추출             │
    │ - region_hints로 타입 보정            │
    │   (y 좌표 → 단위 타입)                │
    └──────────────────────────────────────┘
                          ↓
    ┌──────────────────────────────────────┐
    │ 최종 결과                             │
    │ - 강의 목록                           │
    │ - 섹션 목록 (concept/passage/problem) │
    │ - 정확도 향상 (region_hints 활용)      │
    └──────────────────────────────────────┘
```

---

## 🎯 핵심 포인트

### 1. 사전 구조 가이드 우선
- 파싱 **전**에 템플릿 생성
- 최소한의 인간 개입 (설문조사 + bbox 마킹)
- 자동화된 파싱 정확도 향상

### 2. Region Hints의 역할
- **bbox 마킹** → **페이지 비율** → **파싱 시 y 좌표 기반 타입 분류**
- 패턴 매칭 결과를 보정하여 정확도 향상
- 템플릿 레벨 규칙 (페이지별 오버라이드 아님)

### 3. 재사용 가능성
- 한 번 생성한 템플릿은 동일 교재의 향후 업로드에 재사용
- TOC 기반 강의 목록 추출 자동화
- 파싱 정확도 일관성 유지

---

## 📝 예시 시나리오

### 시나리오: 2026 수능특강 문학 교재 파싱

1. **템플릿 생성** (1회만)
   - 관리자가 TOC 텍스트 붙여넣기
   - 3개 페이지 (12, 14, 16)에 bbox 마킹
   - GPT로 템플릿 생성 → 저장

2. **PDF 업로드** (여러 번 가능)
   - 같은 교재 PDF 업로드
   - 템플릿 자동 매칭 (신뢰도 0.92)
   - region_hints 활용하여 섹션 타입 정확히 분류

3. **결과**
   - 73개 강의 자동 추출
   - 각 강의의 concept/passage/problem 정확히 분류
   - 파싱 정확도 90%+ 달성

---

이 흐름을 통해 **"설문조사처럼 간단한 입력"**으로 **"고정밀도 자동 파싱"**을 달성합니다! 🎉
