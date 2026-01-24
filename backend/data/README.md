# API Data 디렉토리

이 디렉토리는 API에서 생성하고 서빙하는 데이터 파일들을 보관합니다.

## 📁 디렉토리 구조

```
api/data/
└── literature/              # 문학 학습 데이터
    ├── lectures/            # 강의 JSON 파일
    │   ├── lectures.json    # 강의 목록
    │   ├── lecture_01.json  # 강의 상세 (1강)
    │   ├── lecture_02.json  # 강의 상세 (2강)
    │   └── ...
    ├── problems/            # 문제 JSON 파일
    │   ├── problem_p09_01.json
    │   ├── problem_p10_02.json
    │   └── ...
    ├── content/             # 본문 콘텐츠 JSON 파일
    │   ├── content_p09_01.json
    │   ├── content_p12_01.json
    │   └── ...
    ├── concepts_images/      # 개념 이미지 (크롭된 이미지)
    │   ├── concept_p08_01.png
    │   ├── concept_p08_02.png
    │   └── ...
    ├── content_images/       # 본문 이미지 (크롭된 이미지)
    │   ├── content_p09_01.png
    │   ├── content_p12_01.png
    │   └── ...
    ├── problems_images/      # 문제 이미지 (크롭된 이미지)
    │   ├── problem_p09_01.png
    │   ├── problem_p10_02.png
    │   └── ...
    ├── pages/                # 전체 페이지 이미지 (중간 생성물)
    │   ├── page_001.png
    │   ├── page_002.png
    │   └── ...
    ├── visualizations/       # 디버깅용 시각화 이미지 (선택적)
    │   ├── page_001_visualized.png
    │   ├── page_002_visualized.png
    │   └── ...
    └── config.json           # 파이프라인 설정 파일
```

## 📋 폴더 설명

### 필수 폴더 (프론트엔드에서 사용)

- **`lectures/`** - 강의 JSON 파일
  - `lectures.json`: 강의 목록 (API: `GET /literature/lectures`)
  - `lecture_XX.json`: 강의 상세 (API: `GET /literature/lectures/{lecture_id}`)

- **`problems/`** - 문제 JSON 파일
  - `problem_p{page}_{id}.json`: 문제 메타데이터 (API: `GET /literature/problems`)

- **`content/`** - 본문 콘텐츠 JSON 파일
  - `content_p{page}_{id}.json`: 본문 메타데이터 (API: `GET /literature/content`)

- **`concepts_images/`** - 개념 이미지
  - `concept_p{page}_{id}.png`: 개념 섹션 이미지 (API: `/api/data/literature/concepts_images/`)

- **`content_images/`** - 본문 이미지
  - `content_p{page}_{id}.png`: 본문 섹션 이미지 (API: `/api/data/literature/content_images/`)

- **`problems_images/`** - 문제 이미지
  - `problem_p{page}_{id}.png`: 문제 섹션 이미지 (API: `/api/data/literature/problems_images/`)

### 중간 생성물 폴더 (파이프라인 내부 사용)

- **`pages/`** - 전체 페이지 이미지
  - PDF에서 추출한 전체 페이지 이미지
  - 개념/본문/문제 이미지 크롭에 사용됨
  - **참고**: 재생성 가능하지만 크롭 작업에 필요하므로 유지 권장

- **`visualizations/`** - 디버깅용 시각화 이미지
  - 파이프라인 디버깅용 시각화 이미지
  - **참고**: 선택적, 필요시 삭제 가능

## 🔄 생성 방법

이 데이터는 `textbook_pipeline.py`를 통해 자동 생성됩니다:

```bash
cd api
python scripts/run_textbook_pipeline.py --subject literature --pdf "data/pdfs/2026 수능특강_ 문학.pdf"
```

## 📡 API 엔드포인트

이 데이터는 다음 API 엔드포인트를 통해 제공됩니다:

- `GET /literature/lectures` - 강의 목록
- `GET /literature/lectures/{lecture_id}` - 강의 상세
- `GET /literature/problems` - 문제 목록
- `GET /literature/problems/{problem_id}` - 문제 상세
- `GET /literature/content` - 본문 콘텐츠 목록
- `GET /literature/content/{content_id}` - 본문 콘텐츠 상세
- `GET /literature/images/concepts` - 개념 이미지 목록
- `GET /literature/images/content` - 본문 이미지 목록
- `GET /literature/images/problems` - 문제 이미지 목록
- `GET /api/data/literature/{file_path}` - 정적 파일 서빙

## 🗑️ 정리 가이드

### 정기적으로 정리할 수 있는 항목

1. **`visualizations/` 폴더**
   - 디버깅이 완료되면 삭제 가능
   - 필요시 파이프라인 재실행으로 재생성 가능

2. **`pages/` 폴더**
   - 크롭 작업에 필요하므로 일반적으로 유지
   - 디스크 공간이 부족한 경우에만 삭제 (재생성 가능)

### 삭제하면 안 되는 항목

- `lectures/`, `problems/`, `content/` - JSON 메타데이터
- `concepts_images/`, `content_images/`, `problems_images/` - 크롭된 이미지
- `config.json` - 파이프라인 설정

---

*마지막 업데이트: 2025년 1월*
