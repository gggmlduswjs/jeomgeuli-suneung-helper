# 백엔드 폴더 정리 및 리팩토링 전략

## [1] 현재 구조의 문제점

### 1.1 빈 폴더

**문제**: 사용하지 않는 빈 폴더
```
❌ app/pipelines/  (비어있음)
```

**원인**: 폴더는 생성했지만 실제로 사용하지 않음

### 1.2 백업 파일 혼재

**문제**: 소스 코드 폴더에 백업 파일 존재
```
❌ app/services/textbook_pipeline.BACKUP.py (200KB)
✅ app/services/textbook_pipeline.py
```

**원인**: 리팩토링 시 백업 파일을 만들었으나 제거하지 않음

### 1.3 대량의 캐시 파일

**문제**: __pycache__ 디렉토리가 Git에 포함됨
```
❌ 1,966개의 캐시 파일/폴더
app/__pycache__/
app/core/__pycache__/
app/db/__pycache__/
app/parsing/__pycache__/
app/routers/__pycache__/
app/schemas/__pycache__/
app/services/__pycache__/
app/utils/__pycache__/
app/parsing/strategies/__pycache__/
```

**원인**: .gitignore에 __pycache__가 제대로 설정되지 않음

### 1.4 Archived 폴더 정리 필요

**현재**:
```
archived/
├── ai_lecture_generator.py
├── ai_text_postprocessor.py
├── braille_convert.py
├── image_extractor.py
├── literature_extractor.py
├── math_ocr.py
├── pdf_cropper.py
├── toc_parser.py
└── tts_reader.py
```

**문제**:
- 9개 파일이 있지만 실제 사용 여부 불명확
- 참조되고 있으면 삭제하면 안 됨

### 1.5 Scripts 폴더 구조

**현재**:
```
scripts/
├── build_training_dataset.py
├── cleanup_books.py
├── delete_book.py
├── delete_curriculum.py
├── run_textbook_pipeline.py
├── examples/
│   ├── run_pipeline_example.py
│   └── test_parser.py
└── experiments/
    ├── pdf_region_capturer.py
    └── pdf_region_detector.py
```

**문제**:
- 실행 스크립트와 삭제 스크립트가 혼재
- 용도별 분류가 불명확

### 1.6 문서 파일 과다

**문제**: 루트 디렉토리에 리팩토링 문서가 너무 많음
```
api/
├── REFACTORING_PDF_EXTRACTION.md
├── REFACTORING_PROGRESS.md
├── REFACTORING_STRATEGY.md
└── REFACTORING_SUMMARY.md
```

**원인**: 리팩토링 과정에서 생성된 문서들

---

## [2] 백엔드 정리 전략

### Phase 1: 즉시 정리 (Cleanup)

**목표**: 불필요한 파일/폴더 제거

#### 1.1 빈 폴더 제거
```bash
rm -rf app/pipelines/
```

#### 1.2 백업 파일 제거
```bash
rm app/services/textbook_pipeline.BACKUP.py
```

#### 1.3 캐시 파일 제거 (.gitignore 추가)
```bash
# .gitignore에 추가
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# 기존 캐시 파일 제거
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
```

### Phase 2: 문서 정리

**목표**: 리팩토링 문서를 docs/ 폴더로 이동

```bash
mkdir -p docs/refactoring
mv REFACTORING_*.md docs/refactoring/
```

**최종 구조**:
```
docs/
├── refactoring/
│   ├── REFACTORING_PDF_EXTRACTION.md
│   ├── REFACTORING_PROGRESS.md
│   ├── REFACTORING_STRATEGY.md
│   └── REFACTORING_SUMMARY.md
└── README_PARSER.md (현재 위치 유지)
```

### Phase 3: Scripts 재구성

**목표**: 용도별 분류

#### 3.1 권장 구조
```
scripts/
├── pipeline/              (신규, 파이프라인 실행)
│   └── run_textbook_pipeline.py
│
├── admin/                 (신규, 관리자 도구)
│   ├── cleanup_books.py
│   ├── delete_book.py
│   └── delete_curriculum.py
│
├── ml/                    (신규, ML 관련)
│   └── build_training_dataset.py
│
├── examples/              (유지)
│   ├── run_pipeline_example.py
│   └── test_parser.py
│
└── experiments/           (유지)
    ├── pdf_region_capturer.py
    └── pdf_region_detector.py
```

### Phase 4: Archived 폴더 확인

**목표**: 사용하지 않는 파일 확인 후 처리

#### 4.1 참조 확인
```bash
# 각 파일이 import되는지 확인
grep -r "from archived" app/
grep -r "import.*ai_lecture_generator" app/
grep -r "import.*ai_text_postprocessor" app/
# ... 나머지 파일들도 확인
```

#### 4.2 처리 방침
- **참조됨**: archived/ 유지 또는 app/으로 이동
- **참조 없음**: 삭제 또는 docs/archived/로 이동 (참고용)

### Phase 5: 최종 구조 정리

**목표**: 깨끗하고 일관된 구조

