"""
Unit 테이블에 image_path 컬럼 추가하는 마이그레이션 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.session import SessionLocal, engine
from sqlalchemy import text

def add_image_path_column():
    """Unit 테이블에 image_path 컬럼 추가"""
    db = SessionLocal()
    
    try:
        # SQLite에서 컬럼 추가
        with engine.connect() as conn:
            # 컬럼이 이미 있는지 확인
            result = conn.execute(text("PRAGMA table_info(units)"))
            columns = [row[1] for row in result]
            
            if 'image_path' not in columns:
                print("[INFO] image_path 컬럼 추가 중...")
                conn.execute(text("ALTER TABLE units ADD COLUMN image_path VARCHAR"))
                conn.commit()
                print("[SUCCESS] image_path 컬럼 추가 완료")
            else:
                print("[INFO] image_path 컬럼이 이미 존재합니다.")
        
    except Exception as e:
        print(f"[ERROR] 마이그레이션 실패: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_image_path_column()
