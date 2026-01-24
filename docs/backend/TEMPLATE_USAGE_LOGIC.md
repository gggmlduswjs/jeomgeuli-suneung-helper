# 템플릿 관리자 입력 정보 활용 로직

## 📋 개요

템플릿에 저장된 관리자 입력 정보들이 실제 파싱 과정에서 어떻게 활용되는지 설명합니다.

## 🔑 주요 관리자 입력 정보

### 1. `region_text_examples` (우선 사용)
**목적**: 영역 내 텍스트 예시를 통한 패턴 학습 및 섹션 분류

**형식**:
```json
{
  "concept": ["1. 시적 표현", "2. 서정적 자아", "3. 운율"],
  "passage": ["작품 읽기", "본문", "지문"],
  "problem": ["문제", "연습 문제", "확인 문제"]
}
```

**활용 로직** (`section_extractor.py:501-540`):
1. **우선 적용**: 섹션 추출 시 가장 먼저 `region_text_examples`로 매칭 시도
2. **유사도 계산**:
   - 정확한 포함: `example_text in line_text` → 점수 1.0
   - 키워드 매칭: 공통 단어 비율 → 점수 0.7
   - 부분 문자열: 앞 5글자 포함 → 점수 0.5
3. **임계값**: 0.5 이상이면 해당 타입으로 분류
4. **결과**: 매칭 성공 시 섹션 타입 결정 및 신뢰도 기록

**예시**:
```python
# 텍스트: "1. 시적 표현과 형식"
# region_text_examples["concept"]에 "1. 시적 표현"이 있으면
# → 정확한 포함 매칭 → 점수 1.0 → concept 타입으로 분류
```

### 2. `region_hints` (y 좌표 기반 보정)
**목적**: 페이지 내 y 좌표 위치를 기반으로 섹션 타입 보정

**형식**:
```json
{
  "concept": {"y_min": 0.0, "y_max": 0.3},
  "passage": {"y_min": 0.3, "y_max": 0.7},
  "problem": {"y_min": 0.7, "y_max": 1.0}
}
```

**활용 로직** (`section_extractor.py:596-683`):
1. **y 좌표 계산**: 섹션의 bbox에서 y 중심점을 페이지 비율로 변환
2. **영역 확인**: `y_ratio`가 `region_hints[unit_type]` 범위 내에 있는지 확인
3. **신뢰도 계산**:
   - 영역 중앙에 가까울수록 높은 신뢰도 (최대 1.0)
   - 강의 내 위치 고려 (concept은 초반, passage는 중반, problem은 후반)
4. **타입 보정**:
   - 신뢰도 > 임계값(0.55-0.7): `region_hint` 타입으로 강제 변경
   - 신뢰도 낮으면: 패턴 결과 유지하되 힌트 정보 기록
5. **동적 임계값**: 강의 내 위치에 따라 임계값 조정
   - 강의 초반(0.0-0.3): concept에 더 관대 (임계값 0.55)
   - 강의 중반(0.3-0.7): passage에 더 관대 (임계값 0.55)
   - 강의 후반(0.7-1.0): problem에 더 관대 (임계값 0.55)

**예시**:
```python
# 섹션 y 좌표가 페이지 상단 20% (y_ratio=0.2)
# region_hints["concept"] = {"y_min": 0.0, "y_max": 0.3}
# → 영역 내에 있음 → concept 타입으로 보정 (신뢰도 0.85)
```

### 3. `toc_lecture_list` (강의 목록)
**목적**: 강의별 페이지 범위 정보 제공

**형식**:
```json
[
  {
    "lecture_id": 1,
    "title": "1강|시의 표현과 형식",
    "start_page": 8,
    "end_page": 25
  },
  ...
]
```

**활용 로직**:
1. **페이지 범위 계산** (`page_range_calculator.py`):
   - 템플릿에서 강의 목록 추출
   - 최소 시작 페이지와 최대 종료 페이지 계산
   - 필요한 페이지만 추출하여 성능 최적화

2. **강의 내 위치 계산** (`section_extractor.py:94-109`):
   - 현재 페이지가 어느 강의에 속하는지 확인
   - 강의 내 상대 위치 계산 (0.0-1.0)
   - `region_hints` 신뢰도 계산 시 활용

**예시**:
```python
# 페이지 15가 강의 1 (8-25페이지)에 속함
# → 강의 내 위치: (15-8)/(25-8) = 0.41 (중반)
# → passage 타입에 더 관대한 임계값 적용
```

### 4. `toc_text` (전체 목차 텍스트)
**목적**: 목차 정보 참고 (현재는 저장만 하고 직접 활용은 제한적)

**활용**: 향후 AI 파싱이나 목차 기반 검증에 활용 예정

### 5. `region_image_examples` (영역 이미지 예시)
**목적**: 시각적 참고용 (현재는 저장만 하고 직접 활용은 제한적)

**활용**: 향후 이미지 기반 매칭에 활용 예정

## 🔄 활용 순서 및 우선순위

### 섹션 추출 시 (`section_extractor.py:_extract_by_pattern`)

```
1. region_text_examples로 텍스트 매칭 (우선 적용)
   ↓ 매칭 실패 시
2. 기본 패턴 매칭 (concept_title_patterns, content_header_patterns)
   ↓ 섹션 타입 결정 후
3. region_hints로 y 좌표 기반 타입 보정
   - 신뢰도 높으면: 타입 강제 변경
   - 신뢰도 낮으면: 패턴 결과 유지하되 힌트 정보 기록
4. 강의 내 위치 고려한 동적 임계값 적용
```

