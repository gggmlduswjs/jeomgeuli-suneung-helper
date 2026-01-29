# 테스트 가이드

## 테스트 실행 방법

### 1. 단위 테스트 (Unit Tests)

#### 환경 설정
```bash
# backend 디렉토리로 이동
cd backend

# pytest 설치 (없는 경우)
pip install pytest pytest-cov

# 또는 requirements.txt에 추가
pip install -r requirements.txt
```

#### 테스트 실행
```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일만 실행
pytest tests/test_section_extractor.py

# 특정 테스트 클래스만 실행
pytest tests/test_section_extractor.py::TestImprovedSectionExtractor

# 특정 테스트 메서드만 실행
pytest tests/test_section_extractor.py::TestImprovedSectionExtractor::test_extract_by_pattern_success

# 상세 출력 (-v: verbose)
pytest -v

# 출력과 함께 실행 (-s: show print statements)
pytest -v -s

# 커버리지 확인
pytest --cov=app.infrastructure.pdf.parsers.section_extractor --cov-report=html
```

### 2. 실제 데이터로 테스트

#### 방법 1: 스크립트로 테스트
```bash
# 파이프라인 스크립트 실행 (개발/테스트용)
python scripts/pipeline/run_textbook_pipeline.py
```

#### 방법 2: API로 테스트
```bash
# PDF 업로드 및 파싱
curl -X POST http://localhost:8000/api/books/upload \
  -F "file=@data/pdfs/2026 수능특강_ 문학.pdf" \
  -F "subject=literature" \
  -F "title=수능특강 문학"

# 재파싱 (기존 교재)
curl -X POST http://localhost:8000/api/books/{book_id}/reparse
```

#### 방법 3: Python 인터프리터로 직접 테스트
```python
# Python 인터프리터 실행
python

# 테스트 코드
from app.infrastructure.pdf.parsers.section_extractor import ImprovedSectionExtractor
from app.infrastructure.pdf.parsers.literature import LiteratureParser
from pathlib import Path

# 1. 섹션 추출기 직접 테스트
config = {
    'concept_title_patterns': [r'^(\d+)\s*[\.]\s*([가-힣\s]{2,20})$'],
    'content_header_patterns': [r'작품으로 이해하기'],
    'start_content_page': 8
}

extractor = ImprovedSectionExtractor(config=config)

# OCR 데이터 준비 (실제 데이터 사용)
# ocr_data = [...]  # 실제 OCR 데이터

# 섹션 추출
result = extractor.extract(ocr_data)
print(f"섹션 수: {len(result.sections)}")
print(f"방법: {result.method}")
print(f"신뢰도: {result.confidence:.2f}")

# 2. LiteratureParser 통합 테스트
parser = LiteratureParser(
    config_path=Path("data/literature/config.json"),
    enable_ai_parsing=False  # AI 파싱 비활성화 (빠른 테스트)
)

# 실제 OCR 데이터로 테스트
# lecture_ocr_data = [...]  # 강의 OCR 데이터
# sections = parser.extract_sections(lecture_ocr_data)
# print(f"추출된 섹션: {sections}")
```

### 3. 통합 테스트

#### 실제 PDF 파일로 테스트
```python
# test_integration.py 파일 생성
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.pdf.pipeline import UnifiedPipeline
from app.core.config import settings

def test_literature_parsing():
    """실제 PDF로 통합 테스트"""
    
    # PDF 파일 경로
    pdf_path = Path("data/pdfs/2026 수능특강_ 문학.pdf")
    
    if not pdf_path.exists():
        print(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    # 파이프라인 실행
    pipeline = UnifiedPipeline(
        subject="literature",
        book_id="test_book",
        book_title="테스트 교재"
    )
    
    try:
        result = pipeline.process(
            pdf_path=pdf_path,
            extractor_type="pdfplumber",  # 또는 "ocr"
            max_pages=20  # 테스트용으로 페이지 수 제한
        )
        
        # 결과 확인
        print(f"강의 수: {len(result.get('lectures', []))}")
        
        # 첫 번째 강의의 섹션 확인
        if result.get('lectures'):
            first_lecture = result['lectures'][0]
            print(f"첫 번째 강의: {first_lecture.get('title')}")
            print(f"섹션 수: {len(first_lecture.get('sections', []))}")
            
            # 섹션이 비어있지 않은지 확인
            if first_lecture.get('sections'):
                print("✅ 섹션 추출 성공!")
                for section in first_lecture['sections']:
                    print(f"  - {section.get('title')} ({section.get('type')})")
            else:
                print("❌ 섹션이 비어있습니다.")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_literature_parsing()
```

실행:
```bash
python test_integration.py
```

### 4. 기존 데이터 검증

#### lecture_01.json 검증
```python
# validate_lecture.py
import json
from pathlib import Path

def validate_lecture(lecture_path: Path):
    """강의 JSON 파일 검증"""
    
    with open(lecture_path, 'r', encoding='utf-8') as f:
        lecture = json.load(f)
    
    print(f"강의 ID: {lecture.get('lecture_id')}")
    print(f"제목: {lecture.get('title')}")
    print(f"섹션 수: {len(lecture.get('sections', []))}")
    
    if lecture.get('sections'):
        print("✅ 섹션이 있습니다:")
        for section in lecture['sections']:
            print(f"  - {section.get('title')} ({section.get('type')})")
            print(f"    콘텐츠: {len(section.get('content', []))}개 문단")
    else:
        print("❌ 섹션이 비어있습니다.")
    
    return len(lecture.get('sections', [])) > 0

# 사용
lecture_path = Path("data/literature/lectures/lecture_01.json")
if lecture_path.exists():
    validate_lecture(lecture_path)
else:
    print(f"파일을 찾을 수 없습니다: {lecture_path}")
```

## 테스트 체크리스트

### 단위 테스트
- [ ] `test_extract_by_pattern_success` - 패턴 매칭 성공
- [ ] `test_extract_fallback_when_pattern_fails` - 폴백 동작
- [ ] `test_merge_sections` - 섹션 병합
- [ ] `test_merge_sections_duplicate_removal` - 중복 제거

### 통합 테스트
- [ ] 실제 PDF 파일로 파싱
- [ ] 섹션 추출 결과 검증
- [ ] lecture_01.json에 섹션이 있는지 확인

### 성능 테스트
- [ ] 패턴 매칭 속도 (1-3초)
- [ ] 휴리스틱 속도 (1-2초)
- [ ] AI 분석 속도 (5-10초, 선택적)

## 문제 해결

### ImportError 발생 시
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# 또는
cd backend
python -m pytest tests/
```

### 모듈을 찾을 수 없을 때
```python
# 테스트 파일 상단에 추가
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

## 빠른 테스트 명령어

```bash
# 모든 테스트 실행
pytest

# 특정 테스트만 실행
pytest tests/test_section_extractor.py -v

# 실패한 테스트만 재실행
pytest --lf

# 첫 번째 실패에서 중단
pytest -x

# 커버리지 확인
pytest --cov=app --cov-report=term-missing
```
