# 데이터 디렉토리 구조

이 디렉토리는 프로젝트의 모든 데이터 파일을 보관합니다.

## 디렉토리 구조

```
data/
├── uploads/              # API를 통해 업로드된 파일 (자동 생성)
│   ├── bk_xxxxx.pdf      # 업로드된 PDF 교재
│   ├── bk_xxxxx.hwp      # 업로드된 한글 파일
│   └── temp/             # 임시 파일
│
├── lecture_scripts/      # 강의 대본 원본 파일 (한글 파일) - 과목별 폴더
│   ├── 수능특강_문학_2026/
│   │   ├── 00강_오리엔테이션.hwp
│   │   ├── 01강_[교과서_개념]_1_2_(고3_기본).hwp
│   │   ├── 02강_[교과서_개념]_3_4_(고3_기본).hwp
│   │   └── ... (00강~43강, 총 44개)
│   ├── 수능특강_수1_2026/
│   │   ├── 00강_오리엔테이션.hwp
│   │   ├── 01강_...
│   │   └── ... (00강~43강)
│   └── 수능특강_영어_2026/
│       └── ... (00강~43강)
│
├── pdfs/                 # PDF 교재 원본 파일 (과목별 하나씩)
│   ├── 2026 수능특강 문학.pdf
│   ├── 2026 수능특강 수학 I.pdf
│   ├── 2026 수능특강 영어.pdf
│   └── ...
│
├── extracted/            # 추출된 텍스트 캐시 (자동 생성)
│   └── *.txt
│
├── parsed/               # 파싱된 데이터 (자동 생성)
│   └── *.json
│
└── datasets/             # 생성된 학습 데이터셋 (자동 생성)
    └── braille_dataset.json
```

## 파일 보관 방법

### 1. 강의 대본 (한글 파일)

**위치**: `data/lecture_scripts/[과목명]/`

**폴더 구조**: 과목별로 폴더를 만들어서 보관
- `data/lecture_scripts/수능특강_문학_2026/`
- `data/lecture_scripts/수능특강_수1_2026/`
- `data/lecture_scripts/수능특강_영어_2026/`

**파일명 형식**: `[번호]강_[카테고리]_[세부]_[난이도].hwp`

**예시** (문학 과목):
- `00강_오리엔테이션.hwp`
- `01강_[교과서_개념]_1_2_(고3_기본).hwp`
- `05강_[고전_시가]_01_(고3_기본).hwp`
- `40강_[실전_1회]_01_04번_05_10번_(고3_기본).hwp`

**사용 방법**:
```bash
# 1. 과목별 폴더 생성
mkdir -p data/lecture_scripts/수능특강_문학_2026
mkdir -p data/lecture_scripts/수능특강_수1_2026
mkdir -p data/lecture_scripts/수능특강_영어_2026

# 2. 한글 파일을 해당 과목 폴더에 복사
# Windows
copy "C:\path\to\문학\*.hwp" "data\lecture_scripts\수능특강_문학_2026\"

# Linux/Mac
cp /path/to/문학/*.hwp data/lecture_scripts/수능특강_문학_2026/
```

### 2. PDF 교재

**위치**: `data/pdfs/`

**파일명**: 과목별 하나씩 (예: `2026 수능특강 문학.pdf`)

**예시**:
- `2026 수능특강 문학.pdf` (문학 과목 전체)
- `2026 수능특강 수학 I.pdf` (수학 I 과목 전체)
- `2026 수능특강 영어.pdf` (영어 과목 전체)

**사용 방법**:
```bash
# PDF 파일을 pdfs 디렉토리에 복사
# Windows
copy "C:\path\to\*.pdf" "data\pdfs\"

# Linux/Mac
cp /path/to/*.pdf data/pdfs/
```

### 3. 데이터셋 구축

파일을 보관한 후, 데이터셋을 구축하려면:

```bash
cd api
python scripts/build_training_dataset.py
```

스크립트는 자동으로 `data/lecture_scripts/` 하위의 모든 과목 폴더를 탐색하고, `data/pdfs/`의 모든 PDF 파일을 처리합니다.

특정 디렉토리 지정:

```bash
python scripts/build_training_dataset.py \
  --hwp-dir ../../data/lecture_scripts \
  --pdf-dir ../../data/pdfs \
  --output ../../data/datasets/braille_dataset.json
```

**과목별 폴더 구조 예시**:
```
data/
├── lecture_scripts/
│   ├── 수능특강_문학_2026/     # 문학 과목 (44개 강의)
│   │   ├── 00강_오리엔테이션.hwp
│   │   ├── 01강_...
│   │   └── 43강_...
│   ├── 수능특강_수1_2026/      # 수학 I 과목 (44개 강의)
│   └── 수능특강_영어_2026/     # 영어 과목 (44개 강의)
└── pdfs/
    ├── 2026 수능특강 문학.pdf  # 문학 PDF (1개)
    ├── 2026 수능특강 수학 I.pdf
    └── 2026 수능특강 영어.pdf
```

## 주의사항

1. **uploads/**: API를 통해 업로드된 파일이 자동으로 저장됩니다. 수동으로 파일을 넣을 필요는 없습니다.

2. **lecture_scripts/**, **pdfs/**: 학습 데이터셋 구축을 위한 원본 파일을 보관합니다. 이 디렉토리에 파일을 직접 복사해야 합니다.

3. **extracted/**, **parsed/**, **datasets/**: 자동으로 생성되는 디렉토리입니다. 수동으로 파일을 넣을 필요는 없습니다.

4. **파일 크기**: 각 파일은 최대 100MB까지 업로드 가능합니다.

## .gitignore

이 디렉토리의 대부분의 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다. 실제 데이터 파일은 별도로 관리하세요.
