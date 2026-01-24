# 목차 자동 추출 및 강의 범위 계산

## 개요

목차 페이지에서 텍스트를 자동으로 추출하고, 각 강의의 페이지 범위를 자동 계산하는 기능입니다.

## 작동 방식

### 1단계: 목차 텍스트 자동 추출

**API**: `POST /api/v1/templates/extract-toc-text`

**요청**:
```javascript
FormData {
  pdf_file: File,
  toc_pages: "3,4,5"  // 목차가 있는 페이지 번호
}
```

**응답**:
```json
{
  "ok": true,
  "toc_text": "1강 | 시의 표현과 형식\n해 (박두진) 009\n2강 | 시의 내용\n매화 옛 등걸에 ~ 012",
  "pages_extracted": [3, 4, 5],
  "total_lines": 45
}
```

**예시**:
```javascript
const formData = new FormData();
formData.append('pdf_file', pdfFile);
formData.append('toc_pages', '3,4,5');  // 목차 페이지

const response = await fetch('/api/v1/templates/extract-toc-text', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('추출된 목차:', result.toc_text);
```

### 2단계: 관리자가 목차 텍스트 검토/수정

```
추출된 목차 텍스트 (수정 가능):
┌─────────────────────────────────────────┐
│ 1강 | 시의 표현과 형식                    │
│ 해 (박두진) 009                           │
│                                           │
│ 2강 | 시의 내용                           │
│ 매화 옛 등걸에 ~ (매화)                  │
│ 녹양이 천만사인들 ~ (이원익)              │
│ 사랑 사랑 고고히 맺힌 사랑 ~ (작자 미상)  │
│ 012                                       │
│                                           │
│ 3강 | 시의 화자와 상황                    │
│ 사평역에서 ~ (곽재구) 015                 │
└─────────────────────────────────────────┘
```

### 3단계: 템플릿 생성 (자동 강의 범위 계산)

**API**: `POST /api/v1/templates/generate-from-toc`

**요청**:
```javascript
{
  subject: "literature",
  name: "ebs_수능특강_literature_2026",
  toc_text: "1강 | 시의 표현과 형식\n해 (박두진) 009\n...",
  toc_lecture_line_examples: [
    "1강 | 시의 표현과 형식",
    "2강 | 시의 내용"
  ],
  save: true
}
```

**자동 처리**:
1. 목차에서 강의 번호와 시작 페이지 파싱
   ```
   "1강 | 시의 표현과 형식 ... 009" → 강의 1, 시작 페이지 9
   "2강 | 시의 내용 ... 012" → 강의 2, 시작 페이지 12
   "3강 | 시의 화자와 상황 ... 015" → 강의 3, 시작 페이지 15
   ```

2. 강의별 페이지 범위 자동 계산
   ```
   강의 1: 9 ~ 11페이지 (다음 강의 시작 - 1)
   강의 2: 12 ~ 14페이지
   강의 3: 15 ~ 끝페이지
   ```

3. `lecture_page_ranges` 생성
   ```json
   {
     "1": {"start": 9, "end": 11},
     "2": {"start": 12, "end": 14},
     "3": {"start": 15, "end": null}
   }
   ```

4. 템플릿 config에 저장
   ```json
   {
     "config": {
       "lecture_page_ranges": {...},
       "unit_order": ["concept", "passage", "problem"],
       "region_hints": {...}
     }
   }
   ```

### 4단계: 파싱 시 자동 활용

**파싱 프로세스**:
```
PDF 업로드 → 템플릿 매칭 → lecture_page_ranges 로드

강의 1 (9-11페이지):
  ├─ 개념 (concept, Y: 0.1-0.4)
  ├─ 본문 (passage, Y: 0.4-0.7)
  └─ 문제 (problem, Y: 0.7-0.9)

강의 2 (12-14페이지):
  ├─ 개념
  ├─ 본문
  └─ 문제

...
```

## 완전한 워크플로우

### 프론트엔드 구현 예시

```javascript
// 1. PDF 업로드
const pdfFile = document.getElementById('pdfInput').files[0];

// 2. 목차 페이지 입력
const tocPages = "3,4,5";  // 관리자 입력

// 3. 목차 텍스트 자동 추출
const extractTocFormData = new FormData();
extractTocFormData.append('pdf_file', pdfFile);
extractTocFormData.append('toc_pages', tocPages);

const tocResponse = await fetch('/api/v1/templates/extract-toc-text', {
  method: 'POST',
  body: extractTocFormData
});

const tocResult = await tocResponse.json();
console.log('추출된 목차:', tocResult.toc_text);

// 4. 목차 텍스트 표시 (관리자가 수정 가능)
document.getElementById('tocTextArea').value = tocResult.toc_text;

// 5. 템플릿 생성 버튼 클릭 시
document.getElementById('generateBtn').onclick = async () => {
  const editedTocText = document.getElementById('tocTextArea').value;

  const generateRequest = {
    subject: "literature",
    name: "ebs_수능특강_literature_2026",
    version: "2026",
    toc_text: editedTocText,
    toc_lecture_line_examples: [
      "1강 | 시의 표현과 형식",
      "2강 | 시의 내용",
      "3강 | 시의 화자와 상황"
    ],
    curriculum_survey: {
      is_lecture_based: true,
      unit_order: ["concept", "passage", "problem"]
    },
    save: true
  };

  const generateResponse = await fetch('/api/v1/templates/generate-from-toc', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(generateRequest)
  });

  const result = await generateResponse.json();
  console.log('템플릿 생성 완료:', result);
  console.log('강의 범위:', result.template.config.lecture_page_ranges);
};
```

