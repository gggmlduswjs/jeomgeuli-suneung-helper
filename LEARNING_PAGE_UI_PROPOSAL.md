# 학습 페이지 UI 개선 제안

## 현재 방식 vs 제안 방식

### 현재: 수직 스크롤 방식
```
┌─────────────────┐
│  1강 - 개념     │ ← 스크롤
│  [이미지]       │   ↓
│  텍스트...      │   ↓
├─────────────────┤   ↓
│  1강 - 본문     │   ↓
│  [이미지]       │   ↓
│  텍스트...      │   ↓
├─────────────────┤   ↓
│  1강 - 문제     │   ↓
│  [이미지]       │   ↓
│  선택지...      │   ↓
└─────────────────┘
```

**문제점**:
- 긴 스크롤로 인한 피로감
- 이전 unit으로 돌아가기 어려움
- 학습 진행도 파악 어려움
- 모바일에서 비효율적

### 제안: 좌우 스와이프 방식 (카드 UI)

```
┌───────────────────────────────┐
│  1강 - 시의 표현과 형식       │
│  ━━━━━━━━━━━━━━━━━━━━━━━   │
│  ●○○ (1/3)                    │ ← 진행도 표시
├───────────────────────────────┤
│                               │
│  📖 핵심 개념                 │
│  ┌─────────────────────────┐ │
│  │                         │ │
│  │  [크롭된 섹션 이미지]   │ │
│  │                         │ │
│  └─────────────────────────┘ │
│                               │
│  시의 표현 기법에는...        │
│                               │
│                               │
│   ← 이전    [다음] →         │ ← 스와이프 버튼
│                               │
└───────────────────────────────┘
     ↑ 스와이프 →
```

## 상세 UI 구성

### 1. 카드 스와이프 구조

**한 페이지에 하나의 Unit만 표시**:
```
Unit 1: 개념 → Unit 2: 본문 → Unit 3: 문제
    ←              ←              ←
      스와이프       스와이프       스와이프
```

### 2. Unit 카드 레이아웃

```
┌─────────────────────────────────────┐
│ Header                              │
│  - 강의 제목 (1강 - 시의 표현과 형식)│
│  - 진행도 (●●○ 2/3)                │
│  - Unit 타입 아이콘 📖/📚/✏️       │
├─────────────────────────────────────┤
│ Content                             │
│                                     │
│  [대표 이미지]                      │
│  - 크롭된 섹션 이미지 (확대 가능)   │
│  - 고품질 PNG 300 DPI               │
│                                     │
│  [텍스트 내용]                      │
│  - 개념 설명 / 작품 / 문제 지문     │
│                                     │
│  [문제인 경우]                      │
│  - 선택지 (버튼 형태)               │
│  - 정답 확인 버튼                   │
│                                     │
├─────────────────────────────────────┤
│ Footer                              │
│  [← 이전]  [메뉴]  [다음 →]        │
└─────────────────────────────────────┘
```

### 3. 진행도 표시

**시각적 진행도**:
```
1강 (3/8) ●●●○○○○○
          ↑
       현재 위치
```

**상세 진행도 (팝업)**:
```
┌─────────────────────┐
│  1강 학습 진행도     │
├─────────────────────┤
│  ✓ 개념 (완료)      │
│  ✓ 본문 (완료)      │
│  → 문제 (현재)      │
│  ○ 추가 문제        │
└─────────────────────┘
```

## 주요 기능

### 1. 스와이프 제스처

**모바일**:
- 좌→우 스와이프: 이전 Unit
- 우→좌 스와이프: 다음 Unit
- 위→아래: 이미지 확대 모드

**데스크톱**:
- 좌우 화살표 키
- 마우스 클릭 (양쪽 화살표 버튼)
- 마우스 휠 (옵션)

### 2. Unit 타입별 아이콘

```
📖 개념 (CONCEPT)    - 파란색 배경
📚 본문 (PASSAGE)    - 초록색 배경
✏️ 문제 (PROBLEM)    - 주황색 배경
```

### 3. 이미지 확대 기능

**이미지 클릭 시**:
```
┌─────────────────────────────┐
│  [X] 닫기                   │
├─────────────────────────────┤
│                             │
│      [확대된 이미지]         │
│                             │
│  - 핀치 줌 지원             │
│  - 좌우 드래그 지원          │
│                             │
└─────────────────────────────┘
```

### 4. 북마크 기능

```
┌─────────────────┐
│  ⭐ 북마크      │ ← 중요 Unit 표시
│  📝 메모        │ ← Unit별 메모
│  ✓ 완료 표시    │ ← 학습 완료 체크
└─────────────────┘
```

## 프론트엔드 구현 예시

### Vue 3 (Composition API)

