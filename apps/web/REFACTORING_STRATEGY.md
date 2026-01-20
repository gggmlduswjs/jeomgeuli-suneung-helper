# 프론트엔드 리팩토링 전략

## [1] 현재 구조의 문제점

### 1.1 폴더 명명 규칙 불일치

**문제**: 대문자로 시작하는 빈 폴더들과 소문자 폴더 혼재
```
❌ src/Book/              (빈 폴더, 대문자)
❌ src/Lesson/            (빈 폴더, 대문자)
❌ src/Unit/              (빈 폴더, 대문자)
❌ src/LiteratureLearning/ (빈 폴더, 대문자)
❌ src/NotFound/          (빈 폴더, 대문자)
✅ src/pages/             (실제 페이지, 소문자)
✅ src/components/        (실제 컴포넌트, 소문자)
```

**원인**: 이전에 페이지 컴포넌트를 `pages/` 폴더로 이동하면서 빈 폴더가 남음

### 1.2 Components 폴더 비대화

**문제**: 49개 파일, 20개 하위 폴더 → 찾기 어려움
```
components/
├── ai/ (2개)
├── braille/ (7개)
├── common/ (?)
├── curriculum/ (1개)
├── debug/ (1개)
├── home/ (4개)
├── input/ (5개)
├── layout/ (2개)
├── lesson/ (1개)
├── pdf/ (?)
├── progress/ (?)
├── question/ (5개)
├── review/ (?)
├── settings/ (?)
├── subject/ (1개)
├── system/ (5개)
├── textbook/ (7개)
├── ui/ (1개)
├── unit/ (7개)
└── voice/ (1개)
```

**문제**:
- 너무 많은 하위 폴더 (20개)
- 폴더별 파일 개수 불균등 (1개~7개)
- 일부 폴더의 책임이 불명확 (common, pdf, progress)

### 1.3 중복 파일 문제

**중복**:
```
components/unit/AIExplanationCard.tsx    ← 중복
components/ai/AIExplanationCard.tsx      ← 중복
```

**원인**: 코드 이동 시 삭제하지 않고 복사만 함

### 1.4 Services 구조 혼재

**문제**: 일부는 폴더, 일부는 단일 파일
```
services/
├── commands/              (폴더, 5개 파일)
├── learning/              (폴더, 4개 파일)
├── passage/               (폴더, 1개 파일)
├── question/              (폴더, 1개 파일)
├── textbook/              (폴더, 1개 파일)
├── ai.ts                  (단일 파일)
├── answers.ts             (단일 파일)
├── api.ts                 (단일 파일)
├── api-client.ts          (단일 파일)
├── books.ts               (단일 파일)
├── CommandService.ts      (단일 파일)
├── curriculum.ts          (단일 파일)
├── lessons.ts             (단일 파일)
├── literature.ts          (단일 파일)
├── progress.ts            (단일 파일)
├── units.ts               (단일 파일)
└── VoiceService.ts        (단일 파일)
```

**문제**:
- 폴더 안에 파일 1개만 있는 경우 (passage/, question/, textbook/)
- 단일 파일이 너무 많음 (12개)
- 명명 규칙 불일치 (api.ts vs api-client.ts vs CommandService.ts)

### 1.5 lib vs utils 구분 불명확

**문제**: 둘 다 유틸리티 함수인데 차이가 불명확
```
lib/
├── api/
├── voice/
├── api.ts
├── braille.ts
├── brailleMap.ts
├── braillePattern.ts
├── brailleSafe.ts
├── http.ts
└── performance.ts

utils/
├── audioNotification.ts
├── brailleChunk.ts
├── brailleChunkBuilder.ts
├── pdfReferences.ts
├── scriptSectionMatcher.ts
└── subjectMetadata.ts
```

**혼란**:
- `lib/`에 braille 관련 파일 (4개)
- `utils/`에도 braille 관련 파일 (2개)
- 어디에 무엇을 넣어야 할지 불명확

### 1.6 Pages와 컴포넌트 분리 불명확

