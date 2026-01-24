# 템플릿 추가 입력 필드 제안

## 📋 개요

현재 템플릿 시스템에 추가로 입력받으면 파싱 정확도를 크게 향상시킬 수 있는 정보들을 제안합니다.

## 🎯 우선순위별 제안

### 🔴 Priority 1: 즉시 효과 (높은 정확도 향상)

#### 1. **`font_info` (폰트 정보)**
**목적**: 제목/본문 구분, 섹션 타입 판별

**형식**:
```json
{
  "font_info": {
    "concept_title": {
      "size": 14.0,
      "weight": "bold",
      "family": "NanumGothic"
    },
    "passage_title": {
      "size": 12.0,
      "weight": "bold",
      "family": "NanumGothic"
    },
    "problem_number": {
      "size": 11.0,
      "weight": "normal",
      "family": "NanumGothic"
    },
    "body_text": {
      "size": 10.0,
      "weight": "normal",
      "family": "NanumGothic"
    }
  }
}
```

**활용 방법**:
- OCR 결과의 폰트 정보와 비교하여 섹션 타입 판별
- 패턴 매칭 실패 시 폰트 정보로 보정
- 제목/본문 자동 구분

**예상 효과**: 섹션 분류 정확도 +10-15%

---

#### 2. **`layout_info` (레이아웃 정보)**
**목적**: 페이지 구조 이해, 섹션 경계 판별

**형식**:
```json
{
  "layout_info": {
    "header_height": 50,
    "footer_height": 30,
    "margin": {
      "top": 20,
      "bottom": 20,
      "left": 30,
      "right": 30
    },
    "column_count": 2,
    "content_area": {
      "x_min": 30,
      "x_max": 570,
      "y_min": 50,
      "y_max": 800
    }
  }
}
```

**활용 방법**:
- 헤더/푸터 영역 제외하여 섹션 추출
- 컬럼 구조 고려한 텍스트 그룹화
- 여백 정보로 섹션 경계 판별

**예상 효과**: 섹션 경계 정확도 +15-20%

---

#### 3. **`problem_patterns` (문제 번호 패턴 상세)**
**목적**: 문제 추출 정확도 향상

**형식**:
```json
{
  "problem_patterns": {
    "number_format": "1.",  // "1)", "(1)", "①" 등
    "number_position": "start_of_line",  // "start_of_line", "inline", "margin"
    "answer_format": "①",  // "①", "(1)", "1)" 등
    "answer_position": "end_of_problem",  // "end_of_problem", "inline", "separate"
    "problem_separator": "\n\n",  // 문제 간 구분자
    "example_numbers": ["1.", "2.", "3.", "4.", "5."]
  }
}
```

**활용 방법**:
- 문제 번호 패턴으로 정확한 문제 추출
- 답안 형식 인식
- 문제 경계 자동 판별

**예상 효과**: 문제 추출 정확도 +20-25%

---

#### 4. **`section_spacing` (섹션 간 간격 정보)**
**목적**: 섹션 경계 판별

**형식**:
```json
{
  "section_spacing": {
    "concept_to_passage": 20,  // 픽셀 단위
    "passage_to_problem": 30,
    "problem_to_problem": 15,
    "min_section_height": 50,  // 최소 섹션 높이
    "max_section_height": 2000  // 최대 섹션 높이
  }
}
```

**활용 방법**:
- 섹션 간 간격으로 경계 판별
- 너무 작은/큰 섹션 필터링
- 섹션 그룹화

**예상 효과**: 섹션 경계 정확도 +10-15%

---

### 🟡 Priority 2: 중기 효과 (중간 정확도 향상)

#### 5. **`color_info` (색상 정보)**
**목적**: 강조 영역 인식, 섹션 타입 판별

**형식**:
```json
{
  "color_info": {
    "concept_background": "#F0F0F0",
    "problem_background": "#FFFFFF",
    "highlight_color": "#FFFF00",
    "important_text_color": "#FF0000"
  }
}
```

