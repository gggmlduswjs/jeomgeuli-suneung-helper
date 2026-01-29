# Render 배포 가이드

이 문서는 점글이 수능 학습 도우미를 Render에 배포하는 방법을 설명합니다.

## 사전 준비

1. **GitHub 저장소 준비**
   - 프로젝트를 GitHub에 푸시합니다
   - Render는 GitHub 저장소와 연동하여 자동 배포합니다

2. **Render 계정 생성**
   - [Render](https://render.com)에 가입합니다
   - GitHub 계정과 연동합니다

## 배포 단계

### 1. Backend 배포

1. Render 대시보드에서 **"New +"** → **"Blueprint"** 선택
2. GitHub 저장소를 연결하고 `render.yaml` 파일이 있는 저장소를 선택
3. Render가 자동으로 `render.yaml`을 읽어 서비스를 생성합니다

또는 수동으로:

1. Render 대시보드에서 **"New +"** → **"Web Service"** 선택
2. GitHub 저장소 연결
3. 설정:
   - **Name**: `jeomgeuli-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/api/v1/health`

### 2. 환경 변수 설정 (Backend)

Render 대시보드의 **Environment** 탭에서 다음 환경 변수를 설정합니다:

#### 필수 환경 변수

- `OPENAI_API_KEY`: OpenAI API 키 (LLM 기능 사용 시)
- `DATABASE_URL`: PostgreSQL 데이터베이스 URL (Render에서 PostgreSQL 서비스 생성 후 자동 설정 가능)

#### 선택적 환경 변수

- `CORS_ORIGINS`: CORS 허용 도메인 (기본값: `https://jeomgeuli-frontend.onrender.com,http://localhost:5173`)
- `MATHPIX_APP_ID`: MathPix API App ID (수식 OCR 사용 시)
- `MATHPIX_APP_KEY`: MathPix API App Key
- `ROBOFLOW_API_KEY`: Roboflow API Key (YOLO 모델 사용 시)
- `ROBOFLOW_WORKSPACE_ID`: Roboflow Workspace ID
- `ROBOFLOW_PROJECT_ID`: Roboflow Project ID

### 3. PostgreSQL 데이터베이스 생성 (선택)

1. Render 대시보드에서 **"New +"** → **"PostgreSQL"** 선택
2. 데이터베이스 이름 설정 (예: `jeomgeuli-db`)
3. 생성 후 자동으로 `DATABASE_URL` 환경 변수가 설정됩니다
4. Backend 서비스의 환경 변수에 `DATABASE_URL`을 추가합니다

### 4. Persistent Disk 설정 (Backend)

Backend 서비스의 **Settings** → **Disks**에서:

- **Name**: `backend-data`
- **Mount Path**: `/opt/render/project/src/backend/data`
- **Size**: 10GB (필요에 따라 조정)

이 디스크는 강의 데이터(JSON, 이미지)를 저장하는 데 사용됩니다.

### 5. Frontend 배포

1. Render 대시보드에서 **"New +"** → **"Static Site"** 선택
2. GitHub 저장소 연결
3. 설정:
   - **Name**: `jeomgeuli-frontend`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`

### 6. Frontend 환경 변수 설정

Frontend 서비스의 **Environment** 탭에서:

- `VITE_API_BASE_URL`: Backend 서비스 URL (예: `https://jeomgeuli-backend.onrender.com/api/v1`)

**중요**: Backend가 배포된 후 생성된 URL을 사용해야 합니다.

### 7. 데이터 업로드

Backend의 `backend/data` 폴더에 있는 강의 데이터를 Render의 Persistent Disk에 업로드해야 합니다.

방법:
1. Render Shell을 사용하여 SSH 접속
2. 또는 GitHub Actions를 사용하여 자동 업로드
3. 또는 Render의 파일 업로드 기능 사용 (제한적)

## 배포 확인

### Backend 확인

1. Backend 서비스 URL로 접속 (예: `https://jeomgeuli-backend.onrender.com`)
2. Health check: `https://jeomgeuli-backend.onrender.com/api/v1/health`
3. API 문서: `https://jeomgeuli-backend.onrender.com/docs` (FastAPI 자동 생성)

### Frontend 확인

1. Frontend 서비스 URL로 접속 (예: `https://jeomgeuli-frontend.onrender.com`)
2. 브라우저 개발자 도구에서 API 호출이 정상적으로 작동하는지 확인

## 트러블슈팅

### Backend가 시작되지 않는 경우

1. **로그 확인**: Render 대시보드의 **Logs** 탭에서 에러 메시지 확인
2. **환경 변수 확인**: 필수 환경 변수가 모두 설정되었는지 확인
3. **의존성 확인**: `requirements.txt`의 패키지가 모두 설치되는지 확인

### Frontend가 API를 호출하지 못하는 경우

1. **CORS 설정 확인**: Backend의 `CORS_ORIGINS`에 Frontend URL이 포함되어 있는지 확인
2. **API Base URL 확인**: Frontend의 `VITE_API_BASE_URL`이 올바른 Backend URL을 가리키는지 확인
3. **네트워크 확인**: 브라우저 개발자 도구의 Network 탭에서 요청 상태 확인

### 데이터 파일이 없는 경우

1. **Persistent Disk 확인**: Disk가 올바르게 마운트되었는지 확인
2. **파일 경로 확인**: `backend/data` 폴더 구조가 올바른지 확인
3. **권한 확인**: 파일 읽기 권한이 있는지 확인

## 자동 배포

Render는 GitHub 저장소와 연동되어 있으면 자동으로 배포됩니다:

- **자동 배포**: `main` 브랜치에 푸시하면 자동으로 배포
- **수동 배포**: 특정 커밋을 선택하여 배포 가능

## 비용

- **Starter Plan**: 무료 (제한적 리소스, 일정 시간 후 sleep)
- **Standard Plan**: 유료 (항상 실행, 더 많은 리소스)

## 추가 리소스

- [Render 문서](https://render.com/docs)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [Vite 빌드 가이드](https://vitejs.dev/guide/build.html)
