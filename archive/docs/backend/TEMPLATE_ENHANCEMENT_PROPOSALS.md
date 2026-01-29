# 템플릿 관리자 입력 정보 활용 개선 제안

## 📋 현재 상태

### ✅ 현재 활용 중
- `region_text_examples`: 텍스트 유사도 매칭 (섹션 분류)
- `region_hints`: y 좌표 기반 타입 보정
- `toc_lecture_list`: 페이지 범위 계산, 강의 내 위치 계산

### ⏳ 저장만 하고 미활용
- `toc_text`: 전체 목차 텍스트 (저장만 함)
- `region_image_examples`: 영역 이미지 예시 (저장만 함)

## 🚀 개선 제안

### 1. `toc_text` 활용: 강의 제목 검증 및 보정

#### 현재 문제
- 강의 제목 추출이 패턴 매칭에만 의존
- OCR 오류나 패턴 실패 시 강의를 놓칠 수 있음

#### 개선 방안
```python
class LectureTitleValidator:
    """TOC 텍스트를 활용한 강의 제목 검증"""
    
    def __init__(self, toc_text: str, toc_lecture_list: List[Dict]):
        self.toc_text = toc_text
        self.toc_lecture_list = toc_lecture_list
        # TOC에서 강의 제목 키워드 추출
        self.lecture_keywords = self._extract_keywords()
    
    def validate_lecture_title(
        self, 
        extracted_title: str, 
        page_num: int
    ) -> Tuple[bool, Optional[str], float]:
        """추출된 강의 제목 검증 및 보정
        
        Returns:
            (유효성, 보정된 제목, 신뢰도)
        """
        # 1. TOC 텍스트에서 해당 페이지 근처의 강의 제목 찾기
        expected_lecture = self._find_expected_lecture(page_num)
        
        if not expected_lecture:
            return (False, None, 0.0)
        
        # 2. 추출된 제목과 예상 제목 비교
        similarity = self._calculate_similarity(
            extracted_title, 
            expected_lecture['title']
        )
        
        # 3. 유사도가 높으면 보정된 제목 반환
        if similarity > 0.7:
            return (True, expected_lecture['title'], similarity)
        elif similarity > 0.5:
            # 부분 매칭이면 경고하고 보정 제안
            return (False, expected_lecture['title'], similarity)
        else:
            return (False, None, similarity)
    
    def suggest_lecture_title(self, page_num: int) -> Optional[str]:
        """페이지 번호로 예상 강의 제목 제안"""
        lecture = self._find_expected_lecture(page_num)
        return lecture['title'] if lecture else None
```

**활용 시점**:
- `lecture_contents_extractor.py:_find_actual_lecture_start_page`에서 활용
- 강의 제목 추출 실패 시 TOC 텍스트로 보정

**예상 효과**:
- 강의 제목 추출 정확도 향상 (70% → 90%+)
- OCR 오류 보정
- 패턴 매칭 실패 시 폴백 제공

---

### 2. `toc_lecture_list` 활용: 강의 경계 검증

#### 현재 문제
- 강의 경계가 패턴 매칭에만 의존
- 강의가 겹치거나 누락될 수 있음

#### 개선 방안
```python
class LectureBoundaryValidator:
    """강의 목록을 활용한 경계 검증"""
    
    def validate_lecture_boundaries(
        self,
        extracted_lectures: List[Dict],
        toc_lecture_list: List[Dict]
    ) -> List[Dict]:
        """추출된 강의 목록을 TOC와 비교하여 검증 및 보정"""
        
        validated_lectures = []
        
        for extracted in extracted_lectures:
            # TOC에서 가장 유사한 강의 찾기
            best_match = self._find_best_match(extracted, toc_lecture_list)
            
            if best_match:
                # 페이지 범위 검증
                if self._validate_page_range(extracted, best_match):
                    # TOC 정보로 보정
                    extracted['start_page'] = best_match.get('start_page')
                    extracted['end_page'] = best_match.get('end_page')
                    extracted['validated'] = True
                else:
                    extracted['validated'] = False
                    extracted['warning'] = "페이지 범위 불일치"
            
            validated_lectures.append(extracted)
        
        # 누락된 강의 추가
        missing_lectures = self._find_missing_lectures(
            validated_lectures, 
            toc_lecture_list
        )
        validated_lectures.extend(missing_lectures)
        
        return validated_lectures
```

**활용 시점**:
- `unified_parser.py:parse` 메서드에서 강의 추출 후 검증
- `lecture_contents_extractor.py`에서 강의 경계 확인 시

**예상 효과**:
- 강의 누락 방지
- 강의 경계 정확도 향상
- 페이지 범위 자동 보정

---

### 3. `region_image_examples` 활용: 이미지 기반 매칭