**활용 방법**:
- 배경색으로 섹션 타입 판별
- 강조 색상으로 중요 텍스트 인식
- 이미지 기반 매칭 보조

**예상 효과**: 섹션 분류 정확도 +5-10%

---

#### 6. **`image_caption_patterns` (이미지 캡션 패턴)**
**목적**: 이미지와 설명 연결

**형식**:
```json
{
  "image_caption_patterns": {
    "caption_prefix": ["그림", "Figure", "그림"],
    "caption_position": "below",  // "above", "below", "side"
    "caption_format": "그림 1",  // "그림 1", "Figure 1", "①" 등
    "example_captions": ["그림 1", "그림 2", "그림 3"]
  }
}
```

**활용 방법**:
- 이미지와 캡션 자동 연결
- 이미지 설명 추출
- 이미지 기반 섹션 분류

**예상 효과**: 이미지 처리 정확도 +15-20%

---

#### 7. **`table_patterns` (표 패턴)**
**목적**: 표 인식 및 추출

**형식**:
```json
{
  "table_patterns": {
    "has_border": true,
    "header_row_count": 1,
    "column_separator": "|",
    "row_separator": "-",
    "example_headers": ["항목", "내용", "비고"]
  }
}
```

**활용 방법**:
- 표 자동 인식
- 표 구조 추출
- 표 데이터 구조화

**예상 효과**: 표 추출 정확도 +25-30%

---

#### 8. **`lecture_structure_hints` (강의 구조 힌트)**
**목적**: 강의별 예상 섹션 구조

**형식**:
```json
{
  "lecture_structure_hints": {
    "default_structure": {
      "concept_count": 1,
      "passage_count": 1,
      "problem_count": 3
    },
    "by_lecture_type": {
      "theory": {
        "concept_count": 2,
        "passage_count": 0,
        "problem_count": 5
      },
      "practice": {
        "concept_count": 0,
        "passage_count": 1,
        "problem_count": 10
      }
    }
  }
}
```

**활용 방법**:
- 강의별 예상 섹션 수로 검증
- 누락된 섹션 감지
- 섹션 타입 보정

**예상 효과**: 섹션 누락 감지 +15-20%

---

### 🟢 Priority 3: 장기 효과 (추가 정확도 향상)

#### 9. **`page_number_format` (페이지 번호 형식)**
**목적**: 페이지 번호 인식 및 필터링

**형식**:
```json
{
  "page_number_format": {
    "position": "footer_center",  // "header", "footer", "margin"
    "format": "숫자",  // "숫자", "로마숫자", "한글"
    "example": "9",  // 예시
    "exclude_pages": [1, 2, 3]  // 제외할 페이지 (표지 등)
  }
}
```

**활용 방법**:
- 페이지 번호 자동 인식
- 표지/목차 페이지 필터링
- 페이지 범위 검증

**예상 효과**: 페이지 처리 정확도 +5-10%

---

#### 10. **`special_markers` (특수 마커 패턴)**
**목적**: 특수 기호로 섹션 구분

**형식**:
```json
{
  "special_markers": {
    "concept_marker": "●",
    "passage_marker": "◆",
    "problem_marker": "■",
    "important_marker": "★",
    "note_marker": "※"
  }
}
```

**활용 방법**:
- 특수 기호로 섹션 타입 판별
- 중요 텍스트 인식
- 노트/참고사항 추출

**예상 효과**: 섹션 분류 정확도 +5-8%

---

#### 11. **`text_alignment` (텍스트 정렬 정보)**
**목적**: 섹션 타입 판별 보조

**형식**:
```json
{
  "text_alignment": {
    "concept_title": "left",
    "passage_title": "center",
    "problem_number": "left",
    "body_text": "justify"
  }
}
```

**활용 방법**:
- 정렬 정보로 섹션 타입 판별
- 제목/본문 구분
- 레이아웃 검증

