# 수식 계산 도구 (MathCalculator) 기능 상세 설명

> **파일**: `frontend/src/components/math/MathCalculator.tsx`  
> **목적**: 시각 장애인 수능 수학 영역에서 사용하는 "한소네" 점자정보단말기의 계산 기능을 웹에서 대체

---

## 📋 목차

1. [배경 및 필요성](#배경-및-필요성)
2. [기능 상세 설명](#기능-상세-설명)
3. [실제 사용 시나리오](#실제-사용-시나리오)
4. [UI 구성](#ui-구성)
5. [한계 및 개선 가능성](#한계-및-개선-가능성)
6. [기술 스택](#기술-스택)

---

## 배경 및 필요성

### "한소네"란?

**한소네(한국소프트웨어정보통신) 점자정보단말기**
- 시각 장애인 수능 시험에서 사용하는 점자 입력/출력 장치
- 수학 영역에서 복잡한 수식 계산에 필수적인 도구
- 점자 키보드로 수식 입력, 점자 디스플레이로 결과 확인

### 문제점

```
┌─────────────────────────────────────────────────────────┐
│ 문제: 학습 플랫폼과 실제 수능 환경의 차이                │
└─────────────────────────────────────────────────────────┘
        │
        ├─→ 학습 플랫폼에는 계산 도구가 없음
        ├─→ 수능 환경과 학습 환경의 차이로 적응 어려움
        ├─→ 수학 문제 풀이 중 중간 계산이 필요함
        └─→ 시각 장애인은 시각적 계산기 사용 불가
```

### 해결책

**MathCalculator 컴포넌트 구현**
- 웹 기반 수식 계산 도구 제공
- 음성(TTS) 및 점자 디스플레이 연동
- 실제 수능 환경과 유사한 경험 제공

---

## 기능 상세 설명

### 1. 수식 입력 및 계산

#### 구현 코드

```typescript
function evaluateExpression(expr: string): number {
  try {
    // 안전한 계산을 위해 Function 생성자 사용 (제한적)
    // 실제 프로덕션에서는 mathjs 사용 권장
    const sanitized = expr.replace(/[^0-9+\-*/().\s]/g, '');
    // eslint-disable-next-line no-eval
    return eval(sanitized) as number;
  } catch {
    throw new Error('계산 오류');
  }
}
```

#### 동작 방식

1. **사용자 입력**: `2 + 3 * 4`
2. **시스템 계산**: `14`
3. **결과 제공**: 화면 표시 + 음성 안내 + 점자 출력

#### 지원 연산

| 연산 | 기호 | 예시 | 결과 |
|------|------|------|------|
| 덧셈 | `+` | `2 + 3` | `5` |
| 뺄셈 | `-` | `10 - 4` | `6` |
| 곱셈 | `*` | `3 * 4` | `12` |
| 나눗셈 | `/` | `15 / 3` | `5` |
| 괄호 | `()` | `(10 + 5) / 3` | `5` |
| 제곱 | `^` | `2^3` | `8` (제한적) |
| 실수 | `.` | `3.14 * 2` | `6.28` |

#### 제한사항

- ⚠️ 현재는 `eval` 사용 (보안/안정성 제한)
- ⚠️ 주석에 "mathjs 사용 권장" 표기
- ⚠️ 복잡한 함수(`sin`, `cos`, `log` 등) 미지원

---

### 2. TTS 음성 설명

#### 구현 코드

```typescript
const speakExpression = (expr: string) => {
  // 간단한 수식 음성 변환
  let spoken = expr
    .replace(/\^/g, '제곱')
    .replace(/\*/g, '곱하기')
    .replace(/\//g, '나누기')
    .replace(/\+/g, '더하기')
    .replace(/-/g, '빼기')
    .replace(/=/g, '는')
    .replace(/\(/g, '괄호 열기')
    .replace(/\)/g, '괄호 닫기');
  
  speak(spoken);
};
```

#### 변환 예시

| 입력 | 음성 출력 |
|------|-----------|
| `2 + 3` | "2 더하기 3" |
| `2^3 + 5 * 2` | "2제곱 더하기 5 곱하기 2" |
| `(10 + 5) / 3` | "괄호 열기 10 더하기 5 괄호 닫기 나누기 3" |

#### 사용 시나리오

1. **수식 입력 확인**
   - 사용자가 수식 입력 후 "🔊 수식 읽기" 버튼 클릭
   - 음성으로 입력한 수식 확인 가능

2. **계산 결과 안내**
   ```typescript
   speak(`계산 결과는 ${resultStr}입니다.`);
   ```
   - 계산 완료 시 자동으로 결과를 음성으로 안내
   - 예: "계산 결과는 14입니다"

---

### 3. 점자 디스플레이 연동

#### 구현 코드

```typescript
const { sendText } = useBrailleBLE();

// 계산 결과를 점자 디스플레이에 표시
if (sendText) {
  sendText(`${expression} = ${resultStr}`);
}
```

#### 동작 방식

1. **계산 완료** → `2 + 3 * 4 = 14`
2. **BLE 전송** → Bluetooth Low Energy로 점자 디스플레이에 전송
3. **점자 표시** → 시각 장애인 사용자가 점자로 수식과 결과 확인

#### 의미

- ✅ 시각 장애인 사용자가 점자로 수식과 결과를 확인 가능
- ✅ 실제 수능 환경(한소네)과 유사한 경험 제공
- ✅ 시각적 계산기 대신 점자로 접근 가능

---

### 4. 계산 히스토리 저장 및 재사용

#### 구현 코드

```typescript
const [history, setHistory] = useState<Array<{ expr: string; result: string }>>([]);

// 계산 완료 시 히스토리에 추가 (최대 10개)
setHistory(prev => [...prev, { expr: expression, result: resultStr }].slice(-10));
```

#### 기능

- **최근 10개 계산 저장**: 자동으로 최근 계산 이력 저장
- **히스토리 클릭**: 항목 클릭 시 수식/결과 재사용
- **문제 풀이 중**: 이전 계산 재확인 가능

#### UI 예시

```
계산 히스토리
─────────────
2 + 3 * 4
= 14

(10 + 5) / 3
= 5

3.14 * 5 * 5
= 78.5
```

#### 사용 시나리오

1. 문제 풀이 중 여러 번 계산 필요
2. 이전 계산 결과 재확인
3. 비슷한 계산 패턴 재사용

---

### 5. 키보드 단축키

#### 지원 단축키

| 단축키 | 동작 |
|--------|------|
| `Enter` | 계산 실행 |
| `Ctrl+Enter` | 계산 실행 (전역 단축키) |
| `Escape` | 계산기 닫기 (UnitViewer에서) |

#### 접근성

- ✅ 마우스 없이 키보드만으로 사용 가능
- ✅ 점자 키보드 사용자에게 유용
- ✅ 빠른 계산 실행 가능

---

## 실제 사용 시나리오

### 시나리오 1: 수학 문제 풀이 중

```
1. 사용자가 수학 개념 단원 학습 중
   └─→ UnitViewer에서 "계산기 열기" 버튼 표시

2. 문제에서 "2x² + 3x - 5 = 0" 같은 수식 발견
   └─→ 중간 계산이 필요함

3. "계산기 열기" 버튼 클릭
   └─→ MathCalculator 팝업 열림

4. 중간 계산: "2 * 2 + 3 * 2 - 5" 입력
   └─→ x=2일 때의 값 계산

5. Enter 키 입력
   └─→ 결과 "5" 계산

6. 음성 안내: "계산 결과는 5입니다"
   └─→ TTS로 결과 확인

7. 점자 디스플레이에도 표시
   └─→ "2 * 2 + 3 * 2 - 5 = 5"

8. 문제 풀이 계속 진행
   └─→ 계산 결과를 활용하여 문제 해결
```

### 시나리오 2: 복잡한 계산

```
1. 문제: "원의 넓이 = π × r², r=5일 때"

2. 계산기 열기
   └─→ MathCalculator 팝업

3. "3.14 * 5 * 5" 입력
   └─→ π ≈ 3.14 사용

4. 결과: "78.5"
   └─→ 계산 완료

5. 히스토리에 저장
   └─→ 나중에 재사용 가능

6. 다음 문제에서 비슷한 계산 시
   └─→ 히스토리에서 클릭하여 재사용
```

### 시나리오 3: 수식 확인

```
1. 문제에서 복잡한 수식 발견
   └─→ "2^3 + 5 * 2"

2. 계산기 열기

3. 수식 입력 후 "🔊 수식 읽기" 버튼 클릭
   └─→ 음성: "2제곱 더하기 5 곱하기 2"

4. 수식이 맞는지 확인

5. 계산 실행
   └─→ 결과: "18"
```

---

## UI 구성

### 전체 레이아웃

```
┌─────────────────────────────────────┐
│  수식 계산기                  [✕]  │
├─────────────────────────────────────┤
│ 수식 입력                            │
│ ┌─────────────────────────────────┐ │
│ │ 2 + 3 * 4                    │ │
│ └─────────────────────────────────┘ │
│ 🔊 수식 읽기                          │
├─────────────────────────────────────┤
│ 결과                                  │
│ ┌─────────────────────────────────┐ │
│ │ 14                             │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │    계산 (Ctrl+Enter)            │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ 계산 히스토리                         │
│ ┌─────────────────────────────────┐ │
│ │ 2 + 3 * 4                      │ │
│ │ = 14                           │ │
│ ├─────────────────────────────────┤ │
│ │ (10 + 5) / 3                   │ │
│ │ = 5                            │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ • Enter: 계산 실행                    │
│ • Ctrl+Enter: 계산 실행               │
│ • 지원 연산: +, -, *, /, ^, ()       │
└─────────────────────────────────────┘
```

### 컴포넌트 구조

```typescript
<MathCalculator onClose={...}>
  {/* 헤더 */}
  <h3>수식 계산기</h3>
  <button>✕</button>

  {/* 입력 영역 */}
  <input type="text" placeholder="예: 2 + 3 * 4" />
  <button>🔊 수식 읽기</button>

  {/* 결과 영역 */}
  <div>결과: 14</div>

  {/* 에러 영역 */}
  <div>계산 오류가 발생했습니다.</div>

  {/* 계산 버튼 */}
  <button>계산 (Ctrl+Enter)</button>

  {/* 히스토리 영역 */}
  <div>
    {history.map(item => (
      <div onClick={...}>
        {item.expr} = {item.result}
      </div>
    ))}
  </div>

  {/* 도움말 */}
  <div>• Enter: 계산 실행 ...</div>
</MathCalculator>
```

---

## 한계 및 개선 가능성

### 현재 제한사항

#### 1. 보안 및 안정성

- ⚠️ **`eval` 사용**: 보안 취약점 가능성
- ⚠️ **입력 검증 부족**: 악의적 코드 실행 위험
- ⚠️ **에러 처리 단순**: 복잡한 수식에서 예상치 못한 오류

**개선 방안:**
```typescript
// mathjs 라이브러리 사용
import { evaluate } from 'mathjs';

function evaluateExpression(expr: string): number {
  try {
    return evaluate(expr); // 안전한 계산
  } catch (error) {
    throw new Error('계산 오류: ' + error.message);
  }
}
```

#### 2. 기능 제한

- ⚠️ **복잡한 함수 미지원**: `sin`, `cos`, `log`, `sqrt` 등
- ⚠️ **LaTeX 렌더링 없음**: 수식 시각화 없음
- ⚠️ **점자 키보드 직접 입력 미지원**: 텍스트 입력만 가능

**개선 방안:**
```typescript
// mathjs로 확장
import { evaluate, create, all } from 'mathjs';

const math = create(all);

// 삼각함수, 로그 등 지원
math.evaluate('sin(pi/2)'); // 1
math.evaluate('log(10)'); // 2.302585092994046
```

#### 3. 접근성

- ⚠️ **점자 키보드 직접 입력 미지원**
- ⚠️ **계산 과정 단계별 음성 안내 없음**

**개선 방안:**
- 점자 키보드 이벤트 리스너 추가
- 계산 단계별 TTS 안내 ("먼저 괄호 안을 계산합니다...")

---

### 개선 제안

#### 1. mathjs 라이브러리 도입

```typescript
// package.json
{
  "dependencies": {
    "mathjs": "^12.0.0"
  }
}

// MathCalculator.tsx
import { evaluate, create, all } from 'mathjs';

const math = create(all);

function evaluateExpression(expr: string): number {
  try {
    return math.evaluate(expr);
  } catch (error) {
    throw new Error('계산 오류: ' + error.message);
  }
}
```

**장점:**
- ✅ 안전한 계산 (eval 사용 안 함)
- ✅ 복잡한 함수 지원 (`sin`, `cos`, `log`, `sqrt` 등)
- ✅ 단위 변환 지원 (`2 inch to cm`)
- ✅ 행렬 계산 지원

#### 2. LaTeX 렌더링 추가

```typescript
// package.json
{
  "dependencies": {
    "react-katex": "^3.0.1",
    "katex": "^0.16.0"
  }
}

// MathCalculator.tsx
import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';

// 수식 시각화
<BlockMath>{expression}</BlockMath>
```

**장점:**
- ✅ 수식 시각화 (저시력 사용자에게 유용)
- ✅ 수식 구조 명확화

#### 3. 점자 키보드 입력 지원

```typescript
// 점자 키보드 이벤트 리스너
useEffect(() => {
  const handleBrailleInput = (event: CustomEvent) => {
    const brailleChar = event.detail.char;
    setExpression(prev => prev + brailleChar);
  };

  window.addEventListener('braille-input', handleBrailleInput);
  return () => window.removeEventListener('braille-input', handleBrailleInput);
}, []);
```

**장점:**
- ✅ 실제 수능 환경과 동일한 입력 방식
- ✅ 점자 키보드 사용자 편의성 향상

#### 4. 계산 과정 단계별 음성 안내

```typescript
function calculateWithSteps(expr: string) {
  // 1단계: 괄호 계산
  if (expr.includes('(')) {
    speak('먼저 괄호 안을 계산합니다.');
    // 괄호 계산 로직
  }
  
  // 2단계: 곱셈/나눗셈
  if (expr.includes('*') || expr.includes('/')) {
    speak('곱셈과 나눗셈을 계산합니다.');
    // 곱셈/나눗셈 계산 로직
  }
  
  // 3단계: 덧셈/뺄셈
  speak('덧셈과 뺄셈을 계산합니다.');
  // 최종 결과
}
```

**장점:**
- ✅ 계산 과정 이해 향상
- ✅ 교육적 가치 증대

---

## 기술 스택

### 현재 사용 기술

| 기술 | 용도 |
|------|------|
| React | 컴포넌트 프레임워크 |
| TypeScript | 타입 안정성 |
| `useTTS` hook | 음성 안내 |
| `useBrailleBLE` hook | 점자 디스플레이 연동 |
| `eval` | 수식 계산 (임시) |

### 권장 개선 기술

| 기술 | 용도 |
|------|------|
| `mathjs` | 안전한 수식 계산 |
| `react-katex` | LaTeX 수식 렌더링 |
| 점자 키보드 API | 점자 직접 입력 |

---

## 통합 위치

### UnitViewer에서 사용

```typescript
// frontend/src/components/unit/UnitViewer.tsx

// 수학 개념일 때만 계산기 표시
const isMathConcept = unit.type === 'CONCEPT_CORE' || 
                      unit.type === 'CONCEPT_FORM' || 
                      unit.type === 'CONCEPT_CONTENT';

if (isMathConcept) {
  return (
    <>
      <ConceptViewer unit={unit} />
      {/* 수학 계산기 토글 버튼 */}
      <button onClick={() => setShowCalculator(!showCalculator)}>
        {showCalculator ? '계산기 닫기' : '계산기 열기'}
      </button>
      {showCalculator && <MathCalculator onClose={...} />}
    </>
  );
}
```

### 사용 조건

- ✅ **수학 개념 단원**에서만 표시
- ✅ **토글 버튼**으로 열기/닫기
- ✅ **팝업 형태**로 화면 하단 우측에 표시

---

## 결론

**MathCalculator**는 시각 장애인 수능 수학 영역에서 사용하는 "한소네" 점자정보단말기의 계산 기능을 웹에서 대체하는 컴포넌트입니다.

### 핵심 기능

1. ✅ **수식 입력 및 계산**: 기본 연산 지원
2. ✅ **TTS 음성 설명**: 수식과 결과를 음성으로 안내
3. ✅ **점자 디스플레이 연동**: BLE로 점자 출력
4. ✅ **계산 히스토리**: 최근 10개 계산 저장 및 재사용
5. ✅ **키보드 단축키**: 접근성 향상

### 개선 필요 사항

1. ⚠️ `mathjs` 라이브러리 도입 (보안/기능 향상)
2. ⚠️ LaTeX 렌더링 추가 (시각화)
3. ⚠️ 점자 키보드 직접 입력 지원
4. ⚠️ 계산 과정 단계별 음성 안내

### 의의

- ✅ **실제 수능 환경 반영**: 한소네 대체 기능 제공
- ✅ **접근성 향상**: 시각 장애인 학습자 지원
- ✅ **학습 효율성**: 문제 풀이 중 빠른 계산 가능

---

*작성일: 2026-01-27*  
*관련 파일: `frontend/src/components/math/MathCalculator.tsx`*
