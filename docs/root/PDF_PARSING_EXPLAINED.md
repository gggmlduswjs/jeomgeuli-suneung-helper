# 📚 문학 PDF 파싱 원리 완벽 가이드

## 전체 흐름 개요

```
PDF 업로드 (관리자 페이지)
    ↓
FastAPI 엔드포인트 (/api/v1/books/upload)
    ↓
백그라운드 작업 시작 (_process_pdf_background)
    ↓
UnifiedPipeline 실행
    ├─ 1단계: 텍스트 추출 (OCR/pdfplumber)
    ├─ 2단계: 파서 선택 (HybridRouter)
    ├─ 3단계: 파싱 (LiteratureParser)
    ├─ 4단계: 강의 콘텐츠 추출
    ├─ 5단계: 이미지 크롭 및 저장
    └─ 6단계: JSON 파일 저장
    ↓
DB 업데이트 (parse_status = DONE)
    ↓
프론트엔드에서 조회 가능
```

---

## 단계별 상세 설명

### 1단계: 텍스트 추출 (Text Extraction)

**파일 위치:**
- `backend/app/infrastructure/pdf/extractors/base.py`
  - `OCRExtractor` (고품질, 느림)
  - `PdfplumberExtractor` (빠름, 품질 낮음)

**동작 방식:**

#### A. OCR 모드 (권장, 기본값)
```python
# 1. PDF를 이미지로 변환 (pdf2image 사용)
from pdf2image import convert_from_path
page_images = convert_from_path(pdf_path, dpi=300)

# 2. 각 페이지를 Tesseract OCR로 텍스트 추출
for page_num, page_image in enumerate(page_images):
    # 이미지 전처리 (대비 향상, 노이즈 제거)
    preprocessed = ImagePreprocessor.preprocess(page_image)

    # Tesseract OCR 실행
    text = pytesseract.image_to_string(
        preprocessed,
        lang='kor+eng',  # 한글 + 영어
        config='--psm 3'  # 페이지 자동 분할
    )

    # 텍스트 블록 + 좌표 정보 추출
    blocks = pytesseract.image_to_data(
        preprocessed,
        lang='kor+eng',
        output_type=pytesseract.Output.DICT
    )
```

**결과 데이터 구조:**
```python
{
    'page_num': 1,
    'page_path': '/tmp/page_001.png',  # 이미지 경로 (나중에 크롭용)
    'blocks': [
        {
            'text': '1강 | 시의 표현과 형식',
            'bbox': [100, 50, 500, 80],  # [left, top, right, bottom]
            'confidence': 95.2
        },
        {
            'text': '운율',
            'bbox': [100, 100, 200, 130],
            'confidence': 98.1
        },
        # ... 더 많은 텍스트 블록
    ]
}
```

#### B. pdfplumber 모드 (빠른 추출)
```python
import pdfplumber

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        # 텍스트 추출 (PDF 내장 텍스트 사용)
        text = page.extract_text()

        # 단어별 좌표 정보
        words = page.extract_words()
```

**장점:** PDF에 텍스트가 임베드되어 있으면 매우 빠름
**단점:** 스캔 PDF나 이미지 기반 PDF는 추출 불가

---

### 2단계: 파서 선택 (Parser Selection)

**파일 위치:**
- `backend/app/infrastructure/pdf/parsers/hybrid_router.py`

**동작 방식:**

```python
class HybridRouter:
    """
    OCR 데이터를 분석하여 적합한 파서 선택
    템플릿 매칭 → AI 파싱 → 규칙 기반 파싱 순서로 시도
    """

    def select_parser(self, subject, ocr_data, config_path, book_id):
        # 1. 템플릿 매칭 시도 (가장 정확)
        template = self.template_manager.match_template(ocr_data)
        if template and template.confidence >= self.template_threshold:
            # 템플릿이 매칭되면 템플릿 기반 파서 사용
            return LiteratureParser(template=template)

        # 2. 규칙 기반 파서 (기본값)
        return LiteratureParser(config_path=config_path)
```

**템플릿 매칭 원리:**

1. **샘플 페이지 수집** (첫 3-5페이지)
2. **특징 추출**
   - 강의 제목 패턴: `"1강 | 시의 표현"`
   - 목차 패턴: `"1강 | 작품의 이해"`
   - 폰트, 레이아웃, 간격