### 전체 텍스트 블록 분류 시 (`section_extractor.py:_classify_all_text_blocks`)

```
1. region_text_examples로 모든 텍스트 블록 분류
   - 유사도 계산 (정확한 포함, 키워드 매칭)
   - 임계값 0.4 이상이면 분류
2. 이미 섹션으로 분류된 텍스트는 제외
3. 분류된 블록을 섹션 리스트에 추가
```

## 📊 신뢰도 계산 방식

### region_text_examples 신뢰도
- **정확한 포함**: 1.0
- **키워드 매칭**: `공통 단어 수 / 예시 단어 수 * 0.7`
- **부분 문자열**: 0.5
- **임계값**: 0.5 (섹션 추출), 0.4 (전체 블록 분류)

### region_hints 신뢰도
- **기본 신뢰도**: 영역 중앙에 가까울수록 높음 (0.5-1.0)
- **강의 위치 보정**:
  - 예상 위치와 일치: `신뢰도 * 1.3` (최대 1.0)
  - 예상 위치와 불일치: `신뢰도 * 0.8`
- **임계값**: 0.55-0.7 (강의 내 위치에 따라 동적 조정)

## 🎯 실제 활용 예시

### 예시 1: region_text_examples 우선 매칭
```python
# 텍스트: "1. 시적 표현과 형식"
# region_text_examples["concept"] = ["1. 시적 표현", "2. 서정적 자아"]

# 매칭 과정:
# 1. "1. 시적 표현" in "1. 시적 표현과 형식" → True
# 2. 점수: 1.0 (정확한 포함)
# 3. 임계값 0.5 이상 → concept 타입으로 분류
# 4. region_hints 확인 생략 (이미 높은 신뢰도)
```

### 예시 2: region_hints로 타입 보정
```python
# 텍스트: "작품 읽기" (패턴 매칭 실패)
# y 좌표: 페이지 상단 10% (y_ratio=0.1)

# 매칭 과정:
# 1. region_text_examples 매칭 실패
# 2. 기본 패턴 매칭 실패 → section_type = None
# 3. region_hints 확인:
#    - y_ratio=0.1이 concept 영역(0.0-0.3) 내에 있음
#    - 신뢰도: 0.85 (중앙에 가까움)
#    - 강의 초반(0.2) → concept 예상 위치와 일치 → 신뢰도 1.0
# 4. 임계값 0.55 초과 → concept 타입으로 설정
```

### 예시 3: 강의 내 위치 고려
```python
# 페이지 20, 강의 1 (8-25페이지)
# 강의 내 위치: (20-8)/(25-8) = 0.71 (후반)
# 섹션 y 좌표: 페이지 중간 50% (y_ratio=0.5)

# 매칭 과정:
# 1. region_hints["passage"] = {"y_min": 0.3, "y_max": 0.7}
#    - y_ratio=0.5이 영역 내에 있음
# 2. 신뢰도 계산:
#    - 기본 신뢰도: 1.0 (중앙)
#    - 강의 후반(0.71) vs passage 예상 위치(0.3-0.7) → 불일치
#    - 신뢰도: 1.0 * 0.8 = 0.8
# 3. 임계값: 0.65 (일반적인 경우)
# 4. 신뢰도 0.8 > 0.65 → passage 타입으로 보정
```

## 🔍 디버깅 팁

### 로그 확인
```python
# region_text_examples 매칭
logger.debug(f"[region_text_examples] 매칭: '{line_text[:30]}...' -> {best_match_type} (점수: {best_match_score:.2f})")

# region_hints 타입 변경
logger.info(f"[region_hint] 타입 강제 변경: {section_type} -> {hint_type} (신뢰도: {hint_confidence:.2f})")

# 강의 위치 보정
logger.debug(f"[강의 위치 보정] {unit_type} 예상 위치와 일치/불일치")
```

### 템플릿 정보 확인
```python
# unified_parser.py에서 템플릿 로드 시
logger.info(f"[템플릿] region_hints 로드: {list(region_hints.keys())}")
logger.info(f"[템플릿] region_text_examples 로드: {list(region_text_examples.keys())}")
logger.info(f"[템플릿] TOC 강의 목록 로드: {len(toc_lecture_list)}개")
```

## ⚠️ 주의사항

1. **region_text_examples 우선**: 텍스트 매칭이 성공하면 `region_hints` 확인을 생략할 수 있음
2. **region_hints는 보정용**: 패턴 매칭 결과를 보정하는 용도로 사용
3. **강의 내 위치 고려**: 동일한 y 좌표라도 강의 내 위치에 따라 신뢰도가 달라짐
4. **영역 밖 콘텐츠**: `region_hints` 영역 밖의 콘텐츠는 필터링하지 않고 경고만 표시

## 📈 성능 영향

- **region_text_examples**: 텍스트 유사도 계산으로 약간의 오버헤드 (미미함)
- **region_hints**: y 좌표 계산 및 영역 확인 (매우 빠름)
- **toc_lecture_list**: 페이지 범위 계산으로 전체 처리 시간 단축 (큰 효과)
