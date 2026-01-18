# 테스트 파일 구조

## 📁 테스트 파일 구성

### 핵심 테스트

- **`test_pdf_extract.py`** - PDF 추출 기능 테스트
  - 기본 PDF 추출 (PDFPlumber)
  - 문학 PDF 추출
  - Enhanced OCR (선택적)
  - AI 텍스트 후처리 (선택적)

- **`test_parsers.py`** - 과목별 파서 테스트 (통합)
  - 수학Ⅰ 파서
  - 문학 파서
  - 영어 파서
  - 사용법: `python tests/test_parsers.py --subject all` 또는 `--subject math1`

- **`test_pdf_api.py`** - PDF API 엔드포인트 테스트
  - 헬스 체크
  - PDF 구조화 추출 API
  - PDF 이미지 추출 API
  - ⚠️ 서버가 실행 중이어야 함

### HWP 관련 테스트

- **`test_hwp_extract.py`** - 한글 파일 추출 테스트
  - HWP 텍스트 추출
  - 구조 추출
  - 레슨 정보 추출

- **`test_content_generator.py`** - 콘텐츠 자동 생성 테스트
  - HWP 파일 기반 자동 생성
  - 점자 변환

### 헬퍼 파일

- **`test_helpers.py`** - 테스트 공통 헬퍼 함수
  - PDF 파일 찾기
  - 블록 미리보기 포맷팅
  - 블록 타입별 개수 세기
  - 파일 크기 포맷팅

## 🚀 실행 방법

### 개별 테스트 실행

```powershell
# PDF 추출 테스트
python tests/test_pdf_extract.py

# 파서 테스트 (전체)
python tests/test_parsers.py --subject all

# 파서 테스트 (수학Ⅰ만)
python tests/test_parsers.py --subject math1

# API 테스트 (서버 필요)
python tests/test_pdf_api.py

# HWP 추출 테스트
python tests/test_hwp_extract.py

# 콘텐츠 생성 테스트
python tests/test_content_generator.py
```

### 전체 테스트 실행 (예정)

```powershell
# pytest 사용 (향후 지원)
pytest tests/
```

## 📝 테스트 파일 정리

### 삭제된 파일 (통합됨)

다음 파일들은 `test_parsers.py`로 통합되었습니다:
- ~~`test_math1_parser.py`~~ → `test_parsers.py --subject math1`
- ~~`test_literature_parser.py`~~ → `test_parsers.py --subject literature`
- ~~`test_english_parser.py`~~ → `test_parsers.py --subject english`

### 유지되는 파일

- `test_pdf_extract.py` - PDF 추출 단위 테스트
- `test_parsers.py` - 과목별 파서 통합 테스트
- `test_pdf_api.py` - PDF API 통합 테스트
- `test_hwp_extract.py` - HWP 추출 테스트
- `test_content_generator.py` - 콘텐츠 생성 테스트
- `test_helpers.py` - 테스트 헬퍼 함수

## 🔄 통합 계획

### Phase 1: 파서 테스트 통합 ✅
- [x] `test_parsers.py` 생성
- [x] 기존 파서 테스트 파일 통합

### Phase 2: 선택적 통합 (제안)
- [ ] `test_pdf.py`로 PDF 관련 테스트 통합 (선택적)
  - `test_pdf_extract.py` + `test_pdf_api.py`
- [ ] `test_hwp.py`로 HWP 관련 테스트 통합 (선택적)
  - `test_hwp_extract.py` + `test_content_generator.py`

---

**마지막 업데이트**: 2025-01-XX
