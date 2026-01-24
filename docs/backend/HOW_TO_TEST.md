# 테스트 실행 방법 (간단 가이드)

## 1. 빠른 테스트 (추천)

```bash
cd backend
python test_quick.py
```

**결과 확인:**
- 텍스트 전처리기 동작 확인
- 섹션 추출기 동작 확인
- 섹션 병합 동작 확인

## 2. pytest로 단위 테스트

```bash
cd backend

# 모든 테스트 실행
pytest

# 특정 테스트 파일만
pytest tests/test_section_extractor.py

# 상세 출력
pytest -v -s
```

## 3. 실제 데이터로 테스트

### 방법 A: API 사용 (프론트엔드)
1. 관리자 페이지 접속: `http://localhost:3000/admin`
2. "새 교재 업로드" 클릭
3. PDF 업로드
4. 파싱 완료 후 `lecture_01.json` 확인

### 방법 B: 스크립트 사용
```bash
cd backend
python scripts/pipeline/run_textbook_pipeline.py
```

### 방법 C: 재파싱 (기존 교재)
```bash
# API 호출
POST /api/books/{book_id}/reparse
```

## 4. 결과 확인

### lecture_01.json 확인
```bash
# 파일 위치
backend/data/literature/lectures/lecture_01.json

# 섹션이 있는지 확인
cat backend/data/literature/lectures/lecture_01.json
```

**성공 기준:**
- `sections` 배열이 비어있지 않음
- 각 섹션에 `title`, `type`, `content` 포함

## 5. 문제 해결

### ImportError 발생 시
```bash
# PYTHONPATH 설정
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python test_quick.py
```

### pytest를 찾을 수 없을 때
```bash
pip install pytest
```

## 빠른 체크리스트

- [ ] `python test_quick.py` 실행 → 성공
- [ ] `pytest tests/test_section_extractor.py` 실행 → 성공
- [ ] 실제 PDF 업로드 → 파싱 완료
- [ ] `lecture_01.json`에 `sections` 배열이 비어있지 않음