## 목차 형식 예시

### 예시 1: EBS 수능특강 문학
```
1강 | 시의 표현과 형식
해 (박두진) 009

2강 | 시의 내용
매화 옛 등걸에 ~ (매화)
녹양이 천만사인들 ~ (이원익)
사랑 사랑 고고히 맺힌 사랑 ~ (작자 미상) 012

3강 | 시의 화자와 상황
사평역에서 ~ (곽재구) 015
```

**추출 결과**:
```json
{
  "1": {"start": 9, "end": 11},
  "2": {"start": 12, "end": 14},
  "3": {"start": 15, "end": null}
}
```

### 예시 2: 수학 교재
```
I. 지수함수와 로그함수
  01강 지수 13
  02강 로그 21
  03강 지수함수 29

II. 삼각함수
  04강 일반각과 호도법 37
  05강 삼각함수 45
```

**추출 결과**:
```json
{
  "1": {"start": 13, "end": 20},
  "2": {"start": 21, "end": 28},
  "3": {"start": 29, "end": 36},
  "4": {"start": 37, "end": 44},
  "5": {"start": 45, "end": null}
}
```

## 장점

### 1. 자동화
- 목차 페이지만 지정하면 텍스트 자동 추출
- 강의 범위 자동 계산
- 수동 입력 최소화

### 2. 정확성
- 목차에서 직접 페이지 정보 추출
- 계산 오류 방지
- 일관된 범위 설정

### 3. 편의성
- 관리자는 목차 검토만 하면 됨
- 잘못 추출된 부분만 수정
- 빠른 템플릿 생성

### 4. 유연성
- 다양한 목차 형식 지원
- 강의가 없는 교재도 지원 (lecture_page_ranges 비어있음)
- 수동 입력도 여전히 가능

## 주의사항

### 목차 페이지 번호
- 실제 PDF의 페이지 번호 사용 (표지 포함)
- 예: 표지(1) + 머리말(2) + 목차(3,4,5) → "3,4,5"

### 페이지 번호 형식
- 목차에서 페이지 번호 인식 패턴:
  - `009`, `012`, `015` (3자리 숫자)
  - `9`, `12`, `15` (일반 숫자)
  - 줄 끝에 있는 숫자 우선

### 강의 번호 형식
- 지원되는 패턴:
  - `1강`, `2강`, ... (N강)
  - `01강`, `02강`, ... (0N강)
  - `제1장`, `제2장`, ... (제N장)
  - `CHAPTER 1`, `CHAPTER 2`, ...

## API 스펙

### POST /templates/extract-toc-text

**Request**:
```
Content-Type: multipart/form-data

pdf_file: File (required)
toc_pages: string (required) - 예: "3,4,5"
```

**Response**:
```json
{
  "ok": true,
  "toc_text": "string",
  "pages_extracted": [3, 4, 5],
  "total_lines": 45
}
```

**Errors**:
- 400: toc_pages 형식 오류
- 400: 목차 페이지에서 텍스트 추출 실패
- 500: 서버 오류

### POST /templates/generate-from-toc

**기존 필드에 추가**:
- `toc_text`: 목차 텍스트 (필수)
- `toc_lecture_line_examples`: 강의 라인 예시 (필수)

**자동 생성되는 필드**:
- `config.lecture_page_ranges`: 강의별 페이지 범위
- `config.toc_lecture_list`: 강의 목록 (제목, 시작/끝 페이지)

## 로그 예시

```
[목차 추출] 3개 페이지에서 45줄 추출
[템플릿 생성] TOC에서 32개 강의 추출 완료
[템플릿 생성] lecture_page_ranges 생성: 32개 강의
  - 강의 1: 9 ~ 11페이지
  - 강의 2: 12 ~ 14페이지
  - 강의 3: 15 ~ 17페이지
  - 강의 4: 18 ~ 20페이지
  - 강의 5: 21 ~ 23페이지
```

## 결론

이 기능으로:
1. 목차 페이지만 지정하면 텍스트 자동 추출
2. 강의별 페이지 범위 자동 계산
3. 파싱 시 강의별로 정확한 섹션 추출
4. 관리자 작업 시간 대폭 단축

목차 → 강의 범위 → 단위 구성 전체가 자동화됩니다! 🎉
