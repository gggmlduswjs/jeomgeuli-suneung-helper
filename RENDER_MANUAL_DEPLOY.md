# Render 수동 배포 가이드 (무료 플랜)

Blueprint가 결제 정보를 요구하는 경우, 수동으로 서비스를 생성하면 무료로 배포할 수 있습니다.

## 1. Backend 배포 (수동)

1. Render 대시보드에서 **"New +"** → **"Web Service"** 선택
2. GitHub 저장소 연결: `gggmlduswjs/jeomgeuli-suneung-helper`
3. 설정:
   - **Name**: `jeomgeuli-backend`
   - **Region**: `Singapore` (또는 원하는 지역)
   - **Branch**: `refactor/complete-pipeline-separation` (또는 `main`)
   - **Language**: **"Python 3"** 선택 (중요! Docker가 아닌 Python 3)
   - **Root Directory**: (비워두기 또는 `backend`)
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **"Free"** 선택 (무료 플랜)
   - **Health Check Path**: `/api/v1/health`

4. **Environment Variables** 탭에서 추가:
   - `PYTHON_VERSION`: `3.11.0`
   - `OPENAI_API_KEY`: (OpenAI API 키 입력)
   - `DATABASE_URL`: (PostgreSQL 사용 시, 선택사항)
   - `CORS_ORIGINS`: `https://jeomgeuli-frontend.onrender.com,http://localhost:5173`

5. **Create Web Service** 클릭

## 2. Frontend 배포 (수동)

1. Render 대시보드에서 **"New +"** → **"Static Site"** 선택
2. GitHub 저장소 연결: `gggmlduswjs/jeomgeuli-suneung-helper`
3. 설정:
   - **Name**: `jeomgeuli-frontend`
   - **Branch**: `refactor/complete-pipeline-separation` (또는 `main`)
   - **Root Directory**: `frontend` (중요!)
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

4. **Environment Variables** 탭에서 추가:
   - `VITE_API_BASE_URL`: Backend URL (예: `https://jeomgeuli-backend.onrender.com/api/v1`)
   - **중요**: Backend가 배포 완료된 후 URL을 설정하세요!

5. **Create Static Site** 클릭

## 3. 데이터 파일 처리

무료 플랜에서는 Persistent Disk를 사용할 수 없으므로:

**옵션 1: Git에 데이터 포함 (권장)**
- `backend/data` 폴더의 모든 파일을 Git에 커밋
- 배포 시 저장소에서 자동으로 복사됨
- **주의**: 대용량 이미지 파일은 Git LFS 사용 권장

**옵션 2: 외부 스토리지 사용**
- AWS S3, Cloudinary 등 외부 스토리지 사용
- 코드 수정 필요

## 4. 배포 확인

### Backend
- URL: `https://jeomgeuli-backend.onrender.com`
- Health: `https://jeomgeuli-backend.onrender.com/api/v1/health`
- Docs: `https://jeomgeuli-backend.onrender.com/docs`

### Frontend
- URL: `https://jeomgeuli-frontend.onrender.com`

## 무료 플랜 제한사항

- **Sleep**: 15분간 요청이 없으면 자동으로 sleep (다음 요청 시 자동 wake)
- **리소스**: 제한적 CPU/RAM
- **디스크**: Persistent Disk 없음 (Git 저장소 내용만 사용)
- **빌드 시간**: 제한적

## 트러블슈팅

### Backend가 sleep 상태인 경우
- 첫 요청 시 약 30초~1분 정도 wake 시간 필요
- 또는 Render 대시보드에서 수동으로 "Resume" 클릭

### 데이터 파일이 없는 경우
- `backend/data` 폴더가 Git에 포함되어 있는지 확인
- `.gitignore`에서 `backend/data`가 제외되지 않았는지 확인

### CORS 에러
- Backend의 `CORS_ORIGINS`에 Frontend URL이 포함되어 있는지 확인
