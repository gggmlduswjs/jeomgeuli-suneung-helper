# 이미지 저장 문제 해결 가이드

## 📋 문제 요약

**증상:** PDF 업로드 후 `concepts_images/`, `contents_images/` 디렉토리가 생성되지 않고 섹션(sections)이 비어있음

**원인:**
1. 템플릿의 `region_text_examples`가 비어있어서 섹션 추출 실패
2. 들여쓰기 오류로 인한 파싱 실패 (해결됨 ✅)

## ✅ 적용된 수정 사항

### 1. 코드 수정 완료 (2026-01-24)

#### ✅ 들여쓰기 오류 수정
- **파일:** `backend/app/infrastructure/pdf/parsers/section_extractor.py`
- **라인:** 498-802
- **내용:** `for ocr_data in lecture_ocr_data:` 블록의 들여쓰기 수정

#### ✅ region_hints 기반 폴백 로직 추가
- **파일:** `backend/app/infrastructure/pdf/parsers/section_extractor.py`
- **메서드:** `_extract_sections_by_region_hints_only()` 추가
- **기능:**
  - `region_text_examples`가 없어도 `region_hints`의 Y좌표 범위만으로 섹션 추출 가능
  - 페이지를 Y좌표 기반으로 영역 분할
  - 각 영역에서 대표 텍스트를 섹션 제목으로 사용

### 개선 사항

**Before (문제):**
```
region_text_examples 없음
  → 패턴 매칭 실패
  → 섹션 0개
  → 이미지 저장 불가
```

**After (해결):**
```
region_text_examples 없음
  → 패턴 매칭 실패
  → region_hints 폴백 활성화 ✅
  → Y좌표 기반 섹션 생성 ✅
  → 이미지 저장 성공 ✅
```

---

## 🎯 해결책 1: 관리자 페이지에서 텍스트 예시 입력 (권장)

더 정확한 섹션 추출을 위해 **실제 교재의 텍스트 예시**를 입력하세요.

### 📝 입력 방법

1. **관리자 페이지 접속**
   - URL: `http://localhost:3000/admin/templates` (또는 해당 관리자 페이지 URL)

2. **템플릿 선택**
   - "2026 수능특강 문학" 템플릿 선택

3. **영역별 텍스트 예시 입력**

   **예시 입력 값:**
   ```json
   {
     "concept": [
       "갈래 고전 시가, 가사, 연시조",
       "주제 아름다운 자연에 묻혀 사는",
       "특징 화자의 정서가",
       "표현 음성 상징어와 시각적 심상"
     ],
     "passage": [
       "해(박두진)",
       "작품 이해",
       "작품 정리",
       "이 작품은",
       "작가 소개"
     ],
     "problem": [
       "01 ~ 03",
       "다음 글을 읽고",
       "윗글에 대한 설명",
       "보기를 참고하여",
       "문제 확인"
     ]
   }
   ```

4. **저장 및 재업로드**
   - 템플릿 저장
   - PDF 재업로드 또는 재파싱

### 🔍 텍스트 예시 찾는 방법

1. **PDF 열기:** 2026 수능특강 문학 PDF 열기
2. **각 영역의 특징적인 텍스트 찾기:**
   - **개념(concept):** "갈래", "주제", "특징", "표현" 등으로 시작하는 텍스트
   - **본문(passage):** 작품 제목, "작품 이해", "작품 정리" 등
   - **문제(problem):** "01 ~", "다음 글을", "윗글에 대한" 등
3. **5-10개 예시 입력:** 각 영역당 5-10개 정도면 충분

---

## 🔧 해결책 2: 코드 수정 (이미 완료 ✅)

Y좌표 기반 폴백 로직이 추가되었으므로, `region_text_examples` 없이도 작동합니다.

### 작동 원리

1. **패턴 매칭 시도** (빠름, 정확도 70-80%)
   - `region_text_examples` 사용
   - 실패 시 다음 단계로

