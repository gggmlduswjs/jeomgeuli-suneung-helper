# 점글이 웹 프론트엔드

시각장애인을 위한 수능 학습 지원 웹 애플리케이션

## 빠른 시작

### 1. 의존성 설치
```bash
npm install
```

### 2. 개발 서버 실행
```bash
npm run dev
```

브라우저에서 http://localhost:5173 접속

### 3. 빌드
```bash
npm run build
```

### 4. 프리뷰
```bash
npm run preview
```

## 백엔드 연동

백엔드 서버가 `http://localhost:8000`에서 실행 중이어야 합니다.

```bash
cd api
python -m uvicorn app.main:app --reload
```

## 기술 스택

- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안정성
- **Vite** - 빌드 도구
- **Tailwind CSS** - 스타일링
- **React Router** - 라우팅
- **Zustand** - 상태 관리
- **Vite PWA** - PWA 지원

## 주요 기능

- AI 레슨 요약
- AI 순차적 수업
- AI Unit 설명
- AI 질문 답변
- TTS (Text-to-Speech)
- 점자 디바이스 연동
- 음성 명령어

## 개발

### 환경 변수

`.env` 파일 생성 (선택):
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 테스트

```bash
npm run test
```

## 문제 해결

### 의존성 설치 실패
```bash
npm cache clean --force
npm install
```

### 포트 충돌
`vite.config.ts`에서 포트 변경:
```typescript
server: {
  port: 5174, // 다른 포트 사용
}
```
