"""
강의 음성과 텍스트 자동 동기화
"""
from typing import List, Dict, Optional
from pathlib import Path
import difflib

try:
    import speech_recognition as sr
    from pydub import AudioSegment
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False


class AudioTextSync:
    def __init__(self):
        if HAS_SPEECH_RECOGNITION:
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
            print("[audio_sync] speech_recognition 또는 pydub이 설치되지 않았습니다.")
    
    def sync_audio_to_text(
        self, 
        audio_path: Path, 
        text_sections: List[Dict]
    ) -> List[Dict]:
        """음성 파일과 텍스트 섹션을 자동 동기화"""
        if not HAS_SPEECH_RECOGNITION:
            return text_sections
        
        # 1. 음성을 텍스트로 변환 (STT)
        audio_text = self.transcribe_audio(audio_path)
        if not audio_text:
            return text_sections
        
        # 2. 텍스트 매칭 (원본 텍스트와 STT 결과 매칭)
        synced_sections = []
        for section in text_sections:
            # 원본 텍스트와 음성 텍스트를 비교하여 시간 위치 찾기
            timestamp = self.find_timestamp(section["content"], audio_text)
            section["timestamp"] = timestamp
            synced_sections.append(section)
        
        return synced_sections
    
    def transcribe_audio(self, audio_path: Path) -> Optional[List[Dict]]:
        """음성을 텍스트로 변환 (STT)
        
        Returns:
            [{"text": "...", "start": 0.0, "end": 5.0}, ...]
        """
        if not self.recognizer:
            return None
        
        try:
            # 오디오 파일 로드
            audio = AudioSegment.from_file(str(audio_path))
            
            # 오디오를 청크로 분할 (예: 30초 단위)
            chunk_length_ms = 30000
            chunks = []
            for i in range(0, len(audio), chunk_length_ms):
                chunk = audio[i:i + chunk_length_ms]
                chunks.append({
                    "audio": chunk,
                    "start": i / 1000.0,  # 초 단위
                    "end": (i + chunk_length_ms) / 1000.0
                })
            
            # 각 청크를 텍스트로 변환
            transcript = []
            for chunk in chunks:
                try:
                    # WAV 형식으로 변환 (speech_recognition이 요구)
                    wav_data = chunk["audio"].export(format="wav")
                    
                    with sr.AudioFile(wav_data) as source:
                        audio_data = self.recognizer.record(source)
                        text = self.recognizer.recognize_google(audio_data, language="ko-KR")
                        
                        transcript.append({
                            "text": text,
                            "start": chunk["start"],
                            "end": chunk["end"]
                        })
                except sr.UnknownValueError:
                    # 음성을 인식할 수 없음
                    continue
                except sr.RequestError as e:
                    print(f"[audio_sync] STT API 오류: {e}")
                    continue
            
            return transcript
        except Exception as e:
            print(f"[audio_sync] 오디오 변환 실패: {e}")
            return None
    
    def find_timestamp(
        self, 
        text: str, 
        audio_transcript: List[Dict]
    ) -> Optional[float]:
        """텍스트가 음성의 어느 시점에 나오는지 찾기"""
        if not audio_transcript:
            return None
        
        # 문자열 유사도 기반 매칭
        best_match = None
        best_score = 0.0
        
        for segment in audio_transcript:
            # 유사도 계산
            similarity = difflib.SequenceMatcher(
                None, 
                text.lower(), 
                segment["text"].lower()
            ).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = segment
        
        # 유사도가 0.5 이상이면 매칭된 것으로 간주
        if best_match and best_score >= 0.5:
            return best_match["start"]
        
        return None
