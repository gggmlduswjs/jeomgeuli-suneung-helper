/**
 * 음성 명령어 훅
 * 분리된 모듈을 사용하여 명령어 처리
 */
import { useCallback } from "react";
import { route } from "../lib/voice/CommandRouter";

// 타입 정의
export type CommandHandlers = {
  // 기본 제어
	next?: () => void;
	prev?: () => void;
	repeat?: () => void;
	pause?: () => void;
	start?: () => void;
	stop?: () => void;
  
  // 네비게이션
	home?: () => void;
	back?: () => void;
	menu?: () => void;
  
  // 학습 관련 (레거시)
	learn?: () => void;
	quiz?: () => void;
	review?: () => void;
	freeConvert?: () => void;
  
  // 정보탐색
	explore?: () => void;
	news?: () => void;
	weather?: () => void;
  
  // 새로운 Jeomgeuli-Suneung 메뉴
	textbook?: () => void;
	passage?: () => void;
	graphTable?: () => void;
	question?: () => void;
	vocab?: () => void;
	brailleSpeed?: () => void;
	examMode?: () => void;
	examTimer?: () => void;
  
  // 점자 관련
	brailleOn?: () => void;
	brailleOff?: () => void;
	brailleConnect?: () => void;
	brailleDisconnect?: () => void;
  
  // 상세 정보
	detail?: (idx?: number) => void;
	help?: () => void;
  
  // TTS 관련
	speak?: (text: string) => void;
	mute?: () => void;
	unmute?: () => void;
  
  // 입력 관련
	clear?: () => void;
	submit?: () => void;
};

/**
 * 음성 명령어 훅
 * 분리된 모듈(commands, normalizers, matchers)을 사용하여 명령어 처리
 */
export default function useVoiceCommands(handlers: CommandHandlers) {
  const onSpeech = useCallback((text: string): boolean => route(text, handlers), [handlers]);
  return { onSpeech };
}
