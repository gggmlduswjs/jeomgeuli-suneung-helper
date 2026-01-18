# 레슨 블록 기반 학습 시스템 아키텍처 설계

## 1. 설계 배경 및 문제 정의

### 1.1 시각장애 수험생의 학습 환경 제약

시각장애 수험생은 기존 인강 학습에서 다음과 같은 구조적 한계를 경험합니다:

1. **정보 접근 방식의 비대칭성**
   - 시각 정보(화면, 교재)에 의존하는 강의 구조
   - 음성만으로는 맥락 파악이 어려운 순간적 정보 전달
   - "지금 어디를 다루고 있는지" 인지의 어려움

2. **점자 디바이스의 물리적 제약**
   - 6점자 셀 3칸 = 최대 3자 출력
   - 긴 텍스트를 점자로 전달하는 것은 비효율적
   - 점자는 "읽기" 도구가 아니라 "상태 인지" 도구로 재정의 필요

### 1.2 설계 철학의 전환

**기존 접근**: "점자로 모든 내용을 전달한다"
- 문제: 하드웨어 제약으로 인한 정보 손실
- 문제: 점자 읽기 속도와 강의 진행 속도의 불일치

**새로운 접근**: "점자는 신호등, 강의는 경험 문서"
- 점자 = 현재 학습 상태를 알려주는 신호
- 강의 = 하나의 완결된 학습 경험 문서
- 사용자 = "지금 어디에 있는지" 항상 인지 가능

---

## 2. 레슨 블록(Lesson Block) 개념

### 2.1 레슨 블록의 정의

레슨 블록은 **하나의 명확한 학습 목적을 가진 최소 학습 단위**입니다.

강의는 연속된 콘텐츠가 아니라, 다음과 같은 블록들의 순차적 조합입니다:

```
[오리엔테이션] → [강의 목표] → [시험 구조] → [감상 프레임] → [작품 분석] → [문제 적용] → [요약] → [정리 메시지]
```

각 블록은 독립적이면서도, 전체 레슨의 맥락 안에서 의미를 가집니다.

### 2.2 레슨 블록의 필수 요소

각 레슨 블록은 다음 5가지 요소를 반드시 포함합니다:

#### 1. 학습 목적 (Learning Intent)
- **목적**: 이 블록에서 학습자가 달성해야 할 목표
- **예시**: "이 작품의 주제를 파악한다", "문제 풀이 사고 과정을 이해한다"
- **설계 이유**: 시각장애 학습자는 "지금 무엇을 배우는지" 명시적으로 알아야 학습 방향을 잃지 않음

#### 2. 점자 신호 (Braille Signal)
- **형식**: 3셀 점자 패턴 (예: "●○●", "○○○", "●●●")
- **목적**: 현재 블록의 상태를 즉시 인지
- **설계 이유**: 점자 디바이스 제약을 받아들이고, 오히려 "상태 신호"로 활용하여 사용자 인지 부하 감소

#### 3. 음성 강의 범위 (Audio Range)
- **목적**: 이 블록에 해당하는 강의 구간(타임스탬프) 명시
- **예시**: `{start: "00:05:23", end: "00:12:45"}`
- **설계 이유**: 사용자가 강의를 되돌아가거나 특정 블록을 다시 들을 때 정확한 위치 파악

#### 4. 사용자 인지 효과 (User Awareness)
- **목적**: 이 블록을 경험할 때 학습자가 느끼게 되는 인지 상태
- **예시**: "이제 작품 분석 단계에 들어섰다", "문제 풀이를 시작한다"
- **설계 이유**: 시각적 큐가 없는 환경에서 학습자가 자신의 위치를 항상 인지할 수 있도록 보장

#### 5. UI 동작 규칙 (UI Behavior Rules)
- **목적**: 이 블록에서 앱이 어떻게 동작해야 하는지 정의
- **예시**: "자동 재생 시작", "북마크 가능", "복습 모드 진입"
- **설계 이유**: 블록별로 다른 학습 패턴을 지원하기 위해 UI 동작을 블록 타입에 따라 자동화

---

## 3. MongoDB 데이터베이스 설계

### 3.1 Document DB 선택 이유

**왜 MongoDB인가?**

1. **레슨 단위 조회 패턴**
   - 사용자는 항상 "하나의 레슨"을 조회
   - 블록은 레슨과 분리되어 존재할 수 없음
   - 관계형 DB의 정규화는 오히려 불필요한 복잡도 증가

