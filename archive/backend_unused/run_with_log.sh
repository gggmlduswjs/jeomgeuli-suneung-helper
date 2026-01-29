#!/bin/bash
# 기존 로그 파일 삭제
rm -f parsing_log.txt

# 백엔드 실행하면서 로그를 파일과 터미널에 동시 출력
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 2>&1 | tee parsing_log.txt
