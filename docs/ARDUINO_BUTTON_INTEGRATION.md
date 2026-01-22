# Arduino 버튼 제어 통합 가이드

프론트엔드에서 Arduino 버튼 입력을 받아서 점자 텍스트 네비게이션을 제어하는 기능입니다.

## 구현 내용

### 1. Arduino 펌웨어
- 버튼 입력을 시리얼/블루투스로 전송
- 프로토콜: `BTN:1` (이전), `BTN:2` (다음), `BTN:3:PLAY/PAUSE` (재생/일시정지)

### 2. 프론트엔드 Hook
- `useArduinoButtons`: Web Serial API를 사용하여 Arduino와 통신
- `useBrailleChunkReader`: Arduino 버튼 입력을 자동으로 처리

## 사용 방법

### 기본 사용 (자동 통합)

`useBrailleChunkReader`를 사용하면 자동으로 Arduino 버튼이 연결됩니다:

```tsx
import { useBrailleChunkReader } from '../hooks/useBrailleChunkReader';

function MyComponent() {
  const text = "안녕하세요. 점글이입니다.";
  
  const chunkReader = useBrailleChunkReader(text, {
    maxCells: 3,
    strategy: 'word',
    autoPlay: false,
  });

  // Arduino 버튼이 자동으로 작동합니다:
  // - 버튼 1 (A2): 이전 청크
  // - 버튼 2 (A3): 다음 청크
  // - 버튼 3 (A4): 재생/일시정지

  return (
    <div>
      <p>{chunkReader.currentChunk}</p>
      <p>{chunkReader.currentIndex + 1} / {chunkReader.totalChunks}</p>
    </div>
  );
}
```

### 수동 연결

Arduino를 수동으로 연결하려면:

```tsx
import { useArduinoButtons } from '../hooks/useArduinoButtons';

function MyComponent() {
  const { isConnected, connect, disconnect, onButtonPress } = useArduinoButtons();

  useEffect(() => {
    if (isConnected) {
      onButtonPress((event) => {
        switch (event) {
          case 'prev':
            // 이전 동작
            break;
          case 'next':
            // 다음 동작
            break;
          case 'play':
            // 재생
            break;
          case 'pause':
            // 일시정지
            break;
        }
      });
    }
  }, [isConnected, onButtonPress]);

  return (
    <div>
      {!isConnected && (
        <button onClick={connect}>Arduino 연결</button>
      )}
      {isConnected && (
        <button onClick={disconnect}>연결 해제</button>
      )}
    </div>
  );
}
```

### 컴포넌트 사용

`ArduinoButtonControl` 컴포넌트를 사용하면 더 간단합니다:

```tsx
import ArduinoButtonControl from '../components/braille/ArduinoButtonControl';

function MyComponent() {
  const handlePrev = () => {
    // 이전 동작
  };

  const handleNext = () => {
    // 다음 동작
  };

  const handlePlay = () => {
    // 재생
  };

  const handlePause = () => {
    // 일시정지
  };

  return (
    <>
      <ArduinoButtonControl
        onPrev={handlePrev}
        onNext={handleNext}
        onPlay={handlePlay}
        onPause={handlePause}
        autoConnect={true}  // 자동 연결
      />
      {/* 나머지 UI */}
    </>
  );
}
```

## 하드웨어 연결

### 버튼 핀
- **버튼 1 (A2 핀)**: 이전 문자/청크
- **버튼 2 (A3 핀)**: 다음 문자/청크
- **버튼 3 (A4 핀)**: 재생/일시정지

### 연결 방법
1. 각 버튼의 한쪽을 해당 핀에 연결
2. 버튼의 다른 쪽을 GND에 연결
3. 내부 풀업 사용 (코드에서 `INPUT_PULLUP` 설정됨)

## 브라우저 지원

- **Chrome/Edge**: Web Serial API 지원 ✅
- **Firefox/Safari**: 지원 안 함 ❌

## 문제 해결

### 연결이 안 될 때
1. Chrome/Edge 브라우저 사용 확인
2. Arduino가 USB로 연결되어 있는지 확인
3. 다른 프로그램이 시리얼 포트를 사용 중인지 확인
4. 브라우저 콘솔에서 오류 메시지 확인

### 버튼이 작동하지 않을 때
1. Arduino 시리얼 모니터에서 `BTN:1`, `BTN:2`, `BTN:3:PLAY` 메시지 확인
2. 버튼 연결 확인 (핀과 GND)
3. 브라우저 콘솔에서 버튼 이벤트 로그 확인
