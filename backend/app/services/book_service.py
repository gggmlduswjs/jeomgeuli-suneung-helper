"""
교재 처리 서비스
PDF 파이프라인 실행 및 교재 관련 비즈니스 로직
"""
import sys
import logging
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any

from app.infrastructure.pdf.pipeline import UnifiedPipeline
from app.infrastructure.database.models import Book, ParseStatus, Subject, Curriculum, LearningUnit, Lesson, Unit
from app.infrastructure.database.session import SessionLocal
from app.core.config import settings
from app.services.book_conversion import subject_to_pipeline_subject
from app.services.curriculum_service import create_curriculum_from_pipeline

logger = logging.getLogger(__name__)


def process_pdf_background(book_id: str, pdf_path: Path, subject: str, ai_options: dict = None):
    """백그라운드에서 PDF 파이프라인 실행 (UnifiedPipeline 직접 사용)"""
    # 즉시 출력을 위한 logger 사용
    logger.info(f"[book_service] ========================================")
    logger.info(f"[book_service] [백그라운드] PDF 파이프라인 시작")
    logger.info(f"[book_service] ========================================")
    logger.info(f"[book_service] book_id: {book_id}")
    logger.info(f"[book_service] PDF 경로: {pdf_path}")
    logger.info(f"[book_service] PDF 타입: {type(pdf_path)}")
    logger.info(f"[book_service] PDF 존재 여부: {pdf_path.exists() if pdf_path else 'N/A'}")
    logger.info(f"[book_service] 과목: {subject}")
    sys.stdout.flush()

    # 로거 설정 (즉시 출력)
    logger.setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    
    # 콘솔 핸들러 추가 (이미 있으면 재사용)
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if ai_options is None:
        ai_options = {}

    db = SessionLocal()
    try:
        # Subject enum 변환
        subject_enum = Subject(subject)
        pipeline_subject = subject_to_pipeline_subject(subject_enum)

        # 새 PDF 업로드/재파싱 전 기존 데이터 삭제 (교재별 JSON 파일, 이미지 등)
        # 교재별 디렉토리: data/{subject}/{book_id}/
        book_data_dir = settings.API_DIR / "data" / pipeline_subject / book_id
        
        logger.debug(f"[book_service] ========================================")
        logger.info(f"[book_service] PDF 파이프라인 시작")
        logger.debug(f"[book_service] ========================================")
        logger.debug(f"[book_service] PDF 경로: {pdf_path}")
        logger.debug(f"[book_service] 과목: {pipeline_subject}")
        logger.debug(f"[book_service] 교재 ID: {book_id}")
        logger.debug(f"[book_service] UnifiedPipeline 사용 (processing 모듈)")
        logger.debug(f"[book_service] 교재별 데이터 디렉토리: {book_data_dir}")
        logger.info(f"[book_service] 기존 데이터 삭제 시작 (교재별)")
        sys.stdout.flush()
        
        import shutil
        
        # 1. 캐시 삭제 (과목별)
        cache_dir = settings.DATA_DIR / pipeline_subject / "cache"
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                logger.info(f"[book_service] 캐시 삭제 완료: {cache_dir}")
            except Exception as cache_err:
                logger.warning(f"[book_service] 캐시 삭제 실패 (계속 진행): {cache_err}")
        
        # 2. 교재별 JSON 파일 및 이미지 디렉토리 삭제
        if book_data_dir.exists():
            # 전체 교재 디렉토리 삭제 (교재별 완전 분리)
            try:
                shutil.rmtree(book_data_dir)
                logger.info(f"[book_service] 교재별 데이터 디렉토리 삭제 완료: {book_data_dir}")
            except Exception as err:
                logger.warning(f"[book_service] 교재별 데이터 디렉토리 삭제 실패 (계속 진행): {err}")
        else:
            logger.debug(f"[book_service] 교재별 데이터 디렉토리가 없음 (새 교재): {book_data_dir}")
        
        logger.info(f"[book_service] 기존 데이터 삭제 완료 (교재별)")
        sys.stdout.flush()
        logger.info(f"[book_service] AI 옵션: ML dedup={ai_options.get('enable_ml_deduplication', True)}, "
              f"ML class={ai_options.get('enable_ml_classification', True)}, "
              f"DL layout={ai_options.get('enable_layout_analysis', False)}, "
              f"DL math={ai_options.get('enable_math_recognition', False)}, "
              f"LLM meta={ai_options.get('enable_llm_metadata', False)}, "
              f"LLM expl={ai_options.get('enable_llm_explanations', False)}, "
              f"LLM rec={ai_options.get('enable_llm_recommendations', False)}")
        sys.stdout.flush()

        # PDF 페이지 수 확인 (진행률 표시용)
        try:
            import fitz  # PyMuPDF
            pdf_doc = fitz.open(pdf_path)
            total_pages = len(pdf_doc)
            pdf_doc.close()
            logger.info(f"[book_service] PDF 총 페이지 수: {total_pages}")

            # DB에 총 페이지 수 저장
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if book:
                book.total_pages = total_pages
                book.parse_progress = 5  # 시작 5%
                db.commit()
                logger.info(f"[book_service] 진행률 초기화: 5% (페이지 수: {total_pages})")
        except Exception as e:
            logger.warning(f"[book_service] PDF 페이지 수 확인 실패 (계속 진행): {e}")
            total_pages = 0
        sys.stdout.flush()

        # AI 후처리 활성화 여부 결정 (현재는 ML 후처리 비활성화)
        # enable_ml = (ai_options.get('enable_ml_deduplication', True) or
        #             ai_options.get('enable_ml_classification', True))
        enable_ml = False  # ML 후처리는 아직 비활성화

        # config.json 경로
        config_path = settings.API_DIR / "data" / pipeline_subject / "config.json"
        logger.info(f"[book_service] config.json 경로: {config_path}")
        logger.info(f"[book_service] config.json 존재 여부: {config_path.exists() if config_path else 'N/A'}")
        sys.stdout.flush()

        # 청크 단위 처리 설정 (메모리 효율성)
        BATCH_SIZE = 10  # 10페이지씩 처리
        # 배치 처리는 TOC(목차) 페이지를 각 배치에서 볼 수 없어 강의 추출 실패
        # 전체 PDF를 한 번에 처리해야 TOC에서 강의 목록을 추출 가능
        USE_CHUNKED_PROCESSING = False  # 배치 처리 비활성화 (임시)
        # USE_CHUNKED_PROCESSING = total_pages > 20  # 20페이지 초과 시 청크 처리

        logger.info(f"[book_service] UnifiedPipeline 초기화 중...")
        logger.info(f"[book_service] 청크 단위 처리: {'활성화' if USE_CHUNKED_PROCESSING else '비활성화'} (총 {total_pages}페이지)")

        # 진행률 업데이트: 10%
        book = db.query(Book).filter(Book.book_id == book_id).first()
        if book:
            book.parse_progress = 10
            db.commit()
            logger.info(f"[book_service] 진행률 업데이트: 10% (파이프라인 초기화)")
        sys.stdout.flush()

        if USE_CHUNKED_PROCESSING:
            # 청크 단위 처리: 메모리 효율적
            logger.info(f"[book_service] 청크 단위 처리 시작 (배치 크기: {BATCH_SIZE}페이지)")

            # 배치 개수 계산
            num_batches = (total_pages + BATCH_SIZE - 1) // BATCH_SIZE
            logger.info(f"[book_service] 총 {num_batches}개 배치로 처리")
            sys.stdout.flush()

            all_results = {
                'lectures': [],
                'lecture_contents': [],
                'problems': []
            }

            # 배치별 처리
            for batch_idx in range(num_batches):
                start_page = batch_idx * BATCH_SIZE + 1
                end_page = min((batch_idx + 1) * BATCH_SIZE, total_pages)

                logger.info(f"[book_service] ========================================")
                logger.info(f"[book_service] 배치 {batch_idx + 1}/{num_batches}: 페이지 {start_page}-{end_page}")
                logger.info(f"[book_service] ========================================")
                sys.stdout.flush()

                # 배치 진행률 계산: 20% ~ 70% 구간을 배치별로 분할
                batch_progress_start = 20 + int(50 * batch_idx / num_batches)
                batch_progress_end = 20 + int(50 * (batch_idx + 1) / num_batches)

                # 현재 배치 시작
                book = db.query(Book).filter(Book.book_id == book_id).first()
                if book:
                    book.parse_progress = batch_progress_start
                    book.current_page = start_page
                    db.commit()
                    logger.info(f"[book_service] 진행률 업데이트: {batch_progress_start}% (페이지 {start_page}-{end_page} 처리 중)")
                sys.stdout.flush()

                # 배치별 파이프라인 실행
                try:
                    batch_pipeline = UnifiedPipeline(
                        subject=pipeline_subject,
                        use_ocr="auto",  # 자동 모드: pdfplumber 우선 → 필요 시 OCR
                        config_path=config_path,
                        save_results=False,  # 배치별로는 저장 안 함
                        save_images=True,  # bbox 기반 이미지 크롭 저장
                        book_id=book_id,
                        start_page=start_page,  # 시작 페이지
                        end_page=end_page,  # 종료 페이지
                        dpi=300,  # 고품질 OCR (300 DPI)
                        lang='kor+eng',
                        tesseract_cmd=settings.TESSERACT_CMD,  # 자동 감지된 경로 사용
                        use_parallel=True,
                        max_workers=2,  # 워커 수 제한 (메모리 절약)
                        preprocessing_method='aggressive',  # 강력한 전처리 (품질 향상)
                    )

                    # 배치 처리 (첫 페이지 설정)
                    batch_result = batch_pipeline.process(pdf_path)

                    # 결과 병합
                    all_results['lectures'].extend(batch_result.get('lectures', []))
                    all_results['lecture_contents'].extend(batch_result.get('lecture_contents', []))
                    all_results['problems'].extend(batch_result.get('problems', []))

                    # 배치 완료
                    book = db.query(Book).filter(Book.book_id == book_id).first()
                    if book:
                        book.parse_progress = batch_progress_end
                        book.current_page = end_page
                        db.commit()
                        logger.info(f"[book_service] 배치 {batch_idx + 1}/{num_batches} 완료 ({batch_progress_end}%)")
                    sys.stdout.flush()

                    # 메모리 정리
                    import gc
                    gc.collect()

                except Exception as batch_error:
                    logger.error(f"[book_service] 배치 {batch_idx + 1} 처리 실패: {batch_error}")
                    logger.exception(batch_error)
                    # 실패한 배치는 건너뛰고 계속 진행
                    continue

            result = all_results
            logger.info(f"[book_service] 모든 배치 처리 완료")
            sys.stdout.flush()
        else:
            # 일반 처리: 페이지 수가 적을 때
            pipeline = UnifiedPipeline(
                subject=pipeline_subject,
                use_ocr="auto",  # 자동 모드: pdfplumber 우선 → 필요 시 OCR
                config_path=config_path,
                save_results=True,
                save_images=True,  # bbox 기반 이미지 크롭 저장
                book_id=book_id,
                dpi=300,  # 고품질 OCR (300 DPI)
                lang='kor+eng',
                tesseract_cmd=settings.TESSERACT_CMD,  # 자동 감지된 경로 사용
                use_parallel=True,
                max_workers=2,  # 워커 수 제한
                preprocessing_method='aggressive',  # 강력한 전처리 (품질 향상)
                max_pages=None,
            )

            logger.info(f"[book_service] 파이프라인 설정: DPI=200, 병렬=True (워커 2개), OCR=True")
            logger.info(f"[book_service] PDF 파일 확인: {pdf_path}")
            logger.info(f"[book_service] PDF 파일 존재 여부: {pdf_path.exists() if pdf_path else 'N/A'}")
            if pdf_path and pdf_path.exists():
                logger.info(f"[book_service] PDF 파일 크기: {pdf_path.stat().st_size} bytes")
            sys.stdout.flush()

            try:
                logger.info(f"[book_service] 파이프라인 실행 시작...")

                # 진행률 업데이트: 20%
                book = db.query(Book).filter(Book.book_id == book_id).first()
                if book:
                    book.parse_progress = 20
                    db.commit()
                    logger.info(f"[book_service] 진행률 업데이트: 20% (텍스트 추출 시작)")
                sys.stdout.flush()

                # OCR 진행률 업데이트를 위한 콜백 함수
                def update_ocr_progress(page_num: int, total_pages: int):
                    """OCR 진행 중 진행률 업데이트"""
                    try:
                        # 20% ~ 50% 구간을 OCR 진행률로 사용
                        ocr_progress = 20 + int(30 * page_num / total_pages)
                        book = db.query(Book).filter(Book.book_id == book_id).first()
                        if book:
                            book.parse_progress = min(ocr_progress, 50)
                            book.current_page = page_num
                            db.commit()
                            if page_num % 10 == 0 or page_num == total_pages:  # 10페이지마다 또는 마지막 페이지
                                logger.info(f"[book_service] OCR 진행률: {ocr_progress}% ({page_num}/{total_pages}페이지)")
                                sys.stdout.flush()
                    except Exception as e:
                        logger.warning(f"[book_service] 진행률 업데이트 실패 (계속 진행): {e}")

                # 파이프라인에 진행률 콜백 전달
                pipeline.set_progress_callback(update_ocr_progress)

                result = pipeline.process(pdf_path)

                # 진행률 업데이트: 70%
                book = db.query(Book).filter(Book.book_id == book_id).first()
                if book:
                    book.parse_progress = 70
                    db.commit()
                    logger.info(f"[book_service] 진행률 업데이트: 70% (파이프라인 완료)")

                logger.info(f"[book_service] 파이프라인 실행 완료")
                sys.stdout.flush()
            except FileNotFoundError as e:
                logger.error(f"[book_service] ========================================")
                logger.error(f"[book_service] [에러] PDF 파일을 찾을 수 없습니다")
                logger.error(f"[book_service] ========================================")
                logger.error(f"[book_service] 파일 경로: {pdf_path}")
                logger.error(f"[book_service] 에러 메시지: {e}")
                import traceback
                logger.error(traceback.format_exc())
                logger.error(f"[book_service] ========================================")
                sys.stdout.flush()

                book = db.query(Book).filter(Book.book_id == book_id).first()
                if book:
                    book.parse_status = ParseStatus.FAILED
                    db.commit()
                return
            except Exception as e:
                logger.error(f"[book_service] ========================================")
                logger.error(f"[book_service] [에러] 파이프라인 실행 중 예외 발생")
                logger.error(f"[book_service] ========================================")
                logger.error(f"[book_service] 에러 타입: {type(e).__name__}")
                logger.error(f"[book_service] 에러 메시지: {e}")
                logger.error(f"[book_service] PDF 경로: {pdf_path}")
                import traceback
                logger.error(traceback.format_exc())
                logger.error(f"[book_service] ========================================")
                sys.stdout.flush()

                # 파싱 실패 상태 업데이트
                book = db.query(Book).filter(Book.book_id == book_id).first()
                if book:
                    book.parse_status = ParseStatus.FAILED
                    db.commit()
                return

        # 청크 단위 처리 후 결과 저장
        if USE_CHUNKED_PROCESSING:
            logger.info(f"[book_service] 청크 처리 결과 통합 저장 중...")
            sys.stdout.flush()

            # ResultSaver로 저장
            from app.infrastructure.pdf.result_saver import ResultSaver

            data_dir = settings.API_DIR / "data"
            result_saver = ResultSaver(pipeline_subject, data_dir, book_id=book_id)

            # 기존 데이터 삭제
            result_saver.clear()

            # 통합 결과 저장
            result_saver.save(
                all_results['lectures'],
                all_results['lecture_contents'],
                all_results['problems']
            )
            logger.info(f"[book_service] 청크 처리 결과 저장 완료")
            sys.stdout.flush()
        
        # 파이프라인 결과 확인
        lectures = result.get('lectures', [])
        problems = result.get('problems', [])
        
        logger.info(f"[book_service] 파이프라인 결과: 강의 {len(lectures)}개, 문제 {len(problems)}개")
        logger.info(f"[book_service] PDF 경로: {pdf_path}")
        logger.info(f"[book_service] 과목: {pipeline_subject}")
        sys.stdout.flush()
        
        # 강의가 없으면 파싱 실패로 처리
        if not lectures:
            logger.warning(f"[book_service] ========================================")
            logger.warning(f"[book_service] [경고] 강의를 찾을 수 없습니다. 파싱이 실패했습니다.")
            logger.warning(f"[book_service] ========================================")
            logger.warning(f"[book_service] 가능한 원인:")
            logger.warning(f"  1. PDF에 강의 제목이 없거나 인식되지 않음")
            logger.warning(f"  2. 강의 제목 패턴이 PDF 형식과 맞지 않음")
            logger.warning(f"  3. OCR 품질이 낮아 텍스트 추출 실패")
            logger.warning(f"[book_service] 해결 방법:")
            logger.warning(f"  1. 캐시 삭제: data/{pipeline_subject}/cache/ 폴더 삭제 후 재시도")
            logger.warning(f"  2. 강의 제목 패턴 확인: processing/parsers/literature.py의 lecture_title_patterns 확인")
            logger.warning(f"  3. OCR 품질 확인: Tesseract 한국어 언어팩 설치 확인")
            logger.warning(f"[book_service] ========================================")
            logger.warning(f"[book_service] 상세 디버그 로그는 위의 UnifiedPipeline 출력을 확인하세요.")
            logger.warning(f"[book_service] ========================================")
            sys.stdout.flush()
            
            # 파싱 실패 상태 업데이트
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if book:
                book.parse_status = ParseStatus.FAILED
                db.commit()
            return
        
        # 교재 정보 조회 (커리큘럼 생성 전에 필요)
        book = db.query(Book).filter(Book.book_id == book_id).first()
        if not book:
            logger.warning(f"[book_service] 경고: 교재를 찾을 수 없음: {book_id}")
            return

        # 파이프라인 완료 후 커리큘럼 자동 생성
        # 기존 데이터 삭제 (JSON 파일이 새로 생성되었으므로)
        logger.info(f"[book_service] 기존 데이터 삭제 시작: {book_id}, 과목: {subject_enum}")
        
        # Book의 subject 확인 (데이터 일관성 검증)
        if book.subject != subject_enum:
            logger.warning(f"[book_service] ⚠️ 경고: Book의 과목({book.subject})과 파이프라인 과목({subject_enum})이 일치하지 않음!")
            logger.warning(f"[book_service] Book.subject를 {subject_enum}으로 업데이트합니다.")
            book.subject = subject_enum
            db.commit()
        
        # 1. 기존 커리큘럼 및 LearningUnit 삭제 (book_id + subject로 필터링)
        existing_curricula = db.query(Curriculum).filter(
            Curriculum.book_id == book_id,
            Curriculum.subject == subject_enum  # 과목 필터 추가
        ).all()
        for curriculum in existing_curricula:
            learning_units = db.query(LearningUnit).filter(
                LearningUnit.curriculum_id == curriculum.curriculum_id
            ).all()
            for lu in learning_units:
                db.delete(lu)
            db.delete(curriculum)
            logger.info(f"[book_service]   Curriculum 삭제: {curriculum.curriculum_id} (과목: {curriculum.subject}, LearningUnit {len(learning_units)}개)")
        
        # 2. 기존 Lesson 및 Unit 삭제 (book_id로 필터링 - Book.subject가 이미 검증됨)
        existing_lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
        for lesson in existing_lessons:
            units = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).all()
            for unit in units:
                db.delete(unit)
            db.delete(lesson)
            logger.info(f"[book_service]   Lesson 삭제: {lesson.lesson_id} (Unit {len(units)}개)")
        
        db.commit()
        logger.info(f"[book_service] 기존 데이터 삭제 완료: Curriculum {len(existing_curricula)}개 (과목: {subject_enum}), Lesson {len(existing_lessons)}개")
        sys.stdout.flush()
        
        curriculum_id = None
        try:
            # JSON 파일이 생성되었는지 확인 (최대 3초 대기)
            # 교재별 디렉토리: data/{subject}/{book_id}/
            data_dir = settings.API_DIR / "data" / pipeline_subject / book_id
            lectures_dir = data_dir / "lectures"
            
            import time
            max_wait = 3  # 최대 3초 대기
            wait_interval = 0.5  # 0.5초마다 확인
            waited = 0
            
            lecture_files = []
            while waited < max_wait:
                lecture_files = sorted(lectures_dir.glob("lecture_*.json"))
                lecture_files = [f for f in lecture_files if f.name != "lectures.json"]
                if lecture_files:
                    break
                time.sleep(wait_interval)
                waited += wait_interval
                logger.info(f"[book_service] JSON 파일 대기 중... ({waited:.1f}초)")
                sys.stdout.flush()
            
            if not lecture_files:
                logger.warning(f"[book_service] ⚠️ 경고: JSON 파일이 생성되지 않았습니다. {lectures_dir}")
                logger.warning(f"[book_service] 파이프라인은 완료되었지만 JSON 파일이 없어 DB 동기화를 건너뜁니다.")
                logger.warning(f"[book_service] 디렉토리 내용: {list(lectures_dir.glob('*')) if lectures_dir.exists() else '디렉토리 없음'}")
                sys.stdout.flush()
            else:
                logger.info(f"[book_service] ✅ JSON 파일 확인: {len(lecture_files)}개 발견")
                logger.info(f"[book_service] JSON → DB 동기화 시작...")
                sys.stdout.flush()
                
                curriculum_id = create_curriculum_from_pipeline(
                    book_id=book_id,
                    subject_enum=subject_enum,
                    pipeline_subject=pipeline_subject,
                    title=book.title,
                    db=db
                )
                logger.info(f"[book_service] ✅ 커리큘럼 자동 생성 완료: {curriculum_id}")
                sys.stdout.flush()
                
                # Lesson 개수 확인
                lesson_count = db.query(Lesson).filter(Lesson.book_id == book_id).count()
                unit_count = db.query(Unit).join(Lesson).filter(Lesson.book_id == book_id).count()
                logger.info(f"[book_service] ✅ 프론트엔드 연동 완료: {lesson_count}개 Lesson, {unit_count}개 Unit 생성됨")
                sys.stdout.flush()
                
                # 데이터 검증: Lesson과 Unit이 제대로 생성되었는지 확인
                if lesson_count == 0:
                    logger.warning(f"[book_service] ⚠️ 경고: Lesson이 0개입니다. JSON 파일은 있지만 DB 동기화가 실패했을 수 있습니다.")
                    logger.warning(f"[book_service] 수동 동기화 시도: /books/{book_id}/sync-from-json")
                    sys.stdout.flush()
                elif unit_count == 0:
                    logger.warning(f"[book_service] ⚠️ 경고: Lesson은 {lesson_count}개 있지만 Unit이 0개입니다.")
                    logger.warning(f"[book_service] LearningUnit → Unit 변환이 실패했을 수 있습니다.")
                    # 각 Lesson의 Unit 개수 확인
                    lessons = db.query(Lesson).filter(Lesson.book_id == book_id).all()
                    for lesson in lessons:
                        lesson_unit_count = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).count()
                        logger.warning(f"[book_service]   Lesson {lesson.lesson_id} ({lesson.title}): {lesson_unit_count}개 Unit")
                    sys.stdout.flush()
                else:
                    # Lesson별 Unit 개수 확인 (데이터 일관성 검증)
                    lessons = db.query(Lesson).filter(Lesson.book_id == book_id).order_by(Lesson.index).all()
                    lessons_without_units = []
                    for lesson in lessons:
                        lesson_unit_count = db.query(Unit).filter(Unit.lesson_id == lesson.lesson_id).count()
                        if lesson_unit_count == 0:
                            lessons_without_units.append(lesson.title)
                        logger.debug(f"[book_service]   Lesson {lesson.index} ({lesson.title}): {lesson_unit_count}개 Unit")
                    
                    if lessons_without_units:
                        logger.warning(f"[book_service] ⚠️ 경고: Unit이 없는 Lesson {len(lessons_without_units)}개: {', '.join(lessons_without_units)}")
                        sys.stdout.flush()
        except Exception as e:
            logger.error(f"[book_service] ❌ 커리큘럼 생성 실패 (파이프라인은 성공): {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 예외가 발생해도 파싱은 완료된 것으로 표시 (JSON 파일은 생성됨)
            logger.warning(f"[book_service] ⚠️ JSON 파일은 생성되었으므로 수동 동기화 가능: /books/{book_id}/sync-from-json")
            sys.stdout.flush()

        # 파싱 완료 상태 업데이트
        book.parse_status = ParseStatus.DONE
        book.parse_progress = 100  # 진행률 100%
        db.commit()

        # 최종 Lesson 개수 확인
        final_lesson_count = db.query(Lesson).filter(Lesson.book_id == book_id).count()
        logger.info(f"[book_service] ========================================")
        logger.info(f"[book_service] PDF 파이프라인 완료: {book_id}")
        logger.info(f"[book_service]   - 강의: {len(lectures)}개")
        logger.info(f"[book_service]   - 문제: {len(problems)}개")
        logger.info(f"[book_service]   - 커리큘럼: {curriculum_id}")
        logger.info(f"[book_service]   - Lesson: {final_lesson_count}개 (프론트엔드 연동)")
        logger.info(f"[book_service]   - 진행률: 100%")
        logger.info(f"[book_service] ========================================")
        sys.stdout.flush()
            
    except Exception as e:
        logger.error(f"[book_service] ========================================")
        logger.error(f"[book_service] PDF 파이프라인 전체 실패: {e}")
        logger.error(f"[book_service] ========================================")
        import traceback
        logger.error(traceback.format_exc())
        logger.error(f"[book_service] ========================================")
        sys.stdout.flush()
        
        # 파싱 실패 상태 업데이트
        try:
            book = db.query(Book).filter(Book.book_id == book_id).first()
            if book:
                book.parse_status = ParseStatus.FAILED
                db.commit()
        except Exception as db_error:
            logger.error(f"[book_service] DB 업데이트 실패: {db_error}")
            sys.stdout.flush()
    finally:
        db.close()

# LectureScriptParser (삭제된 모듈 대체용)
try:
    from app.services.lecture_script_parser import LectureScriptParser
except ImportError:
    # lecture_script_parser 모듈이 없는 경우 stub 클래스 제공
    class LectureScriptParser:
        def __init__(self, subject: str = "literature"):
            self.subject = subject
        
        def parse(self, text: str) -> dict:
            raise HTTPException(status_code=501, detail="강의 스크립트 파싱이 지원되지 않습니다.")

