"""
파서 테스트 스크립트 (처음 5페이지만)
"""
import sys
from pathlib import Path
import logging
import json

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 프로젝트 경로 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.parsers import DocumentParser, JSONAssembler
from app.services.text_extractors import PdfplumberExtractor


def test_parser():
    """파서 테스트"""
    print("=" * 70)
    print("수능특강 문학 파서 테스트 (처음 5페이지)")
    print("=" * 70)

    # PDF 경로 (절대 경로 사용)
    project_root = Path(__file__).parent
    pdf_path = project_root.parent / "data" / "literature" / "pdf" / "2026 수능특강_ 문학.pdf"

    if not pdf_path.exists():
        print(f"\n[ERROR] PDF 파일이 없습니다: {pdf_path}")
        return

    print(f"\n[PDF] {pdf_path.name}")

    try:
        # 1. 텍스트 추출 (처음 5페이지만)
        print(f"\n[1/4] 텍스트 추출 중... (pdfplumber)")
        extractor = PdfplumberExtractor()

        # 전체 추출
        all_ocr_data = extractor.extract(pdf_path)

        # 처음 5페이지만 사용
        test_pages = 5
        all_ocr_data = all_ocr_data[:test_pages]

        print(f"   [OK] {len(all_ocr_data)}개 페이지 추출 완료")

        # OCR 데이터 샘플 출력
        if all_ocr_data:
            first_page = all_ocr_data[0]
            texts = first_page.get('text', [])
            non_empty_texts = [t for t in texts if t.strip()]
            print(f"   [STAT] 첫 페이지 단어 수: {len(non_empty_texts)}")
            if non_empty_texts:
                print(f"   [SAMPLE] {non_empty_texts[0][:50]}...")

        # 2. 문서 파싱
        print(f"\n[2/4] 문서 파싱 중...")
        doc_parser = DocumentParser(subject="literature")

        intermediate_doc = doc_parser.parse(
            all_ocr_data=all_ocr_data,
            pdf_path=str(pdf_path),
            ocr_method="pdfplumber"
        )

        print(f"   [OK] 파싱 완료")
        print(f"     - 페이지: {intermediate_doc.metadata.total_pages}개")
        print(f"     - 블록: {intermediate_doc.metadata.total_blocks}개")
        print(f"     - 강의: {len(intermediate_doc.lectures)}개")

        # 3. 중간 구조 저장
        print(f"\n[3/4] 중간 구조 저장 중...")
        output_dir = Path("data/literature/test_output")
        output_dir.mkdir(parents=True, exist_ok=True)

        intermediate_path = output_dir / "intermediate_doc.json"
        doc_parser.save_intermediate(intermediate_doc, intermediate_path)
        print(f"   [OK] 저장: {intermediate_path}")

        # 4. 블록 상세 정보 출력
        print(f"\n[4/4] 파싱 결과 상세:")
        print(f"\n   [PAGES] 페이지별 블록 통계:")

        for page in intermediate_doc.pages:
            print(f"\n   페이지 {page.page_num}:")
            print(f"     총 블록: {page.stats.total_blocks}개")
            print(f"     - 개념(concept): {page.stats.concept_count}개")
            print(f"     - 작품(passage): {page.stats.passage_count}개")
            print(f"     - 문제(question): {page.stats.question_count}개")
            print(f"     - 보기(example): {page.stats.example_count}개")

            # 각 블록 상세
            if page.blocks:
                print(f"\n     블록 상세:")
                for block in page.blocks:
                    try:
                        print(f"       [{block.block_type.value}] {block.block_id}")
                        title = block.metadata.title or '(없음)'
                        # ASCII로 표현 가능한 문자만 출력
                        title = title.encode('ascii', errors='ignore').decode('ascii') or '[한글 제목]'
                        print(f"         제목: {title}")
                        if block.metadata.author:
                            print(f"         작가: [작가명]")
                        if block.metadata.work_title:
                            print(f"         작품: [작품명]")
                        if block.metadata.question_id:
                            print(f"         문제번호: {block.metadata.question_id}")
                        print(f"         신뢰도: {block.metadata.confidence:.2f}")
                        print(f"         줄 수: {len(block.raw_lines)}줄")
                        print()
                    except Exception as e:
                        print(f"         [인코딩 오류]")
                        print()

        # 5. 최종 JSON 생성
        print(f"\n[추가] 최종 JSON 생성 중...")
        assembler = JSONAssembler()

        lectures_dir = output_dir / "lectures"
        problems_dir = output_dir / "problems"

        assembler.save_all(
            doc=intermediate_doc,
            lectures_dir=lectures_dir,
            problems_dir=problems_dir
        )
        print(f"   [OK] 강의 JSON: {lectures_dir}/")
        print(f"   [OK] 문제 JSON: {problems_dir}/")

        # 생성된 파일 목록
        if lectures_dir.exists():
            lecture_files = list(lectures_dir.glob("*.json"))
            print(f"\n   [FILES] 생성된 강의 파일: {len(lecture_files)}개")
            for f in lecture_files[:3]:
                print(f"      - {f.name}")

        if problems_dir.exists():
            problem_files = list(problems_dir.glob("*.json"))
            print(f"\n   [FILES] 생성된 문제 파일: {len(problem_files)}개")
            for f in problem_files[:3]:
                print(f"      - {f.name}")

        # 샘플 강의 JSON 내용 출력
        if intermediate_doc.lectures:
            print(f"\n   [SAMPLE] 샘플 강의 JSON (강의 1):")
            lecture_json = assembler.assemble_lecture_json(intermediate_doc, 1)
            print(f"      제목: {lecture_json.get('title', '')}")
            print(f"      섹션: {len(lecture_json.get('sections', []))}개")
            print(f"      문제: {lecture_json.get('problems', [])}")

            # 첫 섹션
            if lecture_json.get('sections'):
                first_section = lecture_json['sections'][0]
                print(f"\n      첫 섹션:")
                print(f"        제목: {first_section.get('title', '')}")
                print(f"        페이지: {first_section.get('page', '')}")
                content = first_section.get('content', [])
                print(f"        내용: {len(content)}줄")
                if content:
                    print(f"        첫 줄: {content[0][:60]}...")

        print(f"\n" + "=" * 70)
        print("[SUCCESS] 테스트 완료!")
        print("=" * 70)
        print(f"\n[INFO] 중간 구조 파일: {intermediate_path}")
        print(f"[INFO] JSON 출력 디렉토리: {output_dir}")

    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        logger.exception("상세 오류:")


if __name__ == "__main__":
    test_parser()
