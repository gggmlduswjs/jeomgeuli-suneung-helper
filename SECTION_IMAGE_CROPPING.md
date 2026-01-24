# 섹션 이미지 자동 크롭 기능

## 개요

파싱 시 각 섹션(개념, 본문, 문제)의 이미지를 자동으로 크롭하여 저장하는 기능입니다.

## 작동 방식

### 1. 섹션 추출 후 자동 이미지 크롭

**파싱 플로우**:
```
PDF 업로드 → OCR 추출 → 파서 선택 → 섹션 추출 → 이미지 크롭 → 결과 반환
```

**이미지 크롭 시점**:
- 섹션 추출 완료 후
- 각 섹션의 bbox를 사용하여 자동으로 이미지 크롭
- 섹션 데이터에 image_path 필드 추가

### 2. 자동 처리

```python
# UnifiedTemplateParser에서 자동 처리
sections = extractor.extract(lecture_ocr_data)

# PDF 경로가 있으면 자동으로 이미지 크롭
if pdf_path and sections:
    sections_with_images = crop_section_images(
        pdf_path=pdf_path,
        sections=sections,
        book_id=book_id
    )
```

### 3. 이미지 저장 구조

**디렉토리 구조**:
```
backend/data/parsing_results/images/
└── {book_id}/
    ├── concept_p001_00.png    # 개념 섹션 (페이지 1, 인덱스 0)
    ├── concept_p001_01.png
    ├── passage_p001_00.png    # 본문 섹션
    ├── problem_p002_00.png    # 문제 섹션 (페이지 2)
    └── ...
```

**파일명 형식**:
```
{section_type}_p{page:03d}_{index:02d}.png

예시:
- concept_p001_00.png  → 1페이지, 개념 섹션, 첫 번째
- passage_p005_02.png  → 5페이지, 본문 섹션, 세 번째
- problem_p010_01.png  → 10페이지, 문제 섹션, 두 번째
```

## 섹션 데이터 구조

### SectionData (types.py)

```python
class SectionData(TypedDict, total=False):
    """섹션 데이터 구조 (개념, 본문 등)"""
    title: str                       # 섹션 제목
    type: str                        # 섹션 타입 (concept, passage, problem 등)
    page: int                        # 시작 페이지 번호
    bbox: Optional[BoundingBox]      # 바운딩 박스 [x0, y0, x1, y1]
    text: Optional[str]              # 섹션 본문
    paragraphs: Optional[List['ParagraphData']]  # 문단 리스트
    image_path: Optional[str]        # 섹션 이미지 경로 (NEW!)
```

### 파싱 결과 예시

```json
{
  "lectures": [
    {
      "lecture_id": 1,
      "title": "1강 | 시의 표현과 형식",
      "sections": [
        {
          "title": "핵심 개념",
          "type": "concept",
          "page": 9,
          "bbox": [100, 150, 500, 400],
          "text": "시의 표현 기법에는...",
          "image_path": "backend/data/parsing_results/images/book123/concept_p009_00.png"
        },
        {
          "title": "작품 읽기",
          "type": "passage",
          "page": 9,
          "bbox": [100, 450, 500, 800],
          "text": "해 (박두진)\n동해가...",
          "image_path": "backend/data/parsing_results/images/book123/passage_p009_00.png"
        },
        {
          "title": "확인 문제",
          "type": "problem",
          "page": 10,
          "bbox": [100, 200, 500, 600],
          "text": "01. 다음 작품의...",
          "image_path": "backend/data/parsing_results/images/book123/problem_p010_00.png"
        }
      ]
    }
  ]
}
```

## 구현 상세

### 1. BaseParser.crop_section_images()

**위치**: `backend/app/infrastructure/pdf/parsers/base.py`

```python
@staticmethod
def crop_section_images(
    pdf_path: Path,
    sections: List[SectionData],
    output_dir: Optional[Path] = None,
    book_id: Optional[str] = None
) -> List[SectionData]:
    """섹션별 이미지 크롭 및 저장

    Args:
        pdf_path: PDF 파일 경로
        sections: 섹션 리스트 (bbox 포함)
        output_dir: 이미지 저장 디렉토리 (None이면 자동 생성)
        book_id: 책 ID (저장 디렉토리 이름에 사용)

    Returns:
        이미지 경로가 추가된 섹션 리스트
    """
```

