# 테스트 실행 명령어 모음

빠른 참조를 위한 테스트 명령어 정리

## 📋 목차

1. [환경 설정](#환경-설정)
2. [백엔드 서버 실행](#백엔드-서버-실행)
3. [한글 파일 테스트](#한글-파일-테스트)
4. [PDF 추출 테스트](#pdf-추출-테스트)
5. [데이터셋 구축 테스트](#데이터셋-구축-테스트)
6. [API 테스트](#api-테스트)

---

## 환경 설정

### 의존성 설치

```powershell
# PowerShell
cd api
pip install -r requirements.txt

# 한글 파일 처리 라이브러리 (필요시)
pip install olefile
```

---

## 백엔드 서버 실행

### 서버 시작

```powershell
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 서버 상태 확인

```powershell
# PowerShell
Invoke-WebRequest -Uri http://localhost:8000/api/v1/health | Select-Object -ExpandProperty Content

# 또는 curl.exe
curl.exe http://localhost:8000/api/v1/health
```

### 서버 로그 확인

```powershell
# 서버를 실행한 터미널에서 확인
# 또는 로그를 파일로 저장
uvicorn app.main:app --reload *> ..\server.log

# 최근 로그만 보기
Get-Content server.log -Tail 50

# 에러만 필터링
Select-String -Pattern "error|exception|traceback" server.log
```

---

## 한글 파일 테스트

### 기본 테스트 (모든 기능)

```powershell
cd api
python test_hwp_extract.py
```

### 자동 제작 시스템 테스트

```powershell
cd api
python test_content_generator.py
```

**예상 결과:**
- ✅ 텍스트 추출 성공
- ✅ 레슨 정보 추출 성공
- ✅ 구조 추출 성공
- ✅ 자동 제작 성공 (7개 섹션 생성)

---

## PDF 추출 테스트

### 서버 실행 확인

```powershell
# 서버가 실행 중인지 확인
curl.exe http://localhost:8000/api/v1/health
```

### PDF 구조화 추출 테스트

```powershell
cd api
python test_pdf_extract.py
```

### PowerShell로 직접 테스트

```powershell
$filePath = "data/pdfs/2026 수능특강_ 문학.pdf"
$uri = "http://localhost:8000/api/v1/pdf/extract-structured"

$form = @{
    file = Get-Item -Path $filePath
}

Invoke-RestMethod -Uri $uri -Method Post -Form $form | ConvertTo-Json -Depth 10
```

### FastAPI 문서 UI로 테스트

1. 브라우저에서 http://localhost:8000/docs 접속
2. `/api/v1/pdf/extract-structured` 엔드포인트 찾기
3. "Try it out" 클릭
4. 파일 선택 후 "Execute" 클릭

---

## 데이터셋 구축 테스트

### 기본 실행

```powershell
cd api
python scripts/build_training_dataset.py
```

### 커스텀 경로 지정

```powershell
python scripts/build_training_dataset.py `
  --hwp-dir ../../data/lecture_scripts `
  --pdf-dir ../../data/pdfs `
  --output ../../data/datasets/braille_dataset.json
```

### 결과 확인

```powershell
# Python으로 확인
python -c "import json; data = json.load(open('../data/datasets/braille_dataset.json')); print(f'총 {len(data[\"items\"])}개 항목')"
```

---

## API 테스트

### 헬스 체크

```powershell
# PowerShell
Invoke-WebRequest -Uri http://localhost:8000/api/v1/health | Select-Object -ExpandProperty Content

# curl.exe
curl.exe http://localhost:8000/api/v1/health
```

### PDF 이미지 추출

```powershell
$filePath = "data/pdfs/2026 수능특강_ 문학.pdf"
$uri = "http://localhost:8000/api/v1/pdf/extract-images"

$form = @{
    file = Get-Item -Path $filePath
    extract_type = "both"
}

Invoke-RestMethod -Uri $uri -Method Post -Form $form | ConvertTo-Json -Depth 10
```

---

## 전체 테스트 시나리오

### 1. 한글 파일 → 데이터셋 구축

```powershell
# 1. 한글 파일 테스트
cd api
python test_hwp_extract.py

# 2. 데이터셋 구축
python scripts/build_training_dataset.py

# 3. 결과 확인
python -c "import json; data = json.load(open('../data/datasets/braille_dataset.json')); print(json.dumps(data['items'][0], indent=2, ensure_ascii=False))"
```

### 2. PDF 교재 업로드 → 구조화 추출

```powershell
# 1. 서버 실행 (별도 터미널)
cd api
uvicorn app.main:app --reload

# 2. PDF 추출 테스트 (새 터미널)
cd api
python test_pdf_extract.py
```

---

## 문제 해결

### 서버 연결 실패

```powershell
# 서버가 실행 중인지 확인
curl.exe http://localhost:8000/api/v1/health

# 서버 재시작
cd api
uvicorn app.main:app --reload
```

### 한글 파일 추출 실패

```powershell
# olefile 설치 확인
pip install olefile

# Python에서 확인
python -c "import olefile; print('olefile 설치됨')"
```

### PDF 처리 시간 초과

- PDF 파일 크기 확인
- 서버 로그 확인
- 더 작은 파일로 테스트

---

## 빠른 참조

| 테스트 | 명령어 | 서버 필요 |
|--------|--------|----------|
| 한글 파일 추출 | `python test_hwp_extract.py` | ❌ |
| 자동 제작 시스템 | `python test_content_generator.py` | ❌ |
| PDF 구조화 추출 | `python test_pdf_extract.py` | ✅ |
| 데이터셋 구축 | `python scripts/build_training_dataset.py` | ❌ |
| 헬스 체크 | `curl.exe http://localhost:8000/api/v1/health` | ✅ |

---

*마지막 업데이트: 2024년*