#### 현재 문제
- 이미지 예시가 저장만 되고 활용 안 됨
- 시각적 패턴을 활용하지 못함

#### 개선 방안
```python
class ImageBasedMatcher:
    """이미지 예시를 활용한 섹션 매칭"""
    
    def __init__(self, region_image_examples: Dict[str, List[str]]):
        self.region_image_examples = region_image_examples
        # 이미지 특징 벡터 캐싱
        self._feature_cache = {}
    
    def match_by_image(
        self,
        section_image: Image.Image,
        section_bbox: List[float]
    ) -> Optional[Tuple[str, float]]:
        """이미지 기반 섹션 타입 매칭
        
        Returns:
            (타입, 신뢰도) 또는 None
        """
        if not self.region_image_examples:
            return None
        
        best_match = None
        best_score = 0.0
        
        # 각 타입의 예시 이미지와 비교
        for unit_type, example_paths in self.region_image_examples.items():
            for example_path in example_paths:
                if not Path(example_path).exists():
                    continue
                
                example_image = Image.open(example_path)
                
                # 이미지 유사도 계산 (SSIM, 구조적 유사도)
                similarity = self._calculate_image_similarity(
                    section_image,
                    example_image
                )
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = unit_type
        
        # 임계값 이상이면 매칭 성공
        if best_match and best_score > 0.6:
            return (best_match, best_score)
        
        return None
    
    def _calculate_image_similarity(
        self,
        img1: Image.Image,
        img2: Image.Image
    ) -> float:
        """이미지 유사도 계산 (SSIM 또는 특징 벡터 기반)"""
        # 방법 1: SSIM (구조적 유사도)
        # 방법 2: 특징 벡터 (CNN 기반)
        # 방법 3: 템플릿 매칭 (OpenCV)
        pass
```

**활용 시점**:
- `section_extractor.py:_extract_by_pattern`에서 패턴 매칭 실패 시
- `image_saver.py`에서 이미지 저장 전 타입 확인

**예상 효과**:
- 시각적 패턴 인식으로 정확도 향상
- 패턴 매칭 실패 시 폴백 제공
- 레이아웃 기반 분류 가능

---

### 4. `toc_lecture_list` 활용: 강의 구조 검증

#### 개선 방안
```python
class LectureStructureValidator:
    """강의 목록을 활용한 구조 검증"""
    
    def validate_lecture_structure(
        self,
        lecture_contents: List[Dict],
        toc_lecture_list: List[Dict]
    ) -> Dict[str, Any]:
        """강의 구조 검증 (concept/passage/problem 순서 등)"""
        
        validation_results = {
            'total_lectures': len(toc_lecture_list),
            'extracted_lectures': len(lecture_contents),
            'missing_lectures': [],
            'structure_warnings': []
        }
        
        # 1. 누락된 강의 찾기
        for toc_lecture in toc_lecture_list:
            lecture_id = toc_lecture.get('lecture_id')
            found = any(
                l.get('lecture_id') == lecture_id 
                for l in lecture_contents
            )
            if not found:
                validation_results['missing_lectures'].append(toc_lecture)
        
        # 2. 각 강의의 섹션 구조 검증
        for lecture_content in lecture_contents:
            sections = lecture_content.get('sections', [])
            
            # unit_order 확인
            expected_order = self.config.get('unit_order', [])
            actual_types = [s.get('type') for s in sections]
            
            # 순서 검증
            if not self._validate_unit_order(actual_types, expected_order):
                validation_results['structure_warnings'].append({
                    'lecture_id': lecture_content.get('lecture_id'),
                    'issue': 'unit_order_mismatch',
                    'expected': expected_order,
                    'actual': actual_types
                })
        
        return validation_results
```

**활용 시점**:
- 파싱 완료 후 검증 단계
- 결과 저장 전 최종 검증

**예상 효과**:
- 파싱 결과 품질 자동 검증
- 누락된 강의 자동 감지
- 구조 오류 사전 발견

---

### 5. 통계 정보 활용: 자동 개선 및 학습

