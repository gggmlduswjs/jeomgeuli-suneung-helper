# 백엔드/프론트엔드 재시작 필요

## 문제 요약
- Vite 프록시 타임아웃 설정 추가 (300초)
- templates.py 로깅 추가
- 백엔드는 실행 중이지만 `/api/v1/templates` 엔드포인트만 404

## 해결 방법

### 1. 백엔드 재시작 (터미널 36)
```powershell
# Ctrl+C로 중단
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 프론트엔드 재시작 (터미널 37)  
```powershell
# Ctrl+C로 중단
npm run dev
```

### 3. 테스트
브라우저에서:
- http://localhost:8000/docs - FastAPI docs 확인
- http://localhost:8000/api/v1/templates - 템플릿 목록 확인
- http://localhost:5173 - 프론트엔드에서 목차 추출 테스트

## 변경 내용
1. `frontend/vite.config.ts`: 프록시 타임아웃 300초
2. `backend/app/routers/templates.py`: 상세 로깅 추가, DPI 동적 조정
