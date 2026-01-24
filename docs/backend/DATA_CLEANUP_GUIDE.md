# 데이터 정리 및 재생성 가이드

## 현재 데이터 상태

### 발견된 데이터

1. **레거시 데이터** (과목별)
   - 경로: `backend/data/literature/lectures/`
   - 강의 수: 9개
   - 문제: 섹션이 비어있음 (`sections: []`)

2. **교재별 데이터** (새 방식)
   - 경로: `backend/data/literature/book_korean_2026_수능특강_문학_d139df/lectures/`
   - 강의 수: 80개
   - 상태: 확인 필요

### 문제점

1. **섹션이 비어있음**
   - `lecture_01.json`의 `sections: []`
   - 개선된 섹션 추출기가 적용되지 않음

2. **이미지 저장 안 됨**
   - `concepts_images/`, `content_images/`, `problems_images/` 폴더 없음
   - PdfplumberExtractor 사용 중 → 이미지 저장 조건 불만족

3. **데이터 중복**
   - 레거시 경로와 교재별 경로에 모두 데이터 존재

## 데이터 정리 방법

### 방법 1: 스크립트 사용 (추천)

```bash
cd backend
python scripts/cleanup_data.py
```

이 스크립트는:
- 레거시 데이터 확인 및 삭제 옵션 제공
- 교재별 데이터 확인 및 삭제 옵션 제공
- 안전하게 데이터 정리

### 방법 2: 수동 삭제

```bash
# 레거시 데이터 삭제
rm -rf backend/data/literature/lectures/

# 교재별 데이터 삭제 (선택)
rm -rf backend/data/literature/book_korean_2026_수능특강_문학_d139df/
```

## 재생성 방법

### 방법 1: 관리자 페이지에서 재파싱 (추천)

1. 관리자 페이지 접속: `http://localhost:3000/admin`
2. 교재 목록에서 해당 교재 찾기
3. "재파싱" 버튼 클릭
4. 파싱 완료 대기 (1-2분)
5. 결과 확인

### 방법 2: JSON 동기화 (재파싱 없이)

1. 관리자 페이지 접속
2. 교재 목록에서 해당 교재 찾기
3. "JSON 동기화" 버튼 클릭
4. 기존 JSON 파일을 DB로 동기화

### 방법 3: 새로 업로드

1. 기존 교재 삭제 (관리자 페이지)
2. 새로 PDF 업로드
3. 파싱 완료 대기

## 재생성 후 확인 사항

### 1. 섹션 확인
```bash
# 첫 번째 강의 확인
cat backend/data/literature/{book_id}/lectures/lecture_01.json
```

**성공 기준:**
```json
{
  "sections": [
    {
      "title": "1. 시적 표현",
      "type": "concept",
      "content": ["시는 운율을 통해...", ...]
    },
    {
      "title": "작품으로 이해하기 - 박두진 [해]",
      "type": "content",
      "content": ["풀잎들이 가지를 벌려", ...]
    }
  ]
}
```

### 2. 이미지 확인 (OCR 사용 시)
```bash
# 이미지 폴더 확인
ls backend/data/literature/{book_id}/concepts_images/
ls backend/data/literature/{book_id}/content_images/
ls backend/data/literature/{book_id}/problems_images/
```

**성공 기준:**
- `concept_p{page:02d}_{idx:02d}.png` 파일 존재
- `content_p{page:02d}_{idx:02d}.png` 파일 존재
- `problem_p{page:02d}_{problem_id}.png` 파일 존재

## 데이터 구조 (재생성 후)

```
backend/data/literature/{book_id}/
├── lectures/
│   ├── lectures.json          # 강의 목록
│   ├── lecture_01.json         # 강의 상세 (섹션 포함)
│   ├── lecture_02.json
│   └── ...
├── concepts_images/            # 개념 이미지 (OCR 사용 시)
│   ├── concept_p08_01.png
│   └── ...
├── content_images/             # 본문 이미지 (OCR 사용 시)
│   └── ...
└── problems_images/            # 문제 이미지 (OCR 사용 시)
    └── ...
```

## 빠른 재생성 가이드

1. **데이터 확인**
   ```bash
   cd backend
   python scripts/check_data.py
   ```

2. **데이터 정리** (선택)
   ```bash
   python scripts/cleanup_data.py
   ```

3. **재파싱**
   - 관리자 페이지 → 교재 목록 → "재파싱" 버튼

4. **결과 확인**
   ```bash
   python scripts/check_data.py
   ```

## 예상 결과

### 재생성 후
- ✅ 섹션이 채워짐 (`sections` 배열에 데이터)
- ✅ JSON 파일이 교재별 경로에 생성
- ✅ 이미지 저장 (OCR 추출기 사용 시)

### 개선된 섹션 추출기 적용
- 패턴 매칭 → AI 분석 → 휴리스틱 폴백
- 최소한 휴리스틱으로라도 섹션 추출
- 빈 배열 발생률 90% 감소