**현재**:
```
pages/
├── Book.tsx (19,015줄) ← 거대한 파일!
├── Curriculum.tsx
├── Learning/
├── Lesson.tsx
├── Main.tsx
├── NotFound.tsx
├── Question.tsx
├── Textbook.tsx (38,061줄) ← 더 거대한 파일!
└── Unit.tsx
```

**문제**:
- `Book.tsx` (19,015줄), `Textbook.tsx` (38,061줄) → God Component!
- 페이지 로직과 UI 로직이 섞여 있음
- 재사용 가능한 로직이 페이지에 갇혀 있음

---

## [2] 프론트엔드 리팩토링 전략

### Phase 1: 정리 (Cleanup)

**목표**: 불필요한 폴더/파일 제거

1. **빈 폴더 삭제**
   ```bash
   rm -rf src/Book src/Lesson src/Unit src/LiteratureLearning src/NotFound
   ```

2. **중복 파일 제거**
   - `components/unit/AIExplanationCard.tsx` 확인 후 삭제 (ai/ 버전 유지)

3. **미사용 파일 식별**
   - `components/common/` 내용 확인
   - `components/pdf/` 내용 확인
   - `components/progress/` 내용 확인
   - `components/review/` 내용 확인
   - `components/settings/` 내용 확인

### Phase 2: 명명 규칙 통일 (Naming Convention)

**목표**: 일관된 명명 규칙 적용

#### 2.1 Services 명명 규칙
```
services/
├── ai/
│   └── index.ts           (기존 ai.ts)
├── api/
│   ├── client.ts          (기존 api-client.ts)
│   └── index.ts           (기존 api.ts)
├── books/
│   └── index.ts           (기존 books.ts)
├── commands/              (유지)
├── curriculum/
│   └── index.ts           (기존 curriculum.ts)
├── learning/              (유지)
├── lessons/
│   └── index.ts           (기존 lessons.ts)
├── literature/
│   └── index.ts           (기존 literature.ts)
├── voice/
│   └── index.ts           (기존 VoiceService.ts)
└── ...
```

**원칙**:
- 단일 파일 → 폴더 + index.ts
- PascalCase 서비스 → camelCase 폴더
- 일관된 구조 유지

#### 2.2 Lib 정리
```
lib/
├── api/                   (유지)
├── braille/               (신규, braille 관련 모두 통합)
│   ├── converter.ts       (기존 braille.ts)
│   ├── map.ts             (기존 brailleMap.ts)
│   ├── pattern.ts         (기존 braillePattern.ts)
│   └── safe.ts            (기존 brailleSafe.ts)
├── http/
│   └── client.ts          (기존 http.ts)
├── performance/
│   └── monitor.ts         (기존 performance.ts)
└── voice/                 (유지)
```

#### 2.3 Utils 정리
```
utils/
├── audio/
│   └── notification.ts    (기존 audioNotification.ts)
├── braille/               (lib/braille/로 이동)
├── pdf/
│   └── references.ts      (기존 pdfReferences.ts)
└── text/
    ├── sectionMatcher.ts  (기존 scriptSectionMatcher.ts)
    └── metadata.ts        (기존 subjectMetadata.ts)
```

### Phase 3: Components 구조 개선

**목표**: 찾기 쉽고 유지보수하기 쉬운 구조

#### 3.1 Feature 기반 재구성
```
components/
├── features/              (신규, 기능별 그룹화)
│   ├── ai/               (기존 ai/ 유지)
│   ├── braille/          (기존 braille/ 유지)
│   ├── curriculum/       (기존 curriculum/ + 관련 컴포넌트)
│   ├── lesson/           (기존 lesson/ + 관련 컴포넌트)
│   ├── question/         (기존 question/ 유지)
│   ├── textbook/         (기존 textbook/ 유지)
│   ├── unit/             (기존 unit/ 유지)
│   └── voice/            (기존 voice/ + input 일부)
│
├── shared/               (신규, 공통 컴포넌트)
│   ├── input/           (기존 input/ 재배치)
│   ├── layout/          (기존 layout/ 유지)
│   └── system/          (기존 system/ 유지)
│
└── ui/                   (기존 ui/ 확장, 순수 UI 컴포넌트)
    ├── buttons/
    ├── cards/
    └── layouts/
```