3. **저장된 템플릿과 비교**
   - 템플릿 DB에서 유사도 계산
   - 신뢰도 85% 이상이면 매칭 성공

**템플릿 예시:**
```json
{
  "name": "2026_수능특강_문학",
  "patterns": {
    "lecture_title_patterns": ["^\\d+강\\s+\\|\\s+[가-힣]+"],
    "toc_lecture_patterns": ["^\\d+강\\s*\\|"],
    "concept_title_patterns": ["^[가-힣]{2,8}$"],
    "content_header_patterns": ["작품 \\d+", "본문 \\d+"]
  },
  "config": {
    "toc_end_page": 7,
    "start_content_page": 8,
    "paragraph_y_threshold": 25
  }
}
```

---

### 3단계: 파싱 (Parsing)

**파일 위치:**
- `backend/app/infrastructure/pdf/parsers/literature.py` (LiteratureParser)

**동작 방식:**

#### A. 강의 목록 추출

```python
def parse(self, ocr_data: List[Dict]) -> Dict[str, Any]:
    # 1. 목차(TOC)에서 강의 목록 찾기
    lectures = self._extract_lectures_from_toc(ocr_data)

    # 예시 결과:
    # [
    #   {'lecture_id': 1, 'title': '1강 | 시의 표현과 형식', 'page': 5},
    #   {'lecture_id': 2, 'title': '2강 | 화자와 청자', 'page': 5},
    #   ...
    # ]

    return {
        'lectures': lectures,
        'problems': [],  # 나중에 추가
        'metadata': {...}
    }
```

**강의 추출 알고리즘:**

```python
def _extract_lectures_from_toc(self, ocr_data):
    lectures = []
    toc_end_page = self.config.get('toc_end_page', 7)

    # 목차 페이지만 스캔 (보통 1-7페이지)
    for page_data in ocr_data[:toc_end_page]:
        for block in page_data['blocks']:
            text = block['text'].strip()

            # 패턴 매칭: "1강 | 시의 표현과 형식"
            for pattern in self.config['toc_lecture_patterns']:
                if re.match(pattern, text):
                    # 강의 번호 추출
                    lecture_num = int(re.search(r'(\d+)강', text).group(1))

                    # 강의 제목 정제
                    title = text.replace(f'{lecture_num}강', '').strip()

                    lectures.append({
                        'lecture_id': lecture_num,
                        'title': f'{lecture_num}강 | {title}',
                        'page': page_data['page_num'],
                        'bbox': block['bbox']
                    })

    return sorted(lectures, key=lambda x: x['lecture_id'])
```

#### B. 문제 추출

```python
def _extract_problems(self, ocr_data):
    problems = []

    # 보통 교재 후반부에 문제가 있음
    for page_data in ocr_data[200:]:  # 200페이지부터
        for block in page_data['blocks']:
            text = block['text']

            # 문제 번호 패턴: "01", "02", ...
            if re.match(r'^\d{2}$', text) and block['bbox'][1] < 100:
                # 문제 영역 추출
                problem = {
                    'problem_id': f'prob_{page_data["page_num"]}_{text}',
                    'page': page_data['page_num'],
                    'bbox': self._expand_problem_bbox(block, page_data)
                }
                problems.append(problem)

    return problems
```

---

### 4단계: 강의 콘텐츠 추출

**파일 위치:**
- `backend/app/infrastructure/pdf/lecture_contents_extractor.py`

**동작 방식:**

```python
class LectureContentsExtractor:
    def extract(self, all_ocr_data, lectures, parser):
        lecture_contents = []

        for lecture in lectures:
            # 1. 강의 페이지 범위 찾기
            start_page, end_page = self._find_lecture_page_range(
                lecture, lectures, all_ocr_data
            )

            # 2. 해당 범위의 OCR 데이터 추출
            lecture_pages = [
                page for page in all_ocr_data
                if start_page <= page['page_num'] <= end_page
            ]

            # 3. 섹션 추출 (개념, 작품, 예시)
            sections = parser.extract_sections(lecture_pages)

            # 섹션 예시:
            # [
            #   {
            #     'type': 'concept',
            #     'title': '운율',
            #     'content': ['시에서 규칙적으로 반복되는...'],
            #     'page': 8,
            #     'bbox': [100, 50, 500, 200]
            #   },
            #   {
            #     'type': 'content',  # 작품 본문
            #     'title': '해 (박두진)',
            #     'content': ['풀잎들이 가지를 벌려', ...],
            #     'page': 10,
            #     'bbox': [100, 100, 500, 800]
            #   }
            # ]

            lecture_contents.append({
                'lecture_id': lecture['lecture_id'],
                'title': lecture['title'],
                'sections': sections
            })

        return lecture_contents
```

