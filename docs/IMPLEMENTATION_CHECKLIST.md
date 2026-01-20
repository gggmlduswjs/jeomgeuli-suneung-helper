# 구현 체크리스트 (Implementation Checklist)

지금까지 논의한 모든 기능을 구현하기 위한 상세 체크리스트입니다.

---

## ✅ Phase 1: 기초 인프라

### 1.1 데이터베이스 마이그레이션
- [x] `api/app/db/models.py` - Lesson 모델 필드 추가 확인
- [ ] `api/scripts/migrate_db.py` - 마이그레이션 스크립트 실행
- [ ] DB 마이그레이션 테스트

### 1.2 PDF 구조 파싱 연동
- [x] `api/app/services/pdf_structure_parser.py` - 생성 완료
- [x] `api/app/services/pdf_to_units_converter.py` - 생성 완료
- [ ] 실제 PDF 파일로 테스트
- [ ] Unit 생성 API 테스트

### 1.3 강의 대본 저장
- [x] `api/app/routers/lessons.py` - HWP 업로드 엔드포인트 추가
- [ ] HWP 파일 업로드 테스트
- [ ] 강의 대본 추출 테스트
- [ ] 레슨 분할 API 테스트

---

## ✅ Phase 2: AI 기능 구현

### 2.1 AI 강의 선생님 실제 동작
- [x] `api/app/services/ai_lecture_teacher.py` - 생성 완료
- [ ] OpenAI/Gemini API 키 설정
- [ ] 실제 API 호출 테스트
- [ ] 에러 처리 및 재시도 로직
- [ ] 토큰 제한 관리

### 2.2 실시간 AI 학습 도우미
- [x] `api/app/routers/ai.py` - 질문 답변 API 생성 완료
- [x] `apps/web/src/hooks/useAILearningAssistant.ts` - 생성 완료
- [x] `apps/web/src/components/ai/AIQuestionInput.tsx` - 생성 완료
- [x] `apps/web/src/components/ai/AIAnswerDisplay.tsx` - 생성 완료
- [ ] 음성 질문 입력 테스트
- [ ] AI 답변 표시 테스트
- [ ] TTS 연동 테스트

### 2.3 AI 학습 내용 요약
- [x] `api/app/routers/lessons.py` - 요약 엔드포인트 추가
- [ ] 프론트엔드: 레슨 시작 시 자동 요약
- [ ] 요약 API 테스트
- [ ] TTS로 요약 재생 테스트

---

## ✅ Phase 3: UI/UX 완성

### 3.1 PDF 내용 표시
- [x] `apps/web/src/components/unit/ConceptViewer.tsx` - 생성 완료
- [x] `apps/web/src/components/unit/WorkViewer.tsx` - 생성 완료
- [x] `apps/web/src/components/unit/UnitViewer.tsx` - 수정 완료
- [ ] 스타일링 개선
- [ ] 반응형 디자인

### 3.2 AI 설명 UI
- [x] `apps/web/src/components/ai/AIExplanationCard.tsx` - 생성 완료
- [x] `apps/web/src/pages/Unit.tsx` - AI 설명 통합 완료
- [ ] 로딩 상태 표시 개선
- [ ] 에러 처리 UI

### 3.3 음성 질문 UI
- [x] `apps/web/src/components/ai/AIQuestionInput.tsx` - 생성 완료
- [ ] 음성 질문 버튼 테스트
- [ ] 질문 입력 UI 개선

---

## ✅ Phase 4: 접근성 기능

### 4.1 TTS 연동
- [x] `apps/web/src/pages/Unit.tsx` - TTS 통합 완료
- [ ] AI 설명 자동 TTS 재생 테스트
- [ ] "다시 듣기" 기능 테스트
- [ ] TTS 속도 조절 (선택)

### 4.2 점자 출력 연동
- [ ] AI 설명 텍스트 → 점자 변환
- [ ] 점자 디바이스 전송
- [ ] 점자 청크 관리

---

## ✅ Phase 5: 통합 테스트

### 5.1 전체 플로우 테스트
- [ ] 관리자: HWP 업로드 → 강의 대본 저장
- [ ] 관리자: PDF 업로드 → Unit 생성
- [ ] 사용자: 레슨 선택 → AI 설명 듣기
- [ ] 사용자: 질문 → AI 답변
- [ ] 점자 출력 테스트
- [ ] TTS 테스트

### 5.2 에러 처리
- [ ] API 에러 처리
- [ ] 네트워크 에러 처리
- [ ] AI API 실패 시 fallback

---

## 🎯 빠른 시작 가이드

### 1. 환경 설정
```bash
# 백엔드
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-ai.txt

# 환경 변수 설정 (.env)
OPENAI_API_KEY=sk-...
# 또는
GEMINI_API_KEY=...
DATABASE_URL=sqlite:///./data/db.sqlite3
UPLOAD_DIR=data/uploads

# 프론트엔드
cd apps/web
npm install
```

### 2. DB 마이그레이션
```bash
cd api
python scripts/migrate_db.py
```

### 3. 서버 실행
```bash
# 백엔드
cd api
uvicorn app.main:app --reload

# 프론트엔드
cd apps/web
npm run dev
```

### 4. 테스트
1. 관리자: HWP 파일 업로드
2. 관리자: PDF 파일 업로드
3. 사용자: 레슨 선택
4. 사용자: AI 설명 확인
5. 사용자: 질문 입력

---

## 📝 구현 순서 추천

### Week 1: 기초 인프라
1. DB 마이그레이션
2. PDF 구조 파싱 테스트
3. 강의 대본 저장 테스트

### Week 2: AI 기능
1. AI 강의 선생님 실제 동작
2. 실시간 AI 학습 도우미
3. AI 학습 내용 요약

### Week 3: UI/UX + 접근성
1. UI 스타일링
2. TTS 연동
3. 점자 출력 연동

### Week 4: 통합 테스트
1. 전체 플로우 테스트
2. 에러 처리
3. 성능 최적화

---

*작성일: 2024년 12월*
