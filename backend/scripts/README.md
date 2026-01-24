# API Scripts 디렉토리

이 디렉토리는 개발 및 운영에 필요한 유틸리티 스크립트들을 포함합니다.

## 📋 스크립트 목록

### 🚀 주요 스크립트

#### 교재 파이프라인
- **`run_textbook_pipeline.py`** - 교재 PDF 파이프라인 실행 (문학/수학Ⅰ/영어)
  - PDF에서 강의, 문제, 본문을 자동으로 추출하고 AI 학습 콘텐츠 생성
  - 과목별 파이프라인 전략 지원 (literature, math1, english)

#### 서버 실행
- **`start_server.sh`** - Linux/Mac 서버 실행 스크립트
- **`start_server.bat`** - Windows 서버 실행 스크립트

#### 데이터셋 구축
- **`build_training_dataset.py`** - 학습 데이터셋 구축 스크립트

#### 데이터 정리
- **`cleanup_books.py`** - 교재 데이터 정리 (더미 데이터, 파일 없는 교재 삭제)
  - 한글 파일(.hwp) 및 PDF 파일에서 점자 변환 학습 데이터셋 생성

## 사용 방법

### 교재 파이프라인 실행
```bash
cd api
python scripts/run_textbook_pipeline.py
```

스크립트는 대화형으로 다음을 입력받습니다:
- 과목 선택 (literature/math1/english)
- PDF 파일 경로 (자동 감지 또는 수동 입력)
- 최적화 옵션 (pdfplumber, 병렬 처리, AI 후처리 등)

또는 명령줄 인자로 실행:
```bash
python scripts/run_textbook_pipeline.py --subject literature --pdf "data/pdfs/2026 수능특강_ 문학.pdf"
```

### 서버 실행
```bash
# Linux/Mac
./api/scripts/start_server.sh

# Windows
api\scripts\start_server.bat
```

### 데이터셋 구축
```bash
cd api
python scripts/build_training_dataset.py --hwp-dir "data/lecture_scripts" --pdf-dir "data/pdfs" --output "data/datasets/braille_dataset.json"
```

### 교재 데이터 정리
```bash
cd api
# file_path가 None이거나 파일이 없는 교재 삭제
python scripts/cleanup_books.py

# 확인 없이 실행
python scripts/cleanup_books.py --yes

# FAILED 상태 교재만 삭제 (7일 이상 경과)
python scripts/cleanup_books.py --failed-old --failed-days 7
```

---

*마지막 업데이트: 2025년 1월*