**예상 효과**: 섹션 분류 정확도 +3-5%

---

#### 12. **`content_density` (콘텐츠 밀도 정보)**
**목적**: 섹션 경계 판별

**형식**:
```json
{
  "content_density": {
    "concept_avg_lines": 10,
    "passage_avg_lines": 30,
    "problem_avg_lines": 5,
    "min_lines_per_section": 3,
    "max_lines_per_section": 100
  }
}
```

**활용 방법**:
- 섹션별 평균 라인 수로 검증
- 비정상적으로 짧은/긴 섹션 감지
- 섹션 경계 판별

**예상 효과**: 섹션 경계 정확도 +5-8%

---

## 📊 통합 활용 예시

### 예시: 다중 정보 기반 섹션 분류

```python
def classify_section_with_multiple_hints(
    self,
    section_text: str,
    font_info: Dict,
    layout_info: Dict,
    y_position: float
) -> str:
    """다중 정보를 활용한 섹션 분류"""
    
    scores = {
        'concept': 0.0,
        'passage': 0.0,
        'problem': 0.0
    }
    
    # 1. 텍스트 패턴 매칭 (기존)
    text_score = self._match_text_pattern(section_text)
    scores['concept'] += text_score.get('concept', 0) * 0.3
    
    # 2. 폰트 정보 매칭 (새로 추가)
    font_score = self._match_font_info(font_info)
    scores['concept'] += font_score.get('concept', 0) * 0.25
    
    # 3. 레이아웃 정보 매칭 (새로 추가)
    layout_score = self._match_layout_info(layout_info, y_position)
    scores['concept'] += layout_score.get('concept', 0) * 0.2
    
    # 4. region_hints (기존)
    region_score = self._match_region_hints(y_position)
    scores['concept'] += region_score.get('concept', 0) * 0.15
    
    # 5. 색상 정보 (새로 추가)
    color_score = self._match_color_info(section_text)
    scores['concept'] += color_score.get('concept', 0) * 0.1
    
    # 최고 점수 섹션 타입 반환
    return max(scores.items(), key=lambda x: x[1])[0]
```

---

## 🎯 구현 우선순위

### Phase 1 (즉시 구현)
1. ✅ `font_info` - 폰트 정보
2. ✅ `layout_info` - 레이아웃 정보
3. ✅ `problem_patterns` - 문제 번호 패턴 상세
4. ✅ `section_spacing` - 섹션 간 간격

### Phase 2 (단기 구현)
5. `color_info` - 색상 정보
6. `image_caption_patterns` - 이미지 캡션 패턴
7. `lecture_structure_hints` - 강의 구조 힌트

### Phase 3 (중기 구현)
8. `table_patterns` - 표 패턴
9. `page_number_format` - 페이지 번호 형식
10. `special_markers` - 특수 마커 패턴

### Phase 4 (장기 구현)
11. `text_alignment` - 텍스트 정렬 정보
12. `content_density` - 콘텐츠 밀도 정보

---

## 💡 자동 수집 방법

### 1. **자동 분석 도구 제공**
- PDF 업로드 시 자동으로 폰트/레이아웃 정보 추출
- 관리자가 확인/수정만 하면 됨

### 2. **샘플 페이지 기반 학습**
- 관리자가 샘플 페이지에서 섹션 선택
- 자동으로 패턴/폰트/레이아웃 정보 추출

### 3. **통계 기반 자동 생성**
- 파싱 결과 통계를 기반으로 자동 제안
- 관리자가 승인/수정

---

## 📈 예상 효과

