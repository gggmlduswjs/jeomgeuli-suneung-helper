# Archive 폴더

포트폴리오 작성을 위해 정리된 파일들입니다.

## 포함된 내용

### 루트 디렉토리 파일들
- **임시 스크립트**: `*.py` 파일들 (테스트, 디버깅용)
- **문서**: `*.md` 파일들 (개발 과정 문서)
- **임시 데이터**: `*.txt`, `*.json` 파일들 (테스트 데이터)
- **캐시 파일**: `.vite`, `.claude` 등
- **샘플 데이터**: 테스트용 PDF, JSON 파일들

### Backend 미사용 파일들 (`backend_unused/`)
- **테스트 파일**: `tests/` 폴더 전체
- **백업 파일**: `*.backup` 파일들
- **개발 스크립트**: `scripts/` 폴더 (개발/디버깅용)
- **문서**: `docs/`, `REFACTORING_SUMMARY.md`
- **배포 설정**: `Dockerfile`, `docker-compose.yml`, `render.yaml` 등
- **DB 마이그레이션**: `create_db.py`, `migrate_db.py`
- **로그 파일**: `*.log` 파일들

### Frontend 미사용 파일들 (`frontend_unused/`)
- **백업 파일**: `*.bak` 파일들 (12개)
- **테스트 파일**: `tests/` 폴더
- **테스트 설정**: `playwright.config.ts`, `vitest.config.ts`
- **문서**: 개발 과정 문서들

### PDF Study 관련 파일들
- **PDFStudy.tsx**: PDF 직접 로딩 및 텍스트 추출을 사용하던 학습 페이지 (구조 파싱 데이터 사용으로 대체됨)

## 핵심 파일 위치

핵심 프로젝트 파일들은 루트 디렉토리에 그대로 유지되어 있습니다:
- `backend/app/` - 백엔드 핵심 코드
- `frontend/src/` - 프론트엔드 핵심 코드
- `.gitignore` - Git 설정
- `README.md` - 프로젝트 메인 README
