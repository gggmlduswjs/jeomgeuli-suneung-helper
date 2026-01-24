# 로컬 개발 및 배포용 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치 (PDF 처리 도구)
RUN apt-get update && apt-get install -y \
    gcc \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 데이터 디렉토리 생성
RUN mkdir -p /app/data/uploads /app/data/extracted /app/data/parsed

# 포트 노출
EXPOSE 8000

# 환경 변수 (Docker 환경에서 자동 감지됨)
ENV POPPLER_PATH=/usr/bin
ENV TESSERACT_CMD=/usr/bin/tesseract

# 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
