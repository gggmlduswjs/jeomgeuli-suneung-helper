# Data 폴더 리팩토링 전략

## 📊 현재 상태 분석

### 루트 data/ 폴더
```
data/
├── datasets/              ❌ 빈 폴더 (0 bytes)
├── extracted/             ❌ 빈 폴더 (0 bytes)
├── lecture_scripts/       ❌ 빈 폴더 (0 bytes)
├── parsed/                ❌ 빈 폴더 (0 bytes)
├── uploads/               ⚠️  314MB (임시 업로드 파일들)
├── pdfs/                  ⚠️  34MB (중복?)
│   ├── 2026 수능특강 수학Ⅰ.pdf.pdf  ⚠️  중복 확장자
│   ├── 2026 수능특강_ 문학.pdf
│   └── 2026 수능특강_영어.pdf
├── literature/            21MB
│   └── pdf/
│       └── 2026 수능특강_ 문학.pdf  ⚠️  pdfs/와 중복
├── math1/                 8.4MB
│   └── pdf/
│       └── 2026 수능특강 수학Ⅰ.pdf.pdf  ⚠️  pdfs/와 중복
├── english/               3.9MB
│   └── pdf/
│       └── 2026 수능특강_영어.pdf  ⚠️  pdfs/와 중복
├── db.sqlite3             12MB
└── README.md              4KB
```

### api/data/ 폴더
```
api/data/
├── literature/            33MB  (파이프라인 생성 데이터)
├── english/               4.6MB (파이프라인 생성 데이터)
├── math1/                 2.5MB (파이프라인 생성 데이터)
├── ml_cache/              66MB  (ML 캐시)
└── README.md              8KB
```

**총 크기**: data/ (~388MB) + api/data/ (~106MB) = 494MB

---

## 🎯 문제점

### 1. 빈 폴더 (Cleanup 필요)
- ❌ `data/datasets/`
- ❌ `data/extracted/`
- ❌ `data/lecture_scripts/`
- ❌ `data/parsed/`

**이유**: README에도 언급되지 않은 미사용 폴더

### 2. 중복 PDF 파일
- `data/pdfs/2026 수능특강_ 문학.pdf` ⚠️  중복
- `data/literature/pdf/2026 수능특강_ 문학.pdf` ⚠️  중복
- (수학, 영어도 동일)

**이유**:
- `data/pdfs/`: API가 서빙하는 원본 PDF 저장소 (권장)
- `data/{subject}/pdf/`: 스크립트(`run_textbook_pipeline.py`)가 찾는 경로

→ **두 위치 중 하나로 통일 필요**

### 3. 파일명 문제
- `2026 수능특강 수학Ⅰ.pdf.pdf` ⚠️  중복 확장자 (`.pdf.pdf`)

### 4. uploads/ 폴더 (314MB)
- `bk_xxxxx.pdf` 파일들 (대부분 21MB씩, 중복된 문학 PDF)
- 임시 업로드 파일이 정리되지 않음

**README 내용**:
> 커리큘럼 생성 시 임시 파일이 생성되지만, 생성 완료 후 자동으로 정리됩니다.
> 오래된 임시 파일은 주기적으로 정리 스크립트를 실행하여 삭제할 수 있습니다.

→ **7일 이상 오래된 파일 정리 필요**

### 5. api/data/ 폴더
- `ml_cache/` 66MB - ML 모델 캐시
- 과목별 폴더 (파이프라인 생성 데이터)

→ **현재는 정상 (용량 확인 필요)**

---

## 📝 리팩토링 전략

### Phase 1: 즉시 정리 (Cleanup)

#### 1.1 빈 폴더 제거
```bash
# 4개 빈 폴더 삭제
data/datasets/
data/extracted/
data/lecture_scripts/
data/parsed/
```

#### 1.2 중복 PDF 통합
**결정**: `data/pdfs/`를 원본 저장소로 사용

**이유**:
- API가 서빙하는 원본 PDF 위치
- 중앙 집중식 관리 용이
- 스크립트 실행 시 `--pdf` 옵션으로 경로 지정 가능

**작업**:
1. `data/{subject}/pdf/` 폴더 제거
2. `data/pdfs/`에만 원본 PDF 보관
3. 스크립트는 `--pdf data/pdfs/파일명.pdf` 형태로 실행

#### 1.3 파일명 정리
```bash
# Before
data/pdfs/2026 수능특강 수학Ⅰ.pdf.pdf

# After
data/pdfs/2026 수능특강 수학Ⅰ.pdf
```

#### 1.4 uploads/ 폴더 정리
**정리 기준**:
- 7일 이상 오래된 파일 삭제
- `bk_xxxxx.pdf` 형태의 임시 파일만 대상
- `book_korean_*` 형태는 유지 (최신 업로드)

