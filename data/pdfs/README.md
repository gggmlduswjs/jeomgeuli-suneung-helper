# PDF 교재 파일 보관 가이드

## 폴더 구조

PDF 교재는 과목별로 하나씩 보관합니다.

```
pdfs/
├── 2026 수능특강 문학.pdf
├── 2026 수능특강 수학 I.pdf
├── 2026 수능특강 영어.pdf
├── 2026 수능특강 독서.pdf
├── 2026 수능특강 화법과작문.pdf
└── ...
```

## 파일 복사 방법

### Windows PowerShell

```powershell
# 모든 PDF 파일 복사
Copy-Item "실제파일경로\*.pdf" -Destination "data\pdfs\"
```

### Windows 탐색기

1. `data\pdfs\` 폴더를 엽니다
2. PDF 파일들을 이 폴더로 드래그 앤 드롭합니다

## 파일명 형식

PDF 파일명은 자유 형식이지만, 과목명이 포함되어 있으면 좋습니다:

- `2026 수능특강 문학.pdf`
- `2026 수능특강 수학 I.pdf`
- `2026 수능특강 영어.pdf`
- `2026 수능특강 독서.pdf`
- `2026 수능특강 화법과작문.pdf`

## 확인 방법

```powershell
# PDF 파일 목록 확인
Get-ChildItem "data\pdfs\*.pdf" | Select-Object Name, Length
```

## 주의사항

- 각 과목별로 하나의 PDF 파일만 보관합니다
- PDF 파일은 교재 전체를 포함합니다
- 파일 크기가 클 수 있으므로 (10MB~45MB) 복사 시간이 걸릴 수 있습니다
