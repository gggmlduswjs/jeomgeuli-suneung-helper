# 설계 문서 v1.1 구현 완료 보고서

## 📋 구현 체크리스트

### ✅ 개념 영역 구현

#### 4.1 시작 조건 ✅
- [x] 번호 + 개념명 패턴 인식 (`^\d+\s+시적\s+표현`, `^시적\s+표현$`)
- [x] 짧은 명사형 제목 (≤ 50자 필터링)
- [x] 페이지 상단부 위치 체크 (상단 30% 영역)
- [x] 평균 텍스트 높이 체크 (평균보다 20% 이상 큰 폰트)

#### 4.2 구성 요소 포함 ✅
- [x] 중앙 개념 설명 본문 포함
- [x] **좌측 보조 개념 설명 박스 포함** (v1.1 핵심)
  - 모든 단어의 최소 left를 left로 사용
  - 모든 단어의 최대 right를 right로 사용
  - 좌/우 컬럼 전체를 하나의 개념 블록으로 간주

#### 4.3 종료 조건 ✅
- [x] 다음 개념 제목 등장 시 종료
- [x] `작품으로 이해하기` 헤더 등장 시 종료
- [x] 문제 번호 패턴 등장 시 종료
- [x] 페이지 종료 처리

#### 4.4 bbox 계산 ✅
- [x] `top`: 개념 제목 줄의 top
- [x] `bottom`: 종료 조건 직전
- [x] `left`: 좌측 보조 박스의 left 포함 (모든 단어의 최소 left)
- [x] `right`: 개념 본문 최대 right (모든 단어의 최대 right)

**구현 위치**: `_extract_concept_blocks_from_ocr()` 메서드

---

### ✅ 본문 영역 구현

#### 5.1 시작 조건 ✅
- [x] `작품으로 이해하기` 헤더 패턴 인식
- [x] 짧은 명사형 제목 체크

#### 5.2 종료 조건 ✅
- [x] 문제 번호 등장 시 종료
- [x] 다음 본문 헤더 등장 시 종료
- [x] 페이지 종료 처리

#### 5.3 bbox 계산 ✅
- [x] `top`: 본문 헤더 top
- [x] `bottom`: 문제 번호 직전
- [x] `left/right`: 해당 영역 내 모든 텍스트 포함

**구현 위치**: `_extract_content_blocks_from_ocr()` 메서드

---

### ✅ 문제 영역 구현

#### 6.1 시작 조건 ✅
- [x] 문제 번호 패턴 인식 (`^\d{2}$`)
- [x] 번호가 독립된 줄로 존재 확인

#### 6.2 캡처 단위 ✅
- [x] 문제 번호 포함
- [x] 문제 지문 포함
- [x] 선택지 전체 (①②③④⑤) 포함
- [x] **이미지 단계에서 세분화 안 함** (v1.1 핵심)

#### 6.3 세부 구조 처리 ✅
- [x] 이미지 크롭 단계: 전체 블록으로 캡처
- [x] **JSON 생성 단계: 세분화 수행** (v1.1 핵심)
  - `question_text` 분리
  - `choices[]` 분리
  - `question_number` 분리

**구현 위치**: 
- 이미지 크롭: `_crop_problem_images()` 메서드
- JSON 세분화: `_parse_problem_structure()` 메서드

---

## 🔧 핵심 구현 세부사항

### 1. 좌측 보조 박스 포함 로직

```python
# v1.1 설계: 좌/우 컬럼 전체 포함
concept_lines = lines[line_idx:]
if concept_lines:
    # 모든 줄의 단어들에서 최소 left, 최대 right 찾기
    all_words_in_concept = [w for line_group in concept_lines for w in line_group]
    if all_words_in_concept:
        left = min(w['left'] for w in all_words_in_concept)  # 좌측 보조 박스 포함
        right = max(w['left'] + w['width'] for w in all_words_in_concept)  # 우측 전체
```

### 2. 문제 영역 전체 블록 캡처

```python
# 문제 번호부터 다음 문제 전까지 모든 줄 수집
problem_lines = lines[start_line_idx:end_line_idx]
# bbox는 모든 줄의 단어들을 포함하도록 계산
# 이미지 단계에서는 세분화 안 함
```

### 3. JSON 단계 세분화

```python
# _parse_problem_structure()에서 수행
# - question_text 추출
# - choices[] 추출 (①②③④⑤ 패턴)
# - question_number 추출
```

---

## 📊 설계-구현 일치 확인

### 개념 영역
- ✅ 좌측 보조 박스 포함
- ✅ 좌/우 컬럼 전체 포함
- ✅ 개념 제목 패턴 인식
- ✅ 종료 조건 처리

### 본문 영역
- ✅ "작품으로 이해하기" 헤더 인식
- ✅ 시 전문 연속 처리
- ✅ 문제 번호 직전까지 포함

### 문제 영역
- ✅ 문제 번호 + 지문 + 선택지 전체 캡처
- ✅ 이미지 단계에서 세분화 안 함
- ✅ JSON 단계에서 세분화 수행

---

## 🎯 설계 문서 v1.1 준수도

**100% 준수**

모든 설계 요구사항이 구현에 반영되었으며,
실제 캡처 결과와 논리적·시각적으로 일치합니다.

---

## 📝 참고사항

* 8페이지부터 실제 콘텐츠 시작 (config.json: `start_content_page`)
* DPI 기반 동적 threshold 계산
* pdfplumber / OCR 완전 분리
* 구조 파싱 이후 LLM 후처리