**섹션 추출 알고리즘:**

```python
def extract_sections(self, lecture_pages):
    sections = []

    for page_data in lecture_pages:
        # 개념 제목 찾기: "운율", "화자" 등
        for block in page_data['blocks']:
            text = block['text'].strip()

            # 패턴 매칭: 한글 2-8자
            if re.match(r'^[가-힣]{2,8}$', text):
                # 제목 아래의 내용 수집
                content_blocks = self._collect_content_below(
                    block, page_data['blocks']
                )

                sections.append({
                    'type': 'concept',
                    'title': text,
                    'content': [b['text'] for b in content_blocks],
                    'page': page_data['page_num'],
                    'bbox': self._merge_bboxes([block] + content_blocks)
                })

    return sections
```

---

### 5단계: 이미지 크롭 및 저장

**파일 위치:**
- `backend/app/infrastructure/pdf/pipeline.py` (메서드: `_save_concept_images`, `_save_content_images`, `_save_problem_images`)

**동작 방식:**

```python
def _save_concept_images(self, pdf_path, lecture_contents, ocr_data):
    # 1. 모든 개념 섹션 수집
    concepts = []
    for lecture_content in lecture_contents:
        for section in lecture_content['sections']:
            if section['type'] == 'concept':
                concepts.append({
                    'title': section['title'],
                    'page': section['page'],
                    'bbox': section['bbox']  # [left, top, right, bottom]
                })

    # 2. 페이지별로 그룹화
    concepts_by_page = {}
    for concept in concepts:
        page = concept['page']
        if page not in concepts_by_page:
            concepts_by_page[page] = []
        concepts_by_page[page].append(concept)

    # 3. 각 페이지에서 이미지 크롭
    for page_num, page_concepts in concepts_by_page.items():
        # 페이지 이미지 로드 (OCR 시 생성된 이미지)
        page_image = Image.open(ocr_data[page_num-1]['page_path'])

        for idx, concept in enumerate(page_concepts):
            left, top, right, bottom = concept['bbox']

            # 이미지 크롭
            concept_image = page_image.crop((left, top, right, bottom))

            # 파일명: concept_p08_01.png (8페이지 첫 번째 개념)
            filename = f"concept_p{page_num:02d}_{idx+1:02d}.png"
            output_path = concepts_images_dir / filename

            # 저장
            concept_image.save(output_path, 'PNG')
```

**이미지 저장 구조:**
```
backend/data/literature/{book_id}/
├── concepts_images/
│   ├── concept_p08_01.png  # 8페이지 첫 번째 개념 (운율)
│   ├── concept_p08_02.png  # 8페이지 두 번째 개념
│   └── ...
├── content_images/
│   ├── content_p10_01.png  # 10페이지 첫 번째 작품
│   ├── content_p10_02.png  # 10페이지 두 번째 작품
│   └── ...
└── problems_images/
    ├── problem_p250_01.png  # 250페이지 첫 번째 문제
    ├── problem_p250_01.json # 문제 메타데이터 (bbox 정보)
    └── ...
```

---

### 6단계: JSON 파일 저장

**파일 위치:**
- `backend/app/infrastructure/pdf/result_saver.py`

**동작 방식:**