**원칙**:
- `features/`: 도메인 로직이 있는 비즈니스 컴포넌트
- `shared/`: 여러 feature에서 공통으로 사용하는 컴포넌트
- `ui/`: 순수 UI 컴포넌트 (로직 없음, 재사용성 높음)

#### 3.2 삭제 후보
```
components/
├── common/    → 내용 확인 후 shared/ 또는 ui/로 이동
├── debug/     → 개발 환경에서만 사용하면 유지, 아니면 삭제
├── home/      → pages/Main.tsx에만 사용되면 pages/Main/ 폴더로 이동
├── pdf/       → 내용 확인 후 features/textbook/로 통합
├── progress/  → 내용 확인 후 features/lesson/ 또는 features/curriculum/로 통합
├── review/    → 내용 확인 후 features/lesson/로 통합
├── settings/  → 내용 확인 후 shared/ 또는 features/로 이동
└── subject/   → 내용 확인 후 features/로 이동
```

### Phase 4: God Component 분리

**목표**: 거대한 페이지 파일 분리

#### 4.1 Book.tsx (19,015줄) 분리 전략
```
pages/Book/
├── index.tsx              (메인 페이지, ~200줄)
├── components/            (페이지 전용 컴포넌트)
│   ├── BookHeader.tsx
│   ├── BookNavigation.tsx
│   └── BookContent.tsx
├── hooks/                 (페이지 전용 훅)
│   ├── useBookData.ts
│   └── useBookNavigation.ts
└── constants.ts           (페이지 전용 상수)
```

#### 4.2 Textbook.tsx (38,061줄) 분리 전략
```
pages/Textbook/
├── index.tsx              (메인 페이지, ~200줄)
├── components/            (페이지 전용 컴포넌트)
│   ├── TextbookHeader.tsx
│   ├── TextbookUpload.tsx
│   ├── TextbookList.tsx
│   └── TextbookViewer.tsx
├── hooks/                 (페이지 전용 훅)
│   ├── useTextbookData.ts
│   ├── useTextbookUpload.ts
│   └── useTextbookParsing.ts
└── constants.ts           (페이지 전용 상수)
```

**원칙**:
- 페이지 파일은 **200줄 이하** 목표
- 비즈니스 로직 → hooks/
- UI 컴포넌트 → components/ (페이지 전용)
- 재사용 가능한 컴포넌트 → components/features/로 이동

### Phase 5: 도메인 기반 재구성 (선택사항)

**목표**: 도메인별로 관련 파일 모으기 (더 나아간 구조)

```
src/
├── features/              (도메인별 feature)
│   ├── braille/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   │
│   ├── textbook/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   │
│   └── voice/
│       ├── components/
│       ├── hooks/
│       ├── lib/
│       ├── services/
│       └── types/
│
├── shared/                (공통)
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   └── types/
│
└── pages/                 (페이지 조립)
    ├── Book/
    ├── Lesson/
    ├── Main/
    └── Textbook/
```

---

## [3] 파일 이동 매핑표

### 3.1 즉시 삭제
| 현재 위치 | 작업 | 이유 |
|----------|------|-----|
| `src/Book/` | 삭제 | 빈 폴더 |
| `src/Lesson/` | 삭제 | 빈 폴더 |
| `src/Unit/` | 삭제 | 빈 폴더 |
| `src/LiteratureLearning/` | 삭제 | 빈 폴더 |
| `src/NotFound/` | 삭제 | 빈 폴더 |

### 3.2 중복 파일 확인/삭제
| 파일 | 작업 | 우선순위 |
|-----|------|---------|
| `components/unit/AIExplanationCard.tsx` | 확인 후 삭제 | 🔴 높음 |

### 3.3 Services 재구성
| 현재 | 이동 후 | 작업 |
|------|---------|------|
| `services/ai.ts` | `services/ai/index.ts` | 폴더로 변환 |
| `services/api.ts` | `services/api/index.ts` | 폴더로 변환 |
| `services/api-client.ts` | `services/api/client.ts` | 통합 |
| `services/books.ts` | `services/books/index.ts` | 폴더로 변환 |
| `services/VoiceService.ts` | `services/voice/index.ts` | 폴더로 변환 + 이름 변경 |

