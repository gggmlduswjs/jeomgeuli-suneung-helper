# 스크립트 (목차·템플릿)

백엔드 API(`localhost:8000`)와 연동해 **목차 추출 → 정제 → 템플릿 생성**을 하는 스크립트들입니다.

**실행 방법:** 프로젝트 **루트**에서 실행하세요.

```bash
# 예: 사용자 목차 처리
python scripts/process_user_toc.py

# 예: PDF에서 목차 추출
python scripts/extract_full_toc.py
```

## 주요 스크립트

| 스크립트 | 설명 |
|----------|------|
| `extract_full_toc.py` | PDF에서 목차 텍스트 추출 → `toc_extracted_full.txt` |
| `clean_and_generate.py` | `toc_extracted_full.txt` 정제 + 템플릿 생성 |
| `process_user_toc.py` | `data/toc_raw_input.txt` 사용자 목차 처리 |
| `generate_template_from_toc.py` | `toc_full.txt`로 템플릿 생성 |
| `fix_page_ranges.py` | `template_final.json` 페이지 범위 수정 → `template_fixed.json` |
| `save_template.py` | `template_fixed.json`을 API로 저장 |
| `test_api_full.py` | API 전체 테스트 |
| `test_clean_toc.py` | 목차 정제·강의 추출 테스트 |

입력/출력 파일은 프로젝트 루트 또는 `data/`에 생성됩니다. 백엔드 서버가 실행 중이어야 합니다.
