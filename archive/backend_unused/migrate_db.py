"""
DB 마이그레이션: books 테이블에 진행률 컬럼 추가
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "db.sqlite3"
print(f"DB 경로: {db_path}")
print(f"DB 존재: {db_path.exists()}")

if not db_path.exists():
    print("DB 파일이 없습니다.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 기존 컬럼 확인
cursor.execute("PRAGMA table_info(books);")
columns = {row[1] for row in cursor.fetchall()}
print(f"기존 컬럼: {columns}")

# 컬럼 추가
columns_to_add = [
    ("parse_progress", "INTEGER DEFAULT 0"),
    ("current_page", "INTEGER DEFAULT 0"),
    ("total_pages", "INTEGER DEFAULT 0"),
]

for col_name, col_def in columns_to_add:
    if col_name not in columns:
        try:
            cursor.execute(f"ALTER TABLE books ADD COLUMN {col_name} {col_def};")
            print(f"✓ {col_name} 컬럼 추가 완료")
        except sqlite3.OperationalError as e:
            print(f"✗ {col_name} 컬럼 추가 실패: {e}")
    else:
        print(f"- {col_name} 컬럼 이미 존재")

conn.commit()
conn.close()

print("\n마이그레이션 완료!")
