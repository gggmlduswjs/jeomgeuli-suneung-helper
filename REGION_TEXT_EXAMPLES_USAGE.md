# region_text_examples 활용도 분석

## 🚨 핵심 문제

**region_text_examples (영역별 텍스트 예시)가 파싱 과정에서 거의 활용되지 않습니다!**

## 현재 활용도

### ✅ region_hints (Y좌표 기반)
**위치**: `extraction_strategies.py`
**활용**: RegionClassifier가 적극 사용

```python
# 매우 적극적으로 사용됨
- extract_sections_by_region_hints_only()
- _extract_page_by_region_hints()
- _apply_region_classification()
```

**용도**:
- Y좌표로 텍스트를 개념/본문/문제 영역으로 분류
- 영역별로 섹션 추출
- 섹션 타입 재분류

### ❌ region_text_examples (텍스트 예시)
**위치**: `extraction_strategies.py:266`
**활용**: TextBlockClassifier가 **한 번만** 사용

```python
# Line 70-73: 생성만 함
self.text_block_classifier = TextBlockClassifier(
    region_text_examples=config.get('region_text_examples', {}),
    config=self.config_obj
)

# Line 266: 딱 한 번만 호출!
text_result = self.text_block_classifier.classify_text_for_section_titles(
    line_text
)
```

**현재 용도**:
- 섹션 제목 판별할 때만 사용
- 그것도 폰트 기반 분류가 실패했을 때만
- 패턴 매칭 전 백업으로만 동작

## 문제점 상세

### 1. 귀중한 정보가 낭비됨

사용자가 수고해서 마킹한 영역에서 추출한 텍스트 예시:

```json
{
  "concept": [
    "핵심 개념",
    "학습 목표",
    "개념 정리",
    "용어 설명"
  ],
  "passage": [
    "작품 읽기",
    "지문 분석",
    "텍스트 이해"
  ],
  "problem": [
    "01",
    "02",
    "확인 문제",
    "연습 문제"
  ]
}
```

**이 정보를 활용할 수 있는 곳**:
- ❌ 섹션 전체 텍스트 분류 → **사용 안 함**
- ❌ 섹션 타입 검증 → **사용 안 함**
- ❌ 불확실한 섹션 보정 → **사용 안 함**
- ✅ 섹션 제목 판별 → **사용함** (하지만 백업으로만)

### 2. 파싱 정확도 개선 기회 상실

**시나리오 1**: Y좌표 기반 분류가 애매한 경우
```
Y좌표 0.50 (개념/본문 경계)
→ region_hints로는 애매함
→ 텍스트 내용: "핵심 개념"
→ region_text_examples와 비교하면 명확히 "concept"
→ 하지만 활용 안 함!
```

**시나리오 2**: 레이아웃이 불규칙한 경우
```
Y좌표 0.30 (본문 영역으로 판단됨)
→ 하지만 텍스트 내용: "01", "02", "03"
→ region_text_examples의 "problem"과 매우 유사
→ 실제로는 문제 영역인데 Y좌표만으로 본문으로 잘못 분류
→ 텍스트 유사도로 보정 가능한데 활용 안 함!
```

## 개선 방안

### 전략 1: 섹션 전체 텍스트 분류 추가

**위치**: `extraction_strategies.py:_extract_page_by_region_hints()`

```python
def _extract_page_by_region_hints(self, ocr_data, start_page):
    # ... 기존 코드 ...

    for section in sections:
        # 1. Y좌표로 초기 분류 (기존 방식)
        initial_type = self._classify_by_y_coordinate(section)

        # 2. 텍스트 유사도로 검증 (신규!)
        section_text = ' '.join(section['text'])
        text_result = self.text_block_classifier.classify_text(section_text)

        # 3. 텍스트 유사도가 높으면 우선
        if text_result.matched and text_result.score > 0.7:
            final_type = text_result.match_type
            logger.info(
                f"[섹션 분류] 텍스트 유사도로 보정: "
                f"{initial_type} → {final_type} (점수: {text_result.score:.2f})"
            )
        else:
            final_type = initial_type

        section['type'] = final_type
```

### 전략 2: 불확실한 섹션 보정

**위치**: `extraction_strategies.py:extract_by_pattern()`

```python
def extract_by_pattern(self, ocr_data):
    # ... 기존 섹션 추출 ...

    # 신뢰도가 낮은 섹션 재분류
    for section in sections:
        if section.get('confidence', 1.0) < 0.6:
            # 텍스트 유사도로 재분류 시도
            section_text = ' '.join(section['text'])
            text_result = self.text_block_classifier.classify_text(section_text)

            if text_result.matched and text_result.score > 0.7:
                old_type = section['type']
                section['type'] = text_result.match_type
                section['confidence'] = text_result.score
                logger.info(
                    f"[섹션 보정] {old_type} → {section['type']} "
                    f"(텍스트 유사도: {text_result.score:.2f})"
                )
```

### 전략 3: 이중 검증 시스템

