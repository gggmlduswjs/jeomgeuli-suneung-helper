# 빠른 구현 계획 (기존 데이터 활용)

**목표**: 문학, 영어, 수학 각 1강 데이터를 활용하여 실제 수능 환경 기능 빠르게 구현

---

## 🚀 빠르게 구현 가능한 기능 (1-2일 내)

### 1. 텍스트 찾기 기능 (Ctrl+F) ⭐⭐⭐
**대상**: 문학(WorkViewer), 영어(WorkViewer), 수학(ConceptViewer)

**구현 위치**:
- `frontend/src/components/unit/WorkViewer.tsx` - 지문 내용 검색
- `frontend/src/components/unit/ConceptViewer.tsx` - 개념 설명 검색

**기능**:
- Ctrl+F 단축키로 검색창 열기
- 특수문자 변형 처리 (가) ↔ ㈎
- 검색 결과 하이라이트
- 음성 안내 ("3개 중 1번째 결과")
- 점자 디스플레이에 검색 위치 표시

**예상 시간**: 2-3시간

---

### 2. 수식 계산 도구 (수학 영역) ⭐⭐⭐
**대상**: 수학 단원

**구현 위치**:
- `frontend/src/components/math/MathCalculator.tsx` (신규)
- 수학 단원 페이지에 계산기 버튼 추가

**기능**:
- 간단한 수식 입력 (키보드 또는 점자 키보드)
- 계산 결과 표시
- 음성으로 계산 결과 읽기
- 점자 디스플레이에 수식/결과 표시

**예상 시간**: 3-4시간

---

### 3. 시험 모드 토글 ⭐⭐
**대상**: 전체 단원 뷰어

**구현 위치**:
- `frontend/src/components/unit/UnitViewer.tsx`에 모드 토글 추가
- `frontend/src/store/examModeStore.ts` (신규)

**기능**:
- 학습 모드 ↔ 시험 모드 전환
- 시험 모드에서:
  - 시간 제한 표시 (1.7배)
  - 도구 제한 (과목별)
  - 답안 작성 영역 표시

**예상 시간**: 2-3시간

---

## 📝 구현 순서

### Phase 1: 텍스트 찾기 (가장 빠름)
1. `TextSearch.tsx` 컴포넌트 생성
2. `WorkViewer.tsx`에 통합
3. `ConceptViewer.tsx`에 통합
4. 특수문자 변형 처리 로직 추가

### Phase 2: 수식 계산기
1. `MathCalculator.tsx` 컴포넌트 생성
2. 수학 단원 페이지에 통합
3. 음성/점자 출력 연동

### Phase 3: 시험 모드
1. `examModeStore.ts` 생성
2. `UnitViewer.tsx`에 모드 토글 추가
3. 과목별 도구 제한 로직

---

## 🎯 최소 구현 (오늘 가능)

**텍스트 찾기 기능만 먼저 구현**:
- WorkViewer에 Ctrl+F 검색 추가
- 특수문자 처리
- 음성 안내

**예상 시간**: 1-2시간

---

## 💡 빠른 구현 팁

1. **기존 컴포넌트 재사용**: UnitViewer 구조 활용
2. **최소 기능부터**: 완벽하지 않아도 동작하는 버전 먼저
3. **점진적 개선**: 기본 기능 → 음성 → 점자 순서