2. **가변적 블록 구조**
   - 과목별로 블록 타입이 다름 (문학 vs 수학)
   - 블록 내 필드도 블록 타입에 따라 다름
   - Document DB의 유연한 스키마가 적합

3. **완결된 문서 조회**
   - 하나의 레슨 = 하나의 완결된 학습 경험
   - 조회 시 JOIN 없이 단일 쿼리로 모든 정보 획득
   - 성능과 개발 복잡도 모두 개선

### 3.2 컬렉션 설계

#### 컬렉션: `lessons`

```javascript
{
  _id: ObjectId("..."),
  lessonId: "korean_01",           // 고유 식별자
  subject: "korean",                // 과목
  title: "1강 시의 표현과 형식",    // 레슨 제목
  order: 1,                         // 순서
  metadata: {
    year: 2026,
    curriculum: "수능특강",
    estimatedDuration: 3600,        // 초 단위
    difficulty: "basic"
  },
  blocks: [                         // 레슨 블록 배열 (순서 중요)
    {
      blockId: "korean_01_b001",
      type: "orientation",          // 블록 타입
      order: 1,                     // 블록 순서
      learningIntent: {
        title: "강의 소개",
        description: "이 강의의 목표와 구성 이해"
      },
      brailleSignal: "●○○",        // 3셀 점자 패턴
      audioRange: {
        start: "00:00:00",
        end: "00:02:30"
      },
      userAwareness: {
        message: "강의가 시작되었습니다",
        context: "오리엔테이션 단계"
      },
      uiBehavior: {
        autoPlay: true,
        bookmarkable: false,
        reviewable: true
      },
      content: {                    // 블록 타입별 가변 필드
        script: "여러분, 안녕하세요? 국어 영역 최선의 선택 최서희입니다...",
        keyPoints: ["강의 목표", "학습 방법"]
      }
    },
    {
      blockId: "korean_01_b002",
      type: "learning_goal",
      order: 2,
      learningIntent: {
        title: "학습 목표 설정",
        description: "이 강의에서 배울 핵심 개념 파악"
      },
      brailleSignal: "●●○",
      audioRange: {
        start: "00:02:30",
        end: "00:05:00"
      },
      userAwareness: {
        message: "학습 목표를 확인합니다",
        context: "목표 설정 단계"
      },
      uiBehavior: {
        autoPlay: true,
        bookmarkable: true,
        reviewable: true
      },
      content: {
        goals: [
          "시의 표현 기법 이해",
          "시의 형식 특징 파악",
          "시의 내용 분석 방법 습득"
        ]
      }
    },
    {
      blockId: "korean_01_b003",
      type: "exam_structure",
      order: 3,
      learningIntent: {
        title: "시험 구조 이해",
        description: "수능에서 시가 어떻게 출제되는지 파악"
      },
      brailleSignal: "●●●",
      audioRange: {
        start: "00:05:00",
        end: "00:08:00"
      },
      userAwareness: {
        message: "시험 출제 구조를 학습합니다",
        context: "시험 구조 분석 단계"
      },
      uiBehavior: {
        autoPlay: true,
        bookmarkable: true,
        reviewable: true
      },
      content: {
        structure: {
          expression: "표현에서 1문제",
          format: "형식에서 1문제",
          content: "내용에서 1문제"
        },
        examples: ["2024학년도 수능", "2023학년도 수능"]
      }
    },
    {
      blockId: "korean_01_b004",
      type: "appreciation_frame",
      order: 4,
      learningIntent: {
        title: "감상 프레임 습득",
        description: "시를 감상하는 사고 틀 이해"
      },
      brailleSignal: "○●○",
      audioRange: {
        start: "00:08:00",
        end: "00:15:00"
      },
      userAwareness: {
        message: "감상 프레임을 학습합니다",
        context: "사고 틀 구축 단계"
      },
      uiBehavior: {
        autoPlay: true,
        bookmarkable: true,
        reviewable: true,
        pausePoints: ["00:10:00", "00:12:00"]  // 자동 일시정지 지점
      },
      content: {
        frame: "화자가 무엇을 어떻게",
        explanation: "소재(무엇) + 정서/태도(어떻게)",
        examples: ["박두진 <해>", "시조 작품들"]
      }
    },
    {
      blockId: "korean_01_b005",
      type: "work_analysis",
      order: 5,
      learningIntent: {
        title: "작품 분석",
        description: "구체적 작품을 통해 감상 프레임 적용"
      },
      brailleSignal: "○●●",
      audioRange: {
        start: "00:15:00",
        end: "00:35:00"
      },
      userAwareness: {
        message: "작품 분석을 시작합니다",
        context: "작품 분석 단계"
      },
      uiBehavior: {
        autoPlay: true,
        bookmarkable: true,
        reviewable: true,
        navigationPoints: [        // 주요 전환 지점
          {time: "00:18:00", label: "작품 배경"},
          {time: "00:25:00", label: "주제 분석"},
          {time: "00:32:00", label: "표현 기법"}
        ]
      },
      content: {
        work: {
          title: "박두진 <해>",
          author: "박두진",
          period: "1946년",
          analysis: {
            theme: "평화와 공존의 이상향 소망",
            expression: ["상징", "대비", "음성 상징어"],
            structure: "AABA 반복과 변주"
          }
        }
      }
    },
    {
      blockId: "korean_01_b006",
      type: "problem_application",
      order: 6,
      learningIntent: {
        title: "문제 적용",
        description: "학습한 내용을 문제 풀이에 적용"
      },
      brailleSignal: "○○●",
      audioRange: {
        start: "00:35:00",
        end: "00:50:00"
      },
      userAwareness: {
        message: "문제 풀이를 시작합니다",
        context: "문제 적용 단계"
      },
      uiBehavior: {
        autoPlay: false,           // 문제는 자동 재생 안 함
        bookmarkable: true,
        reviewable: true,
        problemMode: true          // 문제 모드 활성화
      },
      content: {
        problemNumber: 1,
        question: "시구의 반복과 변주를 통해서 정서의 고조를 드러내고 있다.",
        choices: [
          "① 나열의 방식을 활용하여 반성적인 태도를 드러내고 있다",
          "② 음성 상징어를 활용하여 시각적 이미지를 선명하게 부각하고 있다",
          "③ 활유적 표현은 자연물이 주는 역동적 움직임이 강하게 드러나는 것",
          "④ 가정적 표현을 통해서 화자가 추구하는 이상적 상황을 드러내고 있다"
        ],
        correctAnswer: 2,
        explanation: "반복과 변주는 AABA 구조에서 확인할 수 있으며...",
        thinkingProcess: [
          "1. 반복과 변주 패턴 확인",
          "2. 정서 고조와의 연관성 파악",
          "3. 선지별 검토"
        ]
      }
    },
    {
      blockId: "korean_01_b007",
      type: "summary",
      order: 7,
      learningIntent: {
        title: "요약 정리",
        description: "이 강의에서 배운 핵심 내용 정리"
      },
      brailleSignal: "●○●",
      audioRange: {
        start: "00:50:00",
        end: "00:55:00"
      },
      userAwareness: {
        message: "강의 요약을 확인합니다",
        context: "정리 단계"
      },
      uiBehavior: {
        autoPlay: true,
        bookmarkable: true,
        reviewable: true
      },
      content: {
        keyPoints: [
          "형상화: 정서나 삶의 이치를 구체적 이미지로 표현",
          "화자가 무엇을 어떻게: 소재 + 정서/태도",
          "박두진 <해>: 밝음/어둠 대비, 평화와 공존의 이상향 소망"
        ],
        connections: [
          "다음 강의: 시조 작품 분석",
          "관련 개념: 상징, 대비, 음성 상징어"
        ]
      }
    },
    {
      blockId: "korean_01_b008",
      type: "closing_message",
      order: 8,
      learningIntent: {
        title: "마무리",
        description: "강의 종료 및 다음 학습 안내"
      },
      brailleSignal: "○○○",
      audioRange: {
        start: "00:55:00",
        end: "01:00:00"
      },
      userAwareness: {
        message: "강의가 종료되었습니다",
        context: "마무리 단계"
      },
      uiBehavior: {
        autoPlay: true,
        bookmarkable: false,
        reviewable: true,
        nextLesson: "korean_02"
      },
      content: {
        message: "오늘 배운 내용을 복습하고 다음 강의를 준비하세요",
        nextLessonPreview: "다음 강의에서는 시조 작품을 분석합니다"
      }
    }
  ],
  progress: {                       // 사용자별 진행 상태 (별도 컬렉션으로 분리 가능)
    userId: "u_demo",
    currentBlock: "korean_01_b005",
    completedBlocks: ["korean_01_b001", "korean_01_b002", "korean_01_b003", "korean_01_b004"],
    bookmarks: ["korean_01_b004"],
    lastAccessed: ISODate("2026-01-16T10:30:00Z")
  },
  createdAt: ISODate("2026-01-16T00:00:00Z"),
  updatedAt: ISODate("2026-01-16T00:00:00Z")
}
```

