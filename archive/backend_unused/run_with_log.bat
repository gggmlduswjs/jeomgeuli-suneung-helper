@echo off
REM 기존 로그 파일 삭제
if exist parsing_log.txt del parsing_log.txt

REM 백엔드 실행하면서 로그를 파일로 저장
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 2>&1 | tee parsing_log.txt
