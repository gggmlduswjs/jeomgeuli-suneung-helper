# Data 폴더 구조 분석 및 정리 가이드

## 현재 상태 분석

### ✅ 정상적인 구조

1. **lecture_scripts/** - 강의 대본 (과목별 폴더)
   - `수능특강_문학_2026/` (44개 HWP + 1개 HWPX)
   - `수능특강_수1_2026/` (43개 HWP)
   - `수능특강_영어_2026/` (43개 HWP)
   - ✅ 정상

2. **extracted/** - 추출된 텍스트 캐시
   - 10개 `.txt` 파일 (PDF 추출 결과)
   - ✅ 정상

3. **parsed/** - 파싱된 데이터
   - 비어있음 (아직 파싱 안 함)
   - ✅ 정상

4. **datasets/** - 생성된 데이터셋
   - 비어있음 (아직 생성 안 함)
   - ✅ 정상

5. **db.sqlite3** - SQLite 데이터베이스
   - 1.5MB
   - ✅ 정상

### ⚠️ 문제점 및 개선 필요

#### 1. curricula/ 폴더 구조 문제

**현재 상태:**
```
data/curricula/
└── cur_d6a7bb3a6bd9.json  (루트에 직접 저장)
```

**예상 구조 (코드 기준):**
```
data/curricula/
├── korean/          # 국어/문학 커리큘럼
│   └── cur_xxx.json
├── math1/           # 수학1 커리큘럼
│   └── cur_xxx.json
└── english/         # 영어 커리큘럼
    └── cur_xxx.json
```

**문제:** 코드는 과목별 폴더로 저장하도록 되어있지만, 기존 파일은 루트에 있음

**해결 방법:**
- 기존 파일을 과목별 폴더로 이동
- 또는 코드가 과목별 폴더를 생성하도록 수정

#### 2. uploads/ 폴더 임시 파일 과다

**현재 상태:**
- 약 230개 파일
- 대부분 `cur_xxx_*.hwp` 형식의 임시 파일
- 커리큘럼 생성 시 임시로 저장된 파일들

**문제:**
- 커리큘럼 생성 후 임시 파일이 정리되지 않음
- 디스크 공간 낭비

**해결 방법:**
- 커리큘럼 생성 완료 후 임시 파일 자동 삭제
- 또는 주기적 정리 스크립트 실행

#### 3. pdfs/ 폴더 파일명 문제

**현재 상태:**
- 일부 파일이 `.pdf.pdf` 중복 확장자
  - `2026 수능특강 수학Ⅰ.pdf.pdf`
  - `2026 수능특강 수학Ⅱ.pdf.pdf`
  - `2026 수능특강 기하.pdf.pdf`
  - `2026 수능특강 미적분.pdf.pdf`
  - `2026 수능특강 확률과 통계.pdf.pdf`

**문제:**
- 파일명이 중복 확장자를 가짐
- 일관성 부족

**해결 방법:**
- 파일명 정리 (`.pdf.pdf` → `.pdf`)

## 권장 정리 작업

### 1. curricula/ 폴더 구조 정리

```powershell
# 기존 파일 확인
cd data/curricula
Get-ChildItem *.json

# 과목별 폴더 생성 및 파일 이동
# (JSON 파일 내용을 확인하여 과목 판단 필요)
```

### 2. uploads/ 폴더 정리

```powershell
# 오래된 임시 파일 삭제 (예: 7일 이상 된 파일)
cd data/uploads
Get-ChildItem -Filter "cur_*" | Where-Object {
    $_.LastWriteTime -lt (Get-Date).AddDays(-7)
} | Remove-Item

# 또는 특정 커리큘럼 ID의 파일만 유지
# (DB에서 활성 커리큘럼 ID 확인 후 해당 파일만 유지)
```

### 3. pdfs/ 폴더 파일명 정리

```powershell
cd data/pdfs
Get-ChildItem -Filter "*.pdf.pdf" | ForEach-Object {
    $newName = $_.Name -replace '\.pdf\.pdf$', '.pdf'
    Rename-Item $_.FullName -NewName $newName
}
```

## 최종 권장 구조

```
data/
├── curricula/              # 커리큘럼 JSON (과목별 폴더)
│   ├── korean/
│   │   └── cur_xxx.json
│   ├── math1/
│   │   └── cur_xxx.json
│   └── english/
│       └── cur_xxx.json
│
├── uploads/                # API 업로드 파일 (임시 파일 정리 필요)
│   ├── bk_xxx.pdf          # 교재 업로드
│   ├── bk_xxx.hwp          # 한글 파일 업로드
│   └── temp/               # 임시 파일
│
├── lecture_scripts/        # 강의 대본 원본 (과목별 폴더) ✅
│   ├── 수능특강_문학_2026/
│   ├── 수능특강_수1_2026/
│   └── 수능특강_영어_2026/
│
├── pdfs/                   # PDF 교재 원본 (파일명 정리 필요)
│   ├── 2026 수능특강 문학.pdf
│   ├── 2026 수능특강 수학Ⅰ.pdf  (중복 확장자 제거)
│   └── ...
│
├── extracted/              # 추출된 텍스트 캐시 ✅
├── parsed/                 # 파싱된 데이터 ✅
├── datasets/               # 생성된 데이터셋 ✅
└── db.sqlite3              # SQLite 데이터베이스 ✅
```

## 자동 정리 스크립트 제안

정기적으로 실행할 수 있는 정리 스크립트를 만들 수 있습니다:

```python
# scripts/cleanup_data_folder.py
# - uploads/의 오래된 임시 파일 삭제
# - curricula/의 파일을 과목별 폴더로 정리
# - pdfs/의 중복 확장자 파일명 정리
```

---

*생성일: 2026-01-16*