### 3.3 블록 타입별 스키마

블록 타입에 따라 `content` 필드의 구조가 달라집니다:

#### `orientation` 블록
```javascript
content: {
  script: String,
  keyPoints: [String]
}
```

#### `learning_goal` 블록
```javascript
content: {
  goals: [String],
  prerequisites: [String]  // 선수 학습
}
```

#### `exam_structure` 블록
```javascript
content: {
  structure: Object,      // 과목별 구조
  examples: [String]      // 기출 예시
}
```

#### `appreciation_frame` 블록
```javascript
content: {
  frame: String,          // 프레임 이름
  explanation: String,
  examples: [String]
}
```

#### `work_analysis` 블록
```javascript
content: {
  work: {
    title: String,
    author: String,
    period: String,
    analysis: {
      theme: String,
      expression: [String],
      structure: String
    }
  }
}
```

#### `problem_application` 블록
```javascript
content: {
  problemNumber: Number,
  question: String,
  choices: [String],
  correctAnswer: Number,
  explanation: String,
  thinkingProcess: [String]
}
```

#### `summary` 블록
```javascript
content: {
  keyPoints: [String],
  connections: [String]   // 다른 강의/개념과의 연결
}
```

#### `closing_message` 블록
```javascript
content: {
  message: String,
  nextLessonPreview: String
}
```

