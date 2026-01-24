# 현재 데이터 상태 정리

## 생성된 데이터 위치

### 1. 레거시 데이터 (과목별) ⚠️
**경로:** `backend/data/literature/lectures/`

**내용:**
- 강의 수: 9개
- 파일: `lectures.json`, `lecture_01.json` ~ `lecture_09.json`

**문제점:**
- `sections: []` (섹션이 비어있음)
- 이미지 없음

**예시 (lecture_01.json):**
```json
{
  "subject": "literature",
  "lecture_id": 1,
  "title": "1강|시의표현과형식",
  "sections": [],  // ← 비어있음!
  "problems": ["01", "02", "03", "10"]
}
```

### 2. 교재별 데이터 (새 방식) ✅
**경로:** `backend/data/literature/book_korean_2026_수능특강_문학_d139df/lectures/`

**내용:**
- 강의 수: 80개
- 파일: `lectures.json`, `lecture_01.json` ~ `lecture_80.json`

**형식:**
- `concepts`: 개념 설명 배열
- `works`: 작품 본문 배열
- `problems`: 문제 배열
- `analysis`: 작품 분석

**예시 (lecture_01.json):**
```json
{
  "lecture_id": 1,
  "title": "1강 | 시의 표현과 형식",
  "concepts": [
    {
      "concept_id": "concept_01_01",
      "title": "시의 운율",
      "content": [...]
    }
  ],
  "works": [
    {
      "work_id": "work_01_01",
      "title": "해",
      "author": "박두진",
      "content": [...]
    }
  ],
  "problems": []
}
```

**참고:** 이 형식은 `sections` 대신 `concepts`와 `works`를 사용합니다.

## 데이터 생성 과정

### 관리자 페이지에서 업로드 시

1. **PDF 업로드**
   - 파일 저장: `uploads/{book_id}.pdf`
   - DB에 Book 생성

2. **백그라운드 파싱**
   - `UnifiedPipeline` 실행
   - OCR/PDF 추출 → 파싱 → 섹션 추출 → 저장

3. **데이터 저장**
   - JSON 파일: `data/{subject}/{book_id}/lectures/`
   - 이미지 (OCR 사용 시): `data/{subject}/{book_id}/concepts_images/` 등

4. **DB 동기화**
   - JSON → Curriculum, Lesson, Unit 생성

## 문제점 분석

### 1. 섹션이 비어있는 이유
- **레거시 데이터**: 개선된 섹션 추출기가 적용되지 않음
- **교재별 데이터**: 다른 형식 사용 (`concepts`, `works`)

### 2. 이미지 저장 안 되는 이유
- **조건**: `if isinstance(self.extractor, OCRExtractor):`
- **현재**: PdfplumberExtractor 사용 중
- **해결**: OCR 추출기 사용 필요

## 재생성 방법

### 방법 1: 관리자 페이지에서 재파싱 (가장 간단)

1. 관리자 페이지 접속: `http://localhost:3000/admin`
2. 교재 목록에서 해당 교재 찾기
3. **"재파싱"** 버튼 클릭
4. 파싱 완료 대기 (1-2분)
5. 결과 확인

**장점:**
- 간단함
- 개선된 섹션 추출기 자동 적용
- 기존 데이터 자동 삭제 후 재생성

### 방법 2: JSON 동기화 (재파싱 없이)

1. 관리자 페이지 접속
2. 교재 목록에서 해당 교재 찾기
3. **"JSON 동기화"** 버튼 클릭
4. 기존 JSON 파일을 DB로 동기화

**용도:**
- JSON은 이미 생성되어 있지만 DB에 없을 때
- 재파싱 없이 DB만 업데이트

### 방법 3: 새로 업로드

1. 기존 교재 삭제 (관리자 페이지)
2. 새로 PDF 업로드
3. 파싱 완료 대기

## 재생성 후 확인

### 1. 섹션 확인
```bash
# 교재별 데이터 확인
cat backend/data/literature/{book_id}/lectures/lecture_01.json | grep -A 10 sections
```

**성공 기준:**
- `sections` 배열이 비어있지 않음
- 각 섹션에 `title`, `type`, `content` 포함

### 2. 이미지 확인 (OCR 사용 시)
```bash
# 이미지 폴더 확인
ls backend/data/literature/{book_id}/concepts_images/
ls backend/data/literature/{book_id}/content_images/
```

**성공 기준:**
- PNG 파일 존재
- 파일명 형식: `concept_p{page:02d}_{idx:02d}.png`

## 데이터 정리 스크립트

### 확인
```bash
cd backend
python scripts/check_data.py
```

### 정리
```bash
cd backend
python scripts/cleanup_data.py
```

## 다음 단계

1. ✅ 데이터 구조 확인 완료
2. ⏳ 데이터 정리 (선택)
3. ⏳ 재파싱 실행
4. ⏳ 결과 확인

**추천 순서:**
1. `python scripts/check_data.py` - 현재 상태 확인
2. 관리자 페이지에서 "재파싱" 버튼 클릭
3. 파싱 완료 후 `python scripts/check_data.py` - 결과 확인
