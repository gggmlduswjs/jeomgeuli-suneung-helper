"""
PDF 파싱 모듈의 로거 설정
백그라운드 작업에서도 로그가 제대로 출력되도록 설정
"""
import logging
import sys


def setup_pdf_logging():
    """PDF 파싱 관련 모듈들의 로거를 INFO 레벨로 설정

    백그라운드 작업이나 멀티프로세싱 환경에서도 로그가 출력되도록
    루트 로거와 주요 모듈 로거들을 명시적으로 INFO로 설정합니다.
    """
    # 루트 로거를 INFO로 설정
    root_logger = logging.getLogger()
    if root_logger.level > logging.INFO:
        root_logger.setLevel(logging.INFO)

    # 공통 포맷터
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러 추가 (이미 있으면 재사용)
    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 파일 핸들러 추가 (파싱 로그를 파일로 저장)
    try:
        file_handler = logging.FileHandler('parsing_log.txt', mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"[로깅] 파일 핸들러 추가 실패: {e}")

    # 주요 PDF 파싱 모듈 로거들을 명시적으로 INFO로 설정
    pdf_modules = [
        'app.infrastructure.pdf.parsers.hybrid_router',
        'app.infrastructure.pdf.parsers.unified_parser',
        'app.infrastructure.pdf.parsers.template_manager',
        'app.infrastructure.pdf.parsers.section_extractor',
        'app.infrastructure.pdf.parsers.lecture_boundary_validator',
        'app.infrastructure.pdf.pipeline',
        'app.infrastructure.pdf.lecture_contents_extractor',
        'app.routers.books',
    ]

    for module_name in pdf_modules:
        module_logger = logging.getLogger(module_name)
        module_logger.setLevel(logging.INFO)