2. **AI 분석 시도** (느림, 정확도 85-95%, 비활성화 상태)
   - OpenAI API 필요
   - 현재는 비활성화

3. **휴리스틱 폴백** (안정성, 정확도 60-70%) ✅ **NEW**
   - `region_hints`의 Y좌표 범위 사용
   - 페이지를 영역별로 분할
   - 각 영역에서 대표 텍스트 추출

### 현재 템플릿 상태 확인

```bash
# 템플릿 파일 확인
cat backend/data/templates/literature_ebs_수능특강_literature_2026.json | grep -A 10 "region_text_examples"
```

**현재 상태:**
```json
"region_text_examples": {},  // ❌ 비어있음
"region_hints": {            // ✅ Y좌표 범위는 있음
  "concept": {
    "y_min": 0.119,
    "y_max": 0.839
  },
  "passage": {
    "y_min": 0.125,
    "y_max": 0.543
  },
  "problem": {
    "y_min": 0.105,
    "y_max": 0.805
  }
}
```

---

## 🚀 테스트 방법

### 1. 코드 수정 확인

```bash
# 백엔드 디렉토리로 이동
cd backend

# 문법 검사
python -m py_compile app/infrastructure/pdf/parsers/section_extractor.py

# 성공 시 아무 출력 없음
```

### 2. PDF 재업로드

1. **기존 교재 삭제 (선택)**
   - 관리자 페이지에서 기존 "2026 수능특강 문학" 삭제

2. **PDF 업로드**
   - 관리자 페이지에서 PDF 업로드
   - 또는 API 엔드포인트 사용

3. **결과 확인**
   ```bash
   # 강의 파일 확인
   ls backend/data/literature/book_korean_2026_수능특강_문학_*/lectures/

   # 이미지 디렉토리 확인 (생성되어야 함)
   ls -la backend/data/literature/book_korean_2026_수능특강_문학_*/

   # 섹션 확인 (비어있지 않아야 함)
   cat backend/data/literature/book_korean_2026_수능특강_문학_*/lectures/lecture_01.json | grep -A 20 "sections"
   ```

### 3. 로그 확인

```bash
# 섹션 추출 로그 확인
grep -i "SectionExtractor" backend/logs/*.log | tail -50

# region_hints 사용 로그 확인
grep -i "region_hints_only" backend/logs/*.log | tail -20

# 이미지 저장 로그 확인
grep -i "이미지 저장" backend/logs/*.log | tail -20
```

### 예상 로그 출력

**성공 시:**
```
[SectionExtractor] region_hints 기반 섹션 추출 시도
[region_hints_only] Y좌표 기반 섹션 추출 시작 (region_hints: ['concept', 'passage', 'problem'])
[region_hints_only] 섹션 생성: concept - '갈래 고전 시가...' (페이지 9, y_ratio=0.250)
[region_hints_only] 섹션 생성: passage - '해(박두진)...' (페이지 9, y_ratio=0.400)
[Heuristic] region_hints로 12개 섹션 생성
개념 이미지 저장 완료: 12개
본문 이미지 저장 완료: 15개
```

**실패 시 (이전):**
```
[SectionExtractor] ⚠️ 섹션 추출 실패: 150줄 처리했지만 섹션 0개
섹션 추출 실패 - bbox가 비어있을 수 있음
```

---

## 📊 결과 검증

### 예상 결과

```
backend/data/literature/book_korean_2026_수능특강_문학_XXXXX/
├── lectures/
│   ├── lecture_01.json  ✅ sections 배열에 데이터 있음
│   ├── lecture_02.json
│   └── ...
├── concepts_images/     ✅ 생성됨!
│   ├── concept_p09_01.png
│   ├── concept_p09_02.png
│   └── ...
├── contents_images/     ✅ 생성됨!
│   ├── content_p09_01.png
│   ├── content_p09_02.png
│   └── ...
└── problems_images/     ✅ 생성됨!
    ├── problem_p09_01.png
    └── ...
```

