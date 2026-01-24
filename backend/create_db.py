"""
DB 생성 스크립트
"""
from pathlib import Path
import sys

# backend/ 디렉토리를 Python 경로에 추가
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.infrastructure.database.session import engine, Base
# 모든 모델 import (Base.metadata에 등록하기 위해)
from app.infrastructure.database import models

print("DB 생성 시작...")
print(f"DB URL: {engine.url}")

# 기존 테이블 삭제
print("기존 테이블 삭제 중...")
Base.metadata.drop_all(bind=engine)

# 모든 테이블 생성 (새 스키마로)
print("새 테이블 생성 중...")
Base.metadata.create_all(bind=engine)

print("DB 생성 완료!")
print(f"생성된 테이블: {list(Base.metadata.tables.keys())}")
