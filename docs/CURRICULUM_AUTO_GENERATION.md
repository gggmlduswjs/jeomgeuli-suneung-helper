# 커리큘럼 자동 생성 시스템

강의대본(HWP) 분석을 통해 수능특강 교재별 커리큘럼을 자동으로 생성하는 시스템 설계 문서입니다.

## 📋 목차

1. [문제 상황](#문제-상황)
2. [해결 방안](#해결-방안)
3. [구현 아이디어](#구현-아이디어)
4. [기술 스택](#기술-스택)
5. [구현 단계](#구현-단계)
6. [API 설계](#api-설계)

---

## 문제 상황

### 현재 상황

**수능특강 교재 구조**:

1. **수능특강 문학**
   - 교과서 개념 (개념, 작품으로 이해하기1, 문제1,2,3)
   - 고전시가 (본문, 문제)
   - 현대시 (본문, 문제)
   - 고전 산문 (본문, 문제)
   - 현대 소설 (본문, 문제)
   - 극 수필 (본문, 문제)
   - 갈래 복합 (본문, 문제)
   - 실전 1회 (본문, 문제)
   - 실전 2회 (본문, 문제)

2. **수능특강 수1**
   - 목차별로 (개념정리, 예제, 유제, LEVEL1,2,3)

3. **수능특강 영어**
   - 글의 목적 파악
   - 심경 분위기 파악
   - 요지 파악
   - 주장 파악
   - 함축적 의미 파악
   - 주제 파악
   - 도표
   - 내용 일치 불일치
   - 어법
   - 어휘
   - 빈칸 내용 추론
   - 흐름에 무관한 문장 찾기
   - 문단 내 글의 순서 파악
   - 문장 위치
   - 주어진 문장의 적합한 위치
   - 문단 요약하기
   - 장문 독해

### 문제점

1. **수동 커리큘럼 작성의 한계**
   - 각 교재마다 하나하나 다르게 커리를 짜야 함
   - 시간과 노력이 많이 소요됨
   - 일관성 유지 어려움

2. **유기적 연결의 필요성**
   - 모든 레슨이 유기적으로 연결되어야 함
   - 학습 순서와 의존성 파악 필요
   - 단계별 학습 경로 설계 필요

3. **강의대본 활용 부족**
   - 수능특강 PDF와 강의대본 HWP가 있음
   - 강의대본 분석으로 1강에서 어디 부분에서 자르고 넘어가는지 파악 가능
   - 하지만 현재는 수동으로 처리

---

## 해결 방안

### 핵심 아이디어

**강의대본(HWP) 자동 분석 → 커리큘럼 자동 생성**

1. **강의대본 분석**
   - 강 번호 추출
   - 섹션 분류 (OT, 개념, 예제, 문제 등)
   - 학습 단위 분할 지점 파악
   - PDF와의 매칭 정보 추출

2. **커리큘럼 자동 생성**
   - 교재 구조 파악 (문학/수1/영어)
   - 레슨 간 의존성 분석
   - 학습 순서 자동 결정
   - 유기적 연결 구조 생성

3. **자동화된 콘텐츠 제작**
   - 강의대본 → 학습 자료 자동 변환
   - 말하는 단위 자동 분할
   - 매뉴얼 규칙 자동 적용

---

## 구현 아이디어

### 1. 강의대본 분석 강화

```python
# api/app/services/curriculum_generator.py
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from app.services.lecture_script_parser import LectureScriptParser
from app.services.hwp_extract import extract_text_from_hwp

class CurriculumGenerator:
    """커리큘럼 자동 생성기"""
    
    def __init__(self, subject: str):
        self.subject = subject  # 'literature', 'math1', 'english'
        self.script_parser = LectureScriptParser(subject=subject)
        
    def analyze_lecture_script(self, hwp_path: Path) -> Dict[str, Any]:
        """
        강의대본 분석
        
        Returns:
            {
                'lesson_number': 1,
                'sections': [
                    {
                        'type': 'ot',
                        'content': '...',
                        'start_time': None,  # 추후 음성 동기화로 채움
                        'end_time': None,
                        'break_points': []  # 말하는 단위 분할 지점
                    },
                    {
                        'type': 'concept',
                        'content': '...',
                        'break_points': ['...', '...']
                    },
                    ...
                ],
                'pdf_references': [],  # PDF 페이지/문제 번호 참조
                'learning_units': []  # 학습 단위 목록
            }
        """
        # 1. HWP 파일에서 텍스트 추출
        script_text = extract_text_from_hwp(hwp_path)
        
        # 2. 강의대본 파싱
        parsed = self.script_parser.parse(script_text)
        
        # 3. 학습 단위 분할 지점 파악
        break_points = self._identify_break_points(parsed)
        
        # 4. PDF 참조 정보 추출
        pdf_refs = self._extract_pdf_references(parsed)
        
        # 5. 학습 단위 생성
        learning_units = self._create_learning_units(parsed, break_points)
        
        return {
            'lesson_number': parsed['lesson_number'],
            'sections': parsed['sections'],
            'break_points': break_points,
            'pdf_references': pdf_refs,
            'learning_units': learning_units
        }
    
    def _identify_break_points(self, parsed: Dict) -> List[Dict]:
        """
        말하는 단위 분할 지점 파악
        
        강의대본에서 자연스러운 분할 지점 찾기:
        - 문장 끝
        - "자, 그다음에..." 같은 전환 표현
        - "먼저...", "그리고...", "마지막으로..." 같은 순서 표현
        - 문제 번호 (문제1, 문제2 등)
        """
        break_points = []
        
        for section in parsed['sections']:
            content = section['content']
            paragraphs = section.get('paragraphs', [])
            
            for i, para in enumerate(paragraphs):
                # 전환 표현 감지
                transition_patterns = [
                    r'자,\s*그다음에',
                    r'먼저',
                    r'그리고',
                    r'마지막으로',
                    r'다음\s*페이지',
                    r'이제',
                    r'그럼',
                    r'문제\s*\d+',
                    r'예제\s*\d+',
                ]
                
                for pattern in transition_patterns:
                    if re.search(pattern, para, re.IGNORECASE):
                        break_points.append({
                            'section_type': section['type'],
                            'paragraph_index': i,
                            'text': para[:50] + '...',  # 미리보기
                            'transition_type': self._classify_transition(para)
                        })
                        break
        
        return break_points
    
    def _extract_pdf_references(self, parsed: Dict) -> List[Dict]:
        """
        PDF 참조 정보 추출
        
        강의대본에서 언급되는 PDF 내용:
        - "교과서 개념 1번 문제"
        - "고전시가 본문"
        - "수학Ⅰ 15페이지"
        """
        pdf_refs = []
        
        # 문제 번호 패턴
        problem_pattern = r'(문제|예제|유제)\s*(\d+)'
        # 페이지 참조 패턴
        page_pattern = r'(\d+)\s*페이지'
        # 교재 섹션 참조 패턴
        section_pattern = r'(교과서\s*개념|고전시가|현대시|고전\s*산문|현대\s*소설|극\s*수필|갈래\s*복합|실전)'
        
        for section in parsed['sections']:
            content = section['content']
            
            # 문제 참조 찾기
            for match in re.finditer(problem_pattern, content, re.IGNORECASE):
                pdf_refs.append({
                    'type': 'problem',
                    'number': int(match.group(2)),
                    'section': section['type'],
                    'context': self._extract_context(content, match.start(), match.end())
                })
            
            # 섹션 참조 찾기
            for match in re.finditer(section_pattern, content, re.IGNORECASE):
                pdf_refs.append({
                    'type': 'section',
                    'name': match.group(1),
                    'section': section['type'],
                    'context': self._extract_context(content, match.start(), match.end())
                })
        
        return pdf_refs
    
    def _create_learning_units(self, parsed: Dict, break_points: List[Dict]) -> List[Dict]:
        """
        학습 단위 생성
        
        말하는 단위로 분할된 학습 콘텐츠 단위
        """
        learning_units = []
        unit_index = 0
        
        for section in parsed['sections']:
            # 해당 섹션의 분할 지점 찾기
            section_breaks = [bp for bp in break_points 
                            if bp['section_type'] == section['type']]
            
            if not section_breaks:
                # 분할 지점이 없으면 섹션 전체를 하나의 단위로
                learning_units.append({
                    'unit_index': unit_index,
                    'section_type': section['type'],
                    'content': section['content'],
                    'key_points': section.get('key_points', []),
                    'pdf_references': []
                })
                unit_index += 1
            else:
                # 분할 지점 기준으로 여러 단위로 나누기
                paragraphs = section.get('paragraphs', [section['content']])
                current_unit_content = []
                
                for i, para in enumerate(paragraphs):
                    current_unit_content.append(para)
                    
                    # 분할 지점인지 확인
                    if any(bp['paragraph_index'] == i for bp in section_breaks):
                        learning_units.append({
                            'unit_index': unit_index,
                            'section_type': section['type'],
                            'content': '\n'.join(current_unit_content),
                            'key_points': self._extract_key_points_from_text('\n'.join(current_unit_content)),
                            'pdf_references': []
                        })
                        unit_index += 1
                        current_unit_content = []
                
                # 마지막 남은 내용
                if current_unit_content:
                    learning_units.append({
                        'unit_index': unit_index,
                        'section_type': section['type'],
                        'content': '\n'.join(current_unit_content),
                        'key_points': self._extract_key_points_from_text('\n'.join(current_unit_content)),
                        'pdf_references': []
                    })
                    unit_index += 1
        
        return learning_units
```

### 2. 교재별 커리큘럼 템플릿

```python
class CurriculumTemplate:
    """교재별 커리큘럼 템플릿"""
    
    LITERATURE_TEMPLATE = {
        'structure': [
            {'type': 'textbook_concept', 'order': 1, 'required': True},
            {'type': 'classical_poetry', 'order': 2, 'required': True},
            {'type': 'modern_poetry', 'order': 3, 'required': True},
            {'type': 'classical_prose', 'order': 4, 'required': True},
            {'type': 'modern_novel', 'order': 5, 'required': True},
            {'type': 'drama_essay', 'order': 6, 'required': True},
            {'type': 'genre_complex', 'order': 7, 'required': True},
            {'type': 'practice_1', 'order': 8, 'required': False},
            {'type': 'practice_2', 'order': 9, 'required': False},
        ],
        'dependencies': {
            'classical_poetry': ['textbook_concept'],
            'modern_poetry': ['textbook_concept'],
            'classical_prose': ['textbook_concept'],
            'modern_novel': ['textbook_concept'],
            'drama_essay': ['textbook_concept'],
            'genre_complex': ['classical_poetry', 'modern_poetry', 'classical_prose', 'modern_novel'],
            'practice_1': ['genre_complex'],
            'practice_2': ['practice_1'],
        }
    }
    
    MATH1_TEMPLATE = {
        'structure': [
            {'type': 'concept_review', 'order': 1, 'required': True},
            {'type': 'example', 'order': 2, 'required': True},
            {'type': 'exercise', 'order': 3, 'required': True},
            {'type': 'level1', 'order': 4, 'required': False},
            {'type': 'level2', 'order': 5, 'required': False},
            {'type': 'level3', 'order': 6, 'required': False},
        ],
        'dependencies': {
            'example': ['concept_review'],
            'exercise': ['example'],
            'level1': ['exercise'],
            'level2': ['level1'],
            'level3': ['level2'],
        }
    }
    
    ENGLISH_TEMPLATE = {
        'structure': [
            {'type': 'purpose', 'order': 1, 'required': True},
            {'type': 'mood', 'order': 2, 'required': False},
            {'type': 'main_idea', 'order': 3, 'required': False},
            {'type': 'argument', 'order': 4, 'required': False},
            {'type': 'implication', 'order': 5, 'required': False},
            {'type': 'topic', 'order': 6, 'required': False},
            {'type': 'chart', 'order': 7, 'required': False},
            {'type': 'consistency', 'order': 8, 'required': False},
            {'type': 'grammar', 'order': 9, 'required': False},
            {'type': 'vocabulary', 'order': 10, 'required': False},
            {'type': 'blank_inference', 'order': 11, 'required': False},
            {'type': 'irrelevant_sentence', 'order': 12, 'required': False},
            {'type': 'sentence_order', 'order': 13, 'required': False},
            {'type': 'sentence_position', 'order': 14, 'required': False},
            {'type': 'sentence_placement', 'order': 15, 'required': False},
            {'type': 'paragraph_summary', 'order': 16, 'required': False},
            {'type': 'long_reading', 'order': 17, 'required': False},
        ],
        'dependencies': {
            'mood': ['purpose'],
            'main_idea': ['purpose'],
            'argument': ['main_idea'],
            'long_reading': ['purpose', 'main_idea', 'topic'],
        }
    }
```

### 3. 커리큘럼 자동 생성

```python
class AutoCurriculumBuilder:
    """커리큘럼 자동 빌더"""
    
    def __init__(self, subject: str):
        self.subject = subject
        self.template = self._get_template(subject)
        self.generator = CurriculumGenerator(subject)
        
    def build_curriculum(self, hwp_files: List[Path], pdf_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        전체 커리큘럼 자동 생성
        
        Args:
            hwp_files: 강의대본 HWP 파일 리스트 (순서대로)
            pdf_path: 수능특강 PDF 파일 (선택)
            
        Returns:
            {
                'subject': 'literature',
                'lessons': [
                    {
                        'lesson_number': 0,
                        'title': '오리엔테이션',
                        'learning_units': [...],
                        'dependencies': [],
                        'estimated_time': 30
                    },
                    {
                        'lesson_number': 1,
                        'title': '교과서 개념',
                        'learning_units': [...],
                        'dependencies': [],
                        'estimated_time': 60
                    },
                    ...
                ],
                'learning_path': [
                    {'lesson': 0, 'order': 1},
                    {'lesson': 1, 'order': 2},
                    ...
                ]
            }
        """
        lessons = []
        
        # 1. 각 강의대본 분석
        for hwp_file in sorted(hwp_files):
            analysis = self.generator.analyze_lecture_script(hwp_file)
            
            lesson = {
                'lesson_number': analysis['lesson_number'],
                'title': self._extract_lesson_title(analysis),
                'learning_units': analysis['learning_units'],
                'sections': analysis['sections'],
                'pdf_references': analysis['pdf_references'],
                'dependencies': self._identify_dependencies(analysis),
                'estimated_time': self._estimate_time(analysis),
            }
            
            lessons.append(lesson)
        
        # 2. 학습 경로 생성 (의존성 기반)
        learning_path = self._create_learning_path(lessons)
        
        # 3. 유기적 연결 구조 생성
        connections = self._create_connections(lessons)
        
        return {
            'subject': self.subject,
            'lessons': lessons,
            'learning_path': learning_path,
            'connections': connections,
            'total_lessons': len(lessons),
            'total_units': sum(len(l['learning_units']) for l in lessons)
        }
    
    def _create_learning_path(self, lessons: List[Dict]) -> List[Dict]:
        """
        학습 경로 생성 (의존성 기반)
        
        의존성을 고려하여 학습 순서 결정
        """
        learning_path = []
        completed = set()
        
        # 의존성이 없는 레슨부터 시작
        while len(completed) < len(lessons):
            for lesson in lessons:
                if lesson['lesson_number'] in completed:
                    continue
                
                # 의존성 확인
                dependencies = lesson.get('dependencies', [])
                if all(dep in completed for dep in dependencies):
                    learning_path.append({
                        'lesson': lesson['lesson_number'],
                        'order': len(learning_path) + 1,
                        'title': lesson['title']
                    })
                    completed.add(lesson['lesson_number'])
        
        return learning_path
    
    def _create_connections(self, lessons: List[Dict]) -> List[Dict]:
        """
        레슨 간 유기적 연결 구조 생성
        
        - 이전 레슨에서 언급된 개념
        - 다음 레슨에서 활용할 내용
        - 관련 문제/예제 연결
        """
        connections = []
        
        for i, lesson in enumerate(lessons):
            # 다음 레슨과의 연결
            if i < len(lessons) - 1:
                next_lesson = lessons[i + 1]
                
                # 공통 키워드 찾기
                common_keywords = self._find_common_keywords(
                    lesson['learning_units'],
                    next_lesson['learning_units']
                )
                
                if common_keywords:
                    connections.append({
                        'from_lesson': lesson['lesson_number'],
                        'to_lesson': next_lesson['lesson_number'],
                        'type': 'sequential',
                        'keywords': common_keywords,
                        'description': f"{lesson['title']} → {next_lesson['title']}"
                    })
        
        return connections
```

### 4. PDF와 강의대본 매칭

```python
class PDFScriptMatcher:
    """PDF와 강의대본 매칭"""
    
    def match_pdf_to_script(self, pdf_content: Dict, script_analysis: Dict) -> Dict:
        """
        PDF 내용과 강의대본 매칭
        
        Args:
            pdf_content: PDF에서 추출한 구조화된 내용
            script_analysis: 강의대본 분석 결과
            
        Returns:
            {
                'matched_sections': [
                    {
                        'pdf_section': '교과서 개념',
                        'script_section': 'concept',
                        'pdf_problems': [1, 2, 3],
                        'script_problems': ['문제1', '문제2', '문제3'],
                        'confidence': 0.95
                    },
                    ...
                ]
            }
        """
        matched_sections = []
        
        # 강의대본에서 언급된 PDF 참조 정보
        pdf_refs = script_analysis['pdf_references']
        
        # PDF 섹션과 매칭
        for pdf_section in pdf_content.get('sections', []):
            for ref in pdf_refs:
                if self._is_match(pdf_section, ref):
                    matched_sections.append({
                        'pdf_section': pdf_section['name'],
                        'script_section': ref['section'],
                        'pdf_problems': pdf_section.get('problems', []),
                        'script_problems': self._extract_problem_numbers(ref),
                        'confidence': self._calculate_confidence(pdf_section, ref)
                    })
        
        return {'matched_sections': matched_sections}
```

---

## 기술 스택

### 기존 기능 활용
- **강의대본 파서** (`LectureScriptParser`) - 이미 구현됨
- **HWP 텍스트 추출** (`extract_text_from_hwp`) - 이미 구현됨
- **PDF 파싱** - 이미 구현됨

### 추가 필요 기능
- **자연어 처리**: 문장 분할, 키워드 추출
- **의존성 분석**: 레슨 간 관계 파악
- **템플릿 매칭**: 교재별 구조 템플릿

### AI/ML 활용 (선택적)
- **문장 유사도**: PDF와 강의대본 매칭 정확도 향상
- **키워드 추출**: 핵심 개념 자동 추출
- **의존성 그래프**: 레슨 간 관계 시각화

---

## 구현 단계

### Phase 1: 기본 커리큘럼 생성 (2주)

1. **강의대본 분석 강화** (1주)
   - 분할 지점 파악 로직 구현
   - PDF 참조 정보 추출
   - 학습 단위 생성

2. **커리큘럼 템플릿 정의** (3일)
   - 교재별 템플릿 작성
   - 의존성 규칙 정의

3. **기본 커리큘럼 생성** (4일)
   - 여러 강의대본 분석
   - 학습 경로 자동 생성

### Phase 2: PDF 매칭 및 연결 (1주)

1. **PDF-강의대본 매칭** (3일)
   - 참조 정보 매칭
   - 신뢰도 계산

2. **유기적 연결 구조** (4일)
   - 레슨 간 연결 생성
   - 키워드 기반 연결

### Phase 3: 자동화 통합 (1주)

1. **API 엔드포인트** (3일)
   - `POST /api/v1/curriculum/generate`
   - `GET /api/v1/curriculum/{subject}`

2. **프론트엔드 통합** (4일)
   - 커리큘럼 시각화
   - 학습 경로 표시

---

## API 설계

### 1. 커리큘럼 생성

```http
POST /api/v1/curriculum/generate
Content-Type: multipart/form-data

{
  "subject": "literature",
  "hwp_files": [File, File, ...],
  "pdf_file": File (optional)
}

Response:
{
  "curriculum_id": "cur_123",
  "subject": "literature",
  "total_lessons": 10,
  "total_units": 45,
  "learning_path": [...],
  "status": "completed"
}
```

### 2. 커리큘럼 조회

```http
GET /api/v1/curriculum/{curriculum_id}

Response:
{
  "curriculum_id": "cur_123",
  "subject": "literature",
  "lessons": [...],
  "learning_path": [...],
  "connections": [...]
}
```

### 3. 커리큘럼 수정

```http
PATCH /api/v1/curriculum/{curriculum_id}

{
  "lessons": [...],  # 수정된 레슨 정보
  "learning_path": [...]  # 수정된 학습 경로
}
```

---

## 예상 효과

1. **제작 시간 단축**
   - 커리큘럼 작성 시간 90% 단축
   - 수동 작업 최소화

2. **일관성 향상**
   - 교재별 표준 구조 유지
   - 학습 경로 일관성 보장

3. **확장성**
   - 새로운 교재 추가 시 템플릿만 정의
   - 자동으로 커리큘럼 생성

4. **유기적 연결**
   - 레슨 간 의존성 자동 파악
   - 학습 순서 최적화

---

## 사용 예시

```python
# 커리큘럼 자동 생성
from app.services.curriculum_generator import AutoCurriculumBuilder
from pathlib import Path

# 문학 교재 커리큘럼 생성
builder = AutoCurriculumBuilder(subject='literature')

# 강의대본 파일들
hwp_files = [
    Path('data/hwp/00강_오리엔테이션.hwp'),
    Path('data/hwp/01강_교과서개념.hwp'),
    Path('data/hwp/02강_고전시가.hwp'),
    # ...
]

# PDF 파일 (선택)
pdf_path = Path('data/pdfs/2026_수능특강_문학.pdf')

# 커리큘럼 생성
curriculum = builder.build_curriculum(hwp_files, pdf_path)

# 결과
print(f"총 {curriculum['total_lessons']}개 레슨")
print(f"총 {curriculum['total_units']}개 학습 단위")
print("\n학습 경로:")
for path_item in curriculum['learning_path']:
    print(f"{path_item['order']}. {path_item['title']}")
```

---

*작성일: 2024년*  
*마지막 업데이트: 2024년*
