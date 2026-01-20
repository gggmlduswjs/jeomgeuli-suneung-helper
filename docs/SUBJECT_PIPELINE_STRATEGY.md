# 과목별 PDF 파이프라인 전략

## 현재 상황

- **문학**: 이미 구현 완료 ✅
- **수학Ⅰ**: 기본 구조만 존재 (config만 정의됨)
- **영어**: 기본 구조만 존재 (config만 정의됨)

## 권장 접근: 하이브리드 전략

### Phase 1: 옵션 1 방식 (즉시 구현)

**목적**: 빠르게 수학Ⅰ과 영어 지원 추가

**구조**:
```python
# api/app/services/textbook_pipeline.py
class TextbookPipeline:
    def _extract_lectures(self, ...):
        if self.subject == 'literature':
            return self._extract_lectures_literature(...)
        elif self.subject == 'math1':
            return self._extract_lectures_math1(...)
        elif self.subject == 'english':
            return self._extract_lectures_english(...)
    
    def _extract_sections(self, ...):
        if self.subject == 'literature':
            return self._extract_sections_literature(...)
        elif self.subject == 'math1':
            return self._extract_sections_math1(...)
        elif self.subject == 'english':
            return self._extract_sections_english(...)
```

**장점**:
- ✅ 빠른 구현 (1-2일)
- ✅ 기존 코드 재사용 가능
- ✅ 공통 로직(OCR, 이미지) 공유
- ✅ 즉시 사용 가능

**단점**:
- ⚠️ 파일이 커질 수 있음 (4000+ 줄)
- ⚠️ 과목 추가 시 if문 늘어남

### Phase 2: 옵션 2 방식 (리팩토링)

**목적**: 유지보수성과 확장성 향상

**구조**:
```
api/app/services/pdf_extract/
├── strategies/
│   ├── base_strategy.py       # 기본 전략 클래스
│   ├── literature_strategy.py # 문학 전략
│   ├── math1_strategy.py      # 수학Ⅰ 전략
│   └── english_strategy.py    # 영어 전략
└── extractor_factory.py       # 전략 팩토리
```

**장점**:
- ✅ 각 과목별로 독립적인 파일
- ✅ 확장성 높음 (새 과목 추가 쉬움)
- ✅ 테스트 용이
- ✅ 코드 가독성 향상

**단점**:
- ⚠️ 리팩토링 시간 필요 (3-5일)
- ⚠️ 기존 코드 대량 변경

## 최종 권장: Phase 1 우선 → 필요 시 Phase 2

### 즉시 (Phase 1)

1. **수학Ⅰ 구현** (1-2일)
   - `_extract_lectures_math1()` 메서드 추가
   - `_extract_sections_math1()` 메서드 추가 (개념/예제/유제 분리)
   - Config 확장

2. **영어 구현** (1-2일)
   - `_extract_lectures_english()` 메서드 추가
   - `_extract_passages_english()` 메서드 추가 (지문 추출)
   - Config 확장

3. **테스트 및 검증** (1일)
   - 실제 PDF로 테스트
   - 패턴 조정

### 나중에 (Phase 2, 선택적)

파일이 5000줄 이상이 되거나, 4개 이상의 과목이 필요할 때:
- 전략 클래스 패턴으로 리팩토링
- 각 과목별 파일 분리

## 구조 차이 요약

### 문학
```
강의(lecture) 
  → 섹션(section): 개념(concept) / 본문(content)
  → 문제(problem)
```

### 수학Ⅰ
```
단원(unit)
  → 섹션(section): 개념(concept) / 예제(example) / 유제(exercise)
  → 문제(problem)
```

### 영어
```
Unit
  → 지문(passage)
  → 문제(problem)
```

## 구현 우선순위

1. **수학Ⅰ** (우선)
   - 개념/예제/유제 구조가 명확
   - 문학과 유사한 패턴

2. **영어** (차순)
   - 지문 추출이 핵심
   - 문제 형식이 표준화되어 있음

## 결론

**지금은 옵션 1 방식으로 빠르게 구현하고, 나중에 필요할 때 옵션 2로 리팩토링하는 것이 최선입니다.**

- ✅ 빠른 결과물 (제작자 확대 전략에 부합)
- ✅ 점진적 개선 (기술 부채 최소화)
- ✅ 리스크 관리 (작은 단위로 검증)