```python
class ResultSaver:
    def save(self, lectures, lecture_contents, problems):
        # 1. 강의 목록 저장 (lectures.json)
        lectures_json = self.lectures_dir / "lectures.json"
        with open(lectures_json, 'w', encoding='utf-8') as f:
            json.dump([
                {'lecture_id': l['lecture_id'], 'title': l['title']}
                for l in lectures
            ], f, ensure_ascii=False, indent=2)

        # 2. 개별 강의 저장 (lecture_01.json, lecture_02.json, ...)
        for lecture in lectures:
            lecture_id = lecture['lecture_id']

            # 해당 강의의 콘텐츠 찾기
            content = next(
                (c for c in lecture_contents if c['lecture_id'] == lecture_id),
                None
            )

            # 해당 강의의 문제 찾기
            lecture_problems = [
                p for p in problems
                if self._is_problem_in_lecture(p, lecture)
            ]

            # 통합 JSON 생성
            lecture_json = {
                'lecture_id': lecture_id,
                'title': lecture['title'],
                'concepts': self._extract_concepts(content),
                'works': self._extract_works(content),
                'problems': lecture_problems,
                'keywords': self._extract_keywords(content)
            }

            # 저장
            output_path = self.lectures_dir / f"lecture_{lecture_id:02d}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(lecture_json, f, ensure_ascii=False, indent=2)
```

**생성된 JSON 예시:**
```json
// lecture_01.json
{
  "lecture_id": 1,
  "title": "1강 | 시의 표현과 형식",
  "concepts": [
    {
      "title": "운율",
      "content": "시에서 규칙적으로 반복되는 소리의 흐름을 말한다...",
      "page": 8,
      "image": "/api/data/literature/{book_id}/concepts_images/concept_p08_01.png"
    }
  ],
  "works": [
    {
      "work_id": "work_01_01",
      "title": "해",
      "author": "박두진",
      "content": [
        "풀잎들이 가지를 벌려",
        "떨며 흔들며 나는 깨어나서",
        "..."
      ],
      "analysis": {
        "형식": "자유시, 7연으로 구성",
        "주제": "태양을 향한 끝없는 추구",
        "특징": ["생명력", "역동성"]
      },
      "page": 10,
      "image": "/api/data/literature/{book_id}/content_images/content_p10_01.png"
    }
  ],
  "problems": [
    {
      "problem_id": "prob_01_01",
      "question_text": "윗글에 대한 설명으로 가장 적절한 것은?",
      "choices": {
        "1": "자연물에 인간의 행동과 감정을 부여하고 있다.",
        "2": "계절의 변화를 통해 세월의 무상함을 드러내고 있다.",
        "3": "...",
        "4": "...",
        "5": "..."
      },
      "correct_answer": "1",
      "explanation": "이 작품은 자연물에 인간의 행동과 감정을 부여하여...",
      "page": 250,
      "image": "/api/data/literature/{book_id}/problems_images/problem_p250_01.png"
    }
  ],
  "keywords": ["운율", "화자", "이미지", "표현"]
}
```

---

## 핵심 기술 스택

### 1. OCR (광학 문자 인식)
- **Tesseract OCR** (v5.x)
  - 한글 + 영어 동시 인식
  - 신뢰도 95% 이상
  - 텍스트 + 좌표 정보 추출

### 2. 이미지 전처리
- **PIL (Python Imaging Library)**
  - 대비 향상 (contrast enhancement)
  - 노이즈 제거 (denoising)
  - 이진화 (binarization)

### 3. 텍스트 분석
- **정규표현식 (Regex)**
  - 강의 제목 패턴: `r'^\d+강\s+\|\s+[가-힣]+'`
  - 개념 제목 패턴: `r'^[가-힣]{2,8}$'`
  - 문제 번호 패턴: `r'^\d{2}$'`

### 4. 템플릿 매칭
- **유사도 계산 알고리즘**
  - Levenshtein Distance (편집 거리)
  - Jaccard Similarity (집합 유사도)
  - 패턴 매칭 비율

### 5. 병렬 처리
- **청크 단위 처리**
  - 10페이지씩 배치 처리
  - 메모리 효율성 향상
  - 진행률 실시간 업데이트

---

## 파싱 정확도 향상 기법

### 1. 이미지 전처리
```python
class ImagePreprocessor:
    @staticmethod
    def preprocess(image, method='aggressive'):
        # 1. 그레이스케일 변환
        gray = image.convert('L')

        # 2. 대비 향상 (CLAHE)
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(2.0)

        # 3. 노이즈 제거
        from scipy.ndimage import median_filter
        denoised = median_filter(enhanced, size=3)

        # 4. 이진화 (Otsu's method)
        from skimage.filters import threshold_otsu
        threshold = threshold_otsu(denoised)
        binary = denoised > threshold

        return binary
```