```vue
<template>
  <div class="learning-page">
    <!-- 헤더 -->
    <div class="header">
      <h2>{{ currentLesson.title }}</h2>
      <div class="progress">
        <span>{{ currentIndex + 1 }} / {{ units.length }}</span>
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: `${(currentIndex + 1) / units.length * 100}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Unit 카드 (Swiper) -->
    <swiper
      :slides-per-view="1"
      :space-between="50"
      @slide-change="onSlideChange"
      class="unit-swiper"
    >
      <swiper-slide v-for="unit in units" :key="unit.unit_id">
        <div class="unit-card" :class="`unit-type-${unit.type}`">
          <!-- 타입 아이콘 -->
          <div class="unit-icon">
            {{ getUnitIcon(unit.type) }}
          </div>

          <!-- Unit 제목 -->
          <h3>{{ unit.title }}</h3>

          <!-- 대표 이미지 -->
          <div
            v-if="unit.image_path"
            class="unit-image"
            @click="openImageModal(unit.image_path)"
          >
            <img
              :src="unit.image_path"
              :alt="unit.title"
              loading="lazy"
            />
          </div>

          <!-- 텍스트 내용 -->
          <div class="unit-content">
            <p>{{ unit.content_text }}</p>
          </div>

          <!-- 문제인 경우 -->
          <div v-if="unit.type === 'problem' && unit.question" class="question">
            <p class="question-stem">{{ unit.question.stem }}</p>
            <div class="choices">
              <button
                v-for="(choice, idx) in unit.question.choices"
                :key="idx"
                @click="selectAnswer(idx + 1)"
                :class="{
                  selected: selectedAnswer === idx + 1,
                  correct: showAnswer && unit.question.answer === idx + 1,
                  incorrect: showAnswer && selectedAnswer === idx + 1 && unit.question.answer !== idx + 1
                }"
                class="choice-btn"
              >
                {{ idx + 1 }}. {{ choice }}
              </button>
            </div>
            <button
              @click="checkAnswer"
              class="check-btn"
              :disabled="!selectedAnswer"
            >
              정답 확인
            </button>
          </div>

          <!-- AI 설명 (접기/펼치기) -->
          <details v-if="unit.ai_explanation" class="ai-explanation">
            <summary>AI 설명 보기</summary>
            <p>{{ unit.ai_explanation }}</p>
          </details>

          <!-- 점자 텍스트 (시각장애인용) -->
          <div v-if="unit.braille_text" class="braille-text">
            <details>
              <summary>점자 텍스트 보기</summary>
              <p>{{ unit.braille_text }}</p>
            </details>
          </div>
        </div>
      </swiper-slide>
    </swiper>

    <!-- 하단 네비게이션 -->
    <div class="footer-nav">
      <button
        @click="prevUnit"
        :disabled="currentIndex === 0"
        class="nav-btn"
      >
        ← 이전
      </button>

      <button
        @click="openMenu"
        class="menu-btn"
      >
        ☰ 메뉴
      </button>

      <button
        @click="nextUnit"
        :disabled="currentIndex === units.length - 1"
        class="nav-btn"
      >
        다음 →
      </button>
    </div>

    <!-- 이미지 확대 모달 -->
    <teleport to="body">
      <div v-if="imageModalOpen" class="image-modal" @click="closeImageModal">
        <button class="close-btn">X</button>
        <img :src="modalImageSrc" alt="확대 이미지" />
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { Swiper, SwiperSlide } from 'swiper/vue';
import 'swiper/css';

const route = useRoute();
const lessonId = route.params.lessonId;

const units = ref([]);
const currentIndex = ref(0);
const selectedAnswer = ref(null);
const showAnswer = ref(false);
const imageModalOpen = ref(false);
const modalImageSrc = ref('');

// 데이터 로드
onMounted(async () => {
  const response = await fetch(`/api/v1/lessons/${lessonId}/units`);
  units.value = await response.json();
});

// 현재 강의 정보
const currentLesson = computed(() => {
  if (!units.value.length) return {};
  return {
    title: units.value[0]?.lesson_title || '학습 중'
  };
});

// Unit 타입 아이콘
const getUnitIcon = (type) => {
  const icons = {
    'concept': '📖',
    'passage': '📚',
    'problem': '✏️'
  };
  return icons[type] || '📄';
};

// 네비게이션
const prevUnit = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--;
  }
};

const nextUnit = () => {
  if (currentIndex.value < units.value.length - 1) {
    currentIndex.value++;
  }
};

const onSlideChange = (swiper) => {
  currentIndex.value = swiper.activeIndex;
  // 새 Unit으로 이동 시 상태 초기화
  selectedAnswer.value = null;
  showAnswer.value = false;
};

// 문제 풀이
const selectAnswer = (answerNum) => {
  selectedAnswer.value = answerNum;
};

const checkAnswer = () => {
  showAnswer.value = true;
};

// 이미지 모달
const openImageModal = (imagePath) => {
  modalImageSrc.value = imagePath;
  imageModalOpen.value = true;
};

