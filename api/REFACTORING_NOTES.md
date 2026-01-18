# 리팩토링 노트

## 완료된 작업

### 1. 중복 서비스 파일 통합
- ✅ `langchain_block_decomposer.py` 삭제 (중복 기능)
- ✅ `ai_block_decomposer.py` 정리 (프롬프트만 유지)

### 2. 파일 구조 정리
- ✅ 테스트 파일 정리 가이드 작성 (`tests/README.md`)

## 정리 예정 파일

### 임시 테스트 파일 (api 루트)
다음 파일들은 개발 중 임시 테스트용입니다:
- `test_curriculum_*.py` (커리큘럼 관련 테스트)
- `test_lesson_1_*.py` (레슨 1 관련 테스트)
- `test_hwp_*.py` (HWP 관련 테스트)
- `test_pipeline_*.py` (파이프라인 테스트)
- `test_json_*.py` (JSON 구조 테스트)

이 파일들은 다음 중 하나로 처리됩니다:
1. `tests/` 폴더로 이동 (재사용 가능한 테스트)
2. 삭제 (임시 테스트)

### 사용되지 않는 파일 확인 필요
- `validate_json_output.py`: JSON 검증 스크립트 (필요시 유지)
- `test_*.ps1`: PowerShell 테스트 스크립트 (필요시 유지)

## 다음 단계

1. 테스트 파일 분류 및 정리
2. 사용되지 않는 import 제거
3. 코드 중복 제거
4. 문서 업데이트
