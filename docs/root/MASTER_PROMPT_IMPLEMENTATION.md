# 마스터 프롬프트 구현 완료

## 개요

새로운 마스터 프롬프트 기반 PDF 파싱 템플릿 생성 시스템을 구현했습니다. 이 시스템은 TOC(목차) 텍스트, 커리큘럼 구조 설문, 그리고 파싱 가이드 영역(bbox 힌트)을 활용하여 고정밀도 자동 파싱을 위한 `ParsingTemplate`을 생성합니다.

## 주요 변경 사항

### 1. 마스터 프롬프트 문서 업데이트

- `MASTER_PROMPT_generate_parsing_template_from_toc_v1.md` 파일을 새로운 구조로 업데이트
- 시스템 프롬프트, 배경 컨텍스트, 사용자 입력 형식, 작업 지침 등 포함
- 핵심 원칙: "파싱 정확도는 파싱 시작 전에 결정된다"

### 2. API 요청 모델 확장

`backend/app/routers/templates.py`에 새로운 모델 추가:

#### `ParsingGuideRegion`
- `page`: 페이지 번호 (1-based)
- `label`: 단위 레이블 (concept, passage, problem 등)
- `bbox`: 바운딩 박스 [x_min, y_min, x_max, y_max] (픽셀 좌표)

#### `CurriculumStructureSurvey`
- `is_lecture_based`: 강의 기반 구조 여부
- `lecture_units`: 강의 내 단위 목록
- `unit_order`: 단위 순서

#### `GenerateTemplateFromTOCRequest` 확장
- `year`: 교재 연도 (선택)
- `book_name`: 교재 이름 (선택)
- `curriculum_survey`: 커리큘럼 구조 설문 (선택)
- `parsing_guide_regions`: 파싱 가이드 영역 리스트 (선택)

### 3. 프롬프트 빌더 업데이트

`_build_toc_prompt()` 함수를 새 마스터 프롬프트 구조에 맞게 재작성:

- PDF 메타데이터 섹션
- 커리큘럼 구조 설문 섹션
- TOC 텍스트 섹션
- 파싱 가이드 영역 섹션 (bbox → 정규화된 비율 변환 포함)
- 명확한 출력 형식 지침

### 4. Region Hints 계산 기능

`_compute_region_hints()` 함수 추가:

- 파싱 가이드 영역들의 bbox를 페이지 비율(0.0-1.0)로 정규화
- 레이블별로 그룹화하여 y_min, y_max 범위 계산
- 템플릿의 `config.region_hints`에 저장

### 5. 템플릿 생성 로직 업데이트

`_generate_template_from_toc_via_openai()` 함수 업데이트:

- 새로운 입력 파라미터 처리
- LLM 출력에서 `unit_order` 및 `region_hints` 추출
- 제공된 `parsing_guide_regions`가 있으면 자동으로 region_hints 계산
- `config`에 `unit_order`와 `region_hints` 포함

### 6. 스키마 문서 업데이트

`PARSING_TEMPLATE_SCHEMA_V1.md` 업데이트:

- `unit_order` 필드 설명 추가
- `region_hints` 필드 상세 설명 추가 (형식 및 용도)

## 사용 예시

### 기본 사용 (TOC만 제공)

```python
{
  "subject": "literature",
  "name": "ebs_수능특강_literature_2026",
  "version": "2026",
  "toc_text": "1강 | 시의 표현과 형식\n해 (박두진) 009\n...",
  "toc_lecture_line_examples": [
    "1강 | 시의 표현과 형식",
    "2강 | 시의 내용"
  ],
  "save": false
}
```

### 전체 기능 사용 (커리큘럼 설문 + Region 힌트)

```python
{
  "subject": "literature",
  "name": "ebs_수능특강_literature_2026",
  "version": "2026",
  "year": 2026,
  "book_name": "EBS 수능특강 문학",
  "toc_text": "1강 | 시의 표현과 형식\n...",
  "curriculum_survey": {
    "is_lecture_based": true,
    "lecture_units": ["concept", "passage", "problem"],
    "unit_order": ["concept", "passage", "problem"]
  },
  "parsing_guide_regions": [
    {
      "page": 12,
      "label": "concept",
      "bbox": [120, 90, 980, 320]
    },
    {
      "page": 14,
      "label": "passage",
      "bbox": [110, 340, 980, 820]
    },
    {
      "page": 16,
      "label": "problem",
      "bbox": [120, 600, 980, 980]
    }
  ],
  "toc_lecture_line_examples": [
    "1강 | 시의 표현과 형식",
    "2강 | 시의 내용"
  ],
  "save": true
}
```

## 생성된 템플릿 구조

생성된 템플릿은 다음과 같은 구조를 가집니다:

```json
{
  "name": "ebs_수능특강_literature_2026",
  "subject": "literature",
  "version": "2026",
  "patterns": {
    "lecture_title_patterns": [...],
    "toc_lecture_patterns": [...],
    "concept_title_patterns": [...],
    "content_header_patterns": [...],
    "section_title_patterns": [...],
    "problem_number_pattern": "..."
  },
  "config": {
    "toc_end_page": 7,
    "start_content_page": 8,
    "paragraph_y_threshold": 25,
    "unit_order": ["concept", "passage", "problem"],
    "region_hints": {
      "concept": {"y_min": 0.05, "y_max": 0.35},
      "passage": {"y_min": 0.3, "y_max": 0.7},
      "problem": {"y_min": 0.6, "y_max": 0.95}
    }
  },
  "confidence": 0.85,
  "sample_texts": [...]
}
```

## 핵심 설계 원칙

1. **사전 구조 가이드 우선**: 파싱 전에 구조를 이해하고 템플릿 생성
2. **최소한의 인간 개입**: 설문조사처럼 간단한 입력으로 자동화
3. **일반화된 규칙**: 수동 영역 표시를 페이지별 오버라이드가 아닌 템플릿 레벨 규칙으로 변환
4. **재사용 가능성**: 동일 교재의 향후 업로드에 템플릿 재사용

## 다음 단계

1. 프론트엔드에서 YOLO-style bbox 마킹 UI 구현
2. 파서에서 `region_hints` 활용 로직 구현
3. 템플릿 생성 API 엔드포인트 테스트
4. 실제 교재로 템플릿 생성 및 파싱 정확도 검증

## 참고 파일

- `MASTER_PROMPT_generate_parsing_template_from_toc_v1.md`: 마스터 프롬프트 문서
- `backend/app/routers/templates.py`: 템플릿 생성 API 구현
- `PARSING_TEMPLATE_SCHEMA_V1.md`: 템플릿 스키마 문서