**처리 과정**:
1. 페이지별로 섹션 그룹화
2. PDF 페이지를 이미지로 변환 (300 DPI)
3. 각 섹션의 bbox를 사용하여 이미지 크롭
4. 파일명 생성 후 PNG로 저장
5. 섹션 데이터에 image_path 추가

### 2. UnifiedTemplateParser 통합

**위치**: `backend/app/infrastructure/pdf/parsers/unified_parser.py`

```python
def __init__(
    self,
    subject: str,
    config_path: Optional[Path] = None,
    template: Optional[ParsingTemplate] = None,
    enable_ai_parsing: bool = False,
    pdf_path: Optional[Path] = None,  # NEW!
    book_id: Optional[str] = None     # NEW!
):
    self.pdf_path = pdf_path
    self.book_id = book_id
    # ...
```

**extract_sections 메서드**:
```python
def extract_sections(self, lecture_ocr_data):
    # 섹션 추출
    result = extractor.extract(lecture_ocr_data)

    # 이미지 크롭 (PDF 경로가 있으면)
    if self.pdf_path and result.sections:
        sections_with_images = self.crop_section_images(
            pdf_path=self.pdf_path,
            sections=result.sections,
            book_id=self.book_id
        )
        return sections_with_images

    return result.sections
```

### 3. HybridRouter 업데이트

**위치**: `backend/app/infrastructure/pdf/parsers/hybrid_router.py`

```python
def select_parser(
    self,
    subject: str,
    ocr_data: List[OCRPageData],
    config_path: Optional[Path] = None,
    book_id: Optional[str] = None,
    pdf_path: Optional[Path] = None  # NEW!
) -> Tuple[BaseParser, str, JSONDict]:
```

**모든 파서 생성 메서드에 pdf_path, book_id 전달**:
- `_create_parser_with_template()`
- `_try_ai_parsing()`
- `_create_fallback_parser()`

### 4. Pipeline 통합

**위치**: `backend/app/infrastructure/pdf/pipeline.py`

```python
# 파서 선택 시 pdf_path 전달
parser, strategy, metadata = self.hybrid_router.select_parser(
    subject=self.subject,
    ocr_data=ocr_data,
    config_path=self.config_path,
    book_id=self.book_id,
    pdf_path=pdf_path  # NEW!
)
```

## 사용 예시

### 프론트엔드에서 이미지 표시

```javascript
// API 응답에서 섹션 이미지 경로 사용
const response = await fetch(`/api/v1/books/${bookId}/parse`);
const data = await response.json();

// 강의별로 섹션 이미지 표시
data.lectures.forEach(lecture => {
  lecture.sections.forEach(section => {
    if (section.image_path) {
      // 이미지 표시
      const img = document.createElement('img');
      img.src = `/api/v1/images/${section.image_path}`;
      img.alt = `${section.type} - ${section.title}`;
      container.appendChild(img);
    }
  });
});
```

### 섹션별 이미지 다운로드

```javascript
async function downloadSectionImage(section) {
  if (section.image_path) {
    const response = await fetch(`/api/v1/images/${section.image_path}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${section.type}_${section.title}.png`;
    a.click();
  }
}
```

## 이미지 품질 설정

**DPI 설정**: 300 DPI (고품질)
```python
convert_kwargs = {
    "dpi": 300,  # 고품질 이미지
    "first_page": page_num,
    "last_page": page_num,
}
```

**이미지 포맷**: PNG (무손실 압축)

**좌표 검증**: bbox 좌표가 이미지 범위 내에 있는지 자동 검증
```python
left = max(0, min(int(x_min), img_width - 1))
top = max(0, min(int(y_min), img_height - 1))
right = max(left + 1, min(int(x_max), img_width))
bottom = max(top + 1, min(int(y_max), img_height))
```

## 성능 최적화

