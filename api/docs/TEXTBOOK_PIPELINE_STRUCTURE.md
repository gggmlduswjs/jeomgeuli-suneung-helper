# Textbook Pipeline 구조 및 PDF 전처리 가이드

`textbook_pipeline.py`의 전체 구조와 PDF 전처리 과정을 설명합니다.

## 전체 구조

### 클래스: `TextbookPipeline`

교재 PDF를 자동으로 파싱하여 학습 데이터를 생성하는 메인 파이프라인 클래스입니다.

## 주요 메서드 구조

### 1. 초기화 및 설정

```python
def __init__(
    self,
    subject: str,                    # 과목 ('literature', 'math1', 'english')
    dpi: int = 180,                  # PDF → 이미지 변환 해상도
    use_pdfplumber: bool = True,     # pdfplumber 사용 (텍스트 레이어 추출)
    use_yolo: bool = True,           # YOLO 레이아웃 감지
    yolo_api_key: Optional[str],     # Roboflow API 키
    # ... 기타 옵션
)
```

### 2. 메인 프로세스: `process_pdf()`

전체 파이프라인 실행 흐름:

```
1. PDF → 텍스트 추출
   ├─ pdfplumber (우선) - 텍스트 레이어 직접 추출
   └─ OCR (Fallback) - 이미지 변환 후 OCR

2. YOLO 레이아웃 감지 (선택적)
   └─ Roboflow API로 영역 자동 감지

3. 구조 파싱
   ├─ YOLO 기반 (우선)
   ├─ 통합 파이프라인
   └─ 레거시 방식 (Fallback)

4. 강의 콘텐츠 추출
   └─ 섹션, 본문, 문제 분리

5. 이미지 크롭
   └─ 개념, 본문, 문제 영역 이미지 추출

6. JSON 저장
   └─ lectures.json, lecture_XX.json, problem_XX.json
```

## PDF 전처리 과정

### 단계 1: PDF → 텍스트 추출

#### 방법 A: pdfplumber (우선, 기본값)

```python
def _extract_with_pdfplumber(self, pdf_path: Path) -> List[Dict[str, Any]]:
    """
    pdfplumber로 텍스트 레이어 직접 추출
    
    장점:
    - OCR보다 정확함 (텍스트 레이어 직접 읽기)
    - 매우 빠름 (이미지 변환 불필요)
    - 좌표 정보 정확
    
    단점:
    - 텍스트 레이어가 없는 스캔 PDF는 불가
    """
```

**프로세스:**
1. `pdfplumber.open()`으로 PDF 열기
2. 각 페이지에서 텍스트 추출 (`page.extract_text()`)
3. 단어별 좌표 정보 추출 (`page.extract_words()`)
4. OCR 형식과 호환되는 데이터 구조로 변환

#### 방법 B: OCR (Fallback)

```python
def _pdf_to_images(self, pdf_path: Path) -> List[Image.Image]:
    """
    PDF → 페이지 이미지 변환
    
    프로세스:
    1. pdf2image로 PDF를 이미지로 변환 (DPI: 180-200)
    2. 이미지 전처리 (ImageProcessor 사용)
    3. 페이지별로 저장
    """
```

**이미지 전처리 (`ImageProcessor.preprocess_image`):**
- 밝기 조정 (`ImageEnhance.Brightness`)
- 대비 조정 (`ImageEnhance.Contrast`)
- 선명도 향상 (`ImageFilter.SHARPEN`)
- 노이즈 제거

```python
def _ocr_with_cache(self, page_images: List[Image.Image], pdf_path: Path):
    """
    OCR 수행 (캐싱 지원)
    
    프로세스:
    1. 캐시 확인 (MD5 해시 기반)
    2. 캐시 없으면 OCR 수행
    3. 결과 캐싱
    """
```

**병렬 OCR (`_ocr_pages_parallel`):**
- `ProcessPoolExecutor` 사용
- 최대 8 워커 (또는 CPU 코어 수)
- Tesseract PSM 모드 6 (단일 균일한 텍스트 블록)

### 단계 2: YOLO 레이아웃 감지 (선택적)