---

## 4. 점자 신호 설계 원칙

### 4.1 점자 신호의 역할

점자는 **내용을 전달하는 도구가 아니라, 현재 학습 상태를 알려주는 신호등**입니다.

### 4.2 점자 패턴 설계

3셀 점자 패턴은 다음과 같이 설계됩니다:

| 패턴 | 의미 | 사용 시점 |
|------|------|----------|
| `●○○` | 오리엔테이션 | 강의 시작, 블록 전환 시작 |
| `●●○` | 목표 설정 | 학습 목표 제시 |
| `●●●` | 중요 정보 | 시험 구조, 핵심 개념 |
| `○●○` | 사고 틀 | 감상 프레임, 분석 방법 |
| `○●●` | 작품 분석 | 구체적 작품 분석 중 |
| `○○●` | 문제 풀이 | 문제 적용 단계 |
| `●○●` | 정리 | 요약, 복습 |
| `○○○` | 종료 | 강의 마무리 |

**설계 이유**:
- 패턴이 단순하고 외우기 쉬움
- 블록 타입과 1:1 대응으로 일관성 유지
- 사용자가 패턴만 보고도 "지금 어디인지" 즉시 인지 가능

### 4.3 점자 출력 규칙

**출력하지 않는 것**:
- ❌ 지문 전문
- ❌ 선지 텍스트
- ❌ 긴 설명문
- ❌ 작품 전문

**출력하는 것**:
- ⭕ 현재 블록 타입 (점자 패턴)
- ⭕ 블록 순서 (예: "1/8")
- ⭕ 간단한 상태 메시지 (예: "분석 중")

---

## 5. UI 플로우와 데이터 구조의 일관성

### 5.1 레슨 조회 플로우

```
사용자: "1강 들을래"
  ↓
앱: MongoDB에서 lessonId="korean_01" 조회
  ↓
앱: 단일 쿼리로 레슨 전체 + 모든 블록 획득
  ↓
앱: 첫 번째 블록(orientation) 자동 재생
  ↓
앱: 점자 디바이스에 "●○○" 출력
  ↓
사용자: 현재 상태 인지 ("오리엔테이션 단계")
```

**설계 이유**:
- 레슨 단위 조회로 네트워크 요청 최소화
- 블록별 추가 조회 불필요
- 사용자 대기 시간 최소화

### 5.2 블록 전환 플로우

```
현재 블록 재생 완료
  ↓
다음 블록 자동 로드 (이미 메모리에 있음)
  ↓
점자 패턴 변경 (예: "●○○" → "●●○")
  ↓
음성 안내: "학습 목표를 확인합니다"
  ↓
다음 블록 자동 재생 (uiBehavior.autoPlay === true인 경우)
```

