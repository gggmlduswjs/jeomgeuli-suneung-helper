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
│   ├── 2026 수능특강 수학Ⅰ.pdf
│   ├── 2026 수능특강 영어.pdf
│   └── ...
│
├── extracted/            # 추출된 텍스트 캐시 (자동 생성)
│   └── *.txt
│
├── parsed/               # 파싱된 데이터 (자동 생성)
│   └── *.json
│
├── curricula/            # 커리큘럼 JSON 파일 (과목별 폴더)
│   ├── korean/           # 국어/문학 커리큘럼
│   │   └── cur_xxx.json
│   ├── math1/            # 수학1 커리큘럼
│   │   └── cur_xxx.json
│   └── english/          # 영어 커리큘럼
│       └── cur_xxx.json
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
- `2026 수능특강 수학Ⅰ.pdf` (수학 I 과목 전체)
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
    ├── 2026 수능특강 수학Ⅰ.pdf
    └── 2026 수능특강 영어.pdf
```

## 주의사항

1. **uploads/**: API를 통해 업로드된 파일이 자동으로 저장됩니다. 수동으로 파일을 넣을 필요는 없습니다.
   - 커리큘럼 생성 시 임시 파일(`cur_xxx_*.hwp`)이 생성되지만, 생성 완료 후 자동으로 정리됩니다.
   - 오래된 임시 파일은 주기적으로 정리 스크립트를 실행하여 삭제할 수 있습니다.

2. **lecture_scripts/**, **pdfs/**: 학습 데이터셋 구축을 위한 원본 파일을 보관합니다. 이 디렉토리에 파일을 직접 복사해야 합니다.

3. **extracted/**, **parsed/**, **datasets/**: 자동으로 생성되는 디렉토리입니다. 수동으로 파일을 넣을 필요는 없습니다.

4. **curricula/**: 커리큘럼 생성 시 과목별 폴더(`korean/`, `math1/`, `english/`)에 JSON 파일이 자동으로 저장됩니다.

5. **파일 크기**: 각 파일은 최대 100MB까지 업로드 가능합니다.

## 폴더 정리

정기적으로 폴더를 정리하려면:

```bash
# 프로젝트 루트에서
python scripts/cleanup_data_folder.py
```

이 스크립트는:
- `curricula/` 폴더를 과목별로 정리
- `uploads/` 폴더의 오래된 임시 파일(7일 이상) 삭제
- `pdfs/` 폴더의 중복 확장자 파일명 정리 (`.pdf.pdf` → `.pdf`)

## 현재 상태

자세한 상태는 [DATA_FOLDER_STATUS.md](./DATA_FOLDER_STATUS.md)를 참고하세요.

---

*마지막 업데이트: 2026-01-16*