#### 5.1 최종 디렉토리 구조
```
api/
├── app/
│   ├── assembly/          ✅ (조립 레이어)
│   ├── core/              ✅ (핵심 설정)
│   ├── db/                ✅ (데이터베이스)
│   ├── extraction/        ✅ (추출 레이어)
│   ├── parsing/           ✅ (파싱 레이어)
│   │   ├── block_parsers/
│   │   ├── classifiers/
│   │   └── strategies/
│   ├── routers/           ✅ (API 라우터)
│   ├── schemas/           ✅ (데이터 스키마)
│   ├── services/          ✅ (비즈니스 로직)
│   └── utils/             ✅ (유틸리티)
│
├── archived/              ⚠️ (참조 확인 후 처리)
├── data/                  ✅ (데이터 파일)
├── docs/                  ✅ (문서)
│   ├── refactoring/       (신규)
│   └── README_PARSER.md
├── scripts/               ✅ (스크립트)
│   ├── pipeline/          (신규)
│   ├── admin/             (신규)
│   ├── ml/                (신규)
│   ├── examples/
│   └── experiments/
├── tests/                 ✅ (테스트)
└── venv/                  ✅ (가상환경, Git 무시)
```

---

## [3] 실행 체크리스트

### 단계 1: 즉시 정리 (5분)

- [ ] **빈 폴더 삭제**
  ```bash
  cd api
  rm -rf app/pipelines/
  ```

- [ ] **백업 파일 삭제**
  ```bash
  rm app/services/textbook_pipeline.BACKUP.py
  ```

- [ ] **.gitignore 업데이트**
  ```bash
  # .gitignore에 추가
  __pycache__/
  *.py[cod]
  *$py.class
  ```

- [ ] **캐시 파일 제거**
  ```bash
  find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null
  find . -type f -name "*.pyc" -delete
  find . -type f -name "*.pyo" -delete
  ```

### 단계 2: 문서 정리 (5분)

- [ ] **docs/refactoring/ 폴더 생성**
  ```bash
  mkdir -p docs/refactoring
  ```

- [ ] **리팩토링 문서 이동**
  ```bash
  mv REFACTORING_PDF_EXTRACTION.md docs/refactoring/
  mv REFACTORING_PROGRESS.md docs/refactoring/
  mv REFACTORING_STRATEGY.md docs/refactoring/
  mv REFACTORING_SUMMARY.md docs/refactoring/
  ```

### 단계 3: Scripts 재구성 (10분)

- [ ] **새 폴더 생성**
  ```bash
  mkdir -p scripts/pipeline
  mkdir -p scripts/admin
  mkdir -p scripts/ml
  ```

- [ ] **스크립트 이동**
  ```bash
  mv scripts/run_textbook_pipeline.py scripts/pipeline/
  mv scripts/cleanup_books.py scripts/admin/
  mv scripts/delete_book.py scripts/admin/
  mv scripts/delete_curriculum.py scripts/admin/
  mv scripts/build_training_dataset.py scripts/ml/
  ```

### 단계 4: Archived 확인 (10분)

- [ ] **참조 확인**
  ```bash
  # 각 파일이 사용되는지 확인
  grep -r "ai_lecture_generator" app/ --include="*.py"
  grep -r "ai_text_postprocessor" app/ --include="*.py"
  grep -r "braille_convert" app/ --include="*.py"
  # ... 나머지 파일도 확인
  ```

- [ ] **사용하지 않는 파일 확인 및 문서화**
  - 사용됨: 유지
  - 사용 안 됨: docs/archived/로 이동 또는 삭제

### 단계 5: Git 정리 (5분)

- [ ] **변경사항 확인**
  ```bash
  git status
  ```

- [ ] **캐시 파일이 Git에서 제거되었는지 확인**
  ```bash
  git rm -r --cached app/**/__pycache__/
  ```

- [ ] **커밋**
  ```bash
  git add .
  git commit -m "refactor(api): Clean up backend folder structure"
  ```

---

## [4] .gitignore 업데이트

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data
data/**/cache/
data/**/output/
*.pdf
*.png
*.jpg

# Environment
.env
.env.local

# Logs
*.log
```

---

## [5] 기대 효과

### Before
```
❌ 빈 폴더 (app/pipelines/)
❌ 백업 파일 (textbook_pipeline.BACKUP.py)
❌ 1,966개 캐시 파일
❌ 루트에 리팩토링 문서 4개
❌ scripts/ 폴더 구조 혼재
❌ archived/ 용도 불명확
```

### After
```
✅ 빈 폴더 제거
✅ 백업 파일 제거
✅ 캐시 파일 제거 + .gitignore 업데이트
✅ 문서는 docs/refactoring/로 이동
✅ scripts/는 용도별 분류
✅ archived/ 정리 완료
```

---

## [6] 주의사항

1. **캐시 파일 제거 전 백업**: 혹시 모르니 커밋 먼저
2. **Archived 파일 확인**: 참조되는 파일은 삭제하지 말 것
3. **.gitignore 업데이트**: 캐시 파일이 다시 추가되지 않도록
4. **Scripts 이동 시 import 경로 확인**: 일부 스크립트가 상대 경로를 사용할 수 있음

---

## 예상 소요 시간

- **단계 1**: 5분 (즉시 정리)
- **단계 2**: 5분 (문서 정리)
- **단계 3**: 10분 (Scripts 재구성)
- **단계 4**: 10분 (Archived 확인)
- **단계 5**: 5분 (Git 정리)

**총 예상 시간: 35분**
