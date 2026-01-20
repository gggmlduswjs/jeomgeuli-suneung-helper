# 교재 파이프라인 설치 가이드

## 빠른 시작

### 1. 기본 설치 (필수 패키지)

이미 `requirements.txt`에 포함된 패키지들:
- ✅ `pdf2image>=1.16.0` - PDF → 이미지 변환
- ✅ `Pillow>=10.0.0` - 이미지 처리
- ✅ `pytesseract>=0.3.10` - OCR
- ✅ `langchain>=0.1.0` - LLM 체인

**이미 설치되어 있다면 추가 설치 불필요!**

### 2. 시스템 의존성 (필수)

#### Windows
```bash
# Tesseract OCR 설치 필요
# 다운로드: https://github.com/UB-Mannheim/tesseract/wiki
# 또는 Chocolatey로 설치:
choco install tesseract

# Poppler 설치 (PDF 변환용)
# 다운로드: https://github.com/oschwartz10612/poppler-windows/releases/
# 또는 Chocolatey로 설치:
choco install poppler
```

#### macOS
```bash
brew install tesseract
brew install poppler
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-kor poppler-utils
```

### 3. AI 후처리 사용 시 (선택적)

AI 후처리를 사용하려면 추가 설치:

```bash
pip install openai>=1.0.0
```

또는 `requirements-ai.txt` 설치:
```bash
pip install -r api/requirements-ai.txt
```

**OpenAI API 키 설정:**
```bash
# .env 파일에 추가
OPENAI_API_KEY=your-api-key-here
```

## 설치 확인

### Python 패키지 확인
```bash
python -c "import pdf2image, pytesseract, PIL; print('✅ 기본 패키지 설치됨')"
```

### Tesseract 확인
```bash
# Windows
tesseract --version

# macOS/Linux
tesseract --version
```

### OpenAI 확인 (AI 후처리 사용 시)
```bash
python -c "import openai; print('✅ OpenAI 설치됨')"
```

## 문제 해결

### Tesseract를 찾을 수 없음
```bash
# Windows: 경로 설정 확인
# 코드에서 자동으로 찾지만, 수동 설정:
# C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Poppler를 찾을 수 없음
```python
# Python 코드에서 경로 지정
pipeline = TextbookPipeline(
    subject="literature",
    poppler_path=r"C:\path\to\poppler\bin"  # Windows
)
```

### 메모리 부족 오류
```python
# 병렬 처리 워커 수 줄이기
pipeline = TextbookPipeline(
    subject="literature",
    max_workers=2  # CPU 코어 수보다 적게
)
```

## 최소 요구사항

### 기본 기능만 사용 (AI 후처리 없음)
- Python 3.8+
- Tesseract OCR
- Poppler
- `requirements.txt`의 기본 패키지들

### AI 후처리 사용
- 위 모든 것 +
- OpenAI API 키
- `openai` 패키지

## 패키지 목록 요약

### 필수 (이미 requirements.txt에 있음)
```
pdf2image>=1.16.0
Pillow>=10.0.0
pytesseract>=0.3.10
langchain>=0.1.0
langchain-openai>=0.0.5
```

### 선택적 (AI 후처리)
```
openai>=1.0.0
```

### 표준 라이브러리 (추가 설치 불필요)
- `multiprocessing`
- `concurrent.futures`
- `json`
- `hashlib`
- `time`
- `pathlib`
- `re`
- `logging`
