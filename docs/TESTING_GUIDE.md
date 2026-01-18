# 구현된 기능 테스트 가이드

이 문서는 현재까지 구현된 기능들을 테스트하는 방법을 설명합니다.

> **💡 빠른 참조**: 테스트 명령어만 빠르게 확인하려면 [TEST_COMMANDS.md](./TEST_COMMANDS.md)를 참고하세요.

## 📋 목차

1. [환경 설정](#환경-설정)
2. [한글 파일 처리 테스트](#한글-파일-처리-테스트) - 서버 불필요
3. [데이터셋 구축 스크립트 테스트](#데이터셋-구축-스크립트-테스트) - 서버 불필요
4. [백엔드 서버 실행 및 API 테스트](#백엔드-서버-실행-및-api-테스트) - 서버 필요
5. [PDF 구조화 추출 테스트](#pdf-구조화-추출-테스트) - 서버 필요
6. [프론트엔드 통합 테스트](#프론트엔드-통합-테스트) - 서버 필요

---

## 환경 설정

### 1. 백엔드 의존성 설치

```bash
cd api
pip install -r requirements.txt
```

**필수 의존성:**
- `fastapi`, `uvicorn` - API 서버
- `pdfplumber`, `pdf2image` - PDF 처리
- `Pillow` - 이미지 처리
- `olefile` - 한글 파일 처리 (한글 파일 기능 사용 시 필수)

**Windows에서 pdf2image 사용 시:**
```bash
# Poppler 설치 필요
# https://github.com/oschwartz10612/poppler-windows/releases
# 다운로드 후 PATH에 추가하거나 아래처럼 설정
# api/app/services/pdf_image_extract.py에서 poppler_path 설정
```

### 2. 프론트엔드 의존성 설치

```bash
cd apps/web
npm install
```

### 3. 데이터 폴더 확인

```bash
# 프로젝트 루트에서
python scripts/create_data_folders.py
```

---

## 한글 파일 처리 테스트

**⚠️ 사전 준비**: 한글 파일 처리를 위해서는 `olefile` 라이브러리가 필요합니다.

```bash
# requirements.txt에 포함되어 있지만, 설치되지 않은 경우
pip install olefile

# 또는 requirements.txt 전체 재설치
pip install -r requirements.txt
```

### 1. 직접 서비스 테스트

`test_hwp_extract.py` 파일 생성:

```python
from pathlib import Path
from app.services.hwp_extract import extract_text_from_hwp, extract_structure_from_hwp

# 테스트 파일 경로
hwp_file = Path("data/lecture_scripts/수능특강_문학_2026/01강_[교과서_개념]_1_2_(고3_기본).hwp")

# 텍스트 추출
text = extract_text_from_hwp(hwp_file)
print(f"추출된 텍스트 길이: {len(text)} 문자")
print(f"첫 500자:\n{text[:500]}")

# 구조 추출
structure = extract_structure_from_hwp(hwp_file)
print(f"\n구조 정보:\n{structure}")
```

실행:
```bash
cd api
python test_hwp_extract.py
```

### 2. 자동 제작 시스템 테스트

`test_content_generator.py` 파일 생성:

```python
from pathlib import Path
from app.services.content_auto_generator import ContentAutoGenerator

generator = ContentAutoGenerator()
hwp_file = Path("data/lecture_scripts/수능특강_문학_2026/01강_[교과서_개념]_1_2_(고3_기본).hwp")

result = generator.generate_structured_content(hwp_file)
print(f"생성된 섹션 수: {len(result.get('sections', []))}")
print(f"검증 결과: {result.get('validation', {})}")
```

실행:
```bash
cd api
python test_content_generator.py
```

---

## 데이터셋 구축 스크립트 테스트

### 1. 기본 실행

```bash
cd api
python scripts/build_training_dataset.py
```

### 2. 커스텀 경로 지정

```bash
python scripts/build_training_dataset.py \
  --hwp-dir ../../data/lecture_scripts \
  --pdf-dir ../../data/pdfs \
  --output ../../data/datasets/braille_dataset.json
```

### 3. 결과 확인

생성된 데이터셋 확인:

```bash
# JSON 파일 확인
cat data/datasets/braille_dataset.json | python -m json.tool | head -50

# 또는 Python으로
python -c "import json; data = json.load(open('data/datasets/braille_dataset.json')); print(f'총 {len(data[\"items\"])}개 항목')"
```

**예상 출력:**
```
Processing subject folder: 수능특강_문학_2026 (45 files)
  [1/45] Processing HWP: 01강_[교과서_개념]_1_2_(고3_기본).hwp
    ✅ 완료 (1691 문자)
  ...
Processing 4 PDF files...
  [1/4] Processing PDF: 2026 수능특강_ 문학.pdf (XX.XX MB)
    ✓ 텍스트 추출 완료
    ✅ 완료
Dataset built: 49 items saved to data/datasets/braille_dataset.json
```

---

## 백엔드 서버 실행 및 API 테스트

### 1. 서버 실행

```bash
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면:
- API 문서: http://localhost:8000/docs (Swagger UI)
- 대체 문서: http://localhost:8000/redoc

### 2. 헬스 체크

**Linux/Mac (bash):**
```bash
curl http://localhost:8000/api/v1/health
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/v1/health | Select-Object -ExpandProperty Content
# 또는
curl.exe http://localhost:8000/api/v1/health
```

**브라우저에서:**
- http://localhost:8000/api/v1/health

**예상 응답:**
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

### 3. 서버 로그 확인

**서버 로그 위치:**
- 서버를 실행한 터미널 창에 실시간으로 출력됩니다
- `uvicorn app.main:app --reload` 명령을 실행한 터미널을 확인하세요

**로그가 너무 긴 경우:**

1. **로그를 파일로 저장:**
   ```bash
   # Linux/Mac
   uvicorn app.main:app --reload 2>&1 | tee server.log
   
   # Windows PowerShell
   uvicorn app.main:app --reload *> server.log
   ```

2. **최근 로그만 보기 (마지막 50줄):**
   ```bash
   # Linux/Mac
   tail -f server.log
   
   # Windows PowerShell
   Get-Content server.log -Tail 50 -Wait
   ```

3. **에러만 필터링:**
   ```bash
   # Linux/Mac
   grep -i "error\|exception\|traceback" server.log
   
   # Windows PowerShell
   Select-String -Pattern "error|exception|traceback" server.log
   ```

4. **PDF 처리 관련 로그만 보기:**
   ```bash
   # Linux/Mac
   grep -i "pdf\|extract" server.log
   
   # Windows PowerShell
   Select-String -Pattern "pdf|extract" server.log
   ```

**로그 레벨 조정:**
```bash
# 더 자세한 로그 (debug 레벨)
uvicorn app.main:app --reload --log-level debug

# 간단한 로그만 (warning 레벨)
uvicorn app.main:app --reload --log-level warning
```

### 4. FastAPI 자동 문서로 테스트

1. 브라우저에서 http://localhost:8000/docs 접속
2. 각 엔드포인트를 클릭하여 테스트
3. "Try it out" 버튼으로 직접 테스트 가능

---

## PDF 구조화 추출 테스트

**⚠️ 사전 준비**: 이 테스트는 백엔드 서버가 실행 중이어야 합니다.

### 1. API 엔드포인트 테스트

#### 방법 A: curl 사용

**Linux/Mac (bash):**
```bash
# PDF 구조화 추출
curl -X POST "http://localhost:8000/api/v1/pdf/extract-structured" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/pdfs/2026 수능특강_ 문학.pdf"
```

**Windows (PowerShell):**
```powershell
# PowerShell에서 multipart/form-data 전송
$filePath = "data/pdfs/2026 수능특강_ 문학.pdf"
$uri = "http://localhost:8000/api/v1/pdf/extract-structured"

$form = @{
    file = Get-Item -Path $filePath
}

Invoke-RestMethod -Uri $uri -Method Post -Form $form | ConvertTo-Json -Depth 10

# 또는 curl.exe 사용 (Git Bash 또는 WSL에서)
# curl.exe -X POST "http://localhost:8000/api/v1/pdf/extract-structured" -H "accept: application/json" -F "file=@data/pdfs/2026 수능특강_ 문학.pdf"
```

#### 방법 B: Python 스크립트

`test_pdf_extract.py` 파일 생성:

```python
import requests

url = "http://localhost:8000/api/v1/pdf/extract-structured"

with open("data/pdfs/2026 수능특강_ 문학.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)
    
print(response.json())
```

실행:
```bash
cd api
python test_pdf_extract.py
```

#### 방법 C: FastAPI 문서 UI

1. http://localhost:8000/docs 접속
2. `/api/v1/pdf/extract-structured` 엔드포인트 찾기
3. "Try it out" 클릭
4. 파일 선택 후 "Execute" 클릭

### 2. 예상 응답 형식

```json
{
  "questions": [
    {
      "number": 1,
      "stem": "다음 시의 화자의 태도로 가장 적절한 것은?",
      "choices": [
        {"number": "①", "text": "선택지 1"},
        {"number": "②", "text": "선택지 2"}
      ],
      "page": 1,
      "position": 0
    }
  ],
  "passages": [
    {
      "title": "[작품명]",
      "content": "본문 내용...",
      "page": 1,
      "position": 0
    }
  ],
  "lessons": []
}
```

### 3. 이미지 추출 테스트

**Linux/Mac (bash):**
```bash
curl -X POST "http://localhost:8000/api/v1/pdf/extract-images" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/pdfs/2026 수능특강_ 문학.pdf" \
  -F "extract_type=both"
```

**Windows (PowerShell):**
```powershell
$filePath = "data/pdfs/2026 수능특강_ 문학.pdf"
$uri = "http://localhost:8000/api/v1/pdf/extract-images"

$form = @{
    file = Get-Item -Path $filePath
    extract_type = "both"
}

Invoke-RestMethod -Uri $uri -Method Post -Form $form | ConvertTo-Json -Depth 10
```

**응답:**
```json
{
  "images": [
    {
      "question_number": 1,
      "image": "data:image/png;base64,iVBORw0KG...",
      "page": 1,
      "bbox": [100, 200, 500, 400]
    }
  ],
  "total_count": 10
}
```

---

## 프론트엔드 통합 테스트

### 1. 개발 서버 실행

```bash
cd apps/web
npm run dev
```

서버가 실행되면: http://localhost:5173

### 2. PDF 업로드 테스트

1. 브라우저에서 http://localhost:5173 접속
2. 교재 관리 페이지로 이동
3. PDF 파일 업로드
4. 구조화된 콘텐츠가 표시되는지 확인

### 3. PDF 뷰어 테스트

1. 업로드된 교재 선택
2. 단원 선택
3. `PDFStructuredViewer` 컴포넌트가 렌더링되는지 확인
4. 문제/본문 이미지가 표시되는지 확인
5. 점자 변환이 작동하는지 확인

### 4. 브라우저 개발자 도구 확인

- **Network 탭**: API 호출 확인
  - `/api/v1/pdf/extract-structured` 호출 확인
  - 응답 데이터 확인

- **Console 탭**: 에러 확인
  - JavaScript 에러 확인
  - API 에러 확인

---

## 통합 테스트 시나리오

### 시나리오 1: PDF 교재 업로드 → 구조화 추출 → 화면 표시

1. **백엔드 준비**
   ```bash
   cd api
   uvicorn app.main:app --reload
   ```

2. **프론트엔드 준비**
   ```bash
   cd apps/web
   npm run dev
   ```

3. **테스트 파일 준비**
   - `data/pdfs/` 폴더에 PDF 파일 배치

4. **테스트 실행**
   - 웹 브라우저에서 http://localhost:5173 접속
   - 교재 관리 → PDF 업로드
   - 업로드된 교재 선택 → 단원 선택
   - 구조화된 콘텐츠 확인

### 시나리오 2: 한글 파일 → 데이터셋 구축

1. **파일 준비**
   ```bash
   # 한글 파일이 data/lecture_scripts/수능특강_문학_2026/ 에 있는지 확인
   ls data/lecture_scripts/수능특강_문학_2026/
   ```

2. **데이터셋 구축**
   ```bash
   cd api
   python scripts/build_training_dataset.py
   ```

3. **결과 확인**
   ```bash
   # 생성된 데이터셋 확인
   python -c "import json; data = json.load(open('../data/datasets/braille_dataset.json')); print(json.dumps(data['items'][0], indent=2, ensure_ascii=False))"
   ```

---

## 문제 해결

### 1. requirements.txt 설치 실패 (Windows 인코딩 에러)

**문제**: `pip install -r requirements.txt` 실행 시 `UnicodeDecodeError: 'cp949' codec can't decode byte` 에러

**해결**:
- 파일이 UTF-8 인코딩으로 저장되어 있는지 확인
- 문제가 지속되면 환경 변수 설정:
  ```powershell
  $env:PYTHONIOENCODING="utf-8"
  pip install -r requirements.txt
  ```
- 또는 pip 업그레이드 후 재시도:
  ```powershell
  python.exe -m pip install --upgrade pip
  pip install -r requirements.txt
  ```

### 2. PDF 이미지 추출 실패

**문제**: `pdf2image` 관련 에러

**해결**:
- Windows: Poppler 설치 필요
- Linux: `sudo apt-get install poppler-utils`
- Mac: `brew install poppler`

### 3. 한글 파일 추출 실패

**문제**: `[hwp_extract] 한글 파일 파싱 라이브러리가 설치되지 않았습니다. pyhwp 또는 olefile을 설치해주세요.` 메시지 또는 텍스트 추출 실패

**원인**: `olefile` 라이브러리가 설치되지 않음

**해결**:
```bash
# olefile 설치 (권장)
pip install olefile

# 또는 requirements.txt 재설치
pip install -r requirements.txt
```

**확인 방법**:
```python
# Python에서 확인
python -c "import olefile; print('olefile 설치됨')"
```

**참고**: `olefile`은 `requirements.txt`에 포함되어 있지만, 이전에 설치한 경우 누락될 수 있습니다.

### 4. CORS 에러

**문제**: 프론트엔드에서 API 호출 시 CORS 에러

**해결**: `api/app/core/config.py`에서 CORS_ORIGINS 확인
```python
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",  # Vite 기본 포트
    "http://localhost:3000",  # 다른 포트 사용 시
]
```

### 5. 데이터베이스 에러

**문제**: SQLite 데이터베이스 관련 에러

**해결**:
```bash
# 데이터베이스 파일 확인
ls data/db.sqlite3

# 없으면 자동 생성됨 (서버 실행 시)
```

### 6. PowerShell에서 curl 명령어 실패

**문제**: PowerShell에서 `curl -X POST` 명령어 실행 시 에러 발생

**원인**: PowerShell의 `curl`은 `Invoke-WebRequest`의 별칭이며, curl과 다른 구문을 사용합니다.

**해결**:
1. **PowerShell의 `Invoke-RestMethod` 사용** (권장):
   ```powershell
   $form = @{ file = Get-Item -Path "data/pdfs/파일명.pdf" }
   Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pdf/extract-structured" -Method Post -Form $form
   ```

2. **실제 curl.exe 사용** (Git Bash 또는 WSL 설치 시):
   ```powershell
   curl.exe -X POST "http://localhost:8000/api/v1/pdf/extract-structured" -F "file=@data/pdfs/파일명.pdf"
   ```

3. **Python 스크립트 사용** (가장 안정적):
   - 가이드의 "방법 B: Python 스크립트" 참고

---

## 자동화 테스트 스크립트

### 전체 테스트 실행 스크립트

**Linux/Mac (bash):**

`test_all.sh` 파일 생성:

```bash
#!/bin/bash
# test_all.sh

echo "=== 백엔드 서버 시작 ==="
cd api
uvicorn app.main:app --reload &
SERVER_PID=$!
sleep 3

echo "=== 헬스 체크 ==="
curl http://localhost:8000/api/v1/health

echo "=== PDF 추출 테스트 ==="
# PDF 파일이 있는 경우
if [ -f "../data/pdfs/2026 수능특강_ 문학.pdf" ]; then
    curl -X POST "http://localhost:8000/api/v1/pdf/extract-structured" \
      -F "file=@../data/pdfs/2026 수능특강_ 문학.pdf"
fi

echo "=== 데이터셋 구축 테스트 ==="
python scripts/build_training_dataset.py

echo "=== 서버 종료 ==="
kill $SERVER_PID
```

실행:
```bash
chmod +x test_all.sh
./test_all.sh
```

**Windows (PowerShell):**

`test_all.ps1` 파일 생성:

```powershell
# test_all.ps1

Write-Host "=== 백엔드 서버 시작 ==="
Set-Location api
$job = Start-Job -ScriptBlock { uvicorn app.main:app --reload }
Start-Sleep -Seconds 3

Write-Host "=== 헬스 체크 ==="
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health"
    $response | ConvertTo-Json
} catch {
    Write-Host "서버가 아직 시작되지 않았습니다."
}

Write-Host "=== PDF 추출 테스트 ==="
$pdfPath = "../data/pdfs/2026 수능특강_ 문학.pdf"
if (Test-Path $pdfPath) {
    $form = @{
        file = Get-Item -Path $pdfPath
    }
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pdf/extract-structured" -Method Post -Form $form
        $response | ConvertTo-Json -Depth 5
    } catch {
        Write-Host "PDF 추출 실패: $_"
    }
} else {
    Write-Host "PDF 파일을 찾을 수 없습니다: $pdfPath"
}

Write-Host "=== 데이터셋 구축 테스트 ==="
python scripts/build_training_dataset.py

Write-Host "=== 서버 종료 ==="
Stop-Job $job
Remove-Job $job
```

실행:
```powershell
.\test_all.ps1
```

---

## 다음 단계

테스트가 성공적으로 완료되면:

1. **버그 수정**: 발견된 문제 해결
2. **성능 최적화**: 느린 부분 개선
3. **문서화**: API 문서 보완
4. **다음 기능 개발**: Phase 1 기능 구현 시작

---

*마지막 업데이트: 2024년*