#### 개선 방안
```python
class TemplateAutoImprover:
    """템플릿 통계 정보를 활용한 자동 개선"""
    
    def analyze_parsing_results(
        self,
        template: ParsingTemplate,
        parsing_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """파싱 결과 분석 및 템플릿 개선 제안"""
        
        analysis = {
            'region_text_examples_effectiveness': {},
            'region_hints_effectiveness': {},
            'suggested_improvements': []
        }
        
        # 1. region_text_examples 효과 분석
        for unit_type, examples in template.config.get('region_text_examples', {}).items():
            match_count = sum(
                1 for s in parsing_results.get('sections', [])
                if s.get('type') == unit_type 
                and s.get('matched_by_text_example', False)
            )
            total_count = sum(
                1 for s in parsing_results.get('sections', [])
                if s.get('type') == unit_type
            )
            
            effectiveness = match_count / total_count if total_count > 0 else 0
            analysis['region_text_examples_effectiveness'][unit_type] = effectiveness
            
            # 효과가 낮은 예시 제거 제안
            if effectiveness < 0.3:
                analysis['suggested_improvements'].append({
                    'type': 'remove_ineffective_example',
                    'unit_type': unit_type,
                    'reason': f'효과성 {effectiveness:.2%}'
                })
        
        # 2. region_hints 효과 분석
        region_based_count = sum(
            1 for s in parsing_results.get('sections', [])
            if s.get('from_region_hint', False)
        )
        total_sections = len(parsing_results.get('sections', []))
        
        if total_sections > 0:
            analysis['region_hints_effectiveness'] = {
                'usage_rate': region_based_count / total_sections,
                'average_confidence': self._calculate_avg_confidence(parsing_results)
            }
        
        # 3. 새로운 region_text_examples 제안
        # 자주 매칭되는 텍스트를 예시로 추가 제안
        frequent_texts = self._find_frequent_section_titles(parsing_results)
        for text, count in frequent_texts.items():
            if count >= 3:  # 3번 이상 나타나면
                analysis['suggested_improvements'].append({
                    'type': 'add_text_example',
                    'text': text,
                    'frequency': count
                })
        
        return analysis
    
    def update_template_from_analysis(
        self,
        template: ParsingTemplate,
        analysis: Dict[str, Any]
    ) -> ParsingTemplate:
        """분석 결과를 바탕으로 템플릿 자동 업데이트"""
        
        # 효과가 낮은 예시 제거
        for improvement in analysis.get('suggested_improvements', []):
            if improvement['type'] == 'remove_ineffective_example':
                unit_type = improvement['unit_type']
                # 효과가 낮은 예시 제거 로직
                pass
        
        # 새로운 예시 추가
        for improvement in analysis.get('suggested_improvements', []):
            if improvement['type'] == 'add_text_example':
                # 새로운 텍스트 예시 추가 로직
                pass
        
        return template
```

**활용 시점**:
- 파싱 완료 후 통계 수집
- 주기적으로 템플릿 자동 개선

**예상 효과**:
- 템플릿 품질 자동 향상
- 관리자 수동 작업 감소
- 파싱 정확도 지속적 개선

---

### 6. `toc_text` 활용: 강의 제목 패턴 학습

#### 개선 방안
```python
class PatternLearner:
    """TOC 텍스트에서 패턴 자동 학습"""
    
    def learn_lecture_title_patterns(
        self,
        toc_text: str
    ) -> List[str]:
        """TOC 텍스트에서 강의 제목 패턴 자동 추출"""
        
        patterns = []
        
        # TOC 텍스트를 줄 단위로 분석
        lines = toc_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 강의 제목 패턴 추출
            # 예: "1강 | 시의 표현과 형식" → "^\\d+강\\s*\\|\\s*[가-힣]+"
            if re.search(r'\d+강', line):
                # 패턴 생성 로직
                pattern = self._generate_pattern_from_line(line)
                if pattern:
                    patterns.append(pattern)
        
        # 중복 제거 및 정렬
        patterns = list(set(patterns))
        patterns.sort(key=lambda p: len(p), reverse=True)  # 긴 패턴 우선
        
        return patterns
```

**활용 시점**:
- 템플릿 생성 시 자동 패턴 추출
- 템플릿 업데이트 시 패턴 재학습

**예상 효과**:
- 패턴 수동 입력 불필요
- 교재별 패턴 자동 적응
- 패턴 정확도 향상

---

### 7. 통합 활용: 다단계 검증 시스템

#### 개선 방안
```python
class MultiStageValidator:
    """다단계 검증 시스템"""
    
    def validate_section(
        self,
        section: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """다단계 검증으로 섹션 타입 최종 결정"""
        
        validation_scores = {
            'text_example': 0.0,
            'region_hint': 0.0,
            'image_match': 0.0,
            'lecture_context': 0.0,
            'pattern_match': 0.0
        }
        
        # 1단계: region_text_examples 검증
        if self.region_text_examples:
            score = self._validate_by_text_examples(section)
            validation_scores['text_example'] = score
        
        # 2단계: region_hints 검증
        if self.region_hints:
            score = self._validate_by_region_hints(section)
            validation_scores['region_hint'] = score
        
        # 3단계: region_image_examples 검증 (이미지가 있는 경우)
        if section.get('image') and self.region_image_examples:
            score = self._validate_by_image(section)
            validation_scores['image_match'] = score
        
        # 4단계: 강의 컨텍스트 검증
        if context.get('lecture_info'):
            score = self._validate_by_lecture_context(section, context)
            validation_scores['lecture_context'] = score
        
        # 5단계: 패턴 매칭 검증
        score = self._validate_by_pattern(section)
        validation_scores['pattern_match'] = score
        
        # 가중 평균으로 최종 신뢰도 계산
        weights = {
            'text_example': 0.3,
            'region_hint': 0.25,
            'image_match': 0.2,
            'lecture_context': 0.15,
            'pattern_match': 0.1
        }
        
        final_confidence = sum(
            validation_scores[k] * weights.get(k, 0)
            for k in validation_scores
        )
        
        # 최종 타입 결정
        final_type = self._decide_final_type(
            section,
            validation_scores,
            final_confidence
        )
        
        return {
            'type': final_type,
            'confidence': final_confidence,
            'validation_scores': validation_scores,
            'method': 'multi_stage'
        }
```

