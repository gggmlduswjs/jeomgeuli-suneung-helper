# 파일 정리 요약

## 정리 완료 ✅

### 1. 테스트 파일 정리
- **유지된 파일** (6개 → `tests/` 폴더로 이동):
  - `test_api_simple.py`: 기본 API 통합 테스트
  - `test_block_decomposition.py`: 레슨 블록 분해 테스트
  - `test_langchain_flow.py`: LangChain Flow 테스트
  - `test_lesson_blocks_api.py`: 레슨 블록 API 테스트
  - `test_hwp_extraction.py`: HWP 파일 추출 테스트
  - `validate_json_output.py`: JSON 검증 도구

- **삭제된 파일** (17개):
  - 커리큘럼 관련 임시 테스트: 7개
  - 레슨 1 관련 임시 테스트: 4개
  - 기타 임시 테스트: 4개
  - PowerShell 스크립트: 2개

### 2. 서비스 파일 정리
- **삭제**: `langchain_block_decomposer.py` (중복)
- **정리**: `ai_block_decomposer.py` (프롬프트만 유지)

### 3. 사용되지 않는 import 제거
- `curriculum.py`에서 `PDFScriptMatcher` import 제거 (사용되지 않음)

## 최종 구조

### 핵심 서비스
- `lesson_block_decomposer.py`: 규칙 기반 블록 분해
- `langchain_lesson_flow.py`: LangChain Flow (LLM 통합)
- `ai_block_decomposer.py`: 프롬프트 정의

### 테스트
- `tests/`: 6개 핵심 테스트 파일만 유지

## 향후 사용 예정 파일 (유지)

다음 파일들은 현재 직접 사용되지 않지만 향후 필요:
- `json_to_mongodb_converter.py`: MongoDB 마이그레이션용
- `pdf_script_matcher.py`: PDF-대본 매칭 (향후 구현)
- `lecture_to_json_pipeline.py`: 파이프라인 (향후 사용)