**설계 이유**:
- 블록 전환 시 사용자가 "지금 어디로 이동했는지" 명확히 인지
- 점자 패턴 변경 = 시각적 큐 대체
- 음성 안내 = 추가 확인 수단

### 5.3 북마크 및 복습 플로우

```
사용자: "이 부분 북마크"
  ↓
앱: 현재 블록 ID 저장 (예: "korean_01_b004")
  ↓
사용자: "북마크한 부분 다시 들을래"
  ↓
앱: 북마크된 블록 ID로 해당 블록 찾기
  ↓
앱: 해당 블록의 audioRange로 강의 재생
  ↓
앱: 점자 패턴 출력 (예: "○●○")
```

**설계 이유**:
- 블록 단위 북마크로 정확한 위치 복습 가능
- 블록 ID만 저장하면 모든 정보 접근 가능
- 레슨 전체를 다시 로드할 필요 없음

---

## 6. 설계 결정의 이유 (졸업작품 보고서용)

### 6.1 "왜 Document DB인가?"

**기술적 이유**:
- 레슨 단위 조회가 압도적이므로 JOIN이 불필요
- 블록 구조가 가변적이므로 정규화가 오히려 복잡도 증가

**사용자 경험 이유**:
- 레슨 전체를 한 번에 로드하여 네트워크 지연 최소화
- 사용자가 강의를 들을 때 중간에 로딩 대기 없음

**개발 효율성 이유**:
- 단일 쿼리로 모든 데이터 획득
- 블록 타입별 스키마 변경이 용이

### 6.2 "왜 블록을 Embedded Document로 설계했는가?"

**데이터 일관성**:
- 블록은 레슨과 분리되어 존재할 수 없음
- 블록 순서가 중요하므로 배열로 관리

**조회 성능**:
- 레슨 조회 시 블록도 함께 조회
- 블록 단독 조회는 드물므로 별도 컬렉션 불필요

**데이터 무결성**:
- 레슨 삭제 시 블록도 자동 삭제
- 블록 순서 변경이 용이

### 6.3 "왜 점자를 신호등으로 사용하는가?"

**하드웨어 제약 수용**:
- 3셀 점자로는 긴 텍스트 전달 불가능
- 제약을 인정하고 다른 방식으로 활용

**인지 부하 감소**:
- 긴 텍스트를 읽는 것보다 패턴 인식이 빠름
- "지금 어디인지"만 알면 충분

**일관성 유지**:
- 블록 타입 = 점자 패턴 = 1:1 대응
- 사용자가 패턴만 보고도 상태 파악 가능

### 6.4 "왜 블록에 5가지 필수 요소를 두었는가?"

**학습 목적**: 사용자가 "무엇을 배우는지" 항상 인지
**점자 신호**: 현재 상태를 즉시 파악
**음성 강의 범위**: 정확한 위치 복습
**사용자 인지 효과**: 시각적 큐 대체
**UI 동작 규칙**: 블록별 맞춤형 경험 제공

이 5가지가 모두 있어야 시각장애 학습자가 강의를 "완전히" 경험할 수 있습니다.

---

## 7. 구현 우선순위

### Phase 1: 핵심 구조
1. MongoDB 컬렉션 설계 및 샘플 데이터 생성
2. 레슨 조회 API 구현
3. 블록 전환 로직 구현

### Phase 2: 점자 통합
1. 점자 패턴 매핑 시스템
2. 점자 디바이스 연동
3. 블록 전환 시 점자 출력

### Phase 3: 사용자 경험
1. 북마크 기능
2. 복습 모드
3. 진행 상태 저장

### Phase 4: 고도화
1. 블록별 맞춤형 UI
2. 학습 분석 및 추천
3. 접근성 개선

---

## 8. 결론

이 설계는 **시각장애 수험생의 실제 학습 경험**을 중심으로 한 것입니다.

- 점자 제약을 인정하고, 오히려 "상태 신호"로 활용
- 강의를 "경험 문서"로 재정의하여 완결성 확보
- Document DB로 단순하고 효율적인 데이터 구조 구현
- 블록 기반으로 사용자가 항상 "지금 어디인지" 인지 가능

이 설계는 기술적 완성도뿐만 아니라, **시각장애 학습자의 학습 효과를 극대화**하는 것을 목표로 합니다.