```python
def _run_yolo_detection(
    self,
    all_ocr_data: List[Dict[str, Any]],
    page_images: Optional[List[Image.Image]],
    pdf_path: Path
) -> Optional[Dict[str, Any]]:
    """
    YOLO 기반 레이아웃 감지
    
    프로세스:
    1. LiteratureParsingStrategy.extract_with_yolo() 호출
    2. Roboflow API로 페이지별 영역 감지
    3. 클래스별 분류 (header, section, concept_box, sidebar, passage, question)
    """
```

**감지 클래스:**
- `header`: 강의 제목
- `section`: 개념 제목
- `concept_box`: 개념 내용
- `sidebar`: 세부 개념
- `passage`: 본문
- `question`: 문제

### 단계 3: 구조 파싱

#### YOLO 기반 파싱 (우선)

```python
def _convert_yolo_to_units(...):
    """YOLO 감지 결과를 lectures와 problems로 변환"""

def _convert_yolo_lectures_to_lecture_contents(...):
    """YOLO lectures의 units를 sections로 변환"""
```

#### 레거시 파싱 (Fallback)

```python
def _extract_lectures(...):
    """OCR 데이터에서 강의 목록 추출 (패턴 매칭)"""

def _extract_lecture_contents(...):
    """강의 콘텐츠 추출 (섹션, 본문)"""

def _extract_problems(...):
    """문제 목록 추출"""
```

### 단계 4: 이미지 크롭

```python
def _extract_concept_content_and_problem_images(...):
    """
    개념, 본문, 문제 영역 이미지 크롭
    
    프로세스:
    1. bbox 좌표로 영역 크롭
    2. 이미지 저장 (concepts_images/, content_images/, problems_images/)
    3. 메타데이터 JSON 저장
    """
```

### 단계 5: JSON 저장

```python
def _save_results(...):
    """
    결과를 JSON 파일로 저장
    
    생성 파일:
    - lectures.json: 강의 목록
    - lecture_XX.json: 각 강의의 세부 내용 (sections 포함)
    - problem_pXX_XX.json: 각 문제의 내용
    """
```

## 데이터 흐름

```
PDF 파일
  ↓
[전처리]
  ├─ pdfplumber → 텍스트 레이어 추출 (우선)
  └─ OCR → 이미지 변환 → OCR (Fallback)
  ↓
OCR 데이터 (all_ocr_data)
  ├─ text: List[str]          # 단어별 텍스트
  ├─ left, top, width, height # 단어별 좌표
  └─ page_num                 # 페이지 번호
  ↓
[YOLO 감지] (선택적)
  ↓
YOLO 감지 결과
  ├─ lectures: List[Dict]     # header → 강의
  ├─ problems: List[Dict]     # question → 문제
  ├─ passages: List[Dict]     # passage → 본문
  ├─ sections: List[Dict]     # section → 개념 제목
  ├─ concept_boxes: List[Dict] # concept_box → 개념 내용
  └─ sidebars: List[Dict]     # sidebar → 세부 개념
  ↓
[구조 파싱]
  ↓
Parsed Data
  ├─ lectures: List[Dict]     # 강의 목록
  ├─ lecture_contents: List[Dict]  # 강의 콘텐츠 (sections 포함)
  └─ problems: List[Dict]     # 문제 목록
  ↓
[JSON 저장]
  ├─ lectures.json
  ├─ lecture_XX.json
  └─ problem_XX.json
  ↓
[커리큘럼 생성] (books.py)
  ↓
Lesson & Unit (DB)
```

## 주요 메서드 상세

### PDF → 이미지 변환

```python
def _pdf_to_images(self, pdf_path: Path) -> List[Image.Image]:
    """
    PDF를 페이지 이미지로 변환
    
    최적화:
    - DPI: 180 (기본값, 속도와 품질 균형)
    - 첫 페이지 테스트로 빠른 피드백
    - 페이지 수 미리 확인
    - 병렬 이미지 처리 (ThreadPoolExecutor)
    """
```

### 이미지 전처리

```python
def _preprocess_image(self, image: Image.Image) -> Image.Image:
    """
    OCR 정확도 향상을 위한 이미지 전처리
    
    ImageProcessor.preprocess_image() 사용:
    - 밝기 조정
    - 대비 조정
    - 선명도 향상
    - 노이즈 제거
    """
```