**활용 시점**:
- `section_extractor.py:extract` 메서드에서 섹션 추출 후
- 최종 섹션 타입 결정 시

**예상 효과**:
- 다중 검증으로 정확도 향상
- 단일 방법 실패 시 다른 방법으로 보완
- 신뢰도 기반 타입 결정

---

## 📊 우선순위별 구현 계획

### Phase 1: 즉시 구현 (높은 효과)
1. ✅ **`toc_text` 활용: 강의 제목 검증** (정확도 향상) - 구현 완료
2. ✅ **`toc_lecture_list` 활용: 강의 경계 검증** (누락 방지) - 구현 완료

### Phase 2: 단기 구현 (중간 효과)
3. **`toc_lecture_list` 활용: 강의 구조 검증** (품질 보장)
4. **`toc_text` 활용: 패턴 자동 학습** (자동화)

### Phase 3: 중기 구현 (추가 효과)
5. **`region_image_examples` 활용: 이미지 기반 매칭** (시각적 인식)
6. **통계 정보 활용: 자동 개선** (지속적 향상)
7. **다단계 검증 시스템** (통합 활용)

---

## 💡 구현 예시

### 예시 1: 강의 제목 검증 통합
```python
# lecture_contents_extractor.py에 추가
def _find_actual_lecture_start_page(
    self,
    lecture_id: int,
    lecture_title: str,
    all_ocr_data: List[Dict[str, Any]],
    search_start_hint: int = None
) -> int:
    # 기존 로직...
    
    # TOC 텍스트로 보정 시도
    if self.config.get('toc_text'):
        validator = LectureTitleValidator(
            self.config.get('toc_text'),
            self.config.get('toc_lecture_list', [])
        )
        
        # 추출된 제목 검증
        is_valid, corrected_title, confidence = validator.validate_lecture_title(
            lecture_title,
            search_start_hint or self.start_content_page
        )
        
        if not is_valid and corrected_title:
            logger.info(
                f"강의 제목 보정: '{lecture_title}' -> '{corrected_title}' "
                f"(신뢰도: {confidence:.2f})"
            )
            lecture_title = corrected_title
    
    # 기존 로직 계속...
```

### 예시 2: 강의 경계 검증 통합
```python
# unified_parser.py에 추가
def parse(self, ocr_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    # 기존 파싱 로직...
    lectures = result.get('lectures', [])
    
    # 강의 경계 검증
    if self.config.get('toc_lecture_list'):
        validator = LectureBoundaryValidator()
        validated_lectures = validator.validate_lecture_boundaries(
            lectures,
            self.config.get('toc_lecture_list')
        )
        
        # 검증 결과 로깅
        missing_count = len([
            l for l in validated_lectures 
            if not l.get('validated', False)
        ])
        if missing_count > 0:
            logger.warning(f"{missing_count}개 강의 경계 검증 실패")
        
        result['lectures'] = validated_lectures
        result['validation'] = validator.get_validation_summary()
    
    return result
```

---

## 📈 예상 효과

| 개선 사항 | 정확도 향상 | 구현 난이도 | 우선순위 |
|----------|------------|------------|---------|
| toc_text 강의 제목 검증 | +15-20% | 낮음 | 높음 |
| toc_lecture_list 경계 검증 | +10-15% | 낮음 | 높음 |
| 강의 구조 검증 | +5-10% | 중간 | 중간 |
| 패턴 자동 학습 | +5-10% | 중간 | 중간 |
| 이미지 기반 매칭 | +10-15% | 높음 | 낮음 |
| 자동 개선 시스템 | +5-10% | 높음 | 낮음 |
| 다단계 검증 | +15-20% | 높음 | 중간 |

---

## 🎯 결론

현재 저장만 하고 있는 `toc_text`와 `region_image_examples`를 활용하면 파싱 정확도를 크게 향상시킬 수 있습니다. 특히 `toc_text`를 활용한 강의 제목 검증은 구현이 간단하면서도 효과가 큽니다.
