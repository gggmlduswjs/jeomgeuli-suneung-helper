"""
Tesseract 설치 확인 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "api"))

try:
    import pytesseract
    print("[OK] pytesseract 모듈 설치됨")
except ImportError:
    print("[ERROR] pytesseract 모듈이 설치되지 않았습니다.")
    print("  설치: pip install pytesseract")
    sys.exit(1)

# Tesseract 경로 확인
print("\n[Tesseract 경로 확인]")
if hasattr(pytesseract.pytesseract, 'tesseract_cmd') and pytesseract.pytesseract.tesseract_cmd:
    print(f"  현재 설정된 경로: {pytesseract.pytesseract.tesseract_cmd}")
else:
    print("  경로가 설정되지 않음")

# 일반적인 Windows 설치 경로 확인
common_paths = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(Path.home().name),
]

print("\n[일반적인 설치 경로 확인]")
found = False
for path_str in common_paths:
    path = Path(path_str)
    if path.exists():
        print(f"  [FOUND] {path}")
        found = True
        # 자동으로 설정
        pytesseract.pytesseract.tesseract_cmd = str(path)
        print(f"  [OK] 경로 자동 설정 완료: {path}")
        break
    else:
        print(f"  [NOT FOUND] {path}")

if not found:
    print("  일반적인 경로에서 Tesseract를 찾을 수 없습니다.")

# Tesseract 버전 확인
print("\n[Tesseract 버전 확인]")
try:
    version = pytesseract.get_tesseract_version()
    print(f"  [OK] Tesseract 버전: {version}")
    print("  [OK] Tesseract가 정상적으로 작동합니다!")
except Exception as e:
    print(f"  [ERROR] Tesseract 실행 실패: {e}")
    print("\n[해결 방법]")
    print("  1. Tesseract가 설치되어 있는지 확인")
    print("  2. 다음 명령으로 경로를 수동 설정:")
    print(f"     pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
    print("  3. 또는 환경변수 PATH에 Tesseract 경로 추가")