### OCR 캐싱

```python
def _get_cache_key(self, pdf_path: Path, page_num: int) -> str:
    """MD5 해시 기반 캐시 키 생성"""

def _load_ocr_cache(self, cache_key: str) -> Optional[Dict]:
    """캐시된 OCR 결과 로드 (빈 데이터 검증 포함)"""

def _save_ocr_cache(self, cache_key: str, ocr_data: Dict):
    """OCR 결과 캐싱"""
```

**캐시 위치:** `api/data/{subject}/cache/`

### 병렬 OCR

```python
def _ocr_pages_parallel(
    self,
    page_images: List[Image.Image],
    pdf_path: Path
) -> List[Dict[str, Any]]:
    """
    병렬 OCR 처리
    
    최적화:
    - ProcessPoolExecutor 사용 (GIL 우회)
    - 최대 8 워커
    - 진행 상황 실시간 출력
    """
```

## 성능 최적화

### 1. pdfplumber 우선 사용
- 텍스트 레이어가 있는 PDF: **pdfplumber** (빠르고 정확)
- 스캔 PDF: **OCR** (느리지만 가능)

### 2. OCR 캐싱
- 동일한 PDF 재처리 시 캐시 사용
- MD5 해시 기반 키 생성
- 빈 데이터 자동 검증 및 삭제

### 3. 병렬 처리
- OCR: `ProcessPoolExecutor` (멀티프로세싱)
- 이미지 처리: `ThreadPoolExecutor` (I/O 바운드)

### 4. DPI 최적화
- 기본값: 180 DPI (속도와 품질 균형)
- 권장 범위: 180-200 DPI

### 5. 페이지 제한
- `max_pages` 옵션으로 테스트 시 일부 페이지만 처리

## 설정 파일

### config.json 구조

```json
{
  "subject": "literature",
  "lecture_title_patterns": [
    "\\d+강",
    "작품으로 이해하기 \\d+"
  ],
  "problem_number_pattern": "^\\d{2}$",
  "start_content_page": 8,
  "dpi": 180
}
```

**위치:** `api/data/{subject}/config.json`

## 출력 파일 구조

### lectures.json
```json
[
  {
    "lecture_id": 1,
    "title": "1강 | 시의 표현과 형식"
  },
  ...
]
```

### lecture_XX.json
```json
{
  "subject": "literature",
  "lecture_id": 1,
  "title": "1강 | 시의 표현과 형식",
  "sections": [
    {
      "title": "개념: section",
      "content": ["..."],
      "page": 11
    },
    ...
  ],
  "problems": ["01", "02", ...]
}
```

### problem_pXX_XX.json
```json
{
  "problem_id": "01",
  "page": 9,
  "bbox": [x1, y1, x2, y2],
  "text": "..."
}
```

## 디렉토리 구조

```
api/data/{subject}/
├── pdf/                    # 원본 PDF (선택)
├── pages/                  # 페이지 이미지 (PNG)
├── cache/                  # OCR 캐시
├── lectures/
│   ├── lectures.json       # 강의 목록
│   └── lecture_XX.json    # 각 강의 상세
├── problems/
│   └── problem_pXX_XX.json # 각 문제
├── concepts_images/        # 개념 영역 이미지
├── content_images/         # 본문 영역 이미지
└── problems_images/        # 문제 영역 이미지
```

## 에러 처리

### 빈 OCR 결과
- 캐시 자동 삭제
- Tesseract 설치 확인 안내
- 재시도 권장

### YOLO 감지 실패
- OCR 기반 파싱으로 자동 Fallback
- 오류 로그 출력

### 파싱 실패
- 경고 메시지 출력
- 가능한 원인 제시
- 해결 방법 안내

## 참고

- **pdfplumber**: 텍스트 레이어가 있는 PDF에 최적
- **OCR**: 스캔 PDF 또는 텍스트 레이어 없는 PDF
- **YOLO**: 레이아웃 자동 감지 (문학 과목만 지원)
- **캐싱**: 동일 PDF 재처리 시 속도 향상