**예상 결과**: 314MB → 50MB 이하로 감소

### Phase 2: 폴더 구조 개선

#### 2.1 최종 구조
```
data/
├── pdfs/                  ✅ 원본 PDF 저장소 (권장)
│   ├── 2026 수능특강 수학Ⅰ.pdf
│   ├── 2026 수능특강 문학.pdf
│   └── 2026 수능특강 영어.pdf
│
├── uploads/               ✅ API 업로드 임시 파일 (자동 관리)
│   └── book_korean_*      (최신 업로드만 유지)
│
├── db.sqlite3             ✅ SQLite 데이터베이스
└── README.md              ✅ 문서 (업데이트 필요)
```

#### 2.2 과목별 폴더 제거
```bash
# 제거할 폴더
data/literature/           (pdfs/로 통합)
data/math1/                (pdfs/로 통합)
data/english/              (pdfs/로 통합)
```

**이유**:
- PDF 중복 제거
- 중앙 집중식 관리
- README에서도 `data/pdfs/`를 권장 위치로 명시

### Phase 3: 문서 업데이트

#### 3.1 README.md 업데이트
- 빈 폴더 제거 반영
- 과목별 폴더 제거 반영
- `data/pdfs/`를 유일한 원본 저장소로 명시
- 스크립트 실행 방법 업데이트

---

## ✅ 실행 체크리스트 (1시간 이내)

### Step 1: 백업 (5분)
- [ ] 현재 상태 스냅샷 (git commit)
- [ ] uploads/ 폴더 크기 확인
- [ ] PDF 파일 해시 확인 (중복 여부)

### Step 2: 빈 폴더 제거 (5분)
- [ ] `data/datasets/` 삭제
- [ ] `data/extracted/` 삭제
- [ ] `data/lecture_scripts/` 삭제
- [ ] `data/parsed/` 삭제

### Step 3: PDF 파일 정리 (10분)
- [ ] 파일명 수정: `2026 수능특강 수학Ⅰ.pdf.pdf` → `.pdf`
- [ ] 과목별 폴더 제거 (literature/, math1/, english/)
- [ ] `data/pdfs/`에만 원본 PDF 유지

### Step 4: uploads/ 정리 (10분)
- [ ] 7일 이상 오래된 `bk_*.pdf` 파일 확인
- [ ] 오래된 임시 파일 삭제
- [ ] 최신 업로드 파일만 유지

### Step 5: 문서 업데이트 (10분)
- [ ] `data/README.md` 업데이트
- [ ] 폴더 구조 섹션 수정
- [ ] 스크립트 실행 방법 업데이트

### Step 6: 검증 (10분)
- [ ] 폴더 구조 확인
- [ ] 파일 크기 비교 (Before/After)
- [ ] Git status 확인

### Step 7: 커밋 (10분)
- [ ] 변경사항 커밋
- [ ] 요약 문서 작성

---

## 🎯 예상 효과

### Before
```
data/ 폴더: 388MB
- uploads/: 314MB (불필요한 임시 파일)
- pdfs/: 34MB
- literature/: 21MB (중복)
- math1/: 8.4MB (중복)
- english/: 3.9MB (중복)
- 빈 폴더: 4개
- 파일명 문제: 1개
```

### After
```
data/ 폴더: 80MB 이하 (308MB 감소)
- uploads/: 30MB 이하 (임시 파일 정리)
- pdfs/: 34MB (원본만 유지)
- db.sqlite3: 12MB
- README.md: 업데이트
- 빈 폴더: 0개
- 중복 PDF: 0개
- 파일명 문제: 해결
```

**개선율**: 약 79% 용량 감소

---

## 🚀 실행 명령어

### 1. 빈 폴더 제거
```bash
cd data
rm -rf datasets/ extracted/ lecture_scripts/ parsed/
```

### 2. 파일명 정리
```bash
cd data/pdfs
mv "2026 수능특강 수학Ⅰ.pdf.pdf" "2026 수능특강 수학Ⅰ.pdf"
```

### 3. 과목별 폴더 제거
```bash
cd data
rm -rf literature/ math1/ english/
```

### 4. 오래된 uploads 정리
```bash
cd data/uploads
# 7일 이상 오래된 bk_* 파일 찾기
find . -name "bk_*.pdf" -mtime +7 -delete
```

---

## 📌 주의사항

1. **백업 필수**: 실행 전 반드시 git commit
2. **PDF 파일 확인**: 삭제 전 파일 크기와 내용 확인 (해시 비교)
3. **db.sqlite3**: 절대 삭제하지 않음
4. **api/data/**: 건드리지 않음 (파이프라인 생성 데이터)
5. **uploads/**: 최신 업로드 파일은 유지

---

**작성일**: 2026-01-20
**대상**: data/ 폴더 리팩토링
**예상 소요 시간**: 1시간