**개념**:
1. Y좌표로 1차 분류 (빠르고 안정적)
2. 텍스트 유사도로 2차 검증 (정확도 향상)
3. 두 결과가 다르면 경고 로그

```python
def _classify_section_with_validation(self, section, page_height):
    # 1차: Y좌표 기반
    y_classification = self.region_classifier.classify_by_y(
        section['bbox'],
        page_height
    )

    # 2차: 텍스트 유사도 기반
    section_text = ' '.join(section['text'])
    text_classification = self.text_block_classifier.classify_text(section_text)

    # 검증
    if text_classification.matched:
        if y_classification != text_classification.match_type:
            logger.warning(
                f"[분류 불일치] Y좌표: {y_classification}, "
                f"텍스트: {text_classification.match_type} "
                f"(점수: {text_classification.score:.2f})"
            )

            # 텍스트 유사도가 높으면 우선
            if text_classification.score > 0.8:
                return text_classification.match_type

    return y_classification
```

### 전략 4: 경계 영역 처리 개선

**문제**: Y좌표가 두 영역의 경계에 있을 때
**해결**: 텍스트 유사도로 최종 결정

```python
def _classify_boundary_section(self, section, page_height):
    y_center = self._get_y_center(section['bbox'], page_height)

    # 경계 영역 판단 (±5%)
    is_boundary = any(
        abs(y_center - boundary) < 0.05
        for boundary in [0.3, 0.5, 0.7]  # 주요 경계들
    )

    if is_boundary:
        # 경계 영역이면 텍스트 유사도로 결정
        section_text = ' '.join(section['text'])
        text_result = self.text_block_classifier.classify_text(section_text)

        if text_result.matched:
            logger.info(
                f"[경계 영역] Y={y_center:.2f}, "
                f"텍스트 유사도로 결정: {text_result.match_type} "
                f"(점수: {text_result.score:.2f})"
            )
            return text_result.match_type

    # 일반 영역은 Y좌표로 분류
    return self.region_classifier.classify_by_y(section['bbox'], page_height)
```

## 구현 계획

### Phase 1: 기본 활용 (1-2일)
1. `_extract_page_by_region_hints()`에 텍스트 분류 추가
2. 섹션 전체 텍스트를 region_text_examples와 비교
3. 로깅 추가하여 효과 측정

### Phase 2: 검증 시스템 (2-3일)
4. 이중 검증 시스템 구현 (Y좌표 + 텍스트 유사도)
5. 불일치 케이스 로깅 및 분석
6. 신뢰도 낮은 섹션 재분류

### Phase 3: 경계 영역 개선 (1-2일)
7. 경계 영역 탐지 로직
8. 텍스트 유사도 우선 적용
9. 정확도 측정 및 튜닝

## 기대 효과

### 정확도 개선
- **현재**: Y좌표만으로 분류 → 경계 영역에서 오류 발생
- **개선 후**: Y좌표 + 텍스트 유사도 → 정확도 향상

### 예시

**Before**:
```
섹션: "01 02 03 확인 문제"
Y좌표: 0.52 (본문 영역)
→ 잘못 분류: "passage" ❌
```

**After**:
```
섹션: "01 02 03 확인 문제"
Y좌표: 0.52 (본문 영역)
텍스트 유사도: "problem" (0.85)
→ 올바른 분류: "problem" ✅
```

### 수치 예상
- 섹션 타입 정확도: 85% → 95%
- 경계 영역 정확도: 70% → 90%
- 레이아웃 불규칙 케이스 정확도: 60% → 85%

## 코드 수정 위치

### 주요 파일
1. **`extraction_strategies.py`** (가장 중요)
   - `_extract_page_by_region_hints()`: 섹션 분류 로직 추가
   - `extract_by_pattern()`: 불확실한 섹션 재분류
   - `_apply_region_classification()`: 텍스트 검증 추가

2. **`text_block_classifier.py`** (개선)
   - `classify_section_text()`: 새 메서드 추가 (섹션 전체 텍스트용)
   - 섹션 제목용과 본문용 임계값 분리

### 테스트 필요
- Y좌표와 텍스트 유사도가 일치하는 케이스
- Y좌표와 텍스트 유사도가 불일치하는 케이스
- 경계 영역 케이스
- 레이아웃 불규칙 케이스

## 결론

**핵심 문제**: region_text_examples라는 귀중한 정보가 거의 활용되지 않음

**해결책**:
1. 섹션 전체 텍스트를 region_text_examples와 비교
2. Y좌표 분류를 텍스트 유사도로 검증
3. 불확실한 섹션을 텍스트 유사도로 보정

**기대 효과**:
- 섹션 타입 정확도 10% 향상
- 경계 영역 처리 20% 개선
- 사용자가 마킹한 노력이 실제로 활용됨

이 개선사항을 구현하면 파싱 정확도가 크게 향상되고, 영역 마킹의 가치가 더욱 높아질 것입니다!
