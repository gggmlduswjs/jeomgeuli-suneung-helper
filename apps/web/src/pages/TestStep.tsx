import { useEffect, useMemo, useState } from "react";
import AppShellMobile from "../components/ui/AppShellMobile";
import BottomBar from "../components/ui/BottomBar";
import BraillePanel from "../components/braille/BraillePanel";
import { binsToCells } from "@/lib/brailleSafe"; // ✅ 핵심: bin 문자열 파서 사용

// 예시용 더미. 실제로는 학습에서 생성한 퀴즈목록 props로 받아도 됨.
const QUIZ = [
  { answer: "기역", cells: ["100000"] },
  { answer: "니은", cells: ["101000"] },
  { answer: "디귿", cells: ["110000"] },
  { answer: "리을", cells: ["111000"] },
  { answer: "미음", cells: ["101100"] },
];

export default function TestStep() {
  const [i, setI] = useState(0);
  const cur = QUIZ[i];

  // "100000"[] -> number[6][] -> boolean[][]
  const cells = useMemo(() => {
    const parsed = binsToCells(cur?.cells || []); // number[6][]
    return parsed.map(cell => cell.map(n => !!n)); // boolean[][]
  }, [cur]);

  const prev = () => setI(v => Math.max(0, v - 1));
  const next = () => setI(v => Math.min(QUIZ.length - 1, v + 1));

  const repeat = () => {
    try {
      const u = new SpeechSynthesisUtterance(
        "점자를 촉각으로 확인한 뒤 정답을 말씀해주세요."
      );
      u.lang = "ko-KR";
      speechSynthesis.cancel();
      speechSynthesis.speak(u);
    } catch {}
  };

  // 문제 바뀔 때마다 간단 안내 음성
  useEffect(() => {
    repeat();
  }, [i]);

  if (!cur) {
    return (
      <AppShellMobile title="테스트">
        <div className="card">문항을 불러올 수 없습니다.</div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile title="테스트">
      <div className="space-y-6 pb-28">
        <div className="card">점자를 촉각으로 확인한 뒤 정답을 말씀해주세요.</div>

        <div className="card text-center">
          <BraillePanel braille={{
            status: "ready",
            currentWord: "",
            currentCells: cells,
            demoMode: true,
            queue: [],
            next: () => {},
            repeat: () => {},
            pause: () => {},
            enqueueKeywords: () => {}
          }} />
          <div className="mt-3 text-gray-500">곧 질문합니다</div>
        </div>

        <div className="card">정답: {cur.answer}</div>
      </div>

      <BottomBar
        onLeft={prev}
        onMid={repeat}
        onRight={next}
        rightLabel={i === QUIZ.length - 1 ? "완료" : "다음"}
      />
    </AppShellMobile>
  );
}
