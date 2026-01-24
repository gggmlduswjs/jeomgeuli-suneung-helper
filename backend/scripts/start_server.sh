#!/bin/bash
# API 서버 실행 스크립트 (Linux/Mac)
cd "$(dirname "$0")/.."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
