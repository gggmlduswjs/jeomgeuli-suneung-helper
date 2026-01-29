# 데이터 구조 정리

## 현재 데이터 저장 위치

### 1. 교재별 디렉토리 (새 방식) ✅
```
backend/data/{subject}/{book_id}/
├── lectures/
│   ├── lectures.json          # 강의 목록
│   ├── lecture_01.json       # 강의 상세 (섹션, 문제 포함)
│   ├── lecture_02.json
│   └── ...
├── concepts_images/           # 개념 이미지 (OCR 사용 시)
│   ├── concept_p08_01.png
│   └── ...
├── content_images/            # 본문 이미지 (OCR 사용 시)
│   └── ...
└── problems_images/           # 문제 이미지 (OCR 사용 시)
    └── ...
```

**예시:**
- `backend/data/literature/book_korean_2026_수능특강_문학_d139df/`

### 2. 과목별 디렉토리 (레거시) ⚠️
```
backend/data/{subject}/
├── lectures/
│   ├── lectures.json
│   ├── lecture_01.json
│   └── ...
└── ...
```

**예시:**
- `backend/data/literature/lectures/`

## 문제점

### 현재 상황
1. **두 경로에 데이터가 혼재**
   - 교재별: `book_korean_2026_수능특강_문학_d139df/lectures/`
   - 레거시: `literature/lectures/`

2. **섹션이 비어있음**
   - `lecture_01.json`의 `sections: []`
   - 이미지 저장 불가 (섹션이 없으면 저장할 이미지 없음)

3. **이미지 저장 안 됨**
   - PdfplumberExtractor 사용 중 → 이미지 저장 조건 불만족
   - OCR 추출기 사용해야 이미지 저장됨

## 해결 방법

### 방법 1: 기존 데이터 정리 후 재파싱 (추천)

1. **기존 데이터 삭제**
   ```bash
   # 레거시 데이터 삭제
   rm -rf backend/data/literature/lectures/
   
   # 교재별 데이터 삭제 (선택)
   rm -rf backend/data/literature/book_korean_2026_수능특강_문학_d139df/
   ```

2. **관리자 페이지에서 재파싱**
   - 교재 목록에서 "재파싱" 버튼 클릭
   - 또는 "JSON 동기화" 버튼 클릭

### 방법 2: 새로 업로드

1. **기존 교재 삭제** (관리자 페이지)
2. **새로 업로드**
   - PDF 파일 선택
   - 과목: literature
   - 제목: 수능특강 문학

## 데이터 생성 과정

### 파이프라인 실행 순서
1. PDF 업로드 → `uploads/{book_id}.pdf`
2. OCR/PDF 추출 → 텍스트 + bbox 정보
3. 하이브리드 파싱 → 강의, 문제 추출
4. 섹션 추출 → **개선된 섹션 추출기 사용**
5. 이미지 저장 (OCR 사용 시) → concepts_images, content_images, problems_images
6. JSON 저장 → `data/{subject}/{book_id}/lectures/`

### 생성되는 파일

#### lectures.json
```json
[
  {"lecture_id": 1, "title": "1강 | 시의 표현과 형식"},
  {"lecture_id": 2, "title": "2강 | 시의 내용"},
  ...
]
```

#### lecture_XX.json
```json
{
  "subject": "literature",
  "lecture_id": 1,
  "title": "1강 | 시의 표현과 형식",
  "sections": [
    {
      "title": "1. 시적 표현",
      "type": "concept",
      "page": 8,
      "content": ["시는 운율을 통해...", ...]
    },
    {
      "title": "작품으로 이해하기 - 박두진 [해]",
      "type": "content",
      "page": 9,
      "content": ["풀잎들이 가지를 벌려", ...]
    }
  ],
  "problems": ["01", "02", "03"]
}
```

## 이미지 저장 조건

### 활성화 조건
1. **OCR 추출기 사용** (`extractor_type="ocr"`)
2. **섹션이 있어야 함** (`sections` 배열에 데이터)
3. **bbox 정보 필요** (섹션의 위치 정보)

### 저장 위치
- 개념: `data/{subject}/{book_id}/concepts_images/concept_p{page:02d}_{idx:02d}.png`
- 본문: `data/{subject}/{book_id}/content_images/content_p{page:02d}_{idx:02d}.png`
- 문제: `data/{subject}/{book_id}/problems_images/problem_p{page:02d}_{problem_id}.png`

## 다음 단계

1. **기존 데이터 정리**
2. **재파싱 실행** (개선된 섹션 추출기로)
3. **섹션 확인** (`sections` 배열이 비어있지 않은지)
4. **이미지 저장** (OCR 추출기 사용 시)
