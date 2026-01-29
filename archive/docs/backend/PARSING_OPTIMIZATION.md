# 파싱 최적화 및 멈춤 방지

## 🔧 적용된 개선 사항

### 1. OCR 진행률 실시간 업데이트 ✅

**문제:**
- OCR 처리 중 진행률이 업데이트되지 않아 20%에서 멈춘 것처럼 보임
- 실제로는 OCR이 진행 중이지만 사용자가 확인 불가

**해결:**
- OCR 추출기에 `progress_callback` 추가
- 페이지 처리 시마다 DB에 진행률 업데이트
- 20% ~ 50% 구간을 OCR 진행률로 사용

**코드 변경:**
- `backend/app/infrastructure/pdf/extractors/base.py`: `set_progress_callback()` 추가
- `backend/app/infrastructure/pdf/pipeline.py`: `set_progress_callback()` 추가
- `backend/app/routers/books.py`: OCR 진행률 콜백 함수 추가

### 2. 진행률 구간 개선

**이전:**
- 20%: 텍스트 추출 시작
- 70%: 파이프라인 완료
- 100%: 완료

**개선 후:**
- 5%: 시작
- 10%: 파이프라인 초기화
- 20%: 텍스트 추출 시작
- 20-50%: OCR 진행 중 (실시간 업데이트)
- 50%: OCR 완료
- 70%: 파이프라인 완료
- 100%: 완료

---

## 🚨 멈춤 방지 전략

### 1. 타임아웃 감지

**진단 스크립트:**
```bash
python backend/scripts/diagnose_parsing.py
```

- 9시간 이상 진행 중이면 경고
- 자동으로 FAILED 처리 권장

### 2. 강제 재파싱

**스크립트:**
```bash
python backend/scripts/force_reparse.py
```

- PROCESSING 상태인 책을 PENDING으로 변경
- 관리자 페이지에서 재파싱 가능

### 3. 로깅 강화

**추가된 로그:**
- OCR 진행률 (10페이지마다)
- 현재 페이지 번호
- 총 페이지 수

---

## 📊 예상 효과

### Before
- 진행률: 20%에서 멈춤 (실제로는 진행 중)
- 사용자: 파싱이 멈춘 것으로 오해
- 해결: 재파싱 시도 반복

### After
- 진행률: 20% → 50% 실시간 업데이트
- 사용자: 실제 진행 상황 확인 가능
- 해결: 문제 발생 시 즉시 감지

---

## 🔄 다음 개선 사항 (선택)

### 1. 타임아웃 자동 처리
- 30분 이상 진행률 변화 없으면 자동 FAILED 처리
- 백그라운드 모니터링 태스크

### 2. 메모리 최적화
- OCR 병렬 처리 워커 수 동적 조정
- 메모리 사용량 모니터링

### 3. 에러 복구
- OCR 실패 시 자동 재시도
- 부분 실패 시 부분 결과 저장

---

## ✅ 즉시 사용 가능

1. **재파싱:** 관리자 페이지 → "재파싱" 버튼
2. **진단:** `python backend/scripts/diagnose_parsing.py`
3. **강제 재시작:** `python backend/scripts/force_reparse.py`

**이제 OCR 진행률이 실시간으로 업데이트됩니다!**