### 1. 페이지별 일괄 처리
```python
# 페이지별로 섹션 그룹화
sections_by_page: Dict[int, List[SectionData]] = {}
for section in sections:
    page_num = section.get('page')
    if page_num not in sections_by_page:
        sections_by_page[page_num] = []
    sections_by_page[page_num].append(section)

# 각 페이지를 한 번만 이미지로 변환
for page_num, page_sections in sections_by_page.items():
    page_images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
    # 모든 섹션 크롭
```

### 2. 에러 처리
```python
# 이미지 크롭 실패해도 파싱 결과는 반환
try:
    sections_with_images = crop_section_images(...)
    return sections_with_images
except Exception as e:
    logger.error(f"섹션 이미지 크롭 실패: {e}")
    return sections  # 원본 섹션 반환
```

### 3. 로깅
```python
logger.info(f"[UnifiedParser] 섹션 이미지 크롭 시작: {len(sections)}개 섹션")
logger.info(f"[이미지 크롭] concept_p009_00.png 저장 (concept, 페이지 9)")
logger.info(f"[UnifiedParser] 섹션 이미지 크롭 완료: 15개 이미지 저장")
```

## 장점

### 1. 자동화
- 파싱 시 자동으로 이미지 크롭
- 별도 이미지 처리 단계 불필요
- bbox 기반 정확한 영역 추출

### 2. 유닛 단위 구성
- 각 유닛(concept, passage, problem)마다 독립적인 이미지
- 강의 자료 제작 시 바로 사용 가능
- 섹션별 이미지 관리 용이

### 3. 높은 품질
- 300 DPI 고해상도
- PNG 무손실 포맷
- 좌표 검증으로 오류 방지

### 4. 효율적인 저장
- book_id별 디렉토리 분리
- 명확한 파일명 규칙
- 페이지/인덱스 기반 정렬

## 활용 사례

### 1. 강의 자료 제작
```python
# 특정 강의의 모든 섹션 이미지 수집
lecture = result['lectures'][0]
for section in lecture['sections']:
    if section.get('image_path'):
        # 강의 슬라이드에 섹션 이미지 추가
        add_to_slide(section['image_path'], section['type'])
```

### 2. 교재 분석 도구
```python
# 섹션 타입별 이미지 그룹화
concept_images = [s['image_path'] for s in sections if s['type'] == 'concept']
passage_images = [s['image_path'] for s in sections if s['type'] == 'passage']
problem_images = [s['image_path'] for s in sections if s['type'] == 'problem']

# 통계 분석
print(f"개념: {len(concept_images)}개")
print(f"본문: {len(passage_images)}개")
print(f"문제: {len(problem_images)}개")
```

### 3. 콘텐츠 검증
```python
# 이미지가 누락된 섹션 찾기
missing_images = [
    s for s in sections
    if not s.get('image_path') and s.get('bbox')
]

if missing_images:
    logger.warning(f"{len(missing_images)}개 섹션 이미지 누락")
```

## 에러 처리

### 1. PDF 파일 없음
```python
if not pdf_path or not pdf_path.exists():
    logger.warning(f"PDF 파일 없음: {pdf_path}")
    return sections  # 이미지 없이 섹션만 반환
```

### 2. bbox 없음
```python
if not section.get('bbox'):
    continue  # bbox 없으면 스킵
```

### 3. 라이브러리 없음
```python
try:
    from pdf2image import convert_from_path
    from PIL import Image
except ImportError as e:
    logger.warning(f"필수 라이브러리 없음: {e}")
    return sections
```

## 결론

이 기능으로:
1. 파싱 시 자동으로 섹션 이미지 크롭
2. 각 유닛(concept, passage, problem)마다 독립적인 이미지
3. 파싱 결과에 image_path 필드 포함
4. 고품질 이미지 (300 DPI, PNG)
5. 효율적인 저장 구조 (book_id별 분리)

**사용자는 더 이상 수동으로 이미지를 크롭할 필요가 없으며, 파싱 결과에서 바로 섹션 이미지를 사용할 수 있습니다!** 🎉
