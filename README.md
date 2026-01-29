# 점그리 수능 도우미 (Jeomgeuli Suneung Helper)

수능 학습을 위한 AI 기반 교육 플랫폼

## 프로젝트 구조

```
.
├── backend/          # FastAPI 백엔드
├── frontend/         # React + TypeScript 프론트엔드
├── scripts/         # 목차·템플릿 유틸 스크립트 (python scripts/xxx.py)
├── data/            # 데이터·입력 파일 (toc_raw_input.txt 등)
├── archive/         # 정리된 임시·보관 파일
└── README.md        # 이 파일
```

## 주요 기능

- **PDF 파싱**: 구조화된 PDF 파싱 시스템
- **AI 튜터**: OpenAI 기반 학습 도우미
- **템플릿 시스템**: 재사용 가능한 파싱 템플릿
- **학습 관리**: 강의, 단원, 진도 관리

## 기술 스택

### Backend
- FastAPI
- SQLAlchemy
- PyMuPDF, pdfplumber
- OpenAI API

### Frontend
- React + TypeScript
- Vite
- Tailwind CSS

## 시작하기

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 라이선스

MIT