const closeImageModal = () => {
  imageModalOpen.value = false;
};

const openMenu = () => {
  // 메뉴 열기 (Unit 목록, 북마크 등)
};
</script>

<style scoped>
.learning-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  padding: 1rem;
  background: #f5f5f5;
}

.progress-bar {
  width: 100%;
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  margin-top: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: #4caf50;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.unit-swiper {
  flex: 1;
  overflow: hidden;
}

.unit-card {
  height: 100%;
  padding: 2rem;
  overflow-y: auto;
}

.unit-type-concept { border-left: 4px solid #2196f3; }
.unit-type-passage { border-left: 4px solid #4caf50; }
.unit-type-problem { border-left: 4px solid #ff9800; }

.unit-icon {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.unit-image {
  margin: 1rem 0;
  cursor: pointer;
  transition: transform 0.2s;
}

.unit-image:hover {
  transform: scale(1.02);
}

.unit-image img {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.choices {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 1rem 0;
}

.choice-btn {
  padding: 1rem;
  text-align: left;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.choice-btn:hover {
  border-color: #2196f3;
}

.choice-btn.selected {
  border-color: #2196f3;
  background: #e3f2fd;
}

.choice-btn.correct {
  border-color: #4caf50;
  background: #e8f5e9;
}

.choice-btn.incorrect {
  border-color: #f44336;
  background: #ffebee;
}

.footer-nav {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  background: #f5f5f5;
  border-top: 1px solid #e0e0e0;
}

.nav-btn, .menu-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn {
  background: #2196f3;
  color: white;
}

.nav-btn:disabled {
  background: #e0e0e0;
  cursor: not-allowed;
}

.menu-btn {
  background: white;
  border: 1px solid #e0e0e0;
}

.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0,0,0,0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.image-modal img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 1.5rem;
  cursor: pointer;
}
</style>
```

## 모바일 최적화

### 터치 제스처
```javascript
// Swiper 설정
const swiperOptions = {
  slidesPerView: 1,
  spaceBetween: 20,
  speed: 300,
  touchRatio: 1,
  threshold: 10,
  resistance: true,
  resistanceRatio: 0.85
};
```

### 반응형 디자인
```css
/* 모바일 */
@media (max-width: 768px) {
  .unit-card {
    padding: 1rem;
  }

  .unit-image img {
    max-height: 300px;
  }
}

/* 태블릿 */
@media (min-width: 768px) and (max-width: 1024px) {
  .unit-card {
    padding: 1.5rem;
  }
}

/* 데스크톱 */
@media (min-width: 1024px) {
  .unit-card {
    max-width: 800px;
    margin: 0 auto;
  }
}
```

## 장점

### 1. 집중도 향상
- 한 번에 하나의 Unit만 표시
- 학습 흐름 방해 없음
- 이미지 강조 표시

### 2. 직관적인 네비게이션
- 스와이프로 쉽게 이동
- 진행도 실시간 확인
- 이전 Unit으로 쉽게 복귀

### 3. 모바일 친화적
- 터치 제스처 최적화
- 세로 화면에서도 편안한 학습
- 빠른 로딩 (한 번에 1개 Unit만)

### 4. 학습 관리
- Unit별 완료 체크
- 북마크 기능
- 학습 진행도 추적

## 추가 기능 제안

### 1. 퀴즈 모드
```
- 문제만 연속으로 풀기
- 타이머 기능
- 정답률 통계
```

### 2. 복습 모드
```
- 틀린 문제만 모아보기
- 북마크한 Unit만 모아보기
- 랜덤 셔플 모드
```

### 3. 학습 통계
```
- 일일 학습 시간
- Unit별 소요 시간
- 정답률 그래프
```

## 구현 우선순위

### Phase 1: 핵심 기능 (1-2주)
- [x] 이미지 크롭 및 저장
- [ ] 카드 스와이프 UI
- [ ] 기본 네비게이션
- [ ] 이미지 확대 기능

### Phase 2: 사용성 개선 (1주)
- [ ] 진행도 표시
- [ ] Unit 타입별 스타일
- [ ] 모바일 최적화

### Phase 3: 추가 기능 (2주)
- [ ] 북마크 기능
- [ ] 메모 기능
- [ ] 학습 통계

## 결론

**좌우 스와이프 방식이 수직 스크롤보다 우수한 이유**:

1. ✅ **집중도**: 한 번에 하나의 Unit에 집중
2. ✅ **효율성**: 빠른 네비게이션과 진행도 파악
3. ✅ **모바일**: 터치 제스처에 최적화
4. ✅ **이미지**: 크롭된 섹션 이미지가 더 돋보임
5. ✅ **학습 경험**: 카드 넘기는 느낌으로 학습 동기 부여

**다음 단계**: 카드 스와이프 UI를 프론트엔드에 구현하면, 크롭된 섹션 이미지가 완벽하게 학습 페이지에 통합됩니다! 🎉