### 3.4 Lib 재구성
| 현재 | 이동 후 | 작업 |
|------|---------|------|
| `lib/braille.ts` | `lib/braille/converter.ts` | 폴더로 통합 |
| `lib/brailleMap.ts` | `lib/braille/map.ts` | 폴더로 통합 |
| `lib/braillePattern.ts` | `lib/braille/pattern.ts` | 폴더로 통합 |
| `lib/brailleSafe.ts` | `lib/braille/safe.ts` | 폴더로 통합 |

### 3.5 Utils 재구성
| 현재 | 이동 후 | 작업 |
|------|---------|------|
| `utils/audioNotification.ts` | `utils/audio/notification.ts` | 폴더로 변환 |
| `utils/brailleChunk.ts` | `lib/braille/chunk.ts` | lib로 이동 |
| `utils/brailleChunkBuilder.ts` | `lib/braille/chunkBuilder.ts` | lib로 이동 |

---

## [4] 실행 체크리스트

### 단계 1: 즉시 정리 (10분)
- [ ] 빈 폴더 5개 삭제
  ```bash
  cd apps/web/src
  rm -rf Book Lesson Unit LiteratureLearning NotFound
  ```

- [ ] 중복 파일 확인
  ```bash
  # 두 파일 비교
  diff components/unit/AIExplanationCard.tsx components/ai/AIExplanationCard.tsx
  # 같으면 하나 삭제
  rm components/unit/AIExplanationCard.tsx
  ```

### 단계 2: Lib 재구성 (20분)
- [ ] `lib/braille/` 폴더 생성 및 파일 이동
  ```bash
  mkdir -p lib/braille
  mv lib/braille.ts lib/braille/converter.ts
  mv lib/brailleMap.ts lib/braille/map.ts
  mv lib/braillePattern.ts lib/braille/pattern.ts
  mv lib/brailleSafe.ts lib/braille/safe.ts
  # index.ts 생성 (re-export)
  touch lib/braille/index.ts
  ```

- [ ] `utils/braille*` 파일도 `lib/braille/`로 이동
  ```bash
  mv utils/brailleChunk.ts lib/braille/chunk.ts
  mv utils/brailleChunkBuilder.ts lib/braille/chunkBuilder.ts
  ```

### 단계 3: Services 재구성 (30분)
- [ ] 각 단일 파일을 폴더로 변환
  ```bash
  # 예: ai.ts → ai/index.ts
  mkdir -p services/ai
  mv services/ai.ts services/ai/index.ts

  # 반복...
  ```

### 단계 4: Components 재구성 (60분)
- [ ] `components/features/` 폴더 생성
- [ ] 기존 도메인 컴포넌트 이동
- [ ] `components/shared/` 폴더 생성
- [ ] 공통 컴포넌트 이동

### 단계 5: God Component 분리 (선택, 나중에)
- [ ] `pages/Book/` 폴더로 변환
- [ ] `pages/Textbook/` 폴더로 변환
- [ ] 각 페이지를 컴포넌트/훅으로 분리

---

## [5] 기대 효과

### Before
```
- 총 155개 파일
- components/ 49개 (찾기 어려움)
- services/ 24개 (구조 혼재)
- lib vs utils 구분 불명확
- 거대한 페이지 파일 (38,061줄)
```

### After
```
✅ 빈 폴더 정리 완료
✅ 명명 규칙 통일
✅ lib/ 도메인별 정리
✅ components/ feature 기반 구조
✅ services/ 일관된 구조
✅ 페이지 파일 200줄 이하
```

---

## [6] 주의사항

1. **점진적 리팩토링**: 한 번에 모든 것을 바꾸지 말 것
2. **Import 경로 수정**: 파일 이동 시 모든 import 경로 확인
3. **테스트**: 각 단계마다 빌드 및 실행 확인
4. **Git 커밋**: 단계별로 커밋하여 롤백 가능하도록

---

## 예상 소요 시간

- **단계 1-2**: 30분 (즉시 정리 + Lib 재구성)
- **단계 3-4**: 90분 (Services + Components 재구성)
- **단계 5**: 2-3시간 (God Component 분리, 선택사항)

**총 예상 시간: 2-4시간**
