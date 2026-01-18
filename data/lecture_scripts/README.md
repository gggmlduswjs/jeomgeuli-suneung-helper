# 강의 대본 파일 보관 가이드

## 폴더 구조

각 과목별로 폴더를 만들어서 강의 대본(한글 파일)을 보관합니다.

```
lecture_scripts/
├── 수능특강_문학_2026/     # 문학 과목 (00강~43강, 총 44개)
├── 수능특강_수1_2026/      # 수학 I 과목 (00강~43강, 총 44개)
└── 수능특강_영어_2026/     # 영어 과목 (00강~43강, 총 44개)
```

## 파일 복사 방법

### Windows PowerShell

```powershell
# 문학 과목 파일 복사
Copy-Item "실제파일경로\문학\*.hwp" -Destination "data\lecture_scripts\수능특강_문학_2026\"

# 수학 I 과목 파일 복사
Copy-Item "실제파일경로\수1\*.hwp" -Destination "data\lecture_scripts\수능특강_수1_2026\"

# 영어 과목 파일 복사
Copy-Item "실제파일경로\영어\*.hwp" -Destination "data\lecture_scripts\수능특강_영어_2026\"
```

### Windows 탐색기

1. `data\lecture_scripts\수능특강_문학_2026\` 폴더를 엽니다
2. 문학 과목의 한글 파일들을 이 폴더로 드래그 앤 드롭합니다
3. 다른 과목도 동일하게 반복합니다

## 파일명 형식

각 강의 대본 파일은 다음과 같은 형식을 따릅니다:

- `00강_오리엔테이션.hwp`
- `01강_[교과서_개념]_1_2_(고3_기본).hwp`
- `02강_[교과서_개념]_3_4_(고3_기본).hwp`
- ...
- `43강_[실전_2회]_11_14번_15_17번_완강_(고3_기본).hwp`

## 확인 방법

파일 복사 후 다음 명령어로 확인할 수 있습니다:

```powershell
# 문학 과목 파일 개수 확인
(Get-ChildItem "data\lecture_scripts\수능특강_문학_2026\*.hwp").Count

# 모든 과목 폴더의 파일 개수 확인
Get-ChildItem "data\lecture_scripts" -Directory | ForEach-Object {
    $count = (Get-ChildItem $_.FullName -Filter "*.hwp").Count
    Write-Host "$($_.Name): $count files"
}
```

## 주의사항

- 각 과목 폴더에는 약 44개의 한글 파일이 있어야 합니다 (00강~43강)
- 파일명에 강 번호가 포함되어 있어야 데이터셋 구축 시 자동으로 인식됩니다
- 파일이 올바르게 복사되었는지 확인한 후 데이터셋 구축을 진행하세요