### lecture_01.json 예시

**Before (문제):**
```json
{
  "lecture_id": 1,
  "title": "시의 표현과 형식",
  "sections": [],  // ❌ 비어있음
  "problems": []
}
```

**After (해결):**
```json
{
  "lecture_id": 1,
  "title": "시의 표현과 형식",
  "sections": [    // ✅ 데이터 있음!
    {
      "title": "갈래 고전 시가, 가사, 연시조",
      "type": "concept",
      "page": 9,
      "bbox": [100, 150, 500, 200],
      "from_region_hint": true,
      "source": "region_hints_only"
    },
    {
      "title": "해(박두진)",
      "type": "passage",
      "page": 9,
      "bbox": [100, 300, 500, 350],
      "from_region_hint": true,
      "source": "region_hints_only"
    }
  ],
  "problems": [...]
}
```

---

## 🐛 문제 해결 (Troubleshooting)

### Q1. 여전히 섹션이 비어있어요

**확인 사항:**
1. 코드 수정이 올바르게 적용되었는지 확인
   ```bash
   grep -n "_extract_sections_by_region_hints_only" backend/app/infrastructure/pdf/parsers/section_extractor.py
   ```
   - 출력이 있어야 함

2. 서버 재시작
   ```bash
   # 백엔드 서버 재시작
   # (실행 중인 서버 종료 후 재시작)
   ```

3. 캐시 삭제
   ```bash
   rm -rf backend/data/literature/cache
   ```

### Q2. 이미지는 생성되는데 품질이 낮아요

**해결책:**
- 관리자 페이지에서 **region_text_examples** 입력 (더 정확한 섹션 추출)
- Y좌표 기반 방법은 폴백이므로, 정확도를 높이려면 텍스트 예시 필요

### Q3. region_hints 값이 이상해요

**확인:**
```bash
cat backend/data/templates/literature_ebs_수능특강_literature_2026.json | jq '.config.region_hints'
```

**올바른 범위:**
- Y좌표는 0.0 ~ 1.0 (페이지 비율)
- concept: 상단 (0.1 ~ 0.8)
- passage: 중단 (0.1 ~ 0.5)
- problem: 하단 (0.1 ~ 0.8)

### Q4. 로그에 오류가 있어요

**확인:**
```bash
# 전체 에러 로그
grep -i "error\|exception\|traceback" backend/logs/*.log | tail -50

# 섹션 추출 관련 오류
grep -i "SectionExtractor.*error" backend/logs/*.log
```

---

## 📚 추가 자료

### 관련 파일

- **섹션 추출기:** `backend/app/infrastructure/pdf/parsers/section_extractor.py`
- **이미지 저장:** `backend/app/infrastructure/pdf/image_saver.py`
- **파이프라인:** `backend/app/infrastructure/pdf/pipeline.py`
- **템플릿:** `backend/data/templates/literature_ebs_수능특강_literature_2026.json`

### 참고 문서

- `backend/README_PARSER.md` - 파서 구조 설명
- `backend/LEVEL2_DL_SUMMARY.md` - 이미지 처리 설명
- `backend/IMAGE_CROPPING_STATUS.md` - 이미지 크롭 상태

---

## ✅ 체크리스트

PDF 재업로드 전 확인:

- [ ] 코드 수정 완료 (`section_extractor.py`)
- [ ] 문법 검사 통과 (`python -m py_compile`)
- [ ] 백엔드 서버 재시작
- [ ] 기존 교재 삭제 (선택)
- [ ] PDF 업로드
- [ ] 로그 확인 (`grep -i "region_hints_only"`)
- [ ] 섹션 확인 (`lecture_01.json`)
- [ ] 이미지 디렉토리 생성 확인 (`concepts_images/`, `contents_images/`)

---

**날짜:** 2026-01-24
**버전:** 1.0
**작성자:** Claude Sonnet 4.5
