# 테스트 파일 정리

## 테스트 파일 위치

모든 테스트 파일은 `api/tests/` 디렉토리에 있습니다.

## 주요 테스트 파일 (유지)

### 통합 테스트
- `test_api_simple.py`: 기본 API 통합 테스트 (헬스 체크, 커리큘럼 목록, 콘텐츠 검증, HWP 업로드)
- `test_lesson_blocks_api.py`: 레슨 블록 생성 API 테스트
- `test_langchain_flow.py`: LangChain Flow 테스트 (LLM 통합)

### 기능별 테스트
- `test_block_decomposition.py`: 레슨 블록 분해 테스트 (규칙 기반)
- `test_hwp_extraction.py`: HWP 파일 추출 테스트

### 검증 도구
- `validate_json_output.py`: JSON 파일 품질 검증

## 임시 테스트 파일 (삭제 예정)

다음 파일들은 개발 중 특정 기능을 테스트하기 위한 임시 파일입니다:

### 커리큘럼 관련 (임시)
- `test_curriculum_analysis.py`
- `test_curriculum_detail.py`
- `test_curriculum_generate.py`
- `test_curriculum_structure.py`
- `test_full_literature_curriculum.py`
- `test_improved_curriculum.py`
- `test_new_curriculum.py`

### 레슨 1 관련 (임시)
- `test_lesson_1_detail.py`
- `test_lesson_1_full_content.py`
- `test_lesson_1_json.py`
- `test_lesson_1_summary.py`

### 기타 (임시)
- `test_hwp_structure.py`
- `test_json_structure.py`
- `test_pipeline_single.py`
- `test_pipeline_with_text.py`

### PowerShell 스크립트 (중복)
- `test_curriculum_api.ps1` (Python 버전과 중복)
- `test_hwp_upload.ps1` (Python 버전과 중복)

## 테스트 실행 방법

### 기본 API 테스트
```bash
cd api
python tests/test_api_simple.py
```

### 레슨 블록 분해 테스트
```bash
python tests/test_block_decomposition.py
```

### LangChain Flow 테스트
```bash
# OPENAI_API_KEY 환경변수 설정 필요
python tests/test_langchain_flow.py
```

### JSON 검증
```bash
python tests/validate_json_output.py
```
