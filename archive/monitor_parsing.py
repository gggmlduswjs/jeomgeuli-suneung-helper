"""
파싱 모니터링 스크립트
백엔드 로그를 실시간으로 파일에 저장
"""
import sys
import time
from datetime import datetime

# 로그 파일 경로
log_file = "parsing_monitor_log.txt"

# 기존 로그 삭제
open(log_file, 'w').close()

print(f"[모니터] 로그 저장 시작: {log_file}")
print("[모니터] Ctrl+C로 종료")
print("-" * 80)

try:
    # stdin에서 읽어서 파일에 저장
    while True:
        line = sys.stdin.readline()
        if not line:
            time.sleep(0.1)
            continue

        # 타임스탬프 추가
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {line}"

        # 파일에 저장
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line)

        # 터미널에도 출력
        print(line, end='')

except KeyboardInterrupt:
    print(f"\n[모니터] 로그 저장 완료: {log_file}")