| 추가 필드 | 정확도 향상 | 구현 난이도 | 우선순위 |
|----------|------------|------------|---------|
| font_info | +10-15% | 중간 | 높음 |
| layout_info | +15-20% | 중간 | 높음 |
| problem_patterns | +20-25% | 낮음 | 높음 |
| section_spacing | +10-15% | 낮음 | 높음 |
| color_info | +5-10% | 중간 | 중간 |
| image_caption_patterns | +15-20% | 높음 | 중간 |
| lecture_structure_hints | +15-20% | 낮음 | 중간 |
| table_patterns | +25-30% | 높음 | 낮음 |
| page_number_format | +5-10% | 낮음 | 낮음 |
| special_markers | +5-8% | 낮음 | 낮음 |
| text_alignment | +3-5% | 낮음 | 낮음 |
| content_density | +5-8% | 중간 | 낮음 |

**총 예상 효과**: 현재 정확도에서 **+30-50%** 향상 가능

---

## 🔧 구현 예시

### 예시 1: 폰트 정보 활용

```python
class FontBasedClassifier:
    """폰트 정보 기반 섹션 분류"""
    
    def __init__(self, font_info: Dict[str, Any]):
        self.font_info = font_info
    
    def classify_by_font(
        self,
        text_block: Dict[str, Any]
    ) -> Optional[str]:
        """폰트 정보로 섹션 타입 판별"""
        
        block_font_size = text_block.get('font_size', 0)
        block_font_weight = text_block.get('font_weight', 'normal')
        
        # concept_title과 비교
        concept_font = self.font_info.get('concept_title', {})
        if (abs(block_font_size - concept_font.get('size', 0)) < 1.0 and
            block_font_weight == concept_font.get('weight')):
            return 'concept'
        
        # passage_title과 비교
        passage_font = self.font_info.get('passage_title', {})
        if (abs(block_font_size - passage_font.get('size', 0)) < 1.0 and
            block_font_weight == passage_font.get('weight')):
            return 'passage'
        
        # problem_number와 비교
        problem_font = self.font_info.get('problem_number', {})
        if (abs(block_font_size - problem_font.get('size', 0)) < 1.0):
            return 'problem'
        
        return None
```

### 예시 2: 레이아웃 정보 활용

```python
class LayoutBasedValidator:
    """레이아웃 정보 기반 검증"""
    
    def __init__(self, layout_info: Dict[str, Any]):
        self.layout_info = layout_info
        self.content_area = layout_info.get('content_area', {})
    
    def is_in_content_area(
        self,
        bbox: List[float]
    ) -> bool:
        """bbox가 콘텐츠 영역 내에 있는지 확인"""
        
        x_min, y_min, x_max, y_max = bbox
        
        content_x_min = self.content_area.get('x_min', 0)
        content_x_max = self.content_area.get('x_max', 1000)
        content_y_min = self.content_area.get('y_min', 0)
        content_y_max = self.content_area.get('y_max', 1000)
        
        return (content_x_min <= x_min <= content_x_max and
                content_x_min <= x_max <= content_x_max and
                content_y_min <= y_min <= content_y_max and
                content_y_min <= y_max <= content_y_max)
    
    def filter_header_footer(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """헤더/푸터 영역 섹션 필터링"""
        
        header_height = self.layout_info.get('header_height', 0)
        footer_height = self.layout_info.get('footer_height', 0)
        page_height = 1000  # 실제 페이지 높이
        
        filtered = []
        for section in sections:
            bbox = section.get('bbox', [])
            y_min = bbox[1] if len(bbox) > 1 else 0
            y_max = bbox[3] if len(bbox) > 3 else page_height
            
            # 헤더/푸터 영역 제외
            if y_max < header_height or y_min > (page_height - footer_height):
                continue
            
            filtered.append(section)
        
        return filtered
```

---

## 🎯 결론

현재 템플릿 시스템에 **폰트 정보, 레이아웃 정보, 문제 패턴 상세, 섹션 간격** 정보를 추가하면 파싱 정확도를 크게 향상시킬 수 있습니다. 특히 **폰트 정보**와 **레이아웃 정보**는 구현이 비교적 간단하면서도 효과가 큽니다.

다음 단계로 이 필드들을 템플릿 스키마에 추가하고, UI에서 입력받을 수 있도록 구현하는 것을 제안합니다.
