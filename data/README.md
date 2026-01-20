# 데이터 디렉토리 구조

이 디렉토리는 프로젝트의 원본 데이터 파일과 데이터베이스를 보관합니다.

**참고**: API에서 생성된 학습 데이터는 `api/data/` 폴더에 저장됩니다. 자세한 내용은 [api/data/README.md](../api/data/README.md)를 참고하세요.

## 디렉토리 구조

```
data/
├── uploads/              # API를 통해 업로드된 파일 (자동 생성)
│   ├── bk_xxxxx.pdf      # 업로드된 PDF 교재
│   ├── bk_xxxxx.hwp      # 업로드된 한글 파일
│   └── temp/             # 임시 파일
│
├── pdfs/                 # PDF 교재 원본 파일 (과목별 하나씩) - 권장 위치
│   ├── 2026 수능특강_ 문학.pdf
│   ├── 2026 수능특강 수학Ⅰ.pdf.pdf
│   └── 2026 수능특강_영어.pdf
│
├── literature/           # 문학 원본 PDF (스크립트용, 선택적)
│   └── pdf/              # run_textbook_pipeline.py 스크립트가 이 경로를 찾음
│       └── 2026 수능특강_ 문학.pdf
│
└── db.sqlite3            # SQLite 데이터베이스 파일
```

## 파일 보관 방법

### 1. PDF 교재

**위치**: `data/pdfs/`

**파일명**: 과목별 하나씩 (예: `2026 수능특강_ 문학.pdf`)

**예시**:
- `2026 수능특강_ 문학.pdf` (문학 과목 전체)
- `2026 수능특강 수학Ⅰ.pdf.pdf` (수학 I 과목 전체, 중복 확장자 정리 필요)
- `2026 수능특강_영어.pdf` (영어 과목 전체)

**사용 방법**:
```bash
# PDF 파일을 pdfs 디렉토리에 복사
# Windows
copy "C:\path\to\*.pdf" "data\pdfs\"

# Linux/Mac
cp /path/to/*.pdf data/pdfs/
```


## 주의사항

1. **uploads/**: API를 통해 업로드된 파일이 자동으로 저장됩니다. 수동으로 파일을 넣을 필요는 없습니다.
   - 커리큘럼 생성 시 임시 파일이 생성되지만, 생성 완료 후 자동으로 정리됩니다.
   - 오래된 임시 파일은 주기적으로 정리 스크립트를 실행하여 삭제할 수 있습니다.

2. **pdfs/**: 교재 파이프라인을 위한 원본 PDF 파일을 보관합니다. 이 디렉토리에 파일을 직접 복사해야 합니다. (권장 위치)

   **참고**: `run_textbook_pipeline.py` 스크립트는 `data/{subject}/pdf/` 경로에서도 PDF를 찾습니다. 
   - 예: `data/literature/pdf/`, `data/math1/pdf/`, `data/english/pdf/`
   - 스크립트 사용 시에는 과목별 폴더에 PDF를 넣어야 합니다.
   - 일반적으로는 `data/pdfs/`에 모든 PDF를 모아두고, 스크립트 실행 시 `--pdf` 옵션으로 경로를 지정하는 것을 권장합니다.

3. **db.sqlite3**: SQLite 데이터베이스 파일입니다. 교재, 레슨, 단원, 진행 상황 등이 저장됩니다.

4. **api/data/literature/**: 파이프라인으로 생성된 문학 학습 데이터(JSON, 이미지)가 저장됩니다. 자세한 내용은 [api/data/README.md](../api/data/README.md)를 참고하세요.

5. **파일 크기**: 각 파일은 최대 100MB까지 업로드 가능합니다.

6. **api/data/**: API에서 생성하고 서빙하는 데이터는 `api/data/` 폴더에 저장됩니다. 이 폴더는 파이프라인 실행 시 자동으로 생성됩니다. 자세한 내용은 [api/data/README.md](../api/data/README.md)를 참고하세요.

## 폴더 정리

정기적으로 폴더를 정리하려면:

```bash
# 프로젝트 루트에서
python scripts/cleanup_data_folder.py
```

이 스크립트는:
- `uploads/` 폴더의 오래된 임시 파일(7일 이상) 삭제
- `pdfs/` 폴더의 중복 확장자 파일명 정리 (`.pdf.pdf` → `.pdf`)

---

*마지막 업데이트: 2025년 1월*