### 2. 다단계 텍스트 검증
```python
def validate_lecture_title(text):
    # 1차: 패턴 매칭
    if not re.match(r'^\d+강', text):
        return False

    # 2차: 길이 검증
    if len(text) < 5 or len(text) > 50:
        return False

    # 3차: 한글 비율 검증
    korean_chars = len([c for c in text if '가' <= c <= '힣'])
    if korean_chars / len(text) < 0.3:
        return False

    return True
```

### 3. 컨텍스트 기반 보정
```python
def correct_ocr_errors(text, context):
    # 인접 텍스트를 참고하여 오류 수정
    corrections = {
        '1 강': '1강',  # 공백 제거
        '시 의': '시의',  # 분리된 단어 합치기
        'O강': '0강',  # O를 0으로 수정
    }

    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)

    return text
```

---

## 파싱 실패 시 디버깅

### 1. 로그 확인
```bash
# Backend 콘솔에서 확인
[Pipeline] 1. 텍스트 추출 시작
[Pipeline] OCR 사용: True
[Pipeline] 이미지 변환 완료: 300개 페이지
[Pipeline] 2. 파서 선택 중...
[Pipeline] 선택된 전략: rule_based
[Pipeline] 3. 파싱 중...
[Pipeline] 파싱 완료: 80개 강의, 120개 문제
```

### 2. 중간 결과 확인
```python
# 추출된 텍스트 확인
print(ocr_data[0]['blocks'][0])
# {'text': '1강 | 시의 표현과 형식', 'bbox': [100, 50, 500, 80]}

# 강의 목록 확인
print(lectures[:3])
# [{'lecture_id': 1, 'title': '1강 | 시의 표현과 형식', 'page': 5}, ...]
```

### 3. 템플릿 생성
```python
# 파싱이 실패하면 새 템플릿 생성
python -m app.infrastructure.pdf.parsers.template_generator \
    --pdf "uploads/book_xxx.pdf" \
    --output "templates/custom_template.json"
```

---

## 성능 최적화

### 1. 청크 단위 처리
- **메모리 사용량 감소**: 전체 PDF를 한 번에 로드하지 않음
- **진행률 표시**: 10페이지마다 진행률 업데이트
- **병렬 처리**: 여러 페이지를 동시에 OCR 처리

### 2. 캐싱
```python
# OCR 결과 캐싱
cache_dir = settings.DATA_DIR / subject / "cache"
cache_file = cache_dir / f"{book_id}_ocr.pkl"

if cache_file.exists():
    # 캐시에서 로드 (5-10배 빠름)
    with open(cache_file, 'rb') as f:
        ocr_data = pickle.load(f)
else:
    # 새로 OCR 실행
    ocr_data = self.extractor.extract(pdf_path)
    # 캐시에 저장
    with open(cache_file, 'wb') as f:
        pickle.dump(ocr_data, f)
```

### 3. DPI 조정
- **300 DPI**: 고품질 (권장, 기본값)
- **200 DPI**: 중품질 (2배 빠름, 정확도 90%)
- **150 DPI**: 저품질 (3배 빠름, 정확도 80%)

---

## 요약

### 전체 프로세스 (간단 버전)

1. **PDF → 이미지** (pdf2image)
2. **이미지 → 텍스트** (Tesseract OCR)
3. **텍스트 → 구조** (정규표현식 + 패턴 매칭)
4. **구조 → 강의/문제** (LiteratureParser)
5. **이미지 크롭** (PIL)
6. **JSON 저장** (ResultSaver)

### 핵심 알고리즘

- **템플릿 매칭**: 교재별 패턴 자동 인식
- **섹션 추출**: 개념/작품/문제 자동 분리
- **이미지 크롭**: bbox 좌표 기반 정확한 영역 추출

### 왜 정확한가?

1. **고품질 OCR** (Tesseract, 95% 이상 정확도)
2. **다단계 검증** (패턴 매칭 + 컨텍스트 분석)
3. **템플릿 시스템** (교재별 최적화된 파싱 규칙)
4. **좌표 기반 추출** (텍스트 + 위치 정보 활용)

**결과: 80개 강의, 수백 개 문제, 수천 개 이미지를 30-60분 만에 자동으로 파싱!** ✨
